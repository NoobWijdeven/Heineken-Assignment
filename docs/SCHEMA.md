# Complete CSV schema v1.0

Canonical columns produced by the completed pipeline. Dates are ISO dates; change fields are fractions, not percentages. Fields ending in ratio/coverage/rate can be missing when evidence is unavailable. Account IDs and version fields must be loaded as strings.

| Column | Storage type |
|---|---|
| `account_id` | string |
| `historical_order_count` | number |
| `first_order_date` | string |
| `last_order_date` | string |
| `historical_spend` | number |
| `avg_order_value` | number |
| `city` | string |
| `state` | string |
| `account_age_days` | number |
| `days_since_last_order` | number |
| `active_months` | number |
| `months_observed` | number |
| `annualised_value_proxy` | number |
| `median_order_gap_days` | number (nullable) |
| `mean_order_gap_days` | number (nullable) |
| `std_order_gap_days` | number (nullable) |
| `gap_count` | number |
| `gap_cv` | number (nullable) |
| `cadence_ratio` | number (nullable) |
| `last_completed_gap_days` | number (nullable) |
| `last_completed_gap_ratio` | number (nullable) |
| `days_since_second_last_order` | number (nullable) |
| `recency_vs_gap_p90` | number (nullable) |
| `orders_last_30d` | number |
| `spend_last_30d` | number |
| `orders_last_60d` | number |
| `spend_last_60d` | number |
| `orders_last_90d` | number |
| `spend_last_90d` | number |
| `orders_previous_90d` | number |
| `spend_previous_90d` | number |
| `frequency_change` | number (nullable) |
| `spend_change` | number (nullable) |
| `frequency_change_adjusted` | number (nullable) |
| `spend_change_adjusted` | number (nullable) |
| `historical_category_count` | number |
| `recent_category_count` | number |
| `categories_dropped` | string |
| `categories_dropped_count` | number |
| `category_concentration` | number (nullable) |
| `observed_delivery_count` | number |
| `late_delivery_rate` | number (nullable) |
| `late_delivery_count` | number |
| `avg_days_late` | number (nullable) |
| `delivery_coverage` | number |
| `recent_late_delivery` | number |
| `recent_late_delivery_rate` | number (nullable) |
| `late_delivery_change` | number (nullable) |
| `review_count` | number |
| `avg_review_score` | number (nullable) |
| `latest_review_score` | number (nullable) |
| `recent_avg_review_score` | number (nullable) |
| `review_trend` | number (nullable) |
| `negative_review_count` | number |
| `review_coverage` | number |
| `account_segment` | string |
| `model_eligible` | boolean |
| `evidence_confidence_score` | number |
| `model_confidence` | string |
| `analysis_date` | string |
| `risk_probability` | number (nullable) |
| `risk_score` | number (nullable) |
| `risk_level` | number |
| `explanations_json` | string |
| `top_risk_reason_1` | string |
| `top_risk_reason_2` | string |
| `top_risk_reason_3` | string |
| `model_version` | string |
| `model_name` | string |
| `target_definition` | string |
| `prediction_horizon_days` | number |
| `prediction_status` | string |
| `data_kind` | string |
| `schema_version` | string |
| `current_activity` | string |
