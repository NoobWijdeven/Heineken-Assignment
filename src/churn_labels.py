import numpy as np
import pandas as pd
from .load_data import end_of_day
from .config import ANALYSIS_DATE


def build_labels(data, features, target, observation_end=ANALYSIS_DATE):
    """Right-censored outcomes remain nullable; no label beyond observation end."""
    T = pd.Timestamp(features.analysis_date.iloc[0])
    f = features.set_index("account_id")
    if target == "inactivity_60d":
        horizon = pd.Series(60, index=f.index)
    elif target == "inactivity_90d":
        horizon = pd.Series(90, index=f.index)
    elif target == "frequency_decline_60d":
        horizon = pd.Series(60, index=f.index)
    elif target == "cadence_inactivity":
        horizon = (f.median_order_gap_days * 2).clip(lower=30, upper=90).apply(np.ceil)
    else:
        raise ValueError(f"Unknown target {target}")
    end = T + pd.to_timedelta(horizon, unit="D")
    start = end_of_day(T)
    future = data.orders[(data.orders.order_purchase_timestamp >= start)
                         & (data.orders.order_purchase_timestamp < end_of_day(observation_end))]
    joined = future[["account_id", "order_day"]].merge(end.rename("label_end_date"), left_on="account_id", right_index=True)
    joined = joined.reset_index(drop=True)
    joined = joined[joined.order_day <= joined.label_end_date]
    count = joined.groupby("account_id").size().reindex(f.index, fill_value=0)
    y = pd.Series(pd.NA, index=f.index, dtype="Int64")
    valid = horizon.notna() & (end <= pd.Timestamp(observation_end))
    if target == "frequency_decline_60d":
        # Comparable 60-day windows and at least two historical purchases.
        valid &= f.orders_last_60d >= 2
        result = (count < .5 * f.orders_last_60d).astype(int)
    else:
        result = (count == 0).astype(int)
    y.loc[valid] = result.loc[valid]
    return pd.DataFrame({"account_id": f.index, "target": target,
                         "label": y.values, "label_end_date": end.values,
                         "future_order_count": count.values})


def compare_definitions(data, snapshots):
    rows = []
    for date in ["2018-02-28", "2018-04-30", "2018-05-31"]:
        features = snapshots[date]
        established = features[features.model_eligible]
        for target in ["inactivity_60d", "inactivity_90d", "frequency_decline_60d", "cadence_inactivity"]:
            labels = build_labels(data, established, target).dropna(subset=["label"])
            joined = established.merge(labels, on="account_id")
            rows.append({"cutoff": date, "comparison_role": "development" if date != "2018-05-31" else "retrospective sensitivity only", "definition": target, "eligible_accounts": len(established),
                         "labelled_accounts": len(labels), "positive_accounts": int(labels.label.sum()),
                         "positive_rate": labels.label.mean(),
                         "median_typical_gap_days": established.median_order_gap_days.median(),
                         "p95_typical_gap_days": established.median_order_gap_days.quantile(.95),
                         "fraction_typical_gap_above_60d": (established.median_order_gap_days > 60).mean(),
                         "positive_median_current_cadence_ratio": joined.loc[joined.label == 1, "cadence_ratio"].median()})
    return pd.DataFrame(rows)
