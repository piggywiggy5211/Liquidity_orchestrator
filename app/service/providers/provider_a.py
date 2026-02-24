from .base import BaseProvider


class ProviderA(BaseProvider):
    fee_min = 0.002
    fee_max = 0.005
    latency_min = 30
    latency_max = 50
    timeout_prob = 0.2
    ref_prefix = "a"
