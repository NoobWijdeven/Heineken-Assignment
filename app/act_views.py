"""Streamlit views for Part 3 (Act): the rep's week, the AI call, WhatsApp nudges and the feedback loop."""
import html
import json
import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from app.act_engine import LANES, REASON_OPTIONS, load_priority, load_routes, order_route, plan, pretty

GREEN = "#00834D"


def speak_button(text, key, label="▶ Play 30-second briefing"):
    """Reads text aloud with the browser's own voice: no keys, works on any public link."""
    safe = json.dumps(text)
    components.html(f"""
    <button id="b{key}" style="background:{GREEN};color:white;border:0;border-radius:10px;padding:10px 16px;
      font-size:15px;cursor:pointer;font-family:sans-serif">{html.escape(label)}</button>
    <button id="s{key}" style="background:#e2e9df;color:#172D23;border:0;border-radius:10px;padding:10px 14px;
      font-size:15px;cursor:pointer;margin-left:6px;font-family:sans-serif">■ Stop</button>
    <script>
    const t = {safe};
    document.getElementById("b{key}").onclick = () => {{
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(t); u.lang = "en-GB"; u.rate = 1.02;
      const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.startsWith("en"));
      if (v) u.voice = v;
      speechSynthesis.speak(u);
    }};
    document.getElementById("s{key}").onclick = () => speechSynthesis.cancel();
    </script>""", height=52)


def _bubble(text, who="agent"):
    colour, align = ("#E8F3EC", "flex-start") if who == "agent" else ("#DCF8C6", "flex-end")
    st.markdown(f"<div style='display:flex;justify-content:{align}'><div style='background:{colour};padding:10px 14px;"
                f"border-radius:14px;max-width:80%;margin:4px 0;color:#172D23'>{html.escape(text)}</div></div>",
                unsafe_allow_html=True)


def _lane_badge(lane):
    info = LANES.get(lane, LANES["Monitor"])
    return (f"<span style='background:{info['colour']};color:white;padding:3px 10px;border-radius:999px;"
            f"font-size:.85rem'>{info['icon']} {info['short']}</span>")


def _identify_line(accounts, account_id):
    row = accounts[accounts.account_id == account_id]
    if row.empty or pd.isna(row.iloc[0].risk_probability):
        return "Account Compass 60-day forecast: not modelled (fewer than 10 orders), so Ritmo's rhythm signals carry it."
    r = row.iloc[0]
    return f"Account Compass 60-day forecast: {r.risk_probability:.0%} chance of no order ({r.risk_level} band)."


def why_card(act, accounts, key, history=None):
    rec, offer = act["record"], act["offer"]
    st.markdown(f"{_lane_badge(act['lane'])} &nbsp; **Priority #{int(rec['rank']):,}** · "
                f"{rec['churn_chance_pct']:.0f}% chance of going silent for 60 days · "
                f"value at stake {rec['value_at_risk']:,.0f}", unsafe_allow_html=True)
    st.caption(_identify_line(accounts, rec["account_id"]))
    a, b = st.columns([3, 2])
    with a:
        st.markdown("**Why now**")
        for reason in act["reasons"]:
            st.markdown(f"- {reason}")
        if rec.get("talking_point"):
            st.markdown(f"**Talking point:** {rec['talking_point']}. Open with an apology and ask how it went.")
        st.markdown(f"**Usually buys:** {pretty(rec['top_categories'])}")
    with b:
        with st.container(border=True):
            st.markdown(f"🎁 **{offer['headline']}**")
            st.write(offer["detail"])
    speak_button(act["briefing"], key)
    with st.expander("Briefing text"):
        st.write(act["briefing"])
    if history is not None and not history.empty:
        h = history[history.account_id == rec["account_id"]].copy()
        if not h.empty:
            h["month"] = pd.to_datetime(h.month + "-01")
            fig = px.bar(h, x="month", y="order_count", title="Orders each month", color_discrete_sequence=[GREEN])
            fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None, yaxis_title=None,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch", key=f"hist{key}")


def action_card(action, accounts):
    """Replaces the stub card in the Account workspace."""
    with st.container(border=True):
        st.markdown(f"**{action['title']}**")
        st.write(action["message"])
        act = action.get("plan")
        if act:
            why_card(act, accounts, key=f"ws{act['record']['account_id']}")
            if act["lane"] == "C: WhatsApp nudge":
                _bubble(act["whatsapp"], "agent")
            elif act["lane"] == "B: AI call":
                st.caption("This account is in the AI call list. Open the **Act** tab → AI call to hear the call.")


# ---------------------------------------------------------------- Act tab

def _log_reason(account_id, reason, outcome):
    st.session_state.setdefault("call_log", []).append({"account_id": account_id, "reason": reason, "outcome": outcome})


