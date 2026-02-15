from bisect import bisect_left
from collections import defaultdict
import time
from typing import Callable, Any, Dict
from app.core.config import settings
from app.service.providers import ExecutionStatus


class TaskWrapperMixin:
    async def task_wrapper(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self.uow.session_factory() as session:
            token = self.uow.ctx_session.set(session)
            try:
                return await func(*args, **kwargs)
            finally:
                self.uow.ctx_session.reset(token)


class ProviderStatsMixin:
    _stats: dict[str, dict[str, list]] = defaultdict(lambda: {"latency": [], "availability": []})

    def record_execution(self, provider_name: str, latency: float, status: ExecutionStatus):
        now = time.time()
        is_timeout = status == ExecutionStatus.TIMEOUT
        if not is_timeout:
            self._stats[provider_name]["latency"].append((now, latency))
        self._stats[provider_name]["availability"].append((now, is_timeout))

    def _cleanup(self):
        now = time.time()
        cutoff = now - settings.stats_window_seconds
        for p_name in self._stats:
            for set_name in self._stats[p_name]:
                records = self._stats[p_name][set_name]
                if records and records[0][0] < cutoff:
                    idx_lat = bisect_left(records, cutoff, key=lambda item: item[0])
                    if idx_lat > 0:
                        self._stats[p_name][set_name] = records[idx_lat:]

    @property
    def average_latency(self) -> dict[str, float]:
        self._cleanup()
        result = {}
        for provider, stats in self._stats.items():
            records = stats["latency"]
            if not records:
                result[provider] = 0.0
                continue
            latencies = [r[1] for r in records]
            result[provider] = sum(latencies) / len(latencies)
        return result

    @property
    def timeout_percentage(self) -> dict[str, float]:
        self._cleanup()
        result = {}
        for provider, stats in self._stats.items():
            records = stats["availability"]
            if not records:
                result[provider] = 0.0
                continue
            timeouts = sum(1 for r in records if r[1] is True)
            result[provider] = (timeouts / len(records)) * 100
        return result

