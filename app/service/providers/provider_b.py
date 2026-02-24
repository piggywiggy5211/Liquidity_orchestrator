from .base import BaseProvider


class ProviderB(BaseProvider):
    fee_min = 0.005
    fee_max = 0.01
    latency_min = 10
    latency_max = 30
    timeout_prob = 0.002
    ref_prefix = "b"
