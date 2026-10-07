"""Teammate extension point: consume the documented selected-account payload."""
import pandas as pd
from app.act_engine import plan


def recommended_action(account):
    # Synthetic records and insufficient-history accounts have explicit statuses.
    act = plan(account)
    if act is None:
        return {"title": "No matching Act record",
                "message": "No prioritisation export matches this account and snapshot. Review its history before choosing an action.",
                "plan": None}
    rec, info = act["record"], act["lane_info"]
    ranking = f"priority #{int(rec['rank']):,}" if pd.notna(rec.get("rank")) else "unranked · insufficient history"
    title = f"{info['icon']} {info['short']} · {ranking}"
    return {"title": title, "message": info["why"], "plan": act}
