"""Act layer: turns a flagged account into a channel, an offer and ready-made words.

Reads the Ritmo prioritisation outputs (Part 2) and combines them with the
Identify payload (Part 1). Nothing is re-scored here.
"""
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACT_DIR = Path(os.environ.get("ACT_DATA_DIR", ROOT / "demo_data" / "ritmo"))

LANES = {
    "A: Rep visit": {"short": "Rep visit", "icon": "🚗", "colour": "#00834D",
                     "why": "Rep visit proposed by the supplied priority export. Confirm the account evidence before the visit."},
    "B: AI call": {"short": "AI call", "icon": "📞", "colour": "#2F6FB3",
                   "why": "Proposed AI call: ask what changed and request rep follow-up when appropriate."},
    "C: WhatsApp nudge": {"short": "WhatsApp nudge", "icon": "💬", "colour": "#C77700",
                          "why": "WhatsApp draft proposed by the supplied priority export. Sending and replies are simulated."},
    "Monitor": {"short": "Monitor", "icon": "👁", "colour": "#7A857E",
                "why": "No contact scheduled in this exported priority list. Review the account evidence before acting."},
}

REASON_OPTIONS = ["Price", "Switched to a competitor", "Closed or quiet season", "Delivery or service problem",
                  "Just forgot / no need yet", "Other"]


def pretty(category):
    """Stable neutral portfolio labels; marketplace categories are not beer products."""
    if not isinstance(category, str) or not category:
        return ""
    labels = portfolio_labels()
    return ", ".join(labels.get(c.strip(), "Portfolio line (unmapped)") for c in category.split(",") if c.strip())


@lru_cache(maxsize=1)
def portfolio_labels():
    records = load_priority()
    if records.empty:
        return {}
    codes = {c.strip() for value in records.top_categories for c in value.split(",") if c.strip()}
    codes.update(c for c in records.dropped_category if c)
    return {code: f"Portfolio line {i:02d}" for i, code in enumerate(sorted(codes), 1)}


@lru_cache(maxsize=1)
def load_priority():
    path = ACT_DIR / "priority_list.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype={"account_id": str})
    if not df.account_id.is_unique:
        raise ValueError("Ritmo priority records must have unique account IDs")
    for col in ["why_now", "reason_1", "reason_2", "reason_3", "talking_point", "dropped_category", "top_categories", "route"]:
        df[col] = df[col].fillna("")
    return df.set_index("account_id", drop=False)


@lru_cache(maxsize=1)
def load_routes():
    path = ACT_DIR / "lane_a_routes.csv"
    return pd.read_csv(path, dtype={"account_id": str}) if path.exists() else pd.DataFrame()


def ritmo_record(account_id):
    df = load_priority()
    if df.empty or account_id not in df.index:
        return None
    return df.loc[account_id].to_dict()


def build_offer(rec):
    top = [c.strip() for c in rec.get("top_categories", "").split(",") if c.strip()]
    usual = pretty(top[0]) if top else "the usual portfolio"
    dropped = pretty(rec.get("dropped_category"))
    if dropped:
        if top and pretty(top[0]) == dropped:
            usual = pretty(top[1]) if len(top) > 1 else "the usual portfolio"
        return {"headline": f"Win-back bundle: {dropped} back in the next order",
                "detail": f"10% off {dropped} when added to their usual {usual} order.",
                "pt": f"10% de desconto em {dropped} no seu próximo pedido junto com {usual}".replace("Portfolio line", "Linha do portfólio"),
                "requires_approval": True}
    return {"headline": f"Restock reminder: {usual}",
            "detail": f"Free delivery on the next {usual} order this week.",
            "pt": f"frete grátis no seu próximo pedido de {usual}".replace("Portfolio line", "Linha do portfólio"), "requires_approval": True}


