# API Contract: AgriSmart Main System <-> Bonus Module API

This document defines the intended future integration between the main AgriSmart AI system and this independent bonus-module service.

## Integration Flow

1. The main AgriSmart system processes an image/request and generates ML predictions (e.g., crop type, disease).
2. The main system sends this data, along with optional contextual information (location, etc.), to the Bonus Module API via an HTTP POST request.
3. The Bonus Module API orchestrates the intelligence pipelines (Weather, Irrigation, Sustainability, etc.) and returns the enriched data.

## Contract Definition

### Endpoint
`POST /bonus/analyze`

### Request Payload (Expected from Main System)

The request is designed to be flexible. Not all fields are guaranteed to be available from the main system, so they are considered optional.

```json
{
  "crop": "string (optional) - The identified crop name",
  "disease": "string (optional) - The detected disease",
  "confidence": "float (optional) - Confidence score of the prediction",
  "latitude": "float (optional) - Latitude of the farm",
  "longitude": "float (optional) - Longitude of the farm"
}
```

### Response Payload (From Bonus Module API)

Currently, the service returns a placeholder response indicating it is not yet implemented.

```json
{
  "status": "string - Currently 'not_implemented'",
  "message": "string - Description of the status"
}
```

*Future implementation will include structured data for smart irrigation, sustainability score, farmer assistant, and agentic advisor.*

---

### Endpoint
`GET /bonus/location`

### Request Payload (Expected from Main System / Frontend)

Search by location name (e.g., `GET /bonus/location?query=London`)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The city or location name (2-100 characters) |

### Response Payload (From Bonus Module API)

Returns up to 5 location matches to allow disambiguation.

```json
{
  "results": [
    {
      "name": "London",
      "admin1": "England",
      "country": "United Kingdom",
      "country_code": "GB",
      "latitude": 51.50853,
      "longitude": -0.12574
    }
  ]
}
```

### Error Behavior
- `422 Unprocessable Entity`: Query is missing or outside valid length constraints.
- `502 Bad Gateway`: External geocoding API failed.
- `504 Gateway Timeout`: External geocoding API request timed out.

---

### Endpoint
`POST /bonus/irrigation`

### Request Payload (Expected from Main System)

Requests qualitative weather-based irrigation advice.

```json
{
  "latitude": "float (required) - Latitude of the farm (-90.0 to 90.0)",
  "longitude": "float (required) - Longitude of the farm (-180.0 to 180.0)",
  "crop": "string (optional) - The crop name, currently accepted for future extensibility"
}
```

### Response Payload (From Bonus Module API)

Returns rule-based, qualitative advice prioritizing rain, high winds, and heat.

```json
{
  "irrigation_status": "PAUSE_IRRIGATION",
  "primary_driver": "Natural Precipitation",
  "recommendation_note": "Rain is likely today. Consider delaying irrigation and reassessing after rainfall.",
  "reasons": [
    "Precipitation probability is 86%"
  ],
  "limitations": "Weather-based qualitative guidance only; soil moisture, crop stage and irrigation system are not considered."
}
```

**Possible `irrigation_status` values:**
- `PAUSE_IRRIGATION` (Triggers on high rain probability or current rain)
- `RESTRICT_OVERHEAD_IRRIGATION` (Triggers on high winds >= 35 km/h)
- `HEAT_CAUTION` (Triggers on extreme temperatures >= 35°C)
- `NO_WEATHER_TRIGGER` (Normal conditions)

> **Note**: The decision logic relies on prototype engineering assumptions, not universally validated agronomic thresholds. The module does not calculate exact water quantities.

### Error Behavior
- `422 Unprocessable Entity`: Invalid latitude/longitude format or out of bounds.
- `502 Bad Gateway`: External weather API failed.
- `504 Gateway Timeout`: External weather API request timed out.

### Endpoint
`POST /bonus/weather`

### Request Payload (Expected from Main System)

The request requires valid agricultural coordinates.

```json
{
  "latitude": "float (required) - Latitude of the farm (-90.0 to 90.0)",
  "longitude": "float (required) - Longitude of the farm (-180.0 to 180.0)"
}
```

### Response Payload (From Bonus Module API)

Returns real-time weather and forecast data interpreted for agriculture.

```json
{
  "current": {
    "temperature_c": 35.5,
    "humidity_percent": 45.0,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 12.0
  },
  "forecast": {
    "max_temperature_c": 38.0,
    "min_temperature_c": 22.0,
    "precipitation_probability_percent": 10
  },
  "indicators": {
    "rain_expected": false,
    "high_temperature_flag": true,
    "high_wind_flag": false,
    "irrigation_weather_note": "High heat conditions detected; monitor crop water stress."
  }
}
```

### Error Behavior
- `422 Unprocessable Entity`: Invalid latitude/longitude format or out of bounds.
- `502 Bad Gateway`: External weather API failed or returned an invalid response.
- `504 Gateway Timeout`: External weather API request timed out.

### Endpoint
`POST /bonus/assistant`

### Request Payload (Expected from Main System)

The request should provide all available contextual data for the LLM to explain.

```json
{
  "crop": "string (optional) - The crop name",
  "disease_prediction": "string (optional) - The detected disease name",
  "confidence": "float (optional) - Confidence score of the prediction",
  "temperature_c": "float (optional) - Current temperature in Celsius",
  "humidity_percent": "float (optional) - Current relative humidity percentage",
  "rain_probability": "int (optional) - Probability of precipitation",
  "irrigation_status": "string (optional) - Irrigation status recommendation",
  "irrigation_driver": "string (optional) - Primary driver for irrigation status"
}
```

### Response Payload (From Bonus Module API)

Returns a natural language explanation and low-risk advice from the Farmer Assistant LLM.

```json
{
  "status": "success",
  "source": "llm",
  "content": {
    "summary": "AI suggests Corn has Northern Leaf Blight.",
    "what_it_means": "The warm wet weather favors this disease.",
    "recommended_actions": [
      "Monitor leaves for lesions",
      "Ensure good airflow"
    ],
    "weather_note": "High rain chance today.",
    "irrigation_note": "Irrigation is paused due to expected rain.",
    "warning": "This is an AI prediction, not a confirmed diagnosis.",
    "confidence_note": "The model is highly confident, but monitoring is advised."
  }
}
```

### Error Behavior
- `200 OK` (with `"status": "fallback"`, `"source": "deterministic"`): Returned if the LLM API fails, times out, rate limits, or generates unsafe content. It returns a safe, deterministic JSON response instead of crashing.
