"""
Smart Irrigation module logic based on weather intelligence.
"""
from app.schemas import IrrigationRequest, IrrigationResponse
from app.services import weather_service
import logging

logger = logging.getLogger(__name__)

# --- Prototype Engineering Thresholds ---
# NOTE: These are prototype engineering thresholds used for demonstrating the intelligence 
# module capabilities. They are NOT universally validated agronomic thresholds.
IRRIGATION_RAIN_PROB_THRESHOLD = 60
IRRIGATION_PRECIP_THRESHOLD_MM = 1.0
IRRIGATION_WIND_THRESHOLD_KMH = 35.0
IRRIGATION_HEAT_THRESHOLD_C = 35.0

LIMITATIONS_DISCLAIMER = (
    "Weather-based qualitative guidance only; soil moisture, "
    "crop stage and irrigation system are not considered."
)

async def get_irrigation_recommendation(request: IrrigationRequest) -> IrrigationResponse:
    # 1. Fetch weather intelligence
    weather = await weather_service.get_weather_intelligence(request.latitude, request.longitude)
    
    current = weather.current
    forecast = weather.forecast
    
    # 2. Extract values
    precip_prob = forecast.precipitation_probability_percent
    precip_mm = current.precipitation_mm
    wind_kmh = current.wind_speed_kmh
    max_temp = forecast.max_temperature_c
    current_temp = current.temperature_c
    
    # Defaults for comparisons if forecast is missing
    precip_prob_val = precip_prob if precip_prob is not None else 0
    max_temp_val = max_temp if max_temp is not None else -999.0
    
    # 3. Rule Evaluation
    
    # A. Rain / Significant Precipitation
    if precip_prob_val >= IRRIGATION_RAIN_PROB_THRESHOLD or precip_mm >= IRRIGATION_PRECIP_THRESHOLD_MM:
        status = "PAUSE_IRRIGATION"
        driver = "Natural Precipitation"
        note = "Rain is likely today. Consider delaying irrigation and reassessing after rainfall."
        reasons = []
        if precip_prob_val >= IRRIGATION_RAIN_PROB_THRESHOLD:
            reasons.append(f"Precipitation probability is {precip_prob_val}%")
        if precip_mm >= IRRIGATION_PRECIP_THRESHOLD_MM:
            reasons.append(f"Current precipitation is {precip_mm} mm")
            
    # B. High Wind
    elif wind_kmh >= IRRIGATION_WIND_THRESHOLD_KMH:
        status = "RESTRICT_OVERHEAD_IRRIGATION"
        driver = "High Wind"
        note = "High winds can reduce the efficiency of overhead irrigation through spray drift. Consider postponing overhead irrigation or using a less wind-sensitive method if available."
        reasons = [f"Current wind speed is {wind_kmh} km/h"]
        
    # C. High Temperature
    elif max_temp_val >= IRRIGATION_HEAT_THRESHOLD_C or current_temp >= IRRIGATION_HEAT_THRESHOLD_C:
        status = "HEAT_CAUTION"
        driver = "High Temperature"
        note = "High temperatures may increase crop water demand. Check soil moisture and consider adjusting irrigation timing based on crop and field conditions."
        reasons = []
        if max_temp_val >= IRRIGATION_HEAT_THRESHOLD_C:
            reasons.append(f"Forecasted max temperature is {max_temp_val}°C")
        if current_temp >= IRRIGATION_HEAT_THRESHOLD_C:
            reasons.append(f"Current temperature is {current_temp}°C")
            
    # D. Default
    else:
        status = "NO_WEATHER_TRIGGER"
        driver = "None"
        note = "No significant weather-based irrigation adjustment is indicated. Follow your existing irrigation practice and consider soil moisture and crop requirements."
        reasons = ["Weather conditions are below threshold triggers"]

    return IrrigationResponse(
        irrigation_status=status,
        primary_driver=driver,
        recommendation_note=note,
        reasons=reasons,
        limitations=LIMITATIONS_DISCLAIMER
    )
