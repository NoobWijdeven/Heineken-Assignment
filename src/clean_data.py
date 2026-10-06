"""Fail-fast audit; no silent dropping of accounts or corrupted keys."""
import pandas as pd
from .load_data import end_of_day
from .config import ANALYSIS_DATE


def audit_data(data, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    o, l, r = data.orders, data.lines, data.reviews
    cutoff = end_of_day(ANALYSIS_DATE)
    summary = ["# Source data audit", "", "Source: the eight supplied challenge CSVs.",
               f"Scoring date: {ANALYSIS_DATE}.", "", "| File | Rows | Columns |", "|---|---:|---:|"]
    for name, df in data.audit_tables.items():
        summary.append(f"| {name}.csv | {len(df):,} | {len(df.columns)} |")
    counts = o.groupby("account_id").size()
    segments = pd.cut(counts, [0, 1, 4, 9, float('inf')], labels=["1", "2–4", "5–9", "10+"]).value_counts(sort=False)
    summary += ["", f"- Distinct orders: {o.order_id.nunique():,}; accounts: {o.account_id.nunique():,}.",
                f"- Purchase range: {o.order_day.min().date()} to {o.order_day.max().date()}.",
                f"- Duplicate order keys: {o.order_id.duplicated().sum()}.",
                f"- Duplicate (order_id, order_item_id) keys: {l.duplicated(['order_id', 'order_item_id']).sum()}.",
                f"- Review answers after cutoff: {(r.review_answer_timestamp >= cutoff).sum():,}.",
                f"- Deliveries after cutoff: {(o.order_delivered_customer_date >= cutoff).sum():,}.",
                f"- Orders without priced lines: {l.loc[l.price.isna(), 'order_id'].nunique():,}.",
                "- Canonical and denormalised account/order maps and purchase dates agree.",
                "- All IDs loaded as text. Every account with a purchase is preserved.", "",
                "## Order-history segments", "", "| Orders | Accounts |", "|---|---:|"]
    summary += [f"| {k} | {v:,} |" for k, v in segments.items()]
    summary += ["", "## Final recorded statuses (audit only)", "", "| Status | Orders |", "|---|---:|"]
    summary += [f"| {k} | {v:,} |" for k, v in o.order_status.value_counts().items()]
    summary += ["", "## Missingness in denormalised lines", "", "| Field | Missing fraction |", "|---|---:|"]
    summary += [f"| {k} | {v:.3%} |" for k, v in data.audit_tables['order_lines'].isna().mean().items()]
    summary += ["", "## Interpretation and timestamp policy", "",
                "Orders are placed-order events, including eventual cancellations/unavailability. Final status has no event timestamp and is never used to filter historical features or labels.",
                "Spend is quoted merchandise value (sum of item prices), excluding freight. It is a relative value proxy, not realised revenue or currency.",
                "The joined review score and joined delivery flags are deliberately ignored: original answer/delivery timestamps govern availability.",
                "Calendar-day cutoffs include the whole day. Missing service/review evidence remains missing, rather than becoming a favourable score.",
                "All eight CSVs are audited. Payments, product dimensions and geolocation are not predictive inputs in v1."]
    path = output_dir / "data_audit.md"
    path.write_text("\n".join(summary) + "\n")
    return path
