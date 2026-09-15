from fastapi.testclient import TestClient
from unittest.mock import patch
from httpx import TimeoutException, RequestError
from app.main import app

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
