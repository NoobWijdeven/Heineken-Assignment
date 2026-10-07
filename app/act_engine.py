"""Act layer: turns a flagged account into a channel, an offer and ready-made words.

Reads the Ritmo prioritisation outputs (Part 2) and combines them with the
Identify payload (Part 1). Nothing is re-scored here.
"""
import math
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACT_DIR = Path(os.environ.get("ACT_DATA_DIR", ROOT / "demo_data" / "ritmo"))

LANES = {
    "A: Rep visit": {"short": "Rep visit", "icon": "🚗", "colour": "#00834D",
                     "why": "A regular worth a lot that is fading: worth a rep's time this week."},
    "B: AI call": {"short": "AI call", "icon": "📞", "colour": "#2F6FB3",
                   "why": "Too many accounts like this for reps to visit. The AI agent calls, asks why and hands warm or unhappy ones to the rep."},
    "C: WhatsApp nudge": {"short": "WhatsApp nudge", "icon": "💬", "colour": "#C77700",
                          "why": "Small or new account. A friendly automatic WhatsApp with an offer, replies are logged."},
    "Monitor": {"short": "Monitor", "icon": "👁", "colour": "#7A857E",
                "why": "Ordering on rhythm or low value at stake. No action this week; Ritmo keeps watching."},
}

REASON_OPTIONS = ["Price", "Switched to a competitor", "Closed or quiet season", "Delivery or service problem",
                  "Just forgot / no need yet", "Other"]


def pretty(category):
    return str(category).replace("_", " ") if isinstance(category, str) and category else ""


@lru_cache(maxsize=1)
def load_priority():
    path = ACT_DIR / "priority_list.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype={"account_id": str})
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
    usual = pretty(top[0]) if top else "their usual order"
    dropped = pretty(rec.get("dropped_category"))
    if dropped:
        if top and pretty(top[0]) == dropped:
            usual = pretty(top[1]) if len(top) > 1 else "their usual order"
        return {"headline": f"Win-back bundle: {dropped} back in the next order",
                "detail": f"10% off {dropped} when added to their usual {usual} order.",
                "pt": f"10% de desconto em {dropped} no seu próximo pedido junto com {usual}"}
    return {"headline": f"Restock reminder: {usual}",
            "detail": f"Free delivery on the next {usual} order this week.",
            "pt": f"frete grátis no seu próximo pedido de {usual}"}


def _reasons(rec):
    return [r for r in (rec.get("reason_1"), rec.get("reason_2"), rec.get("reason_3")) if r]


def briefing_text(rec, offer):
    """About 30 seconds when read aloud, for the rep in the car."""
    city = str(rec.get("city", "")).title()
    lines = [f"Next stop: {city}, account {rec['account_id']}, number {int(rec['rank'])} on this week's list."]
    reasons = _reasons(rec)
    if reasons:
        lines.append("What changed: " + "; ".join(reasons[:3]) + ".")
    if rec.get("talking_point"):
        lines.append(f"Heads up: there was a {rec['talking_point'].lower()}. Start by asking how that went.")
    lines.append(f"Ask why they have slowed down, then offer: {offer['detail']}")
    return " ".join(lines)


def call_script(rec, offer):
    days = int(rec.get("days_since_last_order") or 0)
    gap = rec.get("typical_gap_days")
    rhythm = f"you usually order about every {int(gap)} days" if gap and not math.isnan(gap) else "you used to order regularly"
    dropped = pretty(rec.get("dropped_category"))
    opener = (f"Hi, this is Ana, the HEINEKEN assistant. I'm calling because {rhythm}, "
              f"and it's been {days} days since your last order. Is everything okay?")
    if dropped:
        opener += f" I also noticed you stopped ordering {dropped}."
    return {
        "opener": opener,
        "ask": "Can I ask what changed? Was it price, another supplier, a quiet period, or something about our service?",
        "offer": f"Thanks for telling me. To make it easy to come back: {offer['detail']} Shall I add that to your next order?",
        "handover": "I'm sorry to hear that. I'll ask your sales rep to call you personally within two days.",
        "close": "Great, it's on your next order. Thanks for your time and have a good week!",
    }


def whatsapp_text(rec, offer):
    days = int(rec.get("days_since_last_order") or 0)
    return (f"Olá! Aqui é a equipe HEINEKEN 🍺 Sentimos sua falta: já faz {days} dias desde o seu último pedido. "
            f"Preparamos uma oferta só para você: {offer['pt']}. Responda SIM para aproveitar. "
            "Se algo mudou, conte pra gente: 1 Preço · 2 Outro fornecedor · 3 Fechado/temporada · 4 Problema na entrega · 5 Outro")


def plan(account):
    """Full Act plan for one Identify payload, or None when Ritmo has no record."""
    rec = ritmo_record(account.get("account_id"))
    if rec is None:
        return None
    offer = build_offer(rec)
    lane = rec["lane"]
    return {"record": rec, "lane": lane, "lane_info": LANES.get(lane, LANES["Monitor"]), "offer": offer,
            "reasons": _reasons(rec), "briefing": briefing_text(rec, offer),
            "call": call_script(rec, offer), "whatsapp": whatsapp_text(rec, offer)}


def order_route(stops):
    """Greedy nearest-neighbour order so the map shows a drivable sequence."""
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