def _reasons(rec):
    if "identify_reasons" in rec:
        return rec["identify_reasons"]
    reasons = [r for r in (rec.get("reason_1"), rec.get("reason_2"), rec.get("reason_3")) if r]
    if not reasons and pd.isna(rec.get("rank")):
        reasons = [f"{int(rec['orders'])} historical orders; no modelled risk or priority"]
    return reasons


def contact_context(rec):
    """Describe observed activity, without diagnosing churn or recoverability."""
    days = rec.get("days_since_last_order")
    gap = rec.get("typical_gap_days")
    if pd.isna(days):
        return "Unknown activity", "Ordering recency is unavailable. Ask whether a check-in would be useful."
    if pd.isna(gap) or gap <= 0 or rec.get("orders", 0) < 3:
        return "Cadence unavailable", f"Last order was {days:.0f} days ago; there is not enough ordering history to establish a usual cadence. Ask about current needs."
    if days <= gap:
        return "Within usual cadence", f"Last order was {days:.0f} days ago, within the typical {gap:.0f}-day ordering gap. Ask about current needs without assuming a slowdown."
    if days > 60:
        return "Reactivation check", f"Last order was {days:.0f} days ago, beyond the typical {gap:.0f}-day gap and the 60-day activity window. Confirm whether the account is still trading and wants contact."
    return "Cadence check", f"Last order was {days:.0f} days ago, beyond the typical {gap:.0f}-day ordering gap. Ask whether ordering needs have changed."


def service_note(rec):
    note = rec.get("talking_point")
    return (f"Historical export note: {note}. Its date refers to an order, not necessarily the review or delivery event. "
            "Ask whether anything remains unresolved; do not assume a current complaint.") if note else ""


def briefing_text(rec, offer):
    """Evidence-led account briefing, with explicit demo offer conditions."""
    city = str(rec.get("city", "")).title()
    ranking = f"number {int(rec['rank'])} on this week's list" if pd.notna(rec.get("rank")) else "without a modelled priority rank"
    lines = [f"Account {rec['account_id']} in {city}, {ranking} in the supplied prototype export.", contact_context(rec)[1]]
    reasons = _reasons(rec)
    if reasons:
        lines.append("Account evidence: " + "; ".join(reasons[:3]) + ".")
    if service_note(rec):
        lines.append(service_note(rec))
    if rec.get("lane") == "Monitor":
        lines.append("No outreach or offer is scheduled. Monitor the account history.")
    else:
        lines.append(f"If contact is welcome, discuss this illustrative offer only after approval: {offer['detail']}")
    return " ".join(lines)


def call_script(rec, offer):
    status, _ = contact_context(rec)
    if status == "Reactivation check":
        question = "Are you still trading, and would you like us to check in about ordering again?"
    elif status == "Cadence check":
        question = "It's been longer than your typical ordering gap. Have your ordering needs changed?"
    else:
        question = "Would a check-in about your current ordering needs be useful?"
    opener = f"Hi, this is Ana, the HEINEKEN assistant. {question}"
    return {
        "opener": opener,
        "ask": "What would help with your next order? Is there a price, supplier, seasonal or service issue, or do you simply not need stock yet?",
        "offer": f"If you are interested, here's an illustrative offer, subject to approval: {offer['detail']} Would you like your rep to confirm the terms?",
        "handover": "Thanks for explaining. In this demo I can record a request for your sales rep to follow up; no appointment is booked.",
        "pause": "Thanks for letting us know. We can pause contact and ask when it would suit you to check in again.",
        "no_need": "Thanks for letting us know. There is no need to order now. When would you prefer another check-in?",
        "close": "Thanks for your interest. Your rep would need to approve the terms and confirm an order separately.",
    }


