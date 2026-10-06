from streamlit.testing.v1 import AppTest
from src.config import ROOT


def app(monkeypatch):
    monkeypatch.setenv("IDENTIFY_OUTPUT_DIR", str(ROOT / "examples"))
    return AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()


def test_demo_loads_and_account_navigation_works(monkeypatch):
    a = app(monkeypatch)
    assert not a.exception
    assert a.metric[0].value == "12"
    a.selectbox(key="selected_account").set_value("DEMO0004").run()
    assert not a.exception
    assert "DEMO0004" in a.subheader[1].value


def test_search_filter_and_empty_result(monkeypatch):
    a = app(monkeypatch)
    a.text_input(key="search").set_value("DEMO0001").run()
    assert not a.exception
    assert a.metric[0].value == "1"
    assert a.selectbox(key="selected_account").value == "DEMO0001"
    a.text_input(key="search").set_value("no-match-anywhere").run()
    assert not a.exception
    assert a.metric[0].value == "0"


def test_risk_and_activity_filters(monkeypatch):
    a = app(monkeypatch)
    a.multiselect(key="levels").set_value(["High"]).run()
    assert not a.exception
    assert a.metric[0].value == "3"
    a.radio(key="activity").set_value("Ordered within 60 days").run()
    assert not a.exception
    assert a.metric[0].value == "0"
