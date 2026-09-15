# AgriSmart Bonus Module API

This is an independent, production-oriented FastAPI service for the AgriSmart AI SIH 2026 project. 
It houses the future bonus modules:
1. Weather Intelligence
2. Smart Irrigation
3. Sustainability Score
4. Farmer Assistant
5. Agentic Advisor

## IMPORTANT

This is a NEW, independent repository. It is currently a skeleton project designed to eventually integrate with the main AgriSmart-AI system via a well-defined API contract. 
- It does not contain mock or fake prediction responses.
- It does not depend on the main system directly.
- The bonus processing pipelines and external integrations are not yet implemented.

## Running the Application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Endpoints

- `GET /health`: Health check
- `POST /bonus/analyze`: Placeholder endpoint for bonus module processing.
- `POST /bonus/weather`: Weather Intelligence module (Requires `latitude` and `longitude`).
- `GET /bonus/location`: Location Search / Geocoding module.
- `POST /bonus/irrigation`: Smart Irrigation rule-based module.

## Testing

Run the automated test suite (with mocked external APIs):
```bash
pytest -v
```

To test the live Weather Intelligence endpoint against the real Open-Meteo API:
```bash
# Ensure the server is running
curl -X POST "http://127.0.0.1:8000/bonus/weather" -H "Content-Type: application/json" -d "{\"latitude\": 34.05, \"longitude\": -118.24}"
```