def whatsapp_text(rec, offer):
    status, _ = contact_context(rec)
    opening = ("Gostaria de conversar sobre voltar a fazer pedidos?" if status == "Reactivation check" else
               "Suas necessidades de pedido mudaram?" if status == "Cadence check" else
               "Gostaria de conversar sobre suas necessidades de pedido?")
    return (f"Olá! Aqui é a equipe HEINEKEN 🍺 {opening} "
            f"Oferta ilustrativa, sujeita à aprovação: {offer['pt']}. Responda SIM para pedir a confirmação das condições. "
            "Se algo mudou, conte pra gente: 1 Preço · 2 Outro fornecedor · 3 Fechado/temporada · 4 Problema na entrega · 5 Outro")


def plan(account):
    """Full Act plan for one Identify payload, or None when Ritmo has no record."""
    # Bundled Ritmo exports belong to the challenge snapshot, never fictional accounts.
    if account.get("data_kind") == "synthetic":
        return None
    if account.get("analysis_date", "2018-08-31") != "2018-08-31":
        return None
    rec = ritmo_record(account.get("account_id"))
    if rec is None:
        return None
    # The selected Identify payload owns observed facts and the displayed forecast.
    # Keep the static export intact for inspecting the original planning assumptions.
    exported = dict(rec)
    for source, target in {"days_since_last_order": "days_since_last_order", "median_order_gap_days": "typical_gap_days",
                           "historical_order_count": "orders", "last_order_date": "last_order_date",
                           "city": "city", "state": "state"}.items():
        if source in account:
            rec[target] = account[source]
    if "risk_probability" in account:
        rec["identify_reasons"] = [account.get(f"top_risk_reason_{i}") for i in range(1, 4)
                                    if isinstance(account.get(f"top_risk_reason_{i}"), str) and account[f"top_risk_reason_{i}"]]
    if "categories_dropped" in account:
        dropped = account["categories_dropped"] or []
        rec["dropped_category"] = dropped[0] if dropped else ""
    offer = build_offer(rec)
    lane = rec["lane"]
    return {"record": rec, "exported_record": exported, "forecast_probability": account.get("risk_probability"),
            "contact_status": contact_context(rec)[0], "contact_context": contact_context(rec)[1],
            "lane": lane, "lane_info": LANES.get(lane, LANES["Monitor"]), "offer": offer,
            "reasons": _reasons(rec), "briefing": briefing_text(rec, offer),
            "call": call_script(rec, offer), "whatsapp": whatsapp_text(rec, offer)}


def order_route(stops):
    """Illustrative nearest-neighbour sequence; does not estimate road travel."""
    stops = stops.dropna(subset=["lat", "lng"]).copy()
    if stops.empty:
        return stops
    remaining = stops.sort_values("rank").to_dict("records")
    route = [remaining.pop(0)]
    while remaining:
        last = route[-1]
        nxt = min(remaining, key=lambda s: (s["lat"] - last["lat"]) ** 2 + (s["lng"] - last["lng"]) ** 2)
        remaining.remove(nxt)
        route.append(nxt)
    out = pd.DataFrame(route)
    out.insert(0, "stop", range(1, len(out) + 1))
    return out


def morning_briefing_text(stops, route):
    """Daniel's spoken route overview, describing the selected weekly plan."""
    top_stops = stops.sort_values("rank").head(3)
    parts = [f"Good morning. Your selected weekly route has {len(stops)} proposed visits in "
             f"{route.split(' ')[0]}, representing approximately {stops.value_at_risk.sum():,.0f} "
             "in exported prototype value proxy. Confirm priorities before scheduling visits."]
    if not top_stops.empty:
        first = top_stops.iloc[0]
        parts.append(f"Your highest-priority account in the supplied prototype export is {first['account_id']} in "
                     f"{str(first['city']).title()}, ranked number {int(first['rank'])}.")
    if len(top_stops) > 1:
        parts.append("Other accounts to watch closely are " + ", ".join(
            f"{row.account_id} in {str(row.city).title()}" for _, row in top_stops.iloc[1:].iterrows()) + ".")
    parts.append("Review high-value accounts where ordering behaviour has changed. "
                 "Before each visit, play the individual briefing for the talking points and proposed offer.")
    return " ".join(parts)
