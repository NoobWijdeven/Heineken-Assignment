import copy
import numpy as np
import pandas as pd
import pytest
from src.load_data import load_data, end_of_day
from src.build_features import build_features, account_history
from src.churn_labels import build_labels
from src.train_model import temporal_training_split, train_model
from app.data_access import read_outputs, selected_account_payload
from src.config import ROOT


def test_order_counts_and_value_are_not_line_counts(bundle):
    f = build_features(bundle, "2017-01-31").iloc[0]
    assert f.historical_order_count == 2
    assert f.historical_spend == 80
    assert f.historical_category_count == 2
    assert f.median_order_gap_days == 10
    assert f.account_id == "00123"


def test_purchase_cutoff_includes_end_of_day(bundle):
    f = build_features(bundle, "2017-01-01").iloc[0]
    assert f.historical_order_count == 1
    assert f.historical_spend == 30
    assert f.days_since_last_order == 0
    assert end_of_day("2017-01-01") == pd.Timestamp("2017-01-02")


def test_future_reviews_deliveries_and_joined_scores_are_excluded(bundle):
    f = build_features(bundle, "2017-01-31").iloc[0]
    assert f.review_count == 1
    assert f.latest_review_score == 5
    assert f.observed_delivery_count == 1
    assert f.recent_late_delivery == 1
    changed = copy.deepcopy(bundle)
    changed.lines["review_score"] = 99
    changed.lines["is_late"] = False
    changed.reviews.loc[1, "review_score"] = 5
    changed.orders.loc[1, "order_delivered_customer_date"] = pd.Timestamp("2017-02-20")
    pd.testing.assert_frame_equal(build_features(bundle, "2017-01-31"), build_features(changed, "2017-01-31"))


