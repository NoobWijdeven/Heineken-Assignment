from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from .config import DATA_DIR


@dataclass
class DataBundle:
    orders: pd.DataFrame
    lines: pd.DataFrame
    reviews: pd.DataFrame
    audit_tables: dict


def end_of_day(date):
    """Exclusive upper boundary: include every event on the supplied date."""
    return pd.Timestamp(date).normalize() + pd.Timedelta(days=1)


def load_data(data_dir: Path = DATA_DIR) -> DataBundle:
    required = ["order_lines", "orders", "customers", "order_items", "order_payments",
                "order_reviews", "products", "geolocation"]
    missing = [f"{n}.csv" for n in required if not (data_dir / f"{n}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Put all eight challenge CSVs in {data_dir}. Missing: {', '.join(missing)}")
    # Read identifiers as strings before any inference can drop leading zeros.
    tables = {n: pd.read_csv(data_dir / f"{n}.csv", dtype=str) for n in required}
    orders = tables["orders"].copy()
    lines = tables["order_lines"].copy()
    reviews = tables["order_reviews"].copy()
    expected = {"account_id", "order_id", "order_date", "order_item_id", "price", "product_category"}
    if not expected.issubset(lines.columns):
        raise ValueError(f"order_lines.csv is missing {sorted(expected - set(lines.columns))}")
    if orders.order_id.duplicated().any():
        raise ValueError("orders.csv must contain exactly one row per order_id")
    if orders[["account_id", "order_id"]].isna().any().any():
        raise ValueError("Orders have missing account/order keys")
    if lines.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("Duplicate order-line keys: resolve before computing merchandise value")
    # Check the denormalised table against the canonical order/account map.
    check = lines[["order_id", "account_id"]].merge(
        orders[["order_id", "account_id"]], on="order_id", how="left",
        suffixes=("_line", "_order"), validate="many_to_one")
    if check.account_id_order.isna().any() or (check.account_id_line != check.account_id_order).any():
        raise ValueError("Account/order keys disagree between orders and order_lines")
    if set(lines.order_id) != set(orders.order_id):
        raise ValueError("order_lines and orders do not cover the same orders")
    for col in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")
    if orders.order_purchase_timestamp.isna().any():
        raise ValueError("Missing/invalid purchase timestamps")
    orders["order_day"] = orders.order_purchase_timestamp.dt.normalize()
    lines["order_date"] = pd.to_datetime(lines.order_date, errors="raise")
    if not lines.order_date.eq(lines.order_id.map(orders.set_index("order_id").order_day)).all():
        raise ValueError("order_lines.order_date disagrees with canonical purchase date")
    lines["price"] = pd.to_numeric(lines.price, errors="coerce")
    lines["freight_value"] = pd.to_numeric(lines.freight_value, errors="coerce")
    # Categories and quoted line prices are treated as purchase-time attributes.
    values = lines.groupby("order_id").price.sum(min_count=1).fillna(0)
    orders["order_value"] = orders.order_id.map(values)
    location = lines.drop_duplicates("order_id").set_index("order_id")[["city", "state"]]
    orders = orders.join(location, on="order_id")
    for col in ["review_creation_date", "review_answer_timestamp"]:
        reviews[col] = pd.to_datetime(reviews[col], errors="coerce")
    reviews["review_score"] = pd.to_numeric(reviews.review_score, errors="coerce")
    # A score isn't known when the questionnaire is created; require its answer time.
    reviews["available_at"] = reviews[["review_creation_date", "review_answer_timestamp"]].max(axis=1)
    reviews.loc[reviews.review_answer_timestamp.isna(), "available_at"] = pd.NaT
    return DataBundle(orders.sort_values(["order_purchase_timestamp", "order_id"]), lines, reviews, tables)