def _overview(prio):
    st.markdown("#### From warning to action")
    st.write("Account Compass says **how likely** a shop is to stop ordering. Ritmo adds **who to save first** "
             "(money at stake × chance × can it still be saved) and **what to do**. A rep can't visit thousands of shops, "
             "so each flagged account goes down one of three lanes.")
    cols = st.columns(4)
    for col, lane in zip(cols, LANES):
        part = prio[prio.lane == lane]
        info = LANES[lane]
        col.metric(f"{info['icon']} {info['short']} · accounts", f"{len(part):,}",
                   f"value at stake {part.value_at_risk.sum():,.0f}", delta_color="off")
    st.caption("Lane rules: Rep visit = top 150 regulars (5+ orders) by priority, grouped into weekly routes of 12. "
               "AI call = next 850 by priority. WhatsApp = other accounts with a higher-than-median chance of going silent. Monitor = the rest.")


def _rep_week(prio, accounts, history):
    routes = load_routes()
    if routes.empty:
        st.info("No route file found.")
        return
    names = sorted(prio.loc[prio.route != "", "route"].unique(), key=lambda r: (r != "RJ week 1", r))
    route = st.selectbox("This week's route", names, key="route_pick")
    stops = order_route(prio[prio.route == route])
    st.markdown(f"**{len(stops)} visits** in {route.split(' ')[0]} · value at stake {stops.value_at_risk.sum():,.0f}")
    fig = go.Figure()
    fig.add_trace(go.Scattermap(lat=stops.lat, lon=stops.lng, mode="lines", line=dict(width=2, color="#173C2B"),
                                hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scattermap(lat=stops.lat, lon=stops.lng, mode="markers+text",
                                marker=dict(size=16, color=GREEN), text=stops.stop.astype(str),
                                textfont=dict(color="white", size=11), showlegend=False,
                                customdata=stops[["account_id", "city", "rank"]],
                                hovertemplate="Stop %{text}: %{customdata[0]} · %{customdata[1]} · priority #%{customdata[2]}<extra></extra>"))
    span = max(stops.lat.max() - stops.lat.min(), stops.lng.max() - stops.lng.min(), 0.05)
    zoom = max(3.5, min(11, 8.6 - math.log2(span)))
    fig.update_layout(map=dict(style="open-street-map", zoom=zoom,
                               center=dict(lat=(stops.lat.max() + stops.lat.min()) / 2, lon=(stops.lng.max() + stops.lng.min()) / 2)),
                      height=420, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, width="stretch", key="routemap")
    table = stops[["stop", "account_id", "city", "rank", "churn_chance_pct", "value_at_risk", "reason_1"]].copy()
    table["city"] = table.city.str.title()
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "stop": "Stop", "account_id": "Account", "city": "City", "rank": st.column_config.NumberColumn("Priority", format="#%d"),
        "churn_chance_pct": st.column_config.NumberColumn("Chance of going silent", format="%.0f%%"),
        "value_at_risk": st.column_config.NumberColumn("Value at stake", format="%.0f"), "reason_1": "Main reason"})
    options = stops.account_id.tolist()
    default = options.index("A24220") if "A24220" in options else 0
    pick = st.selectbox("Open a stop", options, index=default, key="stop_pick",
                        format_func=lambda a: f"Stop {options.index(a) + 1} · {a} · {stops.set_index('account_id').loc[a, 'city'].title()}")
    act = plan({"account_id": pick})
    if act:
        why_card(act, accounts, key=f"rw{pick}", history=history)


def _agent_id():
    if os.environ.get("ELEVENLABS_AGENT_ID"):
        return os.environ["ELEVENLABS_AGENT_ID"]
    try:
        return st.secrets.get("ELEVENLABS_AGENT_ID")
    except Exception:
        return None


