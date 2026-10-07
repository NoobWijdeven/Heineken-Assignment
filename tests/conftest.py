import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.load_data import DataBundle


@pytest.fixture
def bundle():
    # One account, two orders, three product lines: the first order has two items.
    orders = pd.DataFrame({
        "account_id": ["00123", "00123"], "order_id": ["o1", "o2"],
        "order_purchase_timestamp": pd.to_datetime(["2017-01-01 23:59:59", "2017-01-11 12:00:00"]),
        "order_day": pd.to_datetime(["2017-01-01", "2017-01-11"]),
        "order_value": [30., 50.], "city": ["test city"]*2, "state": ["TEST"]*2,
        "order_delivered_customer_date": pd.to_datetime(["2017-01-03", "2017-02-05"]),
        "order_estimated_delivery_date": pd.to_datetime(["2017-01-02", "2017-01-15"]),
    })
    lines = pd.DataFrame({"account_id": ["00123"]*3, "order_id": ["o1", "o1", "o2"],
                          "order_date": pd.to_datetime(["2017-01-01", "2017-01-01", "2017-01-11"]),
                          "product_category": ["c1", "c2", "c1"], "price": [10., 20., 50.],
                          "review_score": [5, 5, 1], "is_late": [True]*3})
    reviews = pd.DataFrame({"review_id": ["r1", "r2"], "order_id": ["o1", "o2"],
                            "review_score": [5, 1], "available_at": pd.to_datetime(["2017-01-04", "2017-02-06"])})
    return DataBundle(orders, lines, reviews, {})


@pytest.fixture
def raw_dir(tmp_path):
    orders = pd.DataFrame({"account_id": ["00123"], "order_id": ["o1"], "customer_id": ["c1"],
                           "order_purchase_timestamp": ["2017-01-01 23:59:59"], "order_status": ["delivered"],
                           "order_delivered_customer_date": ["2017-01-05"], "order_estimated_delivery_date": ["2017-01-07"]})
    lines = pd.DataFrame({"account_id": ["00123"]*2, "order_id": ["o1"]*2, "order_item_id": ["1", "2"],
                          "order_date": ["2017-01-01"]*2, "price": [10, 20], "freight_value": [3, 4],
                          "product_category": ["c1", "c2"], "city": ["test"]*2, "state": ["TEST"]*2})
    reviews = pd.DataFrame({"review_id": ["r1"], "order_id": ["o1"], "review_score": [1],
                            "review_creation_date": ["2017-01-02"], "review_answer_timestamp": ["2017-02-01"]})
    tables = {"orders": orders, "order_lines": lines, "order_reviews": reviews,
              **{n: pd.DataFrame({"placeholder": ["x"]}) for n in ["customers", "products", "order_items", "order_payments", "geolocation"]}}
    for name, frame in tables.items():
        frame.to_csv(tmp_path / f"{name}.csv", index=False)
    return tmp_path
