import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from app.service.liquidity_service import LiquidityService
from app.service.dto import QuoteDTO

@pytest.fixture
def service():
    return LiquidityService(uow=MagicMock(), http_client=MagicMock())

def test_scoring_logic_ranking(service):
    # ProviderA: лучший курс, но часто timeout (скажем 20%)
    # ProviderB: средний курс, почти всегда работает
    # ProviderC: хуже курс, но низкая latency
    
    quotes = [
        QuoteDTO(provider_name="ProviderA", fee_rate=Decimal("0.001"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="ProviderB", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="ProviderC", fee_rate=Decimal("0.02"), amount_in=Decimal("100")),
    ]
    
    # Метрики
    # ProviderA: fee=0.001 (min), latency=0.5 (max), timeout=20.0 (max)
    # ProviderB: fee=0.01 (mid), latency=0.5 (max), timeout=0.0 (min)
    # ProviderC: fee=0.02 (max), latency=0.1 (min), timeout=0.0 (min)
    
    mock_latency = {
        "ProviderA": 0.5,
        "ProviderB": 0.5,
        "ProviderC": 0.1
    }
    mock_timeouts = {
        "ProviderA": 20.0,
        "ProviderB": 0.0,
        "ProviderC": 0.0
    }
    
    with patch.object(LiquidityService, "average_latency", new_callable=PropertyMock) as mock_lat, \
         patch.object(LiquidityService, "timeout_percentage", new_callable=PropertyMock) as mock_tout:
        
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts
        
        plan = service._build_execution_plan(quotes)
        
        # Расчет баллов (Weights: fee=0.4, latency=0.1, timeout=0.5):
        # fee_rate score: A:10, B:5.737, C:1
        # latency score: A:1, B:1, C:10
        # timeout score: A:1, B:10, C:10
        
        # ProviderA: 10*0.4 + 1*0.1 + 1*0.5 = 4.0 + 0.1 + 0.5 = 4.6
        # ProviderB: 5.737*0.4 + 1*0.1 + 10*0.5 = 2.295 + 0.1 + 5.0 = 7.395
        # ProviderC: 1*0.4 + 10*0.1 + 10*0.5 = 0.4 + 1.0 + 5.0 = 6.4
        
        # Ожидаемый порядок: ProviderB, ProviderC, ProviderA
        assert plan[0].provider_name == "ProviderB"
        assert plan[1].provider_name == "ProviderC"
        assert plan[2].provider_name == "ProviderA"

def test_scoring_identical_values(service):
    quotes = [
        QuoteDTO(provider_name="P1", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="P2", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
    ]
    
    mock_latency = {"P1": 0.5, "P2": 0.5}
    mock_timeouts = {"P1": 2.0, "P2": 2.0}
    
    with patch.object(LiquidityService, "average_latency", new_callable=PropertyMock) as mock_lat, \
         patch.object(LiquidityService, "timeout_percentage", new_callable=PropertyMock) as mock_tout:
        
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts
        
        plan = service._build_execution_plan(quotes)
        assert len(plan) == 2
        # Когда всё одинаково, порядок не важен
        assert {p.provider_name for p in plan} == {"P1", "P2"}
