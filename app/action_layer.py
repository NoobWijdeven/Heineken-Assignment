"""Teammate extension point: consume the documented selected-account payload."""
from app.act_engine import plan


def recommended_action(account):
    # Synthetic records and insufficient-history accounts have explicit statuses.
    act = plan(account)
    if act is None:
        return {"title": "No action this week",
                "message": "Fewer than 3 orders or no Ritmo priority record: too little rhythm to act on yet.",
                "plan": None}
    rec, info = act["record"], act["lane_info"]
    title = f"{info['icon']} {info['short']} · priority #{int(rec['rank']):,}"
    if account.get("data_kind") == "synthetic":
        title += " (demo example)"
    return {"title": title, "message": info["why"], "plan": act}
