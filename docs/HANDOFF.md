# Identify → Act handoff

> **Update:** the Act layer is now built. See [CHANGES_FROM_DEMIAN.md](CHANGES_FROM_DEMIAN.md) for what changed.

## Entry points

Use `examples/scored_accounts.csv` during development. After running the pipeline, switch to `outputs/scored_accounts.csv`; column names remain the same. CSV contains exactly one row per account, with string IDs and schema version `1.0`. Do not infer the account ID or schema version as numeric.

```python
import pandas as pd

accounts = pd.read_csv(
    "outputs/scored_accounts.csv",
    dtype={"account_id": str, "schema_version": str, "model_version": str},
)
modelled = accounts[accounts.prediction_status == "modelled"]
```

In the dashboard, `app.data_access.selected_account_payload(row)` builds a JSON-safe record: missing numeric values become `null`, category lists become native arrays and explanation records become a native `explanations` array. It then calls the teammate-owned `app.action_layer.recommended_action(account)` function. The same JSON is downloadable from the selected-account panel.

```python
def recommended_action(account):
    if account["data_kind"] == "synthetic":
        # Clearly label any proposed action as a demo example.
        pass
    if account["prediction_status"] != "modelled":
        return {"title": "Review account history", "message": "Insufficient evidence for a validated risk estimate."}
    return {"title": "Your next-action card", "message": "Add the action and its rationale here."}
```

Keep risk, evidence confidence, relative value, current inactivity and priority separate. An account can be high-risk but already dormant. Neither probability nor historical value establishes recoverability, causal intervention benefit or urgency. No final priority formula is supplied in Part 1.

## Core fields

| Field | Type / unit | Meaning |
|---|---|---|
| `account_id` | string | Hypothetical account / ZIP-area key; never numeric |
| `city`, `state` | strings | Display/filter location |
| `risk_probability` | nullable float 0–1 | Estimated no-order probability over the next 60 days; null outside coverage |
| `risk_score` | nullable float 0–100 | Probability ×100, rounded to one decimal; not a separate model |
| `risk_level` | string | Low / Medium / High / Insufficient history |
| `model_eligible` | boolean | Meets the documented model-coverage rule |
| `prediction_status` | string | modelled / insufficient_history |
| `current_activity` | string | Ordered within 60 days / Inactive over 60 days, measured at cutoff |
| `model_confidence` | string | High / Medium / Low evidence heuristic, distinct from probability |
| `evidence_confidence_score` | float 0–1 | Illustrative weighted evidence heuristic, not calibrated confidence |
| `historical_order_count` | integer | Distinct placed orders before cutoff |
| `active_months` | integer | Months with at least one placed order |
| `first_order_date`, `last_order_date` | ISO date | Observed purchase dates |
| `days_since_last_order` | integer days | Current inactivity at cutoff |
| `median_order_gap_days` | nullable float days | Median positive gap between distinct order days |
| `cadence_ratio` | nullable float ratio | Inactive days / median gap |
| `orders_last_30d/60d/90d` | integer | Distinct order counts in trailing windows |
| `frequency_change` | nullable float fraction | Recent90 / previous90 −1; `-0.40` is down 40% |
| `historical_spend`, `spend_last_90d` | float relative units | Quoted merchandise-value proxies; exclude freight |
| `spend_change` | nullable float fraction | Recent90 / previous90 −1 |
| `historical_category_count`, `recent_category_count` | integers | Category breadth at cutoff / trailing90 |
| `categories_dropped_count` | integer | Previously repeat categories absent in trailing90 |
| `categories_dropped` | JSON string in CSV; array in JSON | Category names are behavioural portfolio labels |
| `avg_review_score`, `latest_review_score` | nullable floats 1–5 | Only responses available by cutoff |
| `late_delivery_rate` | nullable float fraction | Known late deliveries / known deliveries |
| `recent_late_delivery` | integer | Known late deliveries over the last 90 event-days |
| `top_risk_reason_1/2/3` | strings; empty when absent | Short display reasons |
| `explanations_json` | JSON string in CSV | Detailed reasons, evidence type and local sensitivity when present |
| `explanations` | array, JSON payload only | Parsed detailed reasons; replaces explanations_json in payload |
| `model_version`, `model_name` | strings | Provenance of estimate |
| `analysis_date` | ISO date | 2018-08-31 in v1 |
| `target_definition` | string | inactivity_60d |
| `prediction_horizon_days` | integer | 60 |
| `schema_version` | string | "1.0" |
| `data_kind` | string | challenge / synthetic; never confuse them |

Additional account-profile columns are listed in [SCHEMA.md](SCHEMA.md). Charts consume `account_history.csv` (account/month/order_count/spend/category_count) and `account_gaps.csv` (account/order_day/gap_days). Missing probability, unknown review and unknown delivery rate are deliberately distinct from zero. Empty category lists are valid.

## Explanation semantics

- `model sensitivity`: one input replaced with its training median reduces the model estimate by `probability_delta`; this is neither causal nor additive.
- `observed context`: a descriptive behaviour/service/review observation; it may not be a model input.
- `coverage limitation`: insufficient history for the validated population.

For the selected recency model, review and delivery observations are supporting context, not learned drivers. Do not present them as reasons the model assigned a particular probability.

## Collaboration and delivery

Work in `teammate/action-layer` from this implementation branch, changing `app/action_layer.py` and adding your modules. Coordinate any edits to `app/streamlit_app.py` or schema changes through a PR. Preserve original identifiers and contract fields. A schema change needs a version change, updated example fixtures, documentation and null-safe compatibility handling.

For real analysis, obtain the eight assignment CSVs from the project owner and run the pipeline locally. All source CSVs and full real output tables are ignored in this public repository. Committed `docs/results` contains aggregate measured results; `examples` contains fabricated fixture data. The final public hosted link, 3-minute video, 1-page assignment summary and finished Prioritise/Act stages remain separate submission work.
