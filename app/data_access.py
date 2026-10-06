import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def read_outputs(folder):
    folder = Path(folder)
    accounts = pd.read_csv(folder / "scored_accounts.csv", dtype={"account_id": str, "schema_version": str, "model_version": str}, keep_default_na=True)
    if not accounts.account_id.is_unique:
        raise ValueError("Scored accounts must contain unique text account IDs")
    for col in ["top_risk_reason_1", "top_risk_reason_2", "top_risk_reason_3"]:
        accounts[col] = accounts[col].fillna("")
    history = pd.read_csv(folder / "account_history.csv", dtype={"account_id": str}) if (folder / "account_history.csv").exists() else pd.DataFrame()
    gaps = pd.read_csv(folder / "account_gaps.csv", dtype={"account_id": str}) if (folder / "account_gaps.csv").exists() else pd.DataFrame()
    metadata = json.loads((folder / "model_metadata.json").read_text()) if (folder / "model_metadata.json").exists() else {}
    return accounts, history, gaps, metadata


def filter_accounts(accounts, *, search="", levels=(), states=(), confidence=(), min_value=0, min_orders=0):
    out = accounts
    if search:
        text = out.account_id + " " + out.city.fillna("") + " " + out.state.fillna("")
        out = out[text.str.contains(search.strip(), case=False, regex=False)]
    if levels:
        out = out[out.risk_level.isin(levels)]
    if states:
        out = out[out.state.isin(states)]
    if confidence:
        out = out[out.model_confidence.isin(confidence)]
    return out[(out.historical_spend >= min_value) & (out.historical_order_count >= min_orders)]


def selected_account_payload(row):
    """Stable, JSON-safe handoff. Call app.action_layer.recommended_action here later."""
    payload = json.loads(row.to_json(date_format="iso"))
    payload["categories_dropped"] = json.loads(payload.get("categories_dropped") or "[]")
    payload["explanations"] = json.loads(payload.pop("explanations_json", "[]") or "[]")
    return payload
