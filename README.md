# AgriSmart Bonus Module API

An independent FastAPI service containing additional intelligence modules
for the AgriSmart AI SIH 2026 project.

## Implemented Modules

1. Weather Intelligence
2. Location Search / Geocoding
3. Smart Irrigation
4. Farmer Assistant

The service is designed to integrate with the main AgriSmart AI system
through structured API contracts.

## Architecture

The bonus service is independent of the disease-classification model.
It consumes structured prediction and contextual data rather than loading
or modifying the ML model itself.

Main application:
- Disease prediction

Bonus service:
- Location search
- Weather intelligence
- Weather-aware irrigation guidance
- Farmer-friendly AI explanation
