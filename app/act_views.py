"""Streamlit views for Part 3 (Act): the rep's week, the AI call, WhatsApp nudges and the feedback loop."""
import html
import hashlib
import json
import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.act_engine import LANES, REASON_OPTIONS, load_priority, load_routes, order_route, plan, pretty, morning_briefing_text, service_note
from app.data_access import selected_account_payload

GREEN = "#00834D"


def speak_button(text, key, label="▶ Play account briefing"):
    """Reads text aloud in browsers that support speech synthesis."""
    safe = json.dumps(text).replace("<", "\\u003c")
    key = hashlib.sha256(str(key).encode()).hexdigest()[:16]
    st.iframe(f"""
    <button id="b{key}" style="background:{GREEN};color:white;border:0;border-radius:10px;padding:10px 16px;
      font-size:15px;cursor:pointer;font-family:sans-serif">{html.escape(label)}</button>
    <button id="s{key}" style="background:#e2e9df;color:#172D23;border:0;border-radius:10px;padding:10px 14px;
      font-size:15px;cursor:pointer;margin-left:6px;font-family:sans-serif">■ Stop</button>
    <script>
    const t = {safe};
    document.getElementById("b{key}").onclick = () => {{
      if (!("speechSynthesis" in window)) {{ alert("Audio is unavailable in this browser. Read the briefing text below."); return; }}
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(t); u.lang = "en-GB"; u.rate = 1.02;
      const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.startsWith("en"));
      if (v) u.voice = v;
      speechSynthesis.speak(u);
    }};
    document.getElementById("s{key}").onclick = () => {{ if ("speechSynthesis" in window) speechSynthesis.cancel(); }};
    </script>""", height=52, alt=label)


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
    if row.empty:
        return "No matching Account Compass record is loaded."
    if pd.isna(row.iloc[0].risk_probability):
        return "Account Compass 60-day forecast: outside model coverage (order count, history length or ordering gaps)."
    r = row.iloc[0]
    return f"Account Compass 60-day forecast: {r.risk_probability:.0%} chance of no order ({r.risk_level} band)."


def _account_plan(accounts, account_id):
    row = accounts[accounts.account_id == account_id]
    return plan(selected_account_payload(row.iloc[0])) if not row.empty else None


def why_card(act, accounts, key, history=None):
    rec, offer = act["record"], act["offer"]
    if pd.notna(rec.get("rank")):
        st.markdown(f"{_lane_badge(act['lane'])} &nbsp; **Priority #{int(rec['rank']):,}** · "
                    "supplied prototype ranking", unsafe_allow_html=True)
    else:
        st.markdown(f"{_lane_badge(act['lane'])} &nbsp; **Unranked · insufficient history**", unsafe_allow_html=True)
    st.caption(_identify_line(accounts, rec["account_id"]))
    st.markdown(f"**{act['contact_status']}** · {act['contact_context']}")
    a, b = st.columns([3, 2])
    with a:
        st.markdown("**Loaded account evidence**")
        for reason in act["reasons"]:
            st.markdown(f"- {reason}")
        if service_note(rec):
            st.write(service_note(rec))
        st.markdown(f"**Historical portfolio (export):** {pretty(rec['top_categories'])}")
    with b:
        with st.container(border=True):
            if act["lane"] == "Monitor":
                st.write("No contact or offer scheduled in this priority export.")
            else:
                st.markdown(f"🎁 **{offer['headline']}**")
                st.write(offer["detail"])
                st.caption("Illustrative offer for the demo; terms are not validated by the model.")
    with st.expander("Prototype planning inputs and portfolio codes"):
        exported = act["exported_record"]
        st.write("The supplied Ritmo export uses a separate, unverified model. Its ranking and value proxy "
                 "have not been recalculated from Account Compass and should be reviewed before scheduling contact.")
        if pd.notna(exported.get("churn_chance_pct")):
            st.write(f"Exported Ritmo estimate: {exported['churn_chance_pct']:.0f}% · "
                     f"exported value proxy: {exported['value_at_risk']:,.0f}")
        st.caption("Portfolio labels are neutral aliases for marketplace category codes, not actual HEINEKEN products.")
        codes = [c.strip() for c in exported["top_categories"].split(",") if c.strip()]
        st.dataframe(pd.DataFrame([{"Portfolio label": pretty(c), "Source category code": c} for c in codes]),
                     hide_index=True, width="stretch")
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
    log = st.session_state.setdefault("call_log", [])
    entry = {"account_id": account_id, "reason": reason, "outcome": outcome}
    for index, previous in enumerate(log):
        if previous["account_id"] == account_id:
            log[index] = entry
            return
    log.append(entry)


