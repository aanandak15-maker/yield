#!/usr/bin/env python3
"""
Real-time Crop Yield Prediction for Specific Field

Predicts yield using real satellite (GEE) and weather (OpenWeather) data
for the rice field in Gurugram, Haryana

Field Coordinates: Gurugram district (Delhi NCR)
Crop: Rice variety C 70 (using C 306 as closest match)
Sowing Date: 21 July 2024 (corrected from 2025)
Data Sources: REAL GEE + OpenWeather APIs only (no mocks)
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta


def calculate_field_centroid(coordinates):
    """Calculate centroid of the field polygon"""
    # Parse coordinates
    coords = []
    for coord_pair in coordinates.split(', '):
        if coord_pair.strip():  # Skip empty strings
            try:
                lat, lon = coord_pair.split(', ')
                coords.append({'lat': float(lat), 'lon': float(lon)})
            except ValueError:
                # Skip invalid coordinate pairs
                continue

    if not coords:
        # Default to Delhi NCR center if parsing fails
        return {'latitude': 28.6139, 'longitude': 77.2090}

    # Calculate centroid
    avg_lat = sum(c['lat'] for c in coords) / len(coords)
    avg_lon = sum(c['lon'] for c in coords) / len(coords)

    return {'latitude': avg_lat, 'longitude': avg_lon}


def make_real_prediction():
    """Make a real-time yield prediction using APIs"""

    # Field details
    coordinates = "28.368704, 77.540929, 28.368928, 77.540854, 28.368978, 77.541109, 28.368766, 77.541182"
    location_name = "Gurugram_Field"
    crop_type = "Rice"
    variety_name = "C 306"  # Closest match to C 70 variety
    sowing_date = "2024-07-21"  # Corrected from 2025
    use_real_time_data = True

    # Calculate centroid
    centroid = calculate_field_centroid(coordinates)

    print("🌾 CROP YIELD PREDICTION - REAL DATA ANALYSIS")
    print("=" * 50)
    print("🏭 FIELD DETAILS:")
    print(f"   Location: {location_name} (Gurugram, Haryana)")
    print(f"   Coordinates: Lat {centroid['latitude']:.6f}, Lon {centroid['longitude']:.6f}")
    print(f"   Crop: {crop_type}")
    print(f"   Variety: {variety_name} (C 70 equivalent)")
    print(f"   Sowing Date: {sowing_date}")
    print(f"   Data Source: REAL GEE + OpenWeather APIs")
    print()

    # API Configuration
    api_url = "http://localhost:8000/predict/yield"
    prediction_data = {
        "crop_type": crop_type,
        "variety_name": variety_name,
        "location_name": location_name,
        "latitude": centroid['latitude'],
        "longitude": centroid['longitude'],
        "sowing_date": sowing_date,
        "use_real_time_data": use_real_time_data
    }

    print("🔍 MAKING PREDICTION REQUEST...")
    print(f"   API Endpoint: {api_url}")
    print(f"   Request Data: {json.dumps(prediction_data, indent=2)}")
    print()

    try:
        response = requests.post(api_url, json=prediction_data, timeout=60)
        response.raise_for_status()
        result = response.json()

        print("✅ PREDICTION SUCCESSFUL!")
        print("=" * 50)
        print("📊 PREDICTION RESULTS:")
        print(f"   Prediction ID: {result.get('prediction_id')}")
        print(f"   Timestamp: {result.get('timestamp')}")
        print()

        # Main yield prediction
        prediction = result.get('prediction', {})
        print("🎯 YIELD PREDICTION:")
        print(f"   Yield: {prediction.get('yield_tons_per_hectare', 'N/A')} tons/ha")
        print(".2f")
        print(".6f")
        print()

        # Model information
        model = result.get('model', {})
        print("🤖 MODEL DETAILS:")
        print(f"   Algorithm: {model.get('algorithm', 'N/A')}")
        print(f"   Training Region: {model.get('location_used', 'N/A')}")
        print(f"   Features Used: {model.get('feature_count', 0)}")
        print()

        # Variety intelligence
        factors = result.get('factors', {})
        variety = factors.get('variety_characteristics', {})
        environmental = factors.get('environmental_adjustments', {})

        print("🌱 VARIETY & ENVIRONMENTAL ANALYSIS:")
        print("   VARIETY CHARACTERISTICS:")
        print(f"      Maturity: {variety.get('maturity_days', 'N/A')} days")
        print(f"      Potential Yield: {variety.get('yield_potential', 'N/A')} t/ha")
        print(f"      Drought Tolerance: {variety.get('drought_tolerance', 'N/A')}")
        print()
        print("   ENVIRONMENTAL ADJUSTMENTS:")
        print(".1f")
        print(".1f")
        print(".1f")
        print(".1f")
        print()

        # Data sources
        data_sources = result.get('data_sources', {})
        print("📡 DATA SOURCES:")
        print(f"   Satellite Data Points: {data_sources.get('satellite_data_points', 0)}")
        print(f"   Weather Data Points: {data_sources.get('weather_data_points', 0)}")
        print(f"   Data Freshness: {data_sources.get('data_freshness_hours', 0)} hours")
        print()

        # Processing time
        processing_time = result.get('processing_time_seconds', 0)
        print("⚡ PERFORMANCE:")
        print(".2f")
        print()

        # Summary conclusion
        print("🏆 PREDICTION SUMMARY:")
        print("=" * 50)
        yield_tph = prediction.get('yield_tons_per_hectare', 0)
        confidence = prediction.get('confidence_score', 0)

        if yield_tph > 0:
            print("✅ PREDICTION SUCCESSFUL")

            # Yield categorization
            if crop_type == "Rice":
                if yield_tph >= 6.0:
                    yield_cat = "HIGH YIELD (Excellent farming conditions)"
                elif yield_tph >= 4.5:
                    yield_cat = "GOOD YIELD (Standard production)"
                elif yield_tph >= 3.0:
                    yield_cat = "MODERATE YIELD (Some stress factors)"
                else:
                    yield_cat = "LOW YIELD (Significant challenges)"
            else:
                yield_cat = "Yield prediction completed"

            print(f"   Category: {yield_cat}")
            print(".1f")
            print(".1f")
            print(f"   Growth Period: {(datetime.now() - datetime.fromisoformat(sowing_date)).days} days")
            print()
            print("📋 RECOMMENDATIONS:")
            print("   • Monitor field conditions regularly")
            print("   • Consider additional irrigation if drought stress detected")
            print("   • Implement pest control measures proactively")
            print("   • Plan post-harvest logistics based on predicted yield")

        else:
            print("❌ PREDICTION FAILED")
            print("   Unable to generate yield prediction with current data")
        return result

    except requests.exceptions.RequestException as e:
        print("❌ API REQUEST FAILED!")
        print(f"   Error: {str(e)}")
        if "Connection refused" in str(e):
            print("   ⚠️  API Server not running!")
            print("   Start the server with: python3 run_api.py")
        return None

    except Exception as e:
        print("❌ PREDICTION ERROR!")
        print(f"   Error: {str(e)}")
        return None


def main():
    """Main execution"""
    print("🌾 Gurugram Rice Field Yield Prediction")
    print("=" * 50)
    print("Using real satellite (GEE) and weather (OpenWeather) data")
    print("No mock/synthetic data - authentic API integration")
    print()

    try:
        result = make_real_prediction()

        if result:
            print("🎉 PREDICTION COMPLETED SUCCESSFULLY!")
            print("   Results displayed above")
        else:
            print("❌ PREDICTION FAILED")
            print("   Check server status and try again")

    except KeyboardInterrupt:
        print("\n⏹️  Prediction interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
