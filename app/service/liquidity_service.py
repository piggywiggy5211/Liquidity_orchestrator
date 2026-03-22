import asyncio
import time

import httpx
from loguru import logger

from app.core.config import settings
from app.domain.enums import OrderStatus
from app.domain.enums import OutboxEventType as OET
from app.domain.interfaces import IUnitOfWork
from app.domain.models import Order, Outbox, Quote
from app.domain.routing import build_execution_plan
from app.service.dto import (
    OrderCreateDTO,
    OrderDTO,
    QuoteRequestDTO,
    QuoteResultDTO,
)
from app.service.mixins import ProviderStatsMixin
from app.service.providers import PROVIDERS_LIST, PROVIDERS_MAP, ExecutionStatus, IProvider, OrderExecutionRequest


class LiquidityService(ProviderStatsMixin):
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    async def create_order(self, data: OrderCreateDTO) -> OrderDTO:
        order = Order.create(
            amount=data.amount,
            direction=data.direction,
            pair=data.pair,
            incoming_account=data.incoming_account,
            outgoing_account=data.outgoing_account,
            commission_rate=settings.service_fee,
        )
        async with self.uow as u:
            u.orders.add(order)
            await u.commit()
            logger.info(f"Order created with id: {order.id}")
            return OrderDTO.model_validate(order)

    async def get_order(self, order_id: int) -> OrderDTO | None:
        """
        Retrieves an order by its ID from the database and returns it as a DTO.
        """
        async with self.uow as u:
            order_model = await u.orders.get(order_id)
            return OrderDTO.model_validate(order_model) if order_model else None

    async def execute_order(self, order_id: int) -> None:
        """
        Executes an order by fetching provider quotes, building an execution plan,
        and attempting execution with providers sequentially until successful.
        """
        logger.info(f"Executing order_id {order_id}")
        async with self.uow as u:
            order_model = await u.orders.get(order_id)
            if not order_model:
                logger.error(f"Order {order_id} not found")
                return
            order_model.status = OrderStatus.PROCESSING
            await u.commit()
            order_dto = OrderDTO.model_validate(order_model)

        logger.info(f"Changed order_id {order_dto.id} status to {order_dto.status}")
        quotes = await self._fetch_quotes_from_providers(order_dto)
        execute_plan = build_execution_plan(
            quotes=quotes,
            average_latencies=self.average_latency,
            timeout_percentages=self.timeout_percentage,
            order_id=order_id,
        )

        for quote in execute_plan:
            provider_cls = PROVIDERS_MAP.get(quote.provider_name)
            try:
                request = self._build_provider_request(order_dto, quote)
                response = await self._execute_request_by_provider(provider_cls, request)
                if await self._handle_execution_response(order_id, response, quote):
                    logger.info(f"Order {order_id} successfully completed via {quote.provider_name}")
                    return
                else:
                    logger.warning(
                        f"Order {order_id} execution failed via {quote.provider_name} "
                        f" {response=}."
                        f" Moving to next provider...",
                    )
            except Exception as e:
                logger.warning(f"Error executing order {order_id} via {quote.provider_name}: {e}")

        logger.warning(f"Order {order_id} failed after trying all providers")
        await self._set_order_failure(order_id)

    async def get_quote(self, data: QuoteRequestDTO) -> QuoteResultDTO:
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

    async def _fetch_quotes_from_providers(self, order: OrderDTO) -> list[Quote]:
        logger.info(f"Fetching quotes for order {order.id}")
        tasks = [
            asyncio.create_task(
                self.uow.switch_session_context_for_task(
                    self._fetch_provider_quote, order, provider_instance=provider_cls()
                ),
            )
            for provider_cls in PROVIDERS_LIST
        ]
        results = list()
        async for t in asyncio.as_completed(tasks):
            if t.exception() is None and t.result() is not None:
                results.append(await t)
        logger.info(f"Fetched {len(results)} quotes for order_id {order.id}")
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
                fee_rate=res["fee_rate"],
                provider_name=provider_instance.__class__.__name__,
                valid_until=res["valid_until"],
            )
            async with self.uow as u:
                u.quotes.add(quote)
                await u.commit()
                logger.info(
                    f"Successfully saved quote id: {quote.id} from {provider_instance.__class__.__name__}"
                    f" for order_id {order.id}",
                )
                return quote

        except Exception as e:
            logger.warning(
                f"Failed to fetch or save quote from {provider_instance.__class__.__name__}"
                f" for order_id {order.id}: {e}",
            )
            raise

    def _build_provider_request(self, order_dto: OrderDTO, quote: Quote) -> OrderExecutionRequest:
        return OrderExecutionRequest(
            direction=order_dto.direction,
            pair=order_dto.pair,
            amount=quote.amount_in,
            incoming_account=order_dto.incoming_account,
            outgoing_account=order_dto.outgoing_account,
        )

    async def _execute_request_by_provider(self, provider_cls, request):
        start_time = time.perf_counter()  # TODO ПОПРАВИТЬ
        logger.info(f"Send request for provider {provider_cls.__name__}")
        response = await provider_cls().execute(request)
        latency = time.perf_counter() - start_time
        self._record_execution(provider_cls.__name__, latency, response["status"])
        return response

    async def _handle_execution_response(self, order_id: int, response: dict, quote: Quote) -> bool:
        if response["status"] is ExecutionStatus.SUCCESS:
            order_update_data = {
                "status": OrderStatus.COMPLETED,
                "quote_id": str(quote.id) if quote.id else None,
                "provider_ref": response["provider_ref"],
            }
            outbox_record = Outbox(
                order_id=order_id,
                event_type=OET.ORDER_COMPLETED,
                payload={
                    "order_id": order_id,
                    "status": OrderStatus.COMPLETED.value,
                    "quote_id": quote.id,
                    "provider_ref": response["provider_ref"],
                    "provider_name": quote.provider_name,
                    "amount_in": float(quote.amount_in) if quote.amount_in else None,
                    "amount_out": float(quote.amount_out) if quote.amount_out else None,
                },
            )
            async with self.uow as u:
                await u.orders.update(order_id, **order_update_data)
                u.outbox.add(outbox_record)
                await u.commit()
                return True
        else:
            outbox_record = Outbox(
                order_id=order_id,
                event_type=OET.ORDER_FALLBACK,
                payload={
                    "order_id": order_id,
                    "status": response["status"].value,
                    "quote_id": quote.id,
                    "provider_name": quote.provider_name,
                },
            )
            async with self.uow as u:
                u.outbox.add(outbox_record)
                await u.commit()
        return False

    async def _set_order_failure(self, order_id: int) -> None:
        async with self.uow as u:
            await u.orders.update(order_id, status=OrderStatus.FAILED)
            u.outbox.add(
                Outbox(
                    order_id=order_id,
                    event_type=OET.ORDER_FAILED,
                    payload={
                        "order_id": order_id,
                        "status": OrderStatus.FAILED.value,
                    },
                ),
            )
            await u.commit()
