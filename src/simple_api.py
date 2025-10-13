#!/usr/bin/env python3
"""
Minimal Crop Yield Prediction API for Render Deployment
Working FastAPI with pydantic
"""

from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(
    title="Crop Yield Prediction API",
    version="1.0.0"
)

class PredictionRequest(BaseModel):
    crop_type: str = "Rice"
    latitude: float = 28.6139
    longitude: float = 77.2090

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Crop Yield Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is operational"
    }

@app.post("/predict/yield")
async def predict_yield(request: PredictionRequest):
    """Simple prediction endpoint"""
    try:
        # Mock prediction with random values
        predicted_yield = random.uniform(2000, 6000)  # kg/ha
        confidence = random.uniform(0.70, 0.95)

        return {
            "success": True,
            "predicted_yield": round(predicted_yield, 1),
            "confidence": round(confidence, 2),
            "message": "Prediction completed successfully",
            "crop_type": request.crop_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(__import__("os").environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
