import importlib
import pkgutil
from functools import cache
from typing import TYPE_CHECKING, Sequence

from .base import BaseProvider, ExecutionStatus, IProvider, OrderExecutionRequest


if TYPE_CHECKING:
    PROVIDERS_LIST: Sequence[type[IProvider]]
    PROVIDERS_MAP: dict[str, type[IProvider]]


def discover_providers():
    """Dynamically imports all modules in the current package to register providers."""
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name.startswith("provider_"):
            importlib.import_module(f".{module_name}", __package__)


@cache
def _get_providers() -> Sequence[type[IProvider]]:
    """Returns all subclasses of BaseProvider."""
    discover_providers()
    return BaseProvider.__subclasses__()


@cache
def _get_providers_map() -> dict[str, type[IProvider]]:
    """Returns a map of provider names to provider classes."""
    return {p.name: p for p in _get_providers()}


def __getattr__(name):
    match name:
        case "PROVIDERS_LIST":
            return _get_providers()
        case "PROVIDERS_MAP":
            return _get_providers_map()
        case _:
            raise AttributeError(f"module {__name__} has no attribute {name}")


# provider_map = {p.__name__: p for p in PROVIDERS}


__all__ = (
    "IProvider",
    "ExecutionStatus",
    "OrderExecutionRequest",
    "PROVIDERS_LIST",
    "PROVIDERS_MAP",
)
