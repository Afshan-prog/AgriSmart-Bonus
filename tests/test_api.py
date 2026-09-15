from fastapi.testclient import TestClient
from unittest.mock import patch
from httpx import TimeoutException, RequestError
from app.main import app
import json

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_bonus_analyze_success():
    """Test the bonus analyze endpoint with valid data."""
    payload = {
        "crop": "Wheat",
        "disease": "Rust",
        "confidence": 0.95,
        "latitude": 34.0522,
        "longitude": -118.2437
    }
    response = client.post("/bonus/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    assert "not implemented yet" in data["message"].lower()

def test_bonus_analyze_empty_payload():
    """Test the bonus analyze endpoint with an empty payload."""
    response = client.post("/bonus/analyze", json={})
    assert response.status_code == 200

def test_bonus_analyze_malformed_input():
    """Test the bonus analyze endpoint with invalid data type."""
    response = client.post("/bonus/analyze", json={"confidence": "high"})
    assert response.status_code == 422

# --- Weather Intelligence Tests ---

def test_weather_success():
    mock_json = {
        "current": {
            "temperature_2m": 36.0,
            "relative_humidity_2m": 45,
            "precipitation": 0.0,
            "wind_speed_10m": 42.0
        },
        "daily": {
            "precipitation_probability_max": [10],
            "temperature_2m_max": [38.0],
            "temperature_2m_min": [22.0]
        }
    }
    
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        
        response = client.post("/bonus/weather", json={"latitude": 34.0, "longitude": -118.0})
        
        assert response.status_code == 200
        data = response.json()
        assert data["current"]["temperature_c"] == 36.0
        assert data["indicators"]["high_temperature_flag"] is True
        assert data["indicators"]["high_wind_flag"] is True
        assert data["indicators"]["rain_expected"] is False
        assert "monitor crop water stress" in data["indicators"]["irrigation_weather_note"].lower()

def test_weather_invalid_latitude():
    response = client.post("/bonus/weather", json={"latitude": 100.0, "longitude": -118.0})
    assert response.status_code == 422

def test_weather_invalid_longitude():
    response = client.post("/bonus/weather", json={"latitude": 34.0, "longitude": 200.0})
    assert response.status_code == 422

def test_weather_api_timeout():
    with patch("httpx.AsyncClient.get", side_effect=TimeoutException("Timeout")):
        response = client.post("/bonus/weather", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 504
        assert response.json()["detail"] == "Weather API timeout"

def test_weather_api_failure():
    with patch("httpx.AsyncClient.get", side_effect=RequestError("Network error")):
        response = client.post("/bonus/weather", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 502
        assert response.json()["detail"] == "Weather API request failed"

# --- Geocoding Tests ---

def test_location_search_success():
    mock_json = {
        "results": [
            {
                "name": "Los Angeles",
                "latitude": 34.05223,
                "longitude": -118.24368,
                "country_code": "US",
                "admin1": "California",
                "country": "United States"
            }
        ]
    }
    
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.get("/bonus/location?query=Los%20Angeles")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "Los Angeles"
        assert data["results"][0]["country_code"] == "US"

def test_location_search_no_results():
    mock_json = {}
    
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.get("/bonus/location?query=UnknownPlace123")
        assert response.status_code == 200
        assert response.json()["results"] == []

def test_location_search_invalid_query():
    response = client.get("/bonus/location?query=a")
    assert response.status_code == 422

def test_location_search_api_failure():
    with patch("httpx.AsyncClient.get", side_effect=RequestError("Network error")):
        response = client.get("/bonus/location?query=Los%20Angeles")
        assert response.status_code == 502

# --- Irrigation Tests ---

def test_irrigation_rain():
    mock_json = {
        "current": {"temperature_2m": 20.0, "relative_humidity_2m": 50, "precipitation": 1.5, "wind_speed_10m": 10.0},
        "daily": {"precipitation_probability_max": [60], "temperature_2m_max": [25.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "PAUSE_IRRIGATION"

def test_irrigation_high_wind():
    mock_json = {
        "current": {"temperature_2m": 20.0, "relative_humidity_2m": 50, "precipitation": 0.0, "wind_speed_10m": 40.0},
        "daily": {"precipitation_probability_max": [0], "temperature_2m_max": [25.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "RESTRICT_OVERHEAD_IRRIGATION"

def test_irrigation_high_heat():
    mock_json = {
        "current": {"temperature_2m": 36.0, "relative_humidity_2m": 50, "precipitation": 0.0, "wind_speed_10m": 10.0},
        "daily": {"precipitation_probability_max": [0], "temperature_2m_max": [38.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "HEAT_CAUTION"

def test_irrigation_normal():
    mock_json = {
        "current": {"temperature_2m": 20.0, "relative_humidity_2m": 50, "precipitation": 0.0, "wind_speed_10m": 10.0},
        "daily": {"precipitation_probability_max": [0], "temperature_2m_max": [25.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "NO_WEATHER_TRIGGER"

def test_irrigation_rain_wins_over_heat():
    mock_json = {
        "current": {"temperature_2m": 36.0, "relative_humidity_2m": 50, "precipitation": 2.0, "wind_speed_10m": 10.0},
        "daily": {"precipitation_probability_max": [70], "temperature_2m_max": [38.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "PAUSE_IRRIGATION"

def test_irrigation_wind_wins_over_heat():
    mock_json = {
        "current": {"temperature_2m": 36.0, "relative_humidity_2m": 50, "precipitation": 0.0, "wind_speed_10m": 40.0},
        "daily": {"precipitation_probability_max": [0], "temperature_2m_max": [38.0], "temperature_2m_min": [15.0]}
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MockResponse()
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 200
        assert response.json()["irrigation_status"] == "RESTRICT_OVERHEAD_IRRIGATION"

def test_irrigation_api_timeout():
    with patch("httpx.AsyncClient.get", side_effect=TimeoutException("Timeout")):
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 504

def test_irrigation_api_failure():
    with patch("httpx.AsyncClient.get", side_effect=RequestError("Network error")):
        response = client.post("/bonus/irrigation", json={"latitude": 34.0, "longitude": -118.0})
        assert response.status_code == 502

def test_irrigation_invalid_coordinates():
    response = client.post("/bonus/irrigation", json={"latitude": 100.0, "longitude": -118.0})
    assert response.status_code == 422

# --- Farmer Assistant Tests ---

def get_assistant_payload():
    return {
        "crop": "Corn",
        "disease_prediction": "Northern Leaf Blight",
        "confidence": 0.95,
        "temperature_c": 29.1,
        "humidity_percent": 78,
        "rain_probability": 86,
        "irrigation_status": "PAUSE_IRRIGATION",
        "irrigation_driver": "Natural Precipitation"
    }

def get_mock_llm_json(is_low_confidence=False):
    return json.dumps({
        "summary": "AI suggests Corn has Northern Leaf Blight.",
        "what_it_means": "The warm wet weather favors this disease.",
        "recommended_actions": ["Monitor leaves", "Ensure good airflow"],
        "weather_note": "High rain chance.",
        "irrigation_note": "Irrigation is paused.",
        "warning": "This is an AI prediction, not a confirmed diagnosis.",
        "confidence_note": "Confidence is low." if is_low_confidence else "Confidence is high."
    })

def test_assistant_valid_response():
    mock_json = {
        "choices": [
            {"message": {"content": get_mock_llm_json()}}
        ]
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["source"] == "llm"
        assert "Northern Leaf Blight" in data["content"]["summary"]

def test_assistant_valid_low_confidence():
    mock_json = {
        "choices": [
            {"message": {"content": get_mock_llm_json(is_low_confidence=True)}}
        ]
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    payload = get_assistant_payload()
    payload["confidence"] = 0.54
    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=payload)
        assert response.status_code == 200
        assert response.json()["content"]["confidence_note"] == "Confidence is low."

def test_assistant_api_timeout():
    with patch("httpx.AsyncClient.post", side_effect=TimeoutException("Timeout")), \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fallback"
        assert data["source"] == "deterministic"

def test_assistant_api_429():
    with patch("httpx.AsyncClient.post", side_effect=RequestError("Network error")), \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        assert response.json()["status"] == "fallback"

def test_assistant_api_502():
    with patch("httpx.AsyncClient.post", side_effect=Exception("502 Bad Gateway")), \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        assert response.json()["status"] == "fallback"

def test_assistant_invalid_json():
    mock_json = {
        "choices": [
            {"message": {"content": "This is not valid JSON string!"}}
        ]
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        assert response.json()["status"] == "fallback"

def test_assistant_missing_choices():
    mock_json = {"other_key": []}
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        assert response.json()["status"] == "fallback"

def test_assistant_safety_guard_blocks_unsafe():
    # Model generates explicit dosage (unsafe)
    unsafe_content = get_mock_llm_json()
    unsafe_content = unsafe_content.replace("Monitor leaves", "apply exactly 50 ml/l of chemical")
    
    mock_json = {
        "choices": [
            {"message": {"content": unsafe_content}}
        ]
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        # Should be blocked and return fallback
        assert response.json()["status"] == "fallback"

def test_assistant_safety_guard_allows_safe_phrases():
    # Model correctly outputs the safe phrase (which used to be blocked by naive string match)
    safe_content = get_mock_llm_json()
    safe_content = safe_content.replace("This is an AI prediction, not a confirmed diagnosis.", "This is an AI prediction, not a confirmed diagnosis.")
    
    mock_json = {
        "choices": [
            {"message": {"content": safe_content}}
        ]
    }
    class MockResponse:
        def json(self): return mock_json
        def raise_for_status(self): pass

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.config.settings.OPENROUTER_API_KEY", "dummy_key"):
        mock_post.return_value = MockResponse()
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
def test_assistant_missing_api_key():
    with patch("app.config.settings.OPENROUTER_API_KEY", ""):
        response = client.post("/bonus/assistant", json=get_assistant_payload())
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fallback"
        assert data["source"] == "deterministic"

