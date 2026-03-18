from decimal import Decimal

import pytest

from app.domain.enums import QuoteDirection
from app.service.providers.provider_a import ProviderA
from app.service.providers.provider_b import ProviderB


@pytest.mark.asyncio
async def test_async_cachedmethod_works():
    provider = ProviderA()

    direction = QuoteDirection.ON_RAMP
    pair = "USDT-USD"
    amount_in = Decimal("100")

    # First call
    quote1 = await provider.get_quote(direction=direction, pair=pair, amount_in=amount_in)

    # Second call with the same parameters
    quote2 = await provider.get_quote(direction=direction, pair=pair, amount_in=amount_in)

    # Check that results are identical (including fee_rate, which is generated randomly)
    assert quote1["fee_rate"] == quote2["fee_rate"]
    assert quote1["amount_out"] == quote2["amount_out"]
    assert quote1 == quote2

    # Call with different parameters should give a different result
    quote3 = await provider.get_quote(direction=direction, pair=pair, amount_in=Decimal("200"))
    assert quote3["amount_in"] != quote2["amount_in"]
    assert quote3["amount_in"] != quote1["amount_in"]
    assert quote3 != quote1


async def test_singleton_and_cache_storage():
    # Check singleton and cache commonality between instances of the same provider
    providerA1 = ProviderA()
    providerA2 = ProviderA()
    providerB1 = ProviderB()
    providerB2 = ProviderB()

    # Singleton: instances of the same class should be the same object
    assert providerA1 is providerA2
    assert providerB1 is providerB2
    assert providerA1 is not providerB1

    # Cache: instances of the same class should share the same cache object
    assert id(providerA1._cache) == id(providerA2._cache)
    assert id(providerB1._cache) == id(providerB2._cache)
    # Cache of different providers should be different
    assert id(providerA1._cache) != id(providerB1._cache)
