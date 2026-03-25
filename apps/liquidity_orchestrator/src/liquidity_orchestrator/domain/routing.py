import pandas as pd
from loguru import logger

from liquidity_orchestrator.domain.models import Quote


def build_execution_plan(
    quotes: list[Quote],
    average_latencies: dict[str, float],
    timeout_percentages: dict[str, float],
    order_id: int,
) -> list[Quote]:
    logger.info(f"Building execution plan for order_id {order_id}")
    if not quotes:
        logger.warning(f"No quotes available for order_id {order_id}")
        return []

    # Prepare data for scoring
    data = []
    for q in quotes:
        p_name = q.provider_name
        data.append(
            {
                "quote": q,
                "fee_rate": float(q.fee_rate),
                "latency": average_latencies.get(p_name, 0.0),
                "timeout": timeout_percentages.get(p_name, 0.0),
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
        df["timeout_score"] * timeout_weight + df["fee_score"] * fee_weight + df["latency_score"] * latency_weight
    )

    # Sort by final score descending
    df = df.sort_values("final_score", ascending=False)

    for index, row in df.iterrows():
        logger.info(
            f"Calculated score for quote_id {row['quote'].id},"
            f" provider_name {row['quote'].provider_name},"
            f" final_score {row['final_score']}"
            "("
            f" fee_rate {row['fee_rate']},"
            f" latency {row['latency']},"
            f" timeout {row['timeout']}"
            ")"
        )
    return df["quote"].tolist()
