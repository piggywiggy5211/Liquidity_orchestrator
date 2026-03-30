from unittest.mock import patch

import pytest
from liquidity_orchestrator.domain.enums import ProviderExecutionStatus
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector


@pytest.fixture
def collector():
    return InMemoryMetricsCollector()


def test_metrics_collector_logic(collector):
    collector.record_execution("ProviderA", 0.1, ProviderExecutionStatus.SUCCESS)
    collector.record_execution("ProviderA", 0.2, ProviderExecutionStatus.TIMEOUT)
    collector.record_execution("ProviderB", 0.5, ProviderExecutionStatus.SUCCESS)

    assert collector.average_latency["ProviderA"] == pytest.approx(0.1)
    assert collector.average_latency["ProviderB"] == pytest.approx(0.5)

    assert collector.timeout_percentage["ProviderA"] == 50.0
    assert collector.timeout_percentage["ProviderB"] == 0.0


def test_metrics_collector_moving_window(collector):
    with patch("time.time") as mock_time:
        start_t = 1000.0
        mock_time.return_value = start_t

        collector.record_execution("ProviderA", 0.1, ProviderExecutionStatus.SUCCESS)

        mock_time.return_value = start_t + 30.0
        collector.record_execution("ProviderA", 0.2, ProviderExecutionStatus.SUCCESS)

        mock_time.return_value = start_t + 70.0
        assert collector.average_latency["ProviderA"] == pytest.approx(0.2)
