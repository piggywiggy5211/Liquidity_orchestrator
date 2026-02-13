from datetime import datetime

import httpx
from loguru import logger

from app.core.config import settings
from app.service.dto import (
    QuoteGetDTO,
    QuoteResultDTO,
    OrderCreateDTO,
    OrderDTO,
    OrderExecutionResult,
)
from app.service.enums import OrderStatus, OutboxEventType as OET
from app.service.interfaces import IUnitOfWork
from app.service.models import Order, Quote, Outbox
from app.service.providers import PROVIDERS_LIST, OrderExecutionRequest, ExecutionStatus, IProvider, PROVIDERS_MAP




class LiquidityService:
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    async def create_order(self, data: OrderCreateDTO) -> OrderDTO:
        logger.info(f"Creating order for amount {data.amount} pair {data.pair}")
        commission_amount = data.amount * settings.service_fee
        target_amount_out = data.amount - commission_amount
        order = Order(
            incoming_amount=data.amount,
            outgoing_amount=target_amount_out,
            direction=data.direction,
            pair=data.pair,
            incoming_account=data.incoming_account,
            outgoing_account=data.outgoing_account,
            status=OrderStatus.NEW,
            created_at=datetime.now()
        )
        async with self.uow:
            self.uow.orders.add(order)
            await self.uow.commit()
            return OrderDTO.model_validate(order)

    async def execute_order(self, order_id: int) -> None:
        async with self.uow:
            _, order_dto = await self.uow.orders.get(order_id)

        quotes = await self._fetch_quotes_from_providers(order_dto)
        execute_plan = self._build_execution_plan(quotes)

        for quote in execute_plan:
            request: OrderExecutionRequest = OrderExecutionRequest(
                direction=order_dto.direction,
                pair=order_dto.pair,
                amount=quote.amount_in,
                incoming_account=order_dto.incoming_account,
                outgoing_account=order_dto.outgoing_account,
            )
            provider_cls = PROVIDERS_MAP.get(quote.provider_name)
            try:
                result = await provider_cls().execute(request)
                if result["status"] is ExecutionStatus.SUCCESS:
                    async with self.uow:
                        await self.uow.orders.set_execution_result(
                            OrderExecutionResult(
                                order_id=order_id,
                                status=OrderStatus.COMPLETED,
                                quote_id=quote.id,
                                provider_ref=result["provider_ref"],
                            ),
                        )
                        self.uow.outbox.add(
                            Outbox(
                                order_id=order_id,
                                event_type=OET.ORDER_COMPLETED,
                                payload={},
                            ),
                        )
                        await self.uow.commit()
                        logger.info(f"Order {order_id} successfully completed via {quote.provider_name}")
                        return
                else:
                    async with self.uow:
                        self.uow.outbox.add(
                            Outbox(order_id=order_id, event_type=OET.ORDER_FALLBACK, payload={}),
                        )
                        await self.uow.commit()
                    logger.warning(
                        f"Order {order_id} execution failed via {quote.provider_name} "
                        f"with status {result['status']}. Moving to next provider...",
                    )
            except Exception as e:
                logger.error(f"Error executing order {order_id} via {quote.provider_name}: {e}")

        #############################################################################
        # If we are here, it means no provider succeeded
        async with self.uow:
            await self.uow.orders.set_execution_result(
                OrderExecutionResult(order_id=order_id, status=OrderStatus.FAILED),
            )
            self.uow.outbox.add(
                Outbox(order_id=order_id, event_type=OET.ORDER_FAILED, payload={}),
            )
            await self.uow.commit()
        logger.error(f"Order {order_id} failed after trying all providers")

    async def get_quote(self, data: QuoteGetDTO) -> QuoteResultDTO:
        logger.info(f"calculating quote for pair={data.pair} direction={data.direction}, amount={data.amount}")
        incoming_asset, outgoing_asset, *_ = data.pair.split("-")
        fee_amount = data.amount * settings.service_fee
        outgoing_amount = data.amount - fee_amount

        return QuoteResultDTO(
            incoming_amount=data.amount,
            incoming_asset_code=incoming_asset,
            outgoing_amount=outgoing_amount,
            outgoing_asset_code=outgoing_asset,
            fee_amount=fee_amount,
            fee_asset_code=incoming_asset,
        )

    def _build_execution_plan(self, quotes: list[Quote], ) -> list[Quote]:
        execute_plan = sorted(quotes, key=lambda q: q.amount_fee)
        logger.info(f"built execute plan")  # TODO добавить деталей в лог
        return execute_plan

    async def _fetch_quotes_from_providers(self, order: OrderDTO) -> list[Quote]:
        results = list()
        for provider_cls in PROVIDERS_LIST:
            try:
                res = await self._fetch_provider_quote(order, provider_instance=provider_cls())
                if res is not None:
                    results.append(res)
            except Exception as e:
                logger.error(f"Error fetching quote from {provider_cls.__name__}: {e}")
        return results

    async def _fetch_provider_quote(self, order: OrderDTO, provider_instance: IProvider) -> Quote | None:
        try:
            res = await provider_instance.get_quote(
                direction=order.direction,
                pair=order.pair,
                amount_out=order.outgoing_amount,
            )

            quote = Quote(
                direction=res["direction"],
                pair=res["pair"],
                amount_in=res["amount_in"],
                amount_out=res["amount_out"],
                amount_fee=res["amount_in"] - res["amount_out"],  # TODO поправить на fee_rate  res["fee_rate"]
                provider_name=provider_instance.__class__.__name__,
                valid_until=res["valid_until"],
            )
            async with self.uow:
                self.uow.quotes.add(quote)
                await self.uow.commit()
                logger.info(
                    f"Successfully saved quote id: {quote.id} from {provider_instance.__class__.__name__} for pair {order.pair}",
                )  # TODO добавить данных
                return quote

        except Exception as e:
            logger.error(f"Failed to fetch or save quote from {provider_instance.__class__.__name__}: {e}")
            raise
