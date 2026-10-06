from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
MODEL_DIR = ROOT / "models"
ANALYSIS_DATE = "2018-08-31"
MODEL_VERSION = "identify-v1.0"
SEED = 42
MIN_ORDERS = 10
MIN_AGE_DAYS = 180
HORIZON_DAYS = 60
TARGET = "inactivity_60d"
SNAPSHOT_DATES = [
    "2017-05-31", "2017-06-30", "2017-07-31", "2017-08-31",
    "2017-09-30", "2017-10-31", "2017-11-30", "2017-12-31",
    "2018-01-31", "2018-02-28", "2018-03-31", "2018-04-30",
    "2018-05-31", "2018-06-30",
]
DEV_CUTOFFS = ["2018-02-28", "2018-04-30"]
TEST_CUTOFF = "2018-06-30"
# Continuous inputs only: identities, location and eventual status are excluded.
FEATURES = [
    "days_since_last_order", "median_order_gap_days", "cadence_ratio",
    "gap_cv", "last_completed_gap_ratio", "historical_order_count",
    "account_age_days", "active_months", "orders_last_30d", "orders_last_60d",
    "orders_last_90d", "orders_previous_90d", "frequency_change",
    "frequency_change_adjusted", "historical_spend", "avg_order_value",
    "spend_last_90d", "spend_change", "spend_change_adjusted",
    "historical_category_count", "recent_category_count", "categories_dropped_count",
    "category_concentration", "avg_review_score", "latest_review_score",
    "recent_avg_review_score", "review_trend", "negative_review_count",
    "review_coverage", "late_delivery_rate", "recent_late_delivery",
    "avg_days_late", "delivery_coverage", "late_delivery_change",
]
MODELS = ["recency_baseline", "cadence_baseline", "logistic", "random_forest", "gradient_boosting"]
