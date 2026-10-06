"""One account row per cutoff, with event-time filtering before aggregation."""
import json
import numpy as np
import pandas as pd
from .load_data import end_of_day
from .config import MIN_ORDERS, MIN_AGE_DAYS


def _change(new, old):
    return (new / old.where(old > 0) - 1).replace([np.inf, -np.inf], np.nan)


def build_features(data, date):
    T, end = pd.Timestamp(date).normalize(), end_of_day(date)
    o = data.orders[data.orders.order_purchase_timestamp < end].copy()
    o["order_value"] = pd.to_numeric(o.order_value, errors="raise").astype(float)
    if o.empty:
        raise ValueError(f"No purchases on or before {date}")
    g = o.groupby("account_id", sort=True)
    f = g.agg(historical_order_count=("order_id", "nunique"),
              first_order_date=("order_day", "min"), last_order_date=("order_day", "max"),
              historical_spend=("order_value", "sum"), avg_order_value=("order_value", "mean"))
    latest = o.drop_duplicates("account_id", keep="last").set_index("account_id")
    f[["city", "state"]] = latest[["city", "state"]]
    f["account_age_days"] = (T - f.first_order_date).dt.days
    f["days_since_last_order"] = (T - f.last_order_date).dt.days
    o["month"] = o.order_day.dt.to_period("M").astype(str)
    f["active_months"] = o.groupby("account_id").month.nunique()
    f["months_observed"] = ((T.year - f.first_order_date.dt.year) * 12
                            + T.month - f.first_order_date.dt.month + 1)
    f["annualised_value_proxy"] = f.historical_spend / (f.account_age_days + 1) * 365

    # Cadence is on distinct ordering DAYS: simultaneous orders are bursts, not zero-day rhythms.
    days = o[["account_id", "order_day"]].drop_duplicates().sort_values(["account_id", "order_day"])
    days["gap"] = days.groupby("account_id").order_day.diff().dt.days
    gaps = days.groupby("account_id").gap
    f["median_order_gap_days"] = gaps.median()
    f["mean_order_gap_days"] = gaps.mean()
    f["std_order_gap_days"] = gaps.std()
    f["gap_count"] = gaps.count()
    f["gap_cv"] = f.std_order_gap_days / f.mean_order_gap_days
    f["cadence_ratio"] = f.days_since_last_order / f.median_order_gap_days
    last_gaps = days.drop_duplicates("account_id", keep="last").set_index("account_id").gap
    f["last_completed_gap_days"] = last_gaps
    f["last_completed_gap_ratio"] = last_gaps / f.median_order_gap_days
    # nth retains original row indices; construct the account mapping explicitly.
    second_rows = days.groupby("account_id", group_keys=False).tail(2)
    second_rows = second_rows[second_rows.groupby("account_id").order_day.transform("size") == 2]
    second_map = second_rows.drop_duplicates("account_id").set_index("account_id").order_day
    f["days_since_second_last_order"] = (T - second_map).dt.days
    q90 = gaps.quantile(.9)
    f["recency_vs_gap_p90"] = f.days_since_last_order / q90

    for window in [30, 60, 90]:
        recent = o[o.order_day > T - pd.Timedelta(days=window)]
        f[f"orders_last_{window}d"] = recent.groupby("account_id").order_id.nunique().reindex(f.index, fill_value=0)
        f[f"spend_last_{window}d"] = recent.groupby("account_id").order_value.sum().reindex(f.index, fill_value=0)
    current = o[o.order_day > T - pd.Timedelta(days=90)]
    previous = o[(o.order_day > T - pd.Timedelta(days=180)) & (o.order_day <= T - pd.Timedelta(days=90))]
    f["orders_previous_90d"] = previous.groupby("account_id").size().reindex(f.index, fill_value=0)
    f["spend_previous_90d"] = previous.groupby("account_id").order_value.sum().reindex(f.index, fill_value=0)
    f["frequency_change"] = _change(f.orders_last_90d, f.orders_previous_90d)
    f["spend_change"] = _change(f.spend_last_90d, f.spend_previous_90d)
    # A new account has no fully observed previous window; don't label this a decline.
    f.loc[f.account_age_days < 180, ["frequency_change", "spend_change"]] = np.nan
    global_order_ratio = len(current) / max(len(previous), 1)
    global_value_ratio = current.order_value.sum() / max(previous.order_value.sum(), 1)
    f["frequency_change_adjusted"] = (f.frequency_change + 1) / global_order_ratio - 1
    f["spend_change_adjusted"] = (f.spend_change + 1) / global_value_ratio - 1

    lines = data.lines[data.lines.order_id.isin(o.order_id)].copy()
    categories = lines.dropna(subset=["product_category"]).drop_duplicates(["order_id", "product_category"])
    f["historical_category_count"] = categories.groupby("account_id").product_category.nunique().reindex(f.index, fill_value=0)
    rc = categories[categories.order_date > T - pd.Timedelta(days=90)]
    pc = categories[(categories.order_date > T - pd.Timedelta(days=180)) & (categories.order_date <= T - pd.Timedelta(days=90))]
    f["recent_category_count"] = rc.groupby("account_id").product_category.nunique().reindex(f.index, fill_value=0)
    # Repeat categories: at least two DISTINCT orders in the preceding 90-day window.
    regular = pc.groupby(["account_id", "product_category"]).order_id.nunique()
    regular = regular[regular >= 2].reset_index()[["account_id", "product_category"]]
    recent_keys = rc[["account_id", "product_category"]].drop_duplicates()
    dropped = regular.merge(recent_keys, on=["account_id", "product_category"], how="left", indicator=True)
    dropped = dropped[dropped._merge == "left_only"].groupby("account_id").product_category.agg(lambda s: sorted(s))
    f["categories_dropped"] = [json.dumps(dropped.get(a, [])) if f.loc[a, "account_age_days"] >= 180 else "[]" for a in f.index]
    f["categories_dropped_count"] = f.categories_dropped.map(lambda s: len(json.loads(s)))
    concentration = categories.groupby(["account_id", "product_category"]).size()
    f["category_concentration"] = concentration.groupby(level=0).max() / concentration.groupby(level=0).sum()

    delivered = o[o.order_delivered_customer_date.notna() & (o.order_delivered_customer_date < end)].copy()
    delivered["days_late"] = (delivered.order_delivered_customer_date.dt.normalize()
                              - delivered.order_estimated_delivery_date.dt.normalize()).dt.days
    delivered["late"] = delivered.days_late > 0
    dg = delivered.groupby("account_id")
    f["observed_delivery_count"] = dg.size().reindex(f.index, fill_value=0)
    f["late_delivery_rate"] = dg.late.mean()
    f["late_delivery_count"] = dg.late.sum().reindex(f.index, fill_value=0)
    f["avg_days_late"] = dg.days_late.agg(lambda s: s.clip(lower=0).mean())
    f["delivery_coverage"] = f.observed_delivery_count / f.historical_order_count
    dr = delivered[delivered.order_delivered_customer_date >= end - pd.Timedelta(days=90)]
    dp = delivered[(delivered.order_delivered_customer_date >= end - pd.Timedelta(days=180))
                   & (delivered.order_delivered_customer_date < end - pd.Timedelta(days=90))]
    f["recent_late_delivery"] = dr.groupby("account_id").late.sum().reindex(f.index, fill_value=0)
    f["recent_late_delivery_rate"] = dr.groupby("account_id").late.mean()
    f["late_delivery_change"] = f.recent_late_delivery_rate - dp.groupby("account_id").late.mean()

    reviews = data.reviews[(data.reviews.available_at < end) & data.reviews.order_id.isin(o.order_id)]
    reviews = reviews.sort_values(["available_at", "review_id"]).drop_duplicates("order_id", keep="last")
    reviews = reviews.merge(o[["order_id", "account_id"]], on="order_id", validate="one_to_one")
    reviews = reviews.dropna(subset=["review_score"])
    rg = reviews.groupby("account_id")
    f["review_count"] = rg.size().reindex(f.index, fill_value=0)
    f["avg_review_score"] = rg.review_score.mean()
    f["latest_review_score"] = reviews.drop_duplicates("account_id", keep="last").set_index("account_id").review_score
    rr = reviews[reviews.available_at >= end - pd.Timedelta(days=90)]
    rp = reviews[(reviews.available_at >= end - pd.Timedelta(days=180))
                 & (reviews.available_at < end - pd.Timedelta(days=90))]
    f["recent_avg_review_score"] = rr.groupby("account_id").review_score.mean()
    f["review_trend"] = f.recent_avg_review_score - rp.groupby("account_id").review_score.mean()
    f["negative_review_count"] = reviews[reviews.review_score <= 2].groupby("account_id").size().reindex(f.index, fill_value=0)
    f["review_coverage"] = f.review_count / f.historical_order_count
    f["account_segment"] = pd.cut(f.historical_order_count, [0, 1, 4, 9, np.inf], labels=["1 order", "2–4 orders", "5–9 orders", "10+ orders"]).astype(str)
    f["model_eligible"] = ((f.historical_order_count >= MIN_ORDERS) & (f.account_age_days >= MIN_AGE_DAYS) & (f.gap_count >= 3))
    # Evidence-confidence is a documented heuristic, NOT a probability or statistical interval.
    coverage = (f.review_coverage + f.delivery_coverage) / 2
    f["evidence_confidence_score"] = ((f.historical_order_count / 30).clip(upper=1) * .4
                                      + (f.account_age_days / 365).clip(upper=1) * .25
                                      + (f.gap_count / 15).clip(upper=1) * .2 + coverage * .15).round(3)
    f["model_confidence"] = np.select(
        [~f.model_eligible, (f.historical_order_count >= 20) & (f.account_age_days >= 365) & (f.gap_cv <= 1)],
        ["Low", "High"], default="Medium")
    f["analysis_date"] = str(T.date())
    f = f.replace([np.inf, -np.inf], np.nan).reset_index()
    assert f.account_id.is_unique
    assert (f.last_order_date <= T).all()
    return f


def account_history(data, date):
    """Monthly history including zero-activity months, for UI consumption."""
    T = pd.Timestamp(date).normalize()
    o = data.orders[data.orders.order_purchase_timestamp < end_of_day(date)].copy()
    o["month"] = o.order_day.dt.to_period("M").astype(str)
    grouped = o.groupby(["account_id", "month"]).agg(order_count=("order_id", "nunique"), spend=("order_value", "sum"))
    lines = data.lines[data.lines.order_id.isin(o.order_id)].copy()
    lines["month"] = lines.order_date.dt.to_period("M").astype(str)
    grouped["category_count"] = lines.groupby(["account_id", "month"]).product_category.nunique()
    months = pd.period_range(o.order_day.min().to_period("M"), T.to_period("M"), freq="M").astype(str)
    idx = pd.MultiIndex.from_product([sorted(o.account_id.unique()), months], names=["account_id", "month"])
    result = grouped.reindex(idx).fillna(0).reset_index()
    first_month = o.groupby("account_id").month.min()
    result = result[result.month >= result.account_id.map(first_month)]
    return result
