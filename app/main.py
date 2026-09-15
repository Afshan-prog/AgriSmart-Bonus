from fastapi import FastAPI
from app.api import bonus
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Independent bonus-module service for the AgriSmart AI project."
)

app.include_router(bonus.router, prefix="/bonus", tags=["Bonus"])

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "ok"}
