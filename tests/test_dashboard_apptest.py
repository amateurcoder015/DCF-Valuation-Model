"""Streamlit AppTest smoke test for app.py."""

from streamlit.testing.v1 import AppTest
import pytest


def test_streamlit_app_smoke():
    """Verify that app.py loads, renders input widgets without exceptions, and contains key controls."""
    at = AppTest.from_file("app.py", default_timeout=10.0).run()

    # Assert app loads without throwing unhandled exceptions
    assert not at.exception

    # Assert page title or headline elements rendered
    assert len(at.title) > 0
    assert "Discounted Cash Flow" in at.title[0].value

    # Assert sidebar inputs rendered
    assert len(at.sidebar.text_input) >= 1
    assert at.sidebar.text_input[0].value == "AAPL"

    # Assert Run Valuation button rendered
    assert len(at.sidebar.button) >= 1
    assert "Run DCF Valuation" in at.sidebar.button[0].label