def _overview(prio):
    st.markdown("#### From warning to action")
    st.write("Account Compass estimates future inactivity. Ritmo adds an exported **priority ranking** "
             "(historical value × supplied risk estimate × saveability weight) and a proposed action. A rep can't visit thousands of shops, "
             "so the export groups accounts into three contact lanes or Monitor. These are proposals to review, not approved outreach.")
    cols = st.columns(4)
    for col, lane in zip(cols, LANES):
        part = prio[prio.lane == lane]
        info = LANES[lane]
        col.metric(f"{info['icon']} {info['short']} · accounts", f"{len(part):,}",
                   f"exported value proxy {part.value_at_risk.sum(min_count=1):,.0f}" if part.value_at_risk.notna().any() else "value proxy unavailable",
                   delta_color="off")
    st.caption("Lane rules: Rep visit = top 150 regulars (5+ orders) by priority, grouped into weekly routes of 12. "
               "AI call = next 850 by priority. WhatsApp = other accounts with a higher-than-median chance of going silent. Monitor = the rest.")


def _rep_week(prio, accounts, history):
    routes = load_routes()
    if routes.empty:
        st.info("No route file found.")
        return
    names = sorted(prio.loc[prio.route != "", "route"].unique(), key=lambda r: (r != "RJ week 1", r))
    if not names:
        st.info("No routes match the loaded accounts.")
        return
    route = st.selectbox("This week's route", names, key="route_pick")
    stops = order_route(prio[prio.route == route])
    if stops.empty:
        st.info("No stops with coordinates are available for this route.")
        return
    st.markdown(f"**{len(stops)} proposed weekly visits** in {route.split(' ')[0]} · exported value proxy {stops.value_at_risk.sum():,.0f}")

    morning_briefing = morning_briefing_text(stops, route)

    with st.container(border=True):
        st.markdown("### 🎧 Morning Route Briefing")
        st.write("Your spoken overview of the selected weekly route.")

        speak_button(
            morning_briefing,
            key=f"morning{route.replace(' ', '')}",
            label="▶ Play Morning Briefing"
        )

        with st.expander("Read morning briefing"):
            st.write(morning_briefing)

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
    st.caption("Illustrative stop sequence using coordinate distances. Lines do not represent roads or driving times.")
    table = stops[["stop", "account_id", "city", "rank", "value_at_risk"]].merge(
        accounts[["account_id", "risk_probability", "current_activity", "top_risk_reason_1"]], on="account_id", validate="one_to_one")
    table["city"] = table.city.str.title()
    table["compass_forecast_pct"] = table.pop("risk_probability") * 100
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "stop": "Stop", "account_id": "Account", "city": "City", "rank": st.column_config.NumberColumn("Priority", format="#%d"),
        "compass_forecast_pct": st.column_config.NumberColumn("Compass 60-day forecast", format="%.0f%%"),
        "current_activity": "Current activity", "value_at_risk": st.column_config.NumberColumn("Exported value proxy", format="%.0f"),
        "top_risk_reason_1": "Loaded account evidence"})
    st.caption("Blank forecasts mean the account is outside Identify model coverage. Priorities and value proxies come from the supplied Ritmo export.")
    options = stops.account_id.tolist()
    default = options.index("A24220") if "A24220" in options else 0
    pick = st.selectbox("Open a stop", options, index=default, key="stop_pick",
                        format_func=lambda a: f"Stop {options.index(a) + 1} · {a} · {stops.set_index('account_id').loc[a, 'city'].title()}")
    act = _account_plan(accounts, pick)
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
    st.write("Lane B proposes calls for accounts beyond the rep visit capacity. This English role-play asks "
             "about current needs, proposes an offer, or requests rep follow-up. "
             "The scripted demo does not call customers, book orders or change visit routes.")
    agent_id = _agent_id()
    lane_b = prio[prio.lane == "B: AI call"].sort_values("rank").head(40)
    if lane_b.empty:
        st.info("No AI call accounts match the current filters.")
        return
    pick = st.selectbox("Account to call", lane_b.account_id.tolist(), key="call_pick",
                        format_func=lambda a: f"#{int(lane_b.set_index('account_id').loc[a, 'rank'])} · {a} · "
                                              f"{lane_b.set_index('account_id').loc[a, 'city'].title()}")
    act = _account_plan(accounts, pick)
    rec, script = act["record"], act["call"]
    st.caption("What the agent is given: " + " · ".join(act["reasons"]) + f" · offer: {act['offer']['detail']}")
    st.caption(_identify_line(accounts, pick))
    st.write(act["contact_context"])
    if agent_id:
        variables = json.dumps({"account_id": pick, "city": str(rec["city"]).title(), "reasons": "; ".join(act["reasons"]),
                                "offer": act["offer"]["detail"], "days_silent": str(int(rec["days_since_last_order"]))})
        st.iframe(f"""<elevenlabs-convai agent-id="{html.escape(agent_id)}" dynamic-variables='{html.escape(variables)}'></elevenlabs-convai>
        <script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async></script>""", height=420, alt="Optional voice agent")
        st.caption("Live voice agent: press the call button and play the shop owner.")
    st.markdown("##### The call")
    state_key = f"call_{pick}"
    _bubble(script["opener"])
    _bubble(script["ask"])
    reason = st.radio("Play the shop owner: what is your situation?", REASON_OPTIONS, index=None, key=f"r{pick}", horizontal=True)
    if reason:
        if st.session_state.get(f"last_reason_{pick}") != reason:
            st.session_state[f"offer_{pick}_{reason}"] = "Not decided"
            st.session_state[f"last_reason_{pick}"] = reason
        _bubble(reason, "customer")
        unhappy = reason in ("Delivery or service problem", "Switched to a competitor")
        if unhappy:
            reply = script["handover"]
            _bubble(reply)
            outcome = "Rep follow-up requested (demo)"
            st.warning(f"Demo follow-up requested: '{reason}'. This records a note in this session; visit routes are unchanged.")
        elif reason == "Closed or quiet season":
            reply = script["pause"]
            _bubble(reply)
            outcome = "Contact paused (demo)"
            st.info("Demo: contact paused pending a suitable follow-up date. No offer was accepted.")
        elif reason == "Just forgot / no need yet":
            reply = script["no_need"]
            _bubble(reply)
            outcome = "Needs check-in requested (demo)"
            st.info("Demo: ask about a preferred check-in date. No offer was proposed or order booked.")
        else:
            reply = script["offer"]
            _bubble(reply)
            response = st.radio("Shop owner's response to the offer", ["Not decided", "Accept offer", "Decline offer"],
                                key=f"offer_{pick}_{reason}", horizontal=True)
            outcome = "Offer proposed (demo)"
            if response == "Accept offer":
                _bubble("Okay, I would like that offer.", "customer")
                outcome = "Offer accepted (demo)"
                st.success(f"Demo interest recorded: {act['offer']['detail']} Terms need approval; no order is booked.")
            elif response == "Decline offer":
                _bubble("No thanks, not this time.", "customer")
                outcome = "Offer declined (demo)"
                st.info("Demo: offer declined. No order is booked.")
        signature = (reason, outcome)
        if st.session_state.get(state_key) != signature:
            st.session_state[state_key] = signature
            _log_reason(pick, reason, outcome)
        lines = [script["opener"], script["ask"], reply]
        speak_button(" ".join(lines), key=f"call{pick}", label="▶ Hear the agent's side")
    else:
        speak_button(script["opener"] + " " + script["ask"], key=f"callopen{pick}", label="▶ Hear the agent")


