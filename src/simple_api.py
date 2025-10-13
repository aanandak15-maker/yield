#!/usr/bin/env python3
"""
Simple Crop Yield Prediction API for Render Deployment
Minimal working API - no complex dependencies
"""

import os
import random
from datetime import datetime
from fastapi import FastAPI

app = FastAPI(
    title="Crop Yield Prediction API",
    version="1.0.0"
)

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

@app.post("/predict/yield")
async def predict_yield():
    """Simple prediction endpoint - returns mock data"""
    try:
        # Mock prediction with random values
        predicted_yield = random.uniform(2000, 6000)  # kg/ha
        confidence = random.uniform(0.70, 0.95)

        return {
            "success": True,
            "predicted_yield": round(predicted_yield, 1),
            "confidence": round(confidence, 2),
            "message": "Prediction completed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
