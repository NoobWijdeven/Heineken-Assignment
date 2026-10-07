"""Regression cases observed in the recorded challenge demo."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.act_engine import load_priority, plan, pretty, service_note
from app.data_access import read_outputs, selected_account_payload
from src.config import ROOT


@pytest.fixture(scope="module")
def accounts():
    return read_outputs(ROOT / "demo_data" / "identify")[0].set_index("account_id", drop=False)


def account_plan(accounts, account_id):
    return plan(selected_account_payload(accounts.loc[account_id]))


def test_rep_briefing_uses_selected_identify_facts_without_mutating_export(accounts):
    original = load_priority().loc["A24220"].copy()
    act = account_plan(accounts, "A24220")
    assert original.typical_gap_days == 7
    assert act["record"]["typical_gap_days"] == 5  # Distinct order-day cadence in Identify.
    assert act["forecast_probability"] == pytest.approx(accounts.loc["A24220", "risk_probability"])
    assert act["exported_record"]["churn_chance_pct"] == 24
    assert "typical 5-day" in act["contact_context"]
    assert act["reasons"] == accounts.loc["A24220", [f"top_risk_reason_{i}" for i in range(1, 4)]].tolist()
    pd.testing.assert_series_equal(load_priority().loc["A24220"], original)


def test_dormant_account_is_reactivation_with_historical_service_context(accounts):
    act = account_plan(accounts, "A87013")
    assert act["contact_status"] == "Reactivation check"
    assert "365 days" in act["contact_context"]
    assert "still trading" in act["call"]["opener"]
    assert "Historical export note" in service_note(act["record"])
    assert "do not assume a current complaint" in act["briefing"]
    assert "slowed down" not in act["briefing"]
    assert "baby" not in act["whatsapp"] + act["briefing"] + act["offer"]["detail"]
    assert "Portfolio line" in act["offer"]["detail"]
    assert "Linha do portfólio" in act["whatsapp"]


def test_recent_sparse_account_is_not_presented_as_overdue_or_scored(accounts):
    act = account_plan(accounts, "A56250")
    assert act["forecast_probability"] is None
    assert act["contact_status"] == "Within usual cadence"
    assert "9 days ago" in act["contact_context"]
    assert "89-day" in act["contact_context"]
    assert "longer than" not in act["call"]["opener"]
    assert "not need stock yet" in act["call"]["ask"]


def test_sparse_history_and_monitor_do_not_invent_cadence_or_schedule_offers(accounts):
    sparse = account_plan(accounts, "A01003")
    assert sparse["forecast_probability"] is None
    assert sparse["contact_status"] == "Cadence unavailable"
    assert "not enough ordering history" in sparse["contact_context"]
    monitor_id = load_priority().query("lane == 'Monitor'").iloc[0].account_id
    monitor = account_plan(accounts, monitor_id)
    assert "No outreach or offer is scheduled" in monitor["briefing"]
    assert monitor["offer"]["detail"] not in monitor["briefing"]


def test_offer_uses_loaded_category_absence_not_conflicting_export(accounts):
    payload = selected_account_payload(accounts.loc["A24220"])
    payload["categories_dropped"] = []
    assert plan(payload)["offer"]["headline"].startswith("Restock reminder")
    payload["categories_dropped"] = ["health_beauty"]
    assert pretty("health_beauty") in plan(payload)["offer"]["headline"]
    assert "health_beauty" not in plan(payload)["offer"]["detail"]


def test_spoken_call_matches_pause_and_no_need_outcomes_and_resets_acceptance(monkeypatch):
    spoken = {}
    monkeypatch.setattr("app.act_views.speak_button", lambda text, key, **kwargs: spoken.update({key: text}))
    monkeypatch.setenv("IDENTIFY_OUTPUT_DIR", str(ROOT / "demo_data" / "identify"))
    app = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    account_id = app.selectbox(key="call_pick").value
    app.radio(key=f"r{account_id}").set_value("Closed or quiet season").run()
    assert not app.exception
    assert "pause contact" in spoken[f"call{account_id}"]
    assert "illustrative offer" not in spoken[f"call{account_id}"]
    app.radio(key=f"r{account_id}").set_value("Just forgot / no need yet").run()
    assert not app.exception
    assert "no need to order now" in spoken[f"call{account_id}"]
    assert "illustrative offer" not in spoken[f"call{account_id}"]
    assert app.session_state["call_log"][0]["outcome"] == "Needs check-in requested (demo)"
    assert not any(r.key.startswith(f"offer_{account_id}") for r in app.radio)
    app.radio(key=f"r{account_id}").set_value("Price").run()
    app.radio(key=f"offer_{account_id}_Price").set_value("Accept offer").run()
    assert app.session_state["call_log"][0]["outcome"] == "Offer accepted (demo)"
    app.radio(key=f"r{account_id}").set_value("Closed or quiet season").run()
    app.radio(key=f"r{account_id}").set_value("Price").run()
    assert not app.exception
    assert app.radio(key=f"offer_{account_id}_Price").value == "Not decided"
    assert app.session_state["call_log"][0]["outcome"] == "Offer proposed (demo)"
    assert len(app.session_state["call_log"]) == 1


def test_route_forecasts_and_default_watchlist_use_identify(monkeypatch, accounts):
    monkeypatch.setenv("IDENTIFY_OUTPUT_DIR", str(ROOT / "demo_data" / "identify"))
    app = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    table = next(t.value for t in app.dataframe if "stop" in t.value.columns)
    assert "churn_chance_pct" not in table.columns
    pd.testing.assert_series_equal(table.set_index("account_id").compass_forecast_pct,
                                   accounts.loc[table.account_id, "risk_probability"] * 100, check_names=False)
    first = app.selectbox(key="selected_account").value
    assert accounts.loc[first, "days_since_last_order"] <= 60
    app.text_input(key="search").set_value("A87013").run()
    assert not app.exception
    assert app.selectbox(key="selected_account").value == "A87013"
    texts = " ".join(t.value for t in app.markdown)
    assert "Reactivation check" in texts
    assert "Ritmo 60-day risk estimate" not in texts
