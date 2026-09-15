from fastapi import APIRouter, Query
from app.schemas import (
    BonusAnalyzeRequest, 
    BonusAnalyzeResponse,
    WeatherRequest,
    WeatherResponse,
    LocationSearchResponse
)
from app.services import weather_service, geocoding_service

router = APIRouter()

@router.get("/location", response_model=LocationSearchResponse)
async def search_location(query: str = Query(..., description="Location name to search for")):
    """
    Search for latitude and longitude by location name.
    """
    return await geocoding_service.search_locations(query)

@router.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    Fetch weather intelligence for agricultural decision making.
    """
    return await weather_service.get_weather_intelligence(
        latitude=request.latitude, 
        longitude=request.longitude
    )

@router.post("/analyze", response_model=BonusAnalyzeResponse)
async def analyze_bonus_modules(request: BonusAnalyzeRequest):
    """
    Placeholder endpoint for the bonus module processing pipeline.
    This will eventually orchestrate weather, irrigation, sustainability, 
    and agentic advisor modules based on the inputs from the main AgriSmart system.
    """
    # Note: Do not generate fake results here.
    return BonusAnalyzeResponse(
        status="not_implemented",
        message="The bonus processing pipeline is not implemented yet. This is a placeholder response."
    )
