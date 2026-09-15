"""
Weather service logic using Open-Meteo API.
"""
import httpx
from fastapi import HTTPException
import logging

from app.schemas import (
    CurrentWeather,
    ForecastWeather,
    AgriculturalIndicators,
    WeatherResponse
)

logger = logging.getLogger(__name__)

# --- Prototype / Configurable Engineering Thresholds ---
# NOTE: These are NOT universal agronomic thresholds. They are configurable 
# prototype values for demonstrating the intelligence module capabilities.
HIGH_TEMP_THRESHOLD_C = 35.0
HIGH_WIND_THRESHOLD_KMH = 40.0
RAIN_PRECIPITATION_THRESHOLD_MM = 0.5
RAIN_PROBABILITY_THRESHOLD_PERCENT = 50
# --------------------------------------------------------

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def get_weather_intelligence(latitude: float, longitude: float) -> WeatherResponse:
    """
    Fetches weather data from Open-Meteo, normalizes it, and calculates agricultural indicators.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "precipitation_probability_max,temperature_2m_max,temperature_2m_min",
        "timezone": "auto"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("Weather API timeout")
        raise HTTPException(status_code=504, detail="Weather API timeout")
    except httpx.RequestError as e:
        logger.error(f"Weather API request error: {e}")
        raise HTTPException(status_code=502, detail="Weather API request failed")
    except httpx.HTTPStatusError as e:
        logger.error(f"Weather API returned status error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail="Weather API returned an error")
    except ValueError:
        logger.error("Failed to parse Weather API JSON response")
        raise HTTPException(status_code=502, detail="Invalid response from Weather API")

    # Extract current weather
    current = data.get("current", {})
    temp_c = current.get("temperature_2m", 0.0)
    humidity = current.get("relative_humidity_2m", 0.0)
    precip_mm = current.get("precipitation", 0.0)
    wind_kmh = current.get("wind_speed_10m", 0.0)

    # Extract forecast weather (daily returns arrays, we take today's index 0)
    daily = data.get("daily", {})
    precip_prob_list = daily.get("precipitation_probability_max", [])
    max_temp_list = daily.get("temperature_2m_max", [])
    min_temp_list = daily.get("temperature_2m_min", [])

    precip_prob = precip_prob_list[0] if precip_prob_list else None
    max_temp = max_temp_list[0] if max_temp_list else None
    min_temp = min_temp_list[0] if min_temp_list else None

    # Calculate indicators
    rain_expected = False
    if precip_prob is not None and precip_prob >= RAIN_PROBABILITY_THRESHOLD_PERCENT:
        rain_expected = True
    elif precip_mm >= RAIN_PRECIPITATION_THRESHOLD_MM:
        rain_expected = True

    high_temp_flag = False
    if max_temp is not None and max_temp >= HIGH_TEMP_THRESHOLD_C:
        high_temp_flag = True
    elif temp_c >= HIGH_TEMP_THRESHOLD_C:
        high_temp_flag = True

    high_wind_flag = wind_kmh >= HIGH_WIND_THRESHOLD_KMH

    # Note formulation
    notes = []
    if high_temp_flag:
        notes.append("High heat conditions detected; monitor crop water stress.")
    if rain_expected:
        notes.append("Rain expected; factor precipitation into irrigation schedule.")
    if high_wind_flag:
        notes.append("High winds detected; check for potential mechanical stress on crops.")

    if not notes:
        notes.append("Weather conditions are normal. Proceed with standard irrigation schedule.")

    irrigation_note = " ".join(notes)

    return WeatherResponse(
        current=CurrentWeather(
            temperature_c=temp_c,
            humidity_percent=humidity,
            precipitation_mm=precip_mm,
            wind_speed_kmh=wind_kmh
        ),
        forecast=ForecastWeather(
            max_temperature_c=max_temp,
            min_temperature_c=min_temp,
            precipitation_probability_percent=precip_prob
        ),
        indicators=AgriculturalIndicators(
            rain_expected=rain_expected,
            high_temperature_flag=high_temp_flag,
            high_wind_flag=high_wind_flag,
            irrigation_weather_note=irrigation_note
        )
    )
