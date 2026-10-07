"""Sales-facing Identify dashboard; synthetic fallback requires no raw data."""
import json
import os
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.data_access import read_outputs, filter_accounts, selected_account_payload
from app.action_layer import recommended_action
from app.act_views import action_card, render_act_tab
from app.act_engine import pretty

st.set_page_config(page_title="Account Compass · Identify & Act", page_icon="🧭", layout="wide")
st.markdown("""
<style>
.block-container {padding-top:2rem; padding-bottom:2rem; max-width:1500px;}
[data-testid="stMetric"] {background:white; border:1px solid #e2e9df; border-radius:14px; padding:16px;}
.eyebrow {font-size:.78rem; color:#00834D; letter-spacing:.14em; font-weight:700;}
.hero {background:#173C2B; padding:26px 30px; border-radius:18px; color:white; margin-bottom:18px;}
.hero h1 {color:white; font-size:2.3rem; margin:0 0 8px;}
.hero p {color:#d4e3d7; margin:0; font-size:1rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_outputs(folder, changed_at):
    return read_outputs(folder)


def chart(data, x, y, title, kind="bar"):
    maker = px.bar if kind == "bar" else px.line
    fig = maker(data, x=x, y=y, title=title, color_discrete_sequence=["#00834D"])
    fig.update_layout(height=270, margin=dict(l=10, r=10, t=45, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#172D23"), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, width="stretch")


def show_number(value, suffix="", decimals=0):
    return "—" if pd.isna(value) else f"{value:,.{decimals}f}{suffix}"


default_folder = ROOT / "outputs"
demo_folder = ROOT / "demo_data" / "identify"
configured = os.environ.get("IDENTIFY_OUTPUT_DIR")
folder = Path(configured) if configured else default_folder if (default_folder / "scored_accounts.csv").exists() else demo_folder if (demo_folder / "scored_accounts.csv").exists() else ROOT / "examples"
if not (folder / "scored_accounts.csv").exists():
    st.error("No scored-account file found. Run python -m src.score_accounts, or unset IDENTIFY_OUTPUT_DIR to use the synthetic demo.")
    st.stop()
try:
    # Changing any CSV/metadata invalidates the cached group of outputs.
    changed = max(p.stat().st_mtime_ns for p in folder.glob("*.*"))
    accounts, history, gaps, metadata = cached_outputs(str(folder), changed)
except (ValueError, KeyError, OSError) as error:
    st.error(f"Could not load account outputs: {error}")
    st.stop()
synthetic = metadata.get("data_kind") == "synthetic" or accounts.data_kind.eq("synthetic").all()
if accounts.empty:
    st.error("The scored-account file contains no accounts. Choose a populated output folder.")
    st.stop()

st.markdown('<div class="eyebrow">HEINEKEN × AISO · IDENTIFY · PRIORITISE · ACT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Account Compass</h1><p>Spot changing account behaviour, see who to save first, and act: rep visit, AI call or WhatsApp.</p></div>', unsafe_allow_html=True)
st.caption(f"As of {accounts.analysis_date.iloc[0]} · Forecast: no placed order in the next 60 days · Relative merchandise value, no currency")
if synthetic:
    st.info("SYNTHETIC DEMO · All accounts, histories and risk estimates shown here are fictional. Run the pipeline on the supplied dataset to view measured outputs.")
else:
    st.caption("Adapted marketplace challenge data; ZIP areas represent hypothetical commercial accounts. This is not HEINEKEN customer data.")
if metadata.get("validation_warning"):
    st.warning(metadata["validation_warning"])

with st.sidebar:
    st.header("Find accounts")
    search = st.text_input("Account, city or state", key="search", placeholder="Search accounts…")
    levels = st.multiselect("Risk level", ["High", "Medium", "Low", "Insufficient history"], key="levels")
    states = st.multiselect("State", sorted(accounts.state.dropna().unique()), key="states")
    confidence = st.multiselect("Evidence confidence", ["High", "Medium", "Low"], key="confidence")
    min_orders = st.number_input("Minimum historical orders", min_value=0, value=0, step=1, key="min_orders")
    min_value = st.number_input("Minimum historical value", min_value=0.0, value=0.0, step=100.0, key="min_value")
    current_activity = st.radio("Current activity", ["All accounts", "Ordered within 60 days", "Inactive over 60 days"], key="activity")
    st.divider()
    st.caption("Risk is a forecast. Confidence describes the amount of account evidence. Priority and intervention benefit are separate decisions.")
    st.caption("High/Medium bands use development workload percentiles; they are not permanent churn labels.")

filtered = filter_accounts(accounts, search=search, levels=levels, states=states,
                           confidence=confidence, min_orders=min_orders, min_value=min_value)
if current_activity != "All accounts":
    filtered = filtered[filtered.current_activity == current_activity]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Accounts in view", f"{len(filtered):,}")
c2.metric("High risk", f"{filtered.risk_level.eq('High').sum():,}")
c3.metric("Medium risk", f"{filtered.risk_level.eq('Medium').sum():,}")
c4.metric("High-risk historical value", f"{filtered.loc[filtered.risk_level.eq('High'), 'historical_spend'].sum():,.0f}")
c5.metric("Evidence score", f"{filtered.evidence_confidence_score.mean():.2f}" if len(filtered) else "—")
st.caption(f"{filtered.model_eligible.sum():,} accounts in view have modelled probabilities; {len(filtered) - filtered.model_eligible.sum():,} have insufficient established history. Evidence score is a heuristic from 0 to 1.")

act_tab, work_tab, methods_tab = st.tabs(["Act: this week", "Account workspace", "Validation & handoff"])
with act_tab:
    render_act_tab(filtered, history, synthetic=synthetic)
with work_tab:
    st.subheader("Account watchlist")
    sort_by = st.selectbox("Sort by", ["Early warning (recently active first)", "Highest risk", "Highest historical value", "Longest inactivity"], key="sort")
    if sort_by == "Early warning (recently active first)":
        view = filtered.assign(_already_inactive=filtered.days_since_last_order.gt(60)).sort_values(
            ["_already_inactive", "risk_probability", "account_id"], ascending=[True, False, True], na_position="last").drop(columns="_already_inactive")
        st.caption("Recently active accounts appear first, ranked by forecast risk. Already inactive accounts remain below for reactivation review.")
    else:
        sortcol = {"Highest risk": "risk_probability", "Highest historical value": "historical_spend", "Longest inactivity": "days_since_last_order"}[sort_by]
        view = filtered.sort_values([sortcol, "account_id"], ascending=[False, True], na_position="last")
    display = view[["account_id", "city", "state", "risk_level", "risk_score", "model_confidence",
                    "current_activity",
                    "historical_spend", "historical_order_count", "days_since_last_order", "cadence_ratio",
                    "spend_change", "frequency_change", "categories_dropped_count", "top_risk_reason_1"]].copy()
    display["spend_change"] = display.spend_change * 100
    display["frequency_change"] = display.frequency_change * 100
    st.dataframe(display, hide_index=True, width="stretch", column_config={
        "account_id": "Account", "city": "City", "state": "State", "risk_level": "Risk band",
        "current_activity": "Current activity",
        "risk_score": st.column_config.NumberColumn("Risk estimate", format="%.1f / 100"),
        "model_confidence": "Confidence", "historical_spend": st.column_config.NumberColumn("Historical value", format="%.0f"),
        "historical_order_count": "Orders", "days_since_last_order": "Inactive days",
        "cadence_ratio": st.column_config.NumberColumn("Cadence ratio", format="%.1f×"),
        "spend_change": st.column_config.NumberColumn("Value change", format="%.0f%%"),
        "frequency_change": st.column_config.NumberColumn("Order change", format="%.0f%%"),
        "categories_dropped_count": "Categories absent", "top_risk_reason_1": "Main evidence"}, height=330)
    st.download_button("Download filtered handoff CSV", filtered.to_csv(index=False).encode(),
                       file_name="scored_accounts_filtered.csv", mime="text/csv")
    if view.empty:
        st.info("No accounts match these filters. Broaden the filters to continue.")
    else:
        options = view.account_id.tolist()
        if st.session_state.get("selected_account") not in options:
            st.session_state["selected_account"] = options[0]
        selected = st.selectbox("Open account", options, key="selected_account")
        row = view[view.account_id == selected].iloc[0]
        st.subheader(f"{selected} · {row.city.title()} · {row.state}")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Risk estimate", f"{row.risk_probability:.0%}" if pd.notna(row.risk_probability) else "Unscored", row.risk_level, delta_color="off")
        d2.metric("Evidence confidence", row.model_confidence)
        d3.metric("Typical ordering gap", show_number(row.median_order_gap_days, " days"))
        d4.metric("Since last order", show_number(row.days_since_last_order, " days"))
        st.caption("Percentages are model estimates of future inactivity, not confirmed churn. No future label is available at the scoring date.")
        st.caption(f"Current activity: {row.current_activity}. Forecast risk does not measure recoverability or the value of an intervention.")
        st.markdown("#### Evidence behind the account")
        for reason in json.loads(row.explanations_json):
            text = reason["text"]
            kind = reason["evidence_type"]
            with st.container(border=True):
                st.markdown(f"**{text}**")
                if kind == "model sensitivity":
                    st.caption(f"Model sensitivity · estimate falls {reason['probability_delta']:.1%} when this input is replaced with its training median. This is not a causal effect.")
                elif kind == "observed context":
                    st.caption("Observed context · supporting account evidence, separate from the selected model's measured inputs.")
                else:
                    st.caption("Coverage limitation · this account is outside the validated population.")
        h = history[history.account_id == selected] if not history.empty else pd.DataFrame()
        if not h.empty:
            h = h.copy()
            h["month"] = pd.to_datetime(h.month + "-01")
            a, b = st.columns(2)
            with a:
                chart(h, "month", "order_count", "Orders each month, including gaps")
                chart(h, "month", "category_count", "Categories purchased each month", "line")
            with b:
                chart(h, "month", "spend", "Merchandise value each month")
                gap = gaps[(gaps.account_id == selected) & gaps.gap_days.notna()].copy() if not gaps.empty else pd.DataFrame()
                if not gap.empty:
                    chart(gap, "order_day", "gap_days", "Completed gaps between order days", "line")
                else:
                    st.info("Not enough distinct order days to plot ordering gaps.")
        else:
            st.info("Monthly history is not available in this output folder.")
        with st.expander("Account facts and category evidence"):
            facts = {"Historical orders": row.historical_order_count, "Active months": row.active_months,
                     "First order": row.first_order_date, "Last order": row.last_order_date,
                     "Historical value proxy": row.historical_spend, "Recent 90-day value": row.spend_last_90d,
                     "Categories historically": row.historical_category_count,
                     "Average available review": row.avg_review_score,
                     "Latest available review": row.latest_review_score,
                     "Observed late-delivery rate": row.late_delivery_rate}
            st.dataframe(pd.DataFrame({"Fact": facts.keys(), "Value": [str(v) if pd.notna(v) else "Unavailable" for v in facts.values()]}), hide_index=True, width="stretch")
            categories = json.loads(row.categories_dropped)
            st.write("Repeat portfolio lines absent recently: " + (pretty(", ".join(categories)) if categories else "None identified"))
            st.caption("Category names stand for portfolio lines in this adapted dataset. 'Absent' means ≥2 distinct orders in the previous 90 days and none in the current 90 days; it is a descriptive rule, not validated causal churn evidence.")
        st.markdown("#### Recommended action")
        payload = selected_account_payload(row)
        action = recommended_action(payload)
        action_card(action, accounts)
        st.download_button("Export selected account JSON", json.dumps(payload, indent=2), file_name=f"{selected}_handoff.json", mime="application/json")

with methods_tab:
    st.subheader("How to interpret the forecast")
    st.write("Target: no placed order during the next 60 days. Model coverage: at least 10 orders, 180 days of history and 3 positive ordering-day gaps. Every other account stays visible with a blank probability.")
    st.write("Confidence is an evidence label, separate from risk. High requires at least 20 orders, 365 days of history and ordering-gap variation ≤1. Other eligible accounts are Medium; accounts outside model coverage are Low.")
    if synthetic:
        st.info("This demo has no measured validation results. See docs/results for the completed dataset analysis, or run the pipeline for live diagnostics.")
    else:
        holdout = metadata.get("holdout", {})
        if holdout:
            a, b, c, d = st.columns(4)
            a.metric("Held-out ROC-AUC", f"{holdout['roc_auc']:.3f}")
            b.metric("Held-out PR-AUC", f"{holdout['pr_auc']:.3f}")
            c.metric("Precision · top 100", f"{holdout['precision_at_100']:.0%}")
            d.metric("Top-decile lift", f"{holdout['top_decile_lift']:.2f}×")
        active = metadata.get("active_account_holdout", {})
        if active:
            st.info(f"Early-warning subset: among accounts ordered within the previous 60 days, ROC-AUC {active['roc_auc']:.3f} and top-100 precision {active['precision_at_100']:.0%}, versus inactivity prevalence {active['prevalence']:.0%}. Overall scores also include accounts already inactive for longer.")
        for filename, title in [("model_metrics.csv", "Temporal model comparison"), ("risk_tier_validation.csv", "Historical outcomes by risk band"),
                                ("calibration.csv", "Estimated versus observed inactivity"), ("feature_importance.csv", "Measured predictive inputs"),
                                ("current_activity_metrics.csv", "Recently active versus already inactive"),
                                ("target_sensitivity_metrics.csv", "Alternative-target sensitivity")]:
            path = folder / filename
            if path.exists():
                with st.expander(title):
                    st.dataframe(pd.read_csv(path), hide_index=True, width="stretch")
        summary = folder / "model_summary.md"
        if summary.exists():
            st.download_button("Download model summary", summary.read_text(), file_name="model_summary.md")
    st.markdown("#### Teammate integration")
    st.write("Use the scored-account CSV or selected-account JSON. The Act hook in app/action_layer.py reads the bundled Ritmo exports. Modelled status, nullable probability, target horizon, evidence reasons and schema version travel with the record.")
    st.caption("The repository includes derived challenge outputs in demo_data and fictional examples in examples. Supplied raw CSVs are excluded. Ritmo training and validation scripts are not included.")
