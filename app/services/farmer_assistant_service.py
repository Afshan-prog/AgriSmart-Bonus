import httpx
import json
import re
from fastapi import HTTPException
from app.schemas import AssistantRequest, AssistantResponse, AssistantLLMResponse
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are the Farmer Assistant for AgriSmart AI.

Your job is to explain AI-generated crop disease predictions in simple, farmer-friendly language.

Rules:
1. Treat the disease prediction as an AI prediction, not a confirmed diagnosis.
2. Use only the crop, disease prediction, confidence, weather, and irrigation information supplied by AgriSmart.
3. Do not invent pesticide names, chemical treatments, dosages, application frequency, or treatment schedules.
4. Do not make unsupported agricultural claims.
5. Give practical, low-risk next steps such as inspecting affected leaves, monitoring the crop, and considering locally appropriate agricultural guidance.
6. Clearly explain weather and irrigation information when provided.
7. Mention important limitations when appropriate.
8. Keep the answer concise and easy for a farmer to understand.
9. Clearly communicate uncertainty when model confidence is low.
10. Never guarantee that the disease prediction is correct.

Return ONLY valid JSON with these fields:

{
  "summary": "string",
  "what_it_means": "string",
  "recommended_actions": ["string"],
  "weather_note": "string",
  "irrigation_note": "string",
  "warning": "string",
  "confidence_note": "string"
}"""

FALLBACK_CONTENT = AssistantLLMResponse(
    summary="The AI Assistant is currently experiencing high demand.",
    what_it_means="We could not generate a personalized explanation right now.",
    recommended_actions=[
        "Please refer to the Weather and Irrigation tabs for immediate insights.",
        "Monitor your crop regularly for any unusual signs.",
        "Consult local agricultural guidance if you suspect a serious disease."
    ],
    weather_note="Please see the dedicated weather module for current conditions.",
    irrigation_note="Please refer to the smart irrigation recommendation.",
    warning="This is a deterministic fallback message, not an AI prediction.",
    confidence_note="The disease prediction should always be treated as an estimate, not a confirmed diagnosis."
)

def is_safe_response(content: str) -> bool:
    """Lightweight deterministic safety guard."""
    content_lower = content.lower()
    
    # Flag explicit dosage instructions or guarantees
    dangerous_patterns = [
        r"\b\d+(\.\d+)?\s*(ml/l|g/l|kg/ha|liters/ha|ml per liter|grams per liter)\b",
        r"apply exactly",
        r"spray exactly",
        r"is definitely correct",
        r"is a confirmed diagnosis",
        r"guaranteed to be correct"
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, content_lower):
            return False
            
    return True

async def get_assistant_advice(request: AssistantRequest) -> AssistantResponse:
    if not settings.OPENROUTER_API_KEY:
        return AssistantResponse(status="fallback", source="deterministic", content=FALLBACK_CONTENT)
        
    user_prompt = f"""Crop: {request.crop}
AI Disease Prediction: {request.disease_prediction}
Model Confidence: {request.confidence if request.confidence is not None else 'Unknown'}

Weather:
Temperature: {request.temperature_c if request.temperature_c is not None else 'Unknown'}°C
Humidity: {request.humidity_percent if request.humidity_percent is not None else 'Unknown'}%
Rain probability today: {request.rain_probability if request.rain_probability is not None else 'Unknown'}%

Smart Irrigation:
Status: {request.irrigation_status if request.irrigation_status else 'Unknown'}
Primary Driver: {request.irrigation_driver if request.irrigation_driver else 'Unknown'}"""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValueError("Missing choices in response")
                
            choice = data["choices"][0]
            if "message" not in choice or "content" not in choice["message"]:
                raise ValueError("Missing message content in response")
                
            content_str = choice["message"]["content"]
            if not content_str:
                raise ValueError("Empty content in response")
                
            # Check safety
            if not is_safe_response(content_str):
                return AssistantResponse(status="fallback", source="deterministic", content=FALLBACK_CONTENT)
                
            # Parse JSON
            try:
                parsed_json = json.loads(content_str)
                llm_response = AssistantLLMResponse(**parsed_json)
                return AssistantResponse(status="success", source="llm", content=llm_response)
            except (json.JSONDecodeError, ValueError):
                return AssistantResponse(status="fallback", source="deterministic", content=FALLBACK_CONTENT)
                
    except Exception:
        # Catch all HTTP and parsing errors to ensure fallback
        return AssistantResponse(status="fallback", source="deterministic", content=FALLBACK_CONTENT)
