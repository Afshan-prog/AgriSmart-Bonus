"""
Geocoding service logic using Open-Meteo Geocoding API.
"""
import httpx
from fastapi import HTTPException
import logging

from app.schemas import LocationResult, LocationSearchResponse

logger = logging.getLogger(__name__)

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

async def search_locations(query: str) -> LocationSearchResponse:
    """
    Searches for locations matching the query using Open-Meteo Geocoding API.
    Returns up to 5 matches.
    """
    clean_query = query.strip()
    if len(clean_query) < 2 or len(clean_query) > 100:
        raise HTTPException(status_code=422, detail="Query length must be between 2 and 100 characters.")

    params = {
        "name": clean_query,
        "count": 5,
        "language": "en",
        "format": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(GEOCODING_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("Geocoding API timeout")
        raise HTTPException(status_code=504, detail="Geocoding API timeout")
    except httpx.RequestError as e:
        logger.error(f"Geocoding API request error: {e}")
        raise HTTPException(status_code=502, detail="Geocoding API request failed")
    except httpx.HTTPStatusError as e:
        logger.error(f"Geocoding API returned status error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail="Geocoding API returned an error")
    except ValueError:
        logger.error("Failed to parse Geocoding API JSON response")
        raise HTTPException(status_code=502, detail="Invalid response from Geocoding API")

    raw_results = data.get("results", [])
    if not raw_results:
        return LocationSearchResponse(results=[])

    mapped_results = []
    for item in raw_results:
        mapped_results.append(
            LocationResult(
                name=item.get("name", ""),
                admin1=item.get("admin1"),
                country=item.get("country"),
                country_code=item.get("country_code"),
                latitude=item.get("latitude", 0.0),
                longitude=item.get("longitude", 0.0)
            )
        )
    
    return LocationSearchResponse(results=mapped_results)
