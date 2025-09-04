# tests/unit/test_share_forecast.py
import sys
import types
import pytest
from unittest.mock import patch, MagicMock

from weather_travel_agent.agent.nodes.share_forecast import ShareForecastNode


@pytest.fixture
def fake_state():
    return {
        "origin": "Atlanta, GA",
        "destination": "Nashville, TN",
        "forecasts": [
            {"name": "Atlanta, GA", "summary": "Sunny"},
            {"name": "Chattanooga, TN", "summary": "Cloudy"},
            {"name": "Nashville, TN", "summary": "Rain"},
        ],
    }


def test_create_response_returns_llm_output(fake_state):
    node = ShareForecastNode()

    with patch("weather_travel_agent.agent.nodes.share_forecast.settings") as mock_settings, \
         patch("weather_travel_agent.agent.nodes.share_forecast.ChatOpenAI") as mock_llm_cls:

        mock_settings.openai_api_key = "fake-key"
        mock_settings.openai_model = "gpt-test"

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Your trip looks good!"
        mock_llm_cls.return_value = mock_llm

        result = node(fake_state)

        assert "reply" in result
        assert result["reply"] == "Your trip looks good!"
        mock_llm.invoke.assert_called_once()


def test_create_response_falls_back_to_itinerary_on_empty_llm(fake_state):
    node = ShareForecastNode()

    with patch("weather_travel_agent.agent.nodes.share_forecast.settings") as mock_settings, \
         patch("weather_travel_agent.agent.nodes.share_forecast.ChatOpenAI") as mock_llm_cls:

        mock_settings.openai_api_key = "fake-key"
        mock_settings.openai_model = "gpt-test"

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = ""
        mock_llm_cls.return_value = mock_llm

        result = node(fake_state)
        assert "Trip from Atlanta, GA to Nashville, TN:" in result["reply"]


def test_create_response_falls_back_when_no_api_key(fake_state):
    node = ShareForecastNode()

    with patch("weather_travel_agent.agent.nodes.share_forecast.settings") as mock_settings:
        mock_settings.openai_api_key = None
        mock_settings.openai_model = "gpt-test"

        result = node(fake_state)
        assert "Trip from Atlanta, GA to Nashville, TN:" in result["reply"]
