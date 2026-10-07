"""Regression checks for the combined team demo, including previously failing paths."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.act_engine import load_priority, morning_briefing_text, plan
from app.action_layer import recommended_action
from src.config import ROOT


def challenge_app(monkeypatch):
    monkeypatch.setenv("IDENTIFY_OUTPUT_DIR", str(ROOT / "demo_data" / "identify"))
    return AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()


@pytest.mark.parametrize("account_id", ["A01003", "A01004"])
def test_sparse_account_navigation_and_act_filters(monkeypatch, account_id):
    app = challenge_app(monkeypatch)
    assert not app.exception
    app.text_input(key="search").set_value(account_id).run()
    assert not app.exception
    assert app.metric[0].value == "1"
    assert app.selectbox(key="selected_account").value == account_id
    assert "unranked" in recommended_action({"account_id": account_id})["title"]
    assert sum(int(metric.value.replace(",", "")) for metric in app.metric[5:9]) == 1


def test_fictional_demo_never_loads_challenge_act_accounts(monkeypatch):
    monkeypatch.setenv("IDENTIFY_OUTPUT_DIR", str(ROOT / "examples"))
    app = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "12"
    assert "route_pick" not in [select.key for select in app.selectbox]
    assert "call_pick" not in [select.key for select in app.selectbox]
    # Even a colliding account ID must not join challenge priorities in fictional mode.
    assert plan({"account_id": "A20080", "data_kind": "synthetic"}) is None


def test_different_snapshot_does_not_use_stale_act_records():
    assert plan({"account_id": "A20080", "analysis_date": "2018-06-30"}) is None


def test_morning_briefing_and_route_navigation(monkeypatch):
    app = challenge_app(monkeypatch)
    assert not app.exception
    prio = load_priority()
    for route in ["RJ week 1", "SP week 1"]:
        app.selectbox(key="route_pick").set_value(route).run()
        assert not app.exception
        stops = prio[prio.route.eq(route)]
        expected = morning_briefing_text(stops, route)
        assert expected in [text.value for text in app.markdown]
        labels = app.selectbox(key="stop_pick").options
        assert {label.split(" · ")[1] for label in labels} == set(stops.account_id)
        assert app.selectbox(key="stop_pick").value in set(stops.account_id)
        assert "weekly route" in expected
        assert "60-day risk estimate" in expected


def test_morning_briefing_handles_single_stop():
    stops = pd.DataFrame([{"rank": 2, "account_id": "A00123", "city": "example city",
                           "value_at_risk": 100, "churn_chance_pct": 30}])
    text = morning_briefing_text(stops, "EX week 1")
    assert "A00123" in text
    assert "1 priority visits" in text
    assert "Other accounts" not in text


def test_call_requires_acceptance_and_updates_one_feedback_record(monkeypatch):
    app = challenge_app(monkeypatch)
    assert not app.exception
    account_id = app.selectbox(key="call_pick").value
    app.radio(key=f"r{account_id}").set_value("Price").run()
    assert not app.exception
    assert app.session_state["call_log"][0]["outcome"] == "Offer proposed (demo)"
    app.radio(key=f"offer_{account_id}_Price").set_value("Accept offer").run()
    assert not app.exception
    assert app.session_state["call_log"][0]["outcome"] == "Offer accepted (demo)"
    assert len(app.session_state["call_log"]) == 1
    app.run()
    assert len(app.session_state["call_log"]) == 1
    app.radio(key=f"r{account_id}").set_value("Closed or quiet season").run()
    assert not app.exception
    assert app.session_state["call_log"][0]["outcome"] == "Contact paused (demo)"
    assert len(app.session_state["call_log"]) == 1
    assert not app.success


def test_rep_followup_is_labelled_as_session_demo(monkeypatch):
    app = challenge_app(monkeypatch)
    account_id = app.selectbox(key="call_pick").value
    original_routes = load_priority()[["account_id", "lane", "route"]].copy()
    app.radio(key=f"r{account_id}").set_value("Delivery or service problem").run()
    assert not app.exception
    assert app.session_state["call_log"][0]["outcome"] == "Rep follow-up requested (demo)"
    assert any("visit routes are unchanged" in warning.value for warning in app.warning)
    pd.testing.assert_frame_equal(original_routes, load_priority()[["account_id", "lane", "route"]])
