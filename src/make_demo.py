"""Generate fictional fixtures with the SAME output contract as real scoring."""
import json
import numpy as np
import pandas as pd
from .config import ROOT, ANALYSIS_DATE
from .load_data import DataBundle
from .build_features import build_features, account_history


def make_demo(folder=ROOT / "examples"):
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    orders, lines, reviews = [], [], []
    for i in range(12):
        account_id = f"DEMO{i+1:04d}"
        if i < 3:
            dates = [pd.Timestamp('2018-03-01') + pd.Timedelta(days=i*10), pd.Timestamp('2018-05-20')][:i+1]
        else:
            stop = pd.Timestamp(ANALYSIS_DATE) - pd.Timedelta(days=(i-3)*14)
            dates = list(pd.date_range('2017-03-01', stop, freq=f'{12+i}D'))
        for j, date in enumerate(dates):
            order_id = f"fictional-{i+1}-{j+1}"
            value = round(float(rng.uniform(80, 500)) * (1 + i / 5), 2)
            delivered = date + pd.Timedelta(days=7 + (4 if j % 7 == 0 else 0))
            order = {"account_id": account_id, "order_id": order_id, "order_purchase_timestamp": date,
                     "order_day": date, "order_value": value, "city": f"Demo City {['North','East','South'][i%3]}",
                     "state": ["DEMO-N", "DEMO-E", "DEMO-S"][i%3],
                     "order_delivered_customer_date": delivered, "order_estimated_delivery_date": date + pd.Timedelta(days=9)}
            orders.append(order)
            lines.append({"account_id": account_id, "order_id": order_id, "order_date": date,
                          "product_category": f"portfolio_line_{j%3+1}", "price": value})
            reviews.append({"review_id": f"demo-review-{i}-{j}", "order_id": order_id,
                            "review_score": 2 if j % 11 == 0 else 4, "available_at": delivered + pd.Timedelta(days=1)})
    data = DataBundle(pd.DataFrame(orders).sort_values(["order_purchase_timestamp", "order_id"]),
                      pd.DataFrame(lines), pd.DataFrame(reviews), {})
    f = build_features(data, ANALYSIS_DATE)
    probabilities = [.05, .09, .12, .18, .25, .36, .46, .58, .69, .77, .85, .92]
    f["risk_probability"] = probabilities
    f.loc[~f.model_eligible, "risk_probability"] = np.nan
    f["risk_score"] = (f.risk_probability * 100).round(1)
    f["risk_level"] = np.select([~f.model_eligible, f.risk_probability >= .75, f.risk_probability >= .45],
                                ["Insufficient history", "High", "Medium"], default="Low")
    f["model_version"] = "synthetic-demo-v1"
    f["model_name"] = "synthetic_fixture"
    f["target_definition"] = "inactivity_60d"
    f["prediction_horizon_days"] = 60
    f["prediction_status"] = np.where(f.model_eligible, "modelled", "insufficient_history")
    f["data_kind"] = "synthetic"
    f["schema_version"] = "1.0"
    f["current_activity"] = np.where(f.days_since_last_order > 60, "Inactive over 60 days", "Ordered within 60 days")
    f["explanations_json"] = [json.dumps([{"text": f"Fictional example: {r.days_since_last_order} days since last order", "evidence_type": "observed context"},
                                         {"text": "Risk estimate is a fabricated demo value, not a model prediction", "evidence_type": "observed context"}]) for r in f.itertuples()]
    f["top_risk_reason_1"] = [json.loads(s)[0]['text'] for s in f.explanations_json]
    f["top_risk_reason_2"] = "Fabricated demo estimate"
    f["top_risk_reason_3"] = ""
    f.to_csv(folder / "scored_accounts.csv", index=False)
    account_history(data, ANALYSIS_DATE).to_csv(folder / "account_history.csv", index=False)
    days = data.orders[["account_id", "order_day"]].drop_duplicates().sort_values(["account_id", "order_day"])
    days["gap_days"] = days.groupby("account_id").order_day.diff().dt.days
    days.to_csv(folder / "account_gaps.csv", index=False)
    (folder / "model_metadata.json").write_text(json.dumps({"data_kind": "synthetic", "analysis_date": ANALYSIS_DATE,
        "model_version": "synthetic-demo-v1", "schema_version": "1.0", "selected_model": "synthetic_fixture",
        "prediction_horizon_days": 60, "thresholds": {"medium": .45, "high": .75},
        "notice": "All records, histories, probabilities and thresholds are fictional."}, indent=2) + "\n")


if __name__ == "__main__":
    make_demo()
