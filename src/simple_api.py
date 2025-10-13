#!/usr/bin/env python3
"""
Simple Crop Yield Prediction API for Render Deployment
Minimal working API with basic functionality - no complex dependencies
"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Crop Yield Prediction API",
    description="Simple crop yield prediction service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    crop_type: str
    variety_name: str
    location_name: str
    latitude: float
    longitude: float
    sowing_date: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Crop Yield Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-simple"
    }

@app.post("/predict/simple")
async def simple_prediction(request: PredictionRequest):
    """Simple prediction endpoint - returns mock data for testing"""
    # Mock prediction based on basic logic
    base_yield = {
        "Rice": 4.5,
        "Wheat": 3.2,
        "Maize": 5.1
    }.get(request.crop_type, 3.0)

    # Simple adjustment based on location and variety
    location_bonus = hash(request.location_name) % 10 / 100  # 0-0.09
    variety_adjustment = hash(request.variety_name) % 20 / 100  # 0-0.19

    predicted_yield = base_yield + location_bonus + variety_adjustment

    return {
        "prediction": {
            "yield_tons_per_hectare": round(predicted_yield, 2),
            "crop_type": request.crop_type,
            "variety_name": request.variety_name,
            "location": request.location_name
        },
        "note": "This is a simplified prediction for testing. Full model requires additional dependencies.",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
