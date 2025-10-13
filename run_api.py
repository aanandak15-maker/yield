#!/usr/bin/env python3
"""
Start the Crop Yield Prediction API Server

Run this script to start the Phase 6 real-time prediction service.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Start the API server"""
    # Add src directory to Python path
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("🚀 Starting Crop Yield Prediction API Server...")
    print("📊 Phase 6: Real-time Prediction Service")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("⚡ Press Ctrl+C to stop the server")
    print("-" * 50)

    # Start the server
    uvicorn.run(
        "prediction_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
