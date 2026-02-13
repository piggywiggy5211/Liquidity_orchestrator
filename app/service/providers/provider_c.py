from .base import BaseProvider

class ProviderC(BaseProvider):
    fee_min = 0.01
    fee_max = 0.015
    latency_min = 1
    latency_max = 5
    timeout_prob = 0.01
    ref_prefix = "c"
