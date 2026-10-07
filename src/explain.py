"""Observed evidence separated from a model's local probability sensitivity."""
import json
import numpy as np
import pandas as pd


def describe(feature, row):
    def pct(value):
        return f"{value:+.0%}" if pd.notna(value) else "unknown"
    phrases = {
        "days_since_last_order": f"Last order was {row.days_since_last_order:.0f} days ago",
        "cadence_ratio": f"Inactivity is {row.cadence_ratio:.1f}× the typical ordering gap",
        "median_order_gap_days": f"Typical ordering gap is {row.median_order_gap_days:.0f} days",
        "frequency_change": f"Orders changed {pct(row.frequency_change)} over comparable 90-day windows",
        "frequency_change_adjusted": f"Order share changed {pct(row.frequency_change_adjusted)} after overall volume adjustment",
        "spend_change": f"Merchandise value changed {pct(row.spend_change)} over comparable 90-day windows",
        "spend_change_adjusted": f"Value share changed {pct(row.spend_change_adjusted)} after overall volume adjustment",
        "categories_dropped_count": f"{row.categories_dropped_count:.0f} previously repeat categories absent in the last 90 days",
        "latest_review_score": f"Latest available review is {row.latest_review_score:.0f}/5",
        "avg_review_score": f"Average available review is {row.avg_review_score:.1f}/5",
        "recent_avg_review_score": f"Recent reviews average {row.recent_avg_review_score:.1f}/5",
        "late_delivery_rate": f"{row.late_delivery_rate:.0%} of observed deliveries were late",
        "recent_late_delivery": f"{row.recent_late_delivery:.0f} late deliveries observed in the last 90 days",
        "historical_order_count": f"{row.historical_order_count:.0f} historical orders",
        "orders_last_30d": f"{row.orders_last_30d:.0f} orders in the last 30 days",
        "orders_last_60d": f"{row.orders_last_60d:.0f} orders in the last 60 days",
        "orders_last_90d": f"{row.orders_last_90d:.0f} orders in the last 90 days",
        "orders_previous_90d": f"{row.orders_previous_90d:.0f} orders in the preceding 90 days",
        "historical_spend": f"Historical merchandise value is {row.historical_spend:,.0f}",
        "spend_last_90d": f"Recent 90-day merchandise value is {row.spend_last_90d:,.0f}",
        "account_age_days": f"Account has {row.account_age_days:.0f} days of observed history",
        "active_months": f"Purchases in {row.active_months:.0f} different months",
        "gap_cv": f"Ordering gap variation is {row.gap_cv:.2f}",
        "last_completed_gap_ratio": f"Last completed gap was {row.last_completed_gap_ratio:.1f}× the historical median",
        "avg_order_value": f"Average merchandise value per order is {row.avg_order_value:,.0f}",
        "historical_category_count": f"{row.historical_category_count:.0f} categories purchased historically",
        "recent_category_count": f"{row.recent_category_count:.0f} categories purchased in the last 90 days",
        "category_concentration": f"Most frequent category represents {row.category_concentration:.0%} of category-order occurrences",
        "review_trend": f"Average review changed by {row.review_trend:+.1f} points",
        "negative_review_count": f"{row.negative_review_count:.0f} available reviews were 2/5 or lower",
        "review_coverage": f"Reviews available for {row.review_coverage:.0%} of orders",
        "avg_days_late": f"Average observed delivery delay is {row.avg_days_late:.1f} days (early arrivals counted as zero)",
        "delivery_coverage": f"Delivery outcomes observed for {row.delivery_coverage:.0%} of orders",
        "late_delivery_change": f"Observed late-delivery rate changed {pct(row.late_delivery_change)}",
    }
    if pd.isna(row.get(feature, np.nan)):
        return f"{feature.replace('_', ' ').capitalize()} evidence is unavailable"
    return phrases.get(feature, feature.replace("_", " ").capitalize())


def explanation_records(features, model, reference_medians):
    eligible = features[features.model_eligible].copy()
    probabilities = model.predict(eligible)
    # Replace one input at a time with its fit-sample median. This is a local sensitivity,
    # not an additive SHAP decomposition and not a causal counterfactual.
    deltas = pd.DataFrame(index=eligible.index)
    for feature in model.features:
        altered = eligible.copy()
        altered[feature] = reference_medians[feature]
        deltas[feature] = probabilities - model.predict(altered)
    rows = []
    for idx, row in features.iterrows():
        learned, supporting = [], []
        if row.model_eligible:
            ranked = deltas.loc[idx].sort_values(ascending=False)
            learned = [{"feature": feature, "text": describe(feature, row),
                        "evidence_type": "model sensitivity", "probability_delta": float(delta)}
                       for feature, delta in ranked.items() if delta > .001][:3]
        checks = [
            (pd.notna(row.cadence_ratio) and row.cadence_ratio > 1, "cadence_ratio"),
            (pd.notna(row.frequency_change) and row.frequency_change < 0, "frequency_change"),
            (pd.notna(row.spend_change) and row.spend_change < 0, "spend_change"),
            (row.categories_dropped_count > 0, "categories_dropped_count"),
            (pd.notna(row.latest_review_score) and row.latest_review_score <= 2, "latest_review_score"),
            (row.recent_late_delivery > 0, "recent_late_delivery"),
        ]
        learned_features = {x["feature"] for x in learned}
        supporting = [{"feature": feature, "text": describe(feature, row), "evidence_type": "observed context"}
                      for condition, feature in checks if condition and feature not in learned_features]
        reasons = learned + supporting
        if not row.model_eligible:
            reasons.insert(0, {"text": "Insufficient established history; no validated probability is assigned", "evidence_type": "coverage limitation"})
        if not reasons:
            reasons = [{"text": "No elevated model sensitivity or decline signal identified", "evidence_type": "observed context"}]
        rows.append({"account_id": row.account_id, "explanations_json": json.dumps(reasons),
                     **{f"top_risk_reason_{i+1}": reasons[i]["text"] if i < len(reasons) else "" for i in range(3)}})
    return pd.DataFrame(rows)