def _whatsapp(prio, accounts):
    st.write("Lane C proposes WhatsApp drafts. Each draft includes an illustrative offer "
             "and a numbered reply menu asking what changed. Messages and replies are simulated.")
    lane_c = prio[prio.lane == "C: WhatsApp nudge"].sort_values("rank")
    st.markdown(f"**Draft preview:** {len(lane_c):,} proposed messages to review. First 8 shown.")
    for _, rec in lane_c.head(8).iterrows():
        act = _account_plan(accounts, rec.account_id)
        with st.container(border=True):
            st.markdown(f"**{rec.account_id}** · {str(rec.city).title()} ({rec.state}) · {act['contact_status']}")
            st.caption(_identify_line(accounts, rec.account_id))
            _bubble(act["whatsapp"])
            st.caption(f"In English: {act['contact_context']} Illustrative offer: {act['offer']['detail']} "
                       "Reply YES to request approved terms, or describe your current needs.")
    if st.button(f"Preview {len(lane_c):,} drafts (demo)", key="sendall"):
        st.success(f"Demo preview: {len(lane_c):,} WhatsApp drafts. Nothing is sent or queued; simulated replies appear in 'What we learn'.")


def _learn(prio):
    st.write("Order histories show behaviour changes but do not establish why they occurred. "
             "This dashboard illustrates collecting customer reasons to inform later action evaluation. "
             "Role-play notes are held only in this session; the other replies below are simulated. "
             "The current data does not measure whether an offer causes a customer to return.")
    rng = pd.Series([0.27, 0.22, 0.18, 0.12, 0.15, 0.06], index=REASON_OPTIONS)
    contacted = int(len(prio[prio.lane.isin(["B: AI call", "C: WhatsApp nudge"])]) * 0.18)
    sim = (rng * contacted).round().astype(int).rename("Simulated replies").to_frame()
    log = pd.DataFrame(st.session_state.get("call_log", []))
    sim["Your demo calls"] = log.reason.value_counts().reindex(REASON_OPTIONS).fillna(0).astype(int) if not log.empty else 0
    data = sim.reset_index(names="reason").melt("reason", var_name="source", value_name="replies")
    fig = px.bar(data, x="replies", y="reason", color="source", orientation="h", barmode="stack",
                 color_discrete_map={"Simulated replies": "#9FC7AE", "Your demo calls": GREEN},
                 title="Customer situations: simulated replies and role-play notes")
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=45, b=10), yaxis_title=None, xaxis_title=None,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title=None)
    st.plotly_chart(fig, width="stretch", key="learnchart")
    st.caption(f"Grey-green bars are simulated (about 18% of {contacted / 0.18:,.0f} contacted accounts replying), "
            "to illustrate a possible dashboard. Dark green bars are local role-play notes.")
    if not log.empty:
        st.dataframe(log, hide_index=True, width="stretch")


def render_act_tab(accounts, history, synthetic=False):
    if synthetic:
        st.info("The fictional Identify demo has no matching Act exports. Use the bundled challenge snapshot to explore routes and calls.")
        return
    if not accounts.empty and not accounts.analysis_date.eq("2018-08-31").all():
        st.info("The bundled Act exports belong to 2018-08-31. No matching Act plan is available for this snapshot.")
        return
    prio = load_priority()
    if prio.empty:
        st.info("Ritmo priority list not found (demo_data/ritmo/priority_list.csv).")
        return
    prio = prio[prio.account_id.isin(accounts.account_id)]
    if prio.empty:
        st.info("No Act records match the current account filters.")
        return
    st.info("Ritmo risk estimates and saveability weights are supplied prototype inputs; their independent validation is pending. "
            "Account Compass validation is available in the Validation & handoff tab.")
    _overview(prio)
    t1, t2, t3, t4 = st.tabs(["🚗 Rep's week", "📞 AI call", "💬 WhatsApp", "📊 What we learn"])
    with t1:
        _rep_week(prio, accounts, history)
    with t2:
        _ai_call(prio, accounts)
    with t3:
        _whatsapp(prio, accounts)
    with t4:
        _learn(prio)
