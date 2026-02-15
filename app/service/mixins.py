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

# TODO переделать, не надо пересоздавать список, проверяем бинарным поиском первое вв удаляем как только поподаем окно времени заканчиваем проверку   сд 
class ProviderStatsMixin:
    _stats: dict[str, dict[str, list]] = defaultdict(lambda: {"latency": [], "availability": []})

    def record_execution(self, provider_name: str, latency: float, status: ExecutionStatus):
        now = time.time()
        is_timeout = status == ExecutionStatus.TIMEOUT
        self._stats[provider_name]["latency"].append((now, latency))
        self._stats[provider_name]["availability"].append((now, is_timeout))
        self._cleanup()

    def _cleanup(self):
        now = time.time()
        window = settings.stats_window_seconds
        for provider in list(self._stats.keys()):
            self._stats[provider]["latency"] = [
                s for s in self._stats[provider]["latency"] if now - s[0] <= window
            ]
            self._stats[provider]["availability"] = [
                s for s in self._stats[provider]["availability"] if now - s[0] <= window
            ]

    @property
    def average_latency(self) -> dict[str, float]:
        self._cleanup(time.time())
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
        self._cleanup(time.time())
        result = {}
        for provider, stats in self._stats.items():
            records = stats["availability"]
            if not records:
                result[provider] = 0.0
                continue
            timeouts = sum(1 for r in records if r[1] is True)
            result[provider] = (timeouts / len(records)) * 100
        return result

    @property
    def request_count(self) -> dict[str, int]:
        self._cleanup(time.time())
        return {provider: len(stats["latency"]) for provider, stats in self._stats.items()}
