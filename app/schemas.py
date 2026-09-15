from pydantic import BaseModel, Field
from typing import Optional

class LocationResult(BaseModel):
    name: str = Field(..., description="City or location name")
    admin1: Optional[str] = Field(None, description="State or region")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="2-letter country code")
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")

class LocationSearchResponse(BaseModel):
    results: list[LocationResult] = Field(default_factory=list, description="List of location matches")

class WeatherRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the farm")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the farm")

class CurrentWeather(BaseModel):
    temperature_c: float = Field(..., description="Current temperature in Celsius")
    humidity_percent: float = Field(..., description="Current relative humidity percentage")
    precipitation_mm: float = Field(..., description="Current precipitation in mm")
    wind_speed_kmh: float = Field(..., description="Current wind speed in km/h")

class ForecastWeather(BaseModel):
    max_temperature_c: Optional[float] = Field(None, description="Forecasted maximum temperature in Celsius")
    min_temperature_c: Optional[float] = Field(None, description="Forecasted minimum temperature in Celsius")
    precipitation_probability_percent: Optional[int] = Field(None, description="Probability of precipitation")

class AgriculturalIndicators(BaseModel):
    rain_expected: bool = Field(..., description="Flag indicating if rain is expected based on forecast or current precipitation")
    high_temperature_flag: bool = Field(..., description="Flag indicating high heat conditions")
    high_wind_flag: bool = Field(..., description="Flag indicating high wind conditions")
    irrigation_weather_note: str = Field(..., description="Neutral weather note regarding irrigation")

class WeatherResponse(BaseModel):
    current: CurrentWeather
    forecast: ForecastWeather
    indicators: AgriculturalIndicators

class BonusAnalyzeRequest(BaseModel):
    crop: Optional[str] = Field(None, description="The crop name")
    disease: Optional[str] = Field(None, description="The detected disease name")
    confidence: Optional[float] = Field(None, description="Confidence score of the prediction")
    latitude: Optional[float] = Field(None, description="Latitude of the farm")
    longitude: Optional[float] = Field(None, description="Longitude of the farm")

class BonusAnalyzeResponse(BaseModel):
    status: str
    message: str
    # Future fields for actual results
    # weather_intelligence: Optional[dict] = None
    # smart_irrigation: Optional[dict] = None
    # sustainability_score: Optional[dict] = None
    # farmer_assistant: Optional[dict] = None
    # agentic_advisor: Optional[dict] = None