def test_future_purchases_cannot_change_features(bundle):
    future = copy.deepcopy(bundle)
    row = future.orders.iloc[0].copy()
    row["order_id"] = "future-order"
    row["order_purchase_timestamp"] = pd.Timestamp("2018-01-01")
    row["order_day"] = pd.Timestamp("2018-01-01")
    row["order_value"] = 99999
    future.orders = pd.concat([future.orders, row.to_frame().T], ignore_index=True)
    for c in ["order_purchase_timestamp", "order_day", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        future.orders[c] = pd.to_datetime(future.orders[c])
    pd.testing.assert_frame_equal(build_features(bundle, "2017-01-31"), build_features(future, "2017-01-31"))


def test_missing_evidence_stays_unknown(bundle):
    f = build_features(bundle, "2017-01-01").iloc[0]
    assert pd.isna(f.latest_review_score)
    assert pd.isna(f.late_delivery_rate)
    assert f.review_coverage == 0


def test_new_account_has_no_comparable_previous_window(bundle):
    f = build_features(bundle, "2017-01-31").iloc[0]
    assert pd.isna(f.frequency_change)
    assert pd.isna(f.spend_change)
    assert not f.model_eligible
    assert f.model_confidence == "Low"


def test_zero_activity_months_are_preserved(bundle):
    h = account_history(bundle, "2017-03-31")
    assert h.month.tolist() == ["2017-01", "2017-02", "2017-03"]
    assert h.order_count.tolist() == [2, 0, 0]
    assert h.spend.sum() == 80


def test_label_window_and_right_censoring(bundle):
    f = build_features(bundle, "2017-01-01")
    label = build_labels(bundle, f, "inactivity_60d", observation_end="2017-03-02")
    assert label.label.iloc[0] == 0
    assert label.future_order_count.iloc[0] == 1
    assert label.label_end_date.iloc[0] == pd.Timestamp("2017-03-02")
    assert pd.isna(build_labels(bundle, f, "inactivity_60d", observation_end="2017-03-01").label.iloc[0])
    assert build_labels(bundle, build_features(bundle, "2017-01-31"), "inactivity_60d").label.iloc[0] == 1


def test_multiple_targets_are_implemented(bundle):
    f = build_features(bundle, "2017-01-31")
    for target in ["inactivity_60d", "inactivity_90d", "frequency_decline_60d", "cadence_inactivity"]:
        labels = build_labels(bundle, f, target)
        assert labels.target.iloc[0] == target
        assert labels.label.iloc[0] == 1
    assert build_labels(bundle, f, "cadence_inactivity").label_end_date.iloc[0] == pd.Timestamp("2017-03-02")


def test_ids_and_unique_line_aggregation(raw_dir):
    data = load_data(raw_dir)
    assert data.orders.account_id.iloc[0] == "00123"
    assert data.orders.order_value.iloc[0] == 30
    assert build_features(data, "2017-01-31").review_count.iloc[0] == 0


def test_duplicate_lines_fail_fast(raw_dir):
    p = raw_dir / "order_lines.csv"
    f = pd.read_csv(p, dtype=str)
    pd.concat([f, f.iloc[[0]]]).to_csv(p, index=False)
    with pytest.raises(ValueError, match="Duplicate order-line"):
        load_data(raw_dir)


def test_account_mapping_conflict_fails_fast(raw_dir):
    p = raw_dir / "order_lines.csv"
    f = pd.read_csv(p, dtype=str)
    f.loc[0, "account_id"] = "different"
    f.to_csv(p, index=False)
    with pytest.raises(ValueError, match="keys disagree"):
        load_data(raw_dir)


def test_training_and_calibration_outcomes_are_purged():
    frame = pd.DataFrame({"analysis_date": ["2017-07-31", "2017-08-31", "2017-09-30", "2017-11-30", "2018-01-31"],
                          "label_end_date": pd.to_datetime(["2017-09-29", "2017-10-30", "2017-11-29", "2018-01-29", "2018-04-01"]), "label": [0, 1, 0, 1, 0]})
    fit, cal = temporal_training_split(frame, "2018-02-28")
    assert cal.analysis_date.tolist() == ["2017-11-30"]
    assert fit.label_end_date.max() <= pd.Timestamp(cal.analysis_date.iloc[0])
    assert cal.label_end_date.max() <= pd.Timestamp("2018-02-28")


def test_preprocessing_is_fit_on_training_only():
    fit = pd.DataFrame({"days_since_last_order": np.tile([1, 10, 20, 40], 20),
                        "label": np.tile([0, 0, 1, 1], 20), "analysis_date": "2017-07-31"})
    fit.loc[0, "days_since_last_order"] = np.nan
    cal = pd.DataFrame({"days_since_last_order": [1000, 2000, 3000, 4000], "label": [0, 0, 1, 1], "analysis_date": "2017-11-30"})
    model = train_model("recency_baseline", fit, cal)
    assert model.estimator.named_steps['imputer'].statistics_[0] == fit.days_since_last_order.median()


def test_synthetic_handoff_matches_contract_and_json_nulls():
    a, _, _, meta = read_outputs(ROOT / "examples")
    assert meta['data_kind'] == "synthetic"
    assert a.account_id.is_unique
    payload = selected_account_payload(a[~a.model_eligible].iloc[0])
    assert payload['risk_probability'] is None
    assert isinstance(payload['categories_dropped'], list)
    assert isinstance(payload['explanations'], list)
    assert payload['schema_version'] == "1.0"
    expected = ["risk_probability", "risk_score", "risk_level", "model_confidence", "model_version", "analysis_date",
                "historical_order_count", "active_months", "first_order_date", "last_order_date", "days_since_last_order",
                "median_order_gap_days", "cadence_ratio", "orders_last_30d", "orders_last_60d", "orders_last_90d",
                "frequency_change", "historical_spend", "spend_last_90d", "spend_change", "historical_category_count",
                "recent_category_count", "categories_dropped_count", "categories_dropped", "avg_review_score",
                "latest_review_score", "late_delivery_rate", "recent_late_delivery", "top_risk_reason_1",
                "top_risk_reason_2", "top_risk_reason_3", "current_activity"]
    assert set(expected).issubset(a.columns)