def _ai_call(prio, accounts):
    st.write("Lane B is too big for reps (850 accounts), so an AI voice agent calls them. It knows why each shop was flagged, "
             "**asks the question the data can't answer: why did you slow down?**, makes the offer, and hands unhappy or big "
             "customers to the rep. In Brazil it would speak Portuguese; the demo is in English.")
    agent_id = _agent_id()
    lane_b = prio[prio.lane == "B: AI call"].sort_values("rank").head(40)
    pick = st.selectbox("Account to call", lane_b.account_id.tolist(), key="call_pick",
                        format_func=lambda a: f"#{int(lane_b.set_index('account_id').loc[a, 'rank'])} · {a} · "
                                              f"{lane_b.set_index('account_id').loc[a, 'city'].title()}")
    act = plan({"account_id": pick})
    rec, script = act["record"], act["call"]
    st.caption("What the agent is given: " + " · ".join(act["reasons"]) + f" · offer: {act['offer']['detail']}")
    st.caption(_identify_line(accounts, pick))
    if agent_id:
        variables = json.dumps({"account_id": pick, "city": str(rec["city"]).title(), "reasons": "; ".join(act["reasons"]),
                                "offer": act["offer"]["detail"], "days_silent": str(int(rec["days_since_last_order"]))})
        components.html(f"""<elevenlabs-convai agent-id="{html.escape(agent_id)}" dynamic-variables='{html.escape(variables)}'></elevenlabs-convai>
        <script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async></script>""", height=420)
        st.caption("Live voice agent: press the call button and play the shop owner.")
    st.markdown("##### The call")
    state_key = f"call_{pick}"
    _bubble(script["opener"])
    _bubble("Hmm, yes, we've been ordering less lately.", "customer")
    _bubble(script["ask"])
    reason = st.radio("Play the shop owner: why did you slow down?", REASON_OPTIONS, index=None, key=f"r{pick}", horizontal=True)
    if reason:
        _bubble(reason, "customer")
        unhappy = reason in ("Delivery or service problem", "Switched to a competitor")
        if unhappy:
            _bubble(script["handover"])
            outcome = "Handed to rep"
            st.warning(f"Handed to the rep with a note: '{reason}'. The account joins next week's visit list.")
        else:
            _bubble(script["offer"])
            _bubble("Okay, add it.", "customer")
            _bubble(script["close"])
            outcome = "Offer accepted"
            st.success(f"Offer booked: {act['offer']['detail']}")
        if st.session_state.get(state_key) != reason:
            st.session_state[state_key] = reason
            _log_reason(pick, reason, outcome)
        lines = [script["opener"], script["ask"], script["handover"] if unhappy else script["offer"]]
        speak_button(" ".join(lines), key=f"call{pick}", label="▶ Hear the agent's side")
    else:
        speak_button(script["opener"] + " " + script["ask"], key=f"callopen{pick}", label="▶ Hear the agent")


def _whatsapp(prio):
    st.write("Lane C covers thousands of smaller accounts. Each gets one friendly WhatsApp with a tailored offer "
             "(95% of Brazilian companies use WhatsApp as their main channel). The numbered reply menu collects *why*.")
    lane_c = prio[prio.lane == "C: WhatsApp nudge"].sort_values("rank")
    st.markdown(f"**Outbox:** {len(lane_c):,} messages ready this week. First 8 shown.")
    for _, rec in lane_c.head(8).iterrows():
        act = plan({"account_id": rec.account_id})
        with st.container(border=True):
            st.markdown(f"**{rec.account_id}** · {str(rec.city).title()} ({rec.state}) · {rec.reason_1 or 'Fading rhythm'}")
            _bubble(act["whatsapp"])
            st.caption(f"In English: we miss you, it's been {int(rec.days_since_last_order)} days; offer: {act['offer']['detail']} "
                       "Reply YES, or tell us what changed (price, other supplier, closed, delivery, other).")
    if st.button(f"Send all {len(lane_c):,} (demo)", key="sendall"):
        st.success(f"{len(lane_c):,} WhatsApp messages queued. Replies flow into 'What we learn'. (Demo: nothing is actually sent.)")


def _learn(prio):
    st.write("Part 1 showed the order data can't explain **why** shops slow down: late deliveries and bad reviews don't predict it. "
             "So every call and WhatsApp reply logs a reason. Over time this tells HEINEKEN which offer works for which reason, "
             "the next step towards a real 'next best action' engine like AIDDA.")
    rng = pd.Series([0.27, 0.22, 0.18, 0.12, 0.15, 0.06], index=REASON_OPTIONS)
    contacted = int(len(prio[prio.lane.isin(["B: AI call", "C: WhatsApp nudge"])]) * 0.18)
    sim = (rng * contacted).round().astype(int).rename("Simulated replies").to_frame()
    log = pd.DataFrame(st.session_state.get("call_log", []))
    sim["Your demo calls"] = log.reason.value_counts().reindex(REASON_OPTIONS).fillna(0).astype(int) if not log.empty else 0
    data = sim.reset_index(names="reason").melt("reason", var_name="source", value_name="replies")
    fig = px.bar(data, x="replies", y="reason", color="source", orientation="h", barmode="stack",
                 color_discrete_map={"Simulated replies": "#9FC7AE", "Your demo calls": GREEN},
                 title="Why customers say they slowed down")
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=45, b=10), yaxis_title=None, xaxis_title=None,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title=None)
    st.plotly_chart(fig, width="stretch", key="learnchart")
    st.caption(f"Grey-green bars are simulated (about 18% of {contacted / 0.18:,.0f} contacted accounts replying), "
               "to show the dashboard once calls run. Dark green bars are the calls you made in this demo.")
    if not log.empty:
        st.dataframe(log, hide_index=True, width="stretch")


def render_act_tab(accounts, history):
    prio = load_priority()
    if prio.empty:
        st.info("Ritmo priority list not found (demo_data/ritmo/priority_list.csv).")
        return
    _overview(prio)
    t1, t2, t3, t4 = st.tabs(["🚗 Rep's week", "📞 AI call", "💬 WhatsApp", "📊 What we learn"])
    with t1:
        _rep_week(prio, accounts, history)
    with t2:
        _ai_call(prio, accounts)
    with t3:
        _whatsapp(prio)
    with t4:
        _learn(prio)
