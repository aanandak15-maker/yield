# 🚀 Railway Deployment Guide - Complete Setup

## Pre-deployment Checklist ✅

- [x] Railway configuration updated (`railway.toml`)
- [x] Dependencies file updated (`requirements.txt`)
- [x] Entry point conflicts resolved
- [x] Source code committed to GitHub
- [x] GitHub repository URL: `https://github.com/aanandak15-maker/yield.git`

## 🔑 API Authentication Setup

### 1. **Google Earth Engine (GEE) Setup**

**Step 1: Create Service Account**
```bash
# Go to Google Cloud Console
1. Visit: https://console.cloud.google.com
2. Select your project (create if needed)
3. Navigate: IAM & Admin > Service Accounts
4. Create Service Account: "crop-yield-api"
5. Add roles: Earth Engine Resource Viewer, Storage Admin
6. Create JSON private key - DO NOT SHARE THIS FILE!
```

**Step 2: Enable GEE API**
```bash
# In Google Cloud Console
1. APIs & Services > Library
2. Search "Earth Engine API"
3. Enable the API
```

**Step 3: Add GEE Access**
```bash
1. Visit: https://code.earthengine.google.com
2. Sign in with your Google account
3. Register for Earth Engine access if prompted
4. Request access for your service account email
```

### 2. **OpenWeather API Setup**

**Step 1: Get API Key**
```bash
# Visit: https://openweathermap.org/api
1. Sign up for free account
2. Verify email
3. Go to API keys section
4. Generate new key
# Free tier: 1,000 calls/day, 60 calls/minute
```

## 📋 Railway Environment Variables

Add these exact variables in Railway dashboard:

**Required:**
```env
ENVIRONMENT=production
GEE_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com
OPENWEATHER_API_KEY=your-openweather-api-key-here
```

**Optional but recommended:**
```env
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
SOURCE_COMMIT=41dd69e82ca945f34053e7fed0ae774dcbd1b1b4
```

## 🚀 Railway Deployment Steps

### Step 1: Connect Repository
```bash
1. Go to: https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway with your GitHub account
5. Search for: "yield" (or your repo name)
6. Select: aanandak15-maker/yield
7. Click "Deploy"
```

### Step 2: Configure Environment
```bash
# After deployment starts:
1. Go to your Railway project dashboard
2. Click on your service (crop-yield-prediction)
3. Navigate to "Variables" tab
4. Add the environment variables listed above
5. Redeploy will happen automatically
```

### Step 3: Monitor Build & Startup
```bash
# Expected build process:
1. Clone repository (✓)
2. Install requirements.txt (5-10 minutes) - scikit-learn, earthengine-api
3. Start service with "python src/prediction_api.py"
4. Health check every 300 seconds at /health
```

### Step 4: Verify Deployment
```bash
# Test health endpoint
curl https://your-railway-url.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-14T12:30:00.000Z",
  "version": "6.0.0",
  "components": {
    "api_manager": "ready",
    "gee_client": "ready",  // or "unavailable" if API key issues
    "weather_client": "ready", // or "unavailable"
    "variety_db": "ready",
    "sowing_intelligence": "ready",
    "models_loaded": 5   // Number of location models
  }
}
```

## 🐛 Troubleshooting

### Build Failures
**Issue:** Package installation timeout
**Fix:** Railway has 5GB RAM limit. Our scikit-learn models are heavy.

**Issue:** Earth Engine authentication
**Fix:** Check GEE service account has proper IAM roles

### Startup Failures
**Issue:** `ModuleNotFoundError`
**Fix:** Check requirements.txt includes all dependencies

**Issue:** Model loading failure
**Fix:** Ensure `models/` directory with `.pkl` files exists

### API Key Issues
**Issue:** `gee_client: "unavailable"`
**Fix:** Verify service account JSON and GEE access

**Issue:** `weather_client: "unavailable"`
**Fix:** Check OpenWeather API key validity

## 📊 Railway Configuration

Your `railway.toml` contains:
```toml
[deploy]
restartPolicyType = "NEVER"
healthcheckPath = "/health"
healthcheckTimeout = 600
startCommand = "python src/prediction_api.py"
buildCommand = "pip install -r requirements.txt"
```

## 💰 Railway Costs

- **Free Tier:** 512MB RAM, 8GB storage, $0/month
- **Our expected usage:**
  - Startup time: 2-5 minutes (due to ML models)
  - Request time: ~3 seconds per prediction
  - Memory usage: ~300-500MB during operation

## 🎯 Post-deployment Testing

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-url.up.railway.app/health

# Validate input
curl -X POST https://your-url.up.railway.app/validate \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "variety_name": "Basmati 370",
    "location_name": "Bhopal",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "sowing_date": "2024-07-15"
  }'

# Make prediction
curl -X POST https://your-url.up.railway.app/predict/yield \
  [same JSON as above]
```

## 🛠️ Scaling & Maintenance

- **Auto-scaling:** Railway handles automatically
- **Logs:** Available in Railway dashboard
- **Updates:** Push to GitHub main branch → auto-deploy
- **Monitoring:** Railway provides uptime monitoring

## 👥 API Usage Limits

- **OpenWeather:** 1,000 calls/day (free), 60/minute
- **Google Earth Engine:** Varies by asset access
- **Railway:** No API limits - only compute time charges

---

**Ready to deploy!** 🚀 Your real ML-powered crop yield prediction API is production-ready.
