"""Smoke tests for the Cooking Assistant Flask app.

These tests exercise the app without requiring any LLM API keys; the agent
falls back to the keyword router in that case.
"""

from __future__ import annotations

import os

import pytest

# Make sure no real LLM provider is selected for tests.
os.environ.setdefault("LLM_PROVIDER", "none")

from app.api import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_app_starts() -> None:
    app = create_app()
    assert app is not None
    assert app.name


def test_health_endpoint(client) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "cooking-assistant"
    assert "timestamp" in payload


def test_list_recipes(client) -> None:
    resp = client.get("/api/recipes")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "recipes" in payload
    assert isinstance(payload["recipes"], list)
    assert len(payload["recipes"]) >= 1
    first = payload["recipes"][0]
    for field in ("id", "name", "cuisine", "difficulty"):
        assert field in first


def test_chat_keyword_fallback(client) -> None:
    resp = client.post(
        "/api/chat",
        json={"session_id": "smoke", "message": "Show me Italian recipes"},
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "response" in payload
    assert isinstance(payload["response"], str)
    assert payload["response"].strip()
    # With LLM_PROVIDER=none the agent must operate in fallback mode.
    assert payload.get("llm_enabled") is False


def test_convert_units(client) -> None:
    resp = client.post(
        "/api/convert",
        json={"amount": 1, "from_unit": "cup", "to_unit": "ml"},
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["type"] == "volume"
    assert payload["converted"]["unit"] == "ml"
    # 1 cup = 236.588 ml (rounded to 236.59 by the API).
    assert payload["converted"]["amount"] == pytest.approx(236.59, rel=1e-3)
