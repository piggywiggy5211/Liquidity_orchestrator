import asyncio
import time
from datetime import datetime
from decimal import Decimal

import httpx
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.service.dto import (
    QuoteGetDTO,
    QuoteResultDTO,
    OrderCreateDTO,
    OrderDTO,
    OrderExecutionResult,
    QuoteDTO,
)
from app.service.enums import OrderStatus, OutboxEventType as OET
from app.service.interfaces import IUnitOfWork
from app.service.mixins import TaskWrapperMixin, ProviderStatsMixin
from app.service.models import Order, Quote, Outbox
from app.service.providers import PROVIDERS_LIST, OrderExecutionRequest, ExecutionStatus, IProvider, PROVIDERS_MAP


class LiquidityService(TaskWrapperMixin, ProviderStatsMixin):
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    def validate_sum(self, amount: Decimal) -> bool:
        return amount <= settings.max_order_amount

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
            created_at=datetime.now(),
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
            provider_cls = PROVIDERS_MAP.get(quote.provider_name)
            try:
                request = self._build_provider_request(order_dto, quote)
                response = await self._execute_request_by_provider(provider_cls, request)
                if await self._handle_execution_response(order_id, response, quote):
                    logger.info(f"Order {order_id} successfully completed via {quote.provider_name}")
                    return
                else:
                    logger.info(
                        f"Order {order_id} execution failed via {quote.provider_name} "
                        f" {response=}."
                        f" Moving to next provider...",
                    )
            except Exception as e:
                logger.error(f"Error executing order {order_id} via {quote.provider_name}: {e}")

        logger.error(f"Order {order_id} failed after trying all providers")
        await self._set_order_failure(order_id)

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

    def _build_execution_plan(self, quotes: list[QuoteDTO], ) -> list[QuoteDTO]:
        if not quotes:
            return []

        # Prepare data for scoring
        avg_latencies_by_providers = self.average_latency
        timeout_percentages_by_providers = self.timeout_percentage

        data = []
        for q in quotes:
            p_name = q.provider_name
            data.append(
                {
                    "quote": q,
                    "fee_rate": float(q.fee_rate),
                    "latency": avg_latencies_by_providers.get(p_name, 0.0),
                    "timeout": timeout_percentages_by_providers.get(p_name, 0.0),
                },
            )

        df = pd.DataFrame(data)

        def interpolate_score(series):
            if series.max() == series.min():
                return 10.0
            # Linear interpolation: min -> 10, max -> 1 (lower is better for all our metrics)
            min_score = 10.0
            max_score = 1.0
            return min_score + (max_score - min_score) * (series - series.min()) / (series.max() - series.min())

        df["fee_score"] = interpolate_score(df["fee_rate"])
        df["latency_score"] = interpolate_score(df["latency"])
        df["timeout_score"] = interpolate_score(df["timeout"])

        timeout_weight = 0.5
        fee_weight = 0.4
        latency_weight = 0.1

        df["final_score"] = (
                df["timeout_score"] * timeout_weight +
                df["fee_score"] * fee_weight +
                df["latency_score"] * latency_weight
        )

        # Sort by final score descending
        df = df.sort_values("final_score", ascending=False)

        logger.info(f"Built execution plan with scores:\n{df[['fee_rate', 'latency', 'timeout', 'final_score']]}")
        return df["quote"].tolist()

    async def _fetch_quotes_from_providers(self, order: OrderDTO) -> list[QuoteDTO]:
        tasks = [
            asyncio.create_task(
                self.task_wrapper(
                    self._fetch_provider_quote, order, provider_instance=provider_cls(),
                ),
            )
            for provider_cls in PROVIDERS_LIST
        ]
        results = list()
        async for t in asyncio.as_completed(tasks):
            if t.exception() is None and t.result() is not None:
                results.append(await t)
        return results

    async def _fetch_provider_quote(self, order: OrderDTO, provider_instance: IProvider) -> QuoteDTO | None:
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
            async with self.uow:
                self.uow.quotes.add(quote)
                await self.uow.commit()
                logger.info(
                    f"Successfully saved quote id: {quote.id} from {provider_instance.__class__.__name__} for pair {order.pair}",
                )  # TODO add data
                return QuoteDTO.model_validate(quote)

        except Exception as e:
            logger.error(f"Failed to fetch or save quote from {provider_instance.__class__.__name__}: {e}")
            raise

    def _build_provider_request(self, order_dto: OrderDTO, quote: QuoteDTO) -> OrderExecutionRequest:
        return OrderExecutionRequest(
            direction=order_dto.direction,
            pair=order_dto.pair,
            amount=quote.amount_in,
            incoming_account=order_dto.incoming_account,
            outgoing_account=order_dto.outgoing_account,
        )

    async def _execute_request_by_provider(self, provider_cls, request):
        start_time = time.perf_counter()
        response = await provider_cls().execute(request)
        latency = time.perf_counter() - start_time
        self.record_execution(provider_cls.__name__, latency, response["status"])
        return response

    async def _handle_execution_response(self, order_id: int, response: dict, quote: QuoteDTO) -> bool:
        if response["status"] is ExecutionStatus.SUCCESS:
            order_update_data = OrderExecutionResult(
                order_id=order_id,
                status=OrderStatus.COMPLETED,
                quote_id=quote.id,
                provider_ref=response["provider_ref"],
            )
            outbox_record = Outbox(
                order_id=order_id,
                event_type=OET.ORDER_COMPLETED,
                payload={},
            )
            async with self.uow:
                await self.uow.orders.set_execution_result(order_update_data)
                self.uow.outbox.add(outbox_record)
                await self.uow.commit()
                return True
        else:
            outbox_record = Outbox(order_id=order_id, event_type=OET.ORDER_FALLBACK, payload={})
            async with self.uow:
                self.uow.outbox.add(outbox_record)
                await self.uow.commit()
        return False

    async def _set_order_failure(self, order_id: int) -> None:
        async with self.uow:
            await self.uow.orders.set_execution_result(
                OrderExecutionResult(order_id=order_id, status=OrderStatus.FAILED),
            )
            self.uow.outbox.add(
                Outbox(order_id=order_id, event_type=OET.ORDER_FAILED, payload={}),
            )
            await self.uow.commit()
