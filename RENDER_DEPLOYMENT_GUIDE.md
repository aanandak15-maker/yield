# 🚀 Render Deployment Guide - Crop Yield Prediction API v6.1.0

## Overview

This guide covers deploying the Crop Yield Prediction API to Render with the latest features:
- ✅ Optional variety selection (v6.1.0)
- ✅ NumPy 2.x and scikit-learn 1.7.x compatibility
- ✅ Automatic variety selection based on location
- ✅ Enhanced error handling and fallback systems
- ✅ Comprehensive health monitoring

**Deployment Time**: 20-30 minutes  
**Downtime**: None (zero-downtime deployment)

---

## Pre-Deployment Checklist

### 1. Code Verification

```bash
# Verify all tests pass
python test_optional_variety_e2e.py
python test_end_to_end_predictions.py
python test_api_startup.py

# Check API version
grep "api_version" src/prediction_api.py
# Should show: 'api_version': '6.1.0'
```

### 2. Environment Requirements

- ✅ Python 3.11.10
- ✅ NumPy 2.3.0+
- ✅ scikit-learn 1.7.0+
- ✅ All dependencies in `requirements.txt`

### 3. Required Files

Verify these files exist:
- ✅ `render.yaml` - Render configuration
- ✅ `Dockerfile` - Container configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ `run_api.py` - API startup script
- ✅ `src/production_environment_guard.py` - Environment validation
- ✅ `models/*.pkl` - Trained ML models (15 files)
- ✅ `data/database/crop_prediction.db` - Variety database

### 4. API Credentials (Optional for Enhanced Features)

**Google Earth Engine** (for real-time satellite data):
- Service account email
- Private key JSON file
- GEE assets shared with service account

**OpenWeather API** (for real-time weather data):
- API key from https://openweathermap.org/api
- Free tier: 1,000,000 calls/month

**Note**: API works without these credentials using fallback data.

---

## Deployment Steps

### Step 1: Prepare GitHub Repository

#### 1.1 Create Repository (if not exists)

```bash
# Create new repository on GitHub
# Name: crop-yield-api
# Visibility: Public or Private
```

#### 1.2 Push Code to GitHub

```bash
# Verify you're on the main branch
git branch

# Add all files
git add .

# Commit changes
git commit -m "Deploy v6.1.0 with optional variety feature"

# Push to GitHub
git push origin main
```

#### 1.3 Verify Repository Contents

Ensure these directories/files are pushed:
- `src/` - All source code
- `models/` - All 15 trained models
- `data/database/` - Variety database
- `config/` - Configuration files
- `render.yaml`, `Dockerfile`, `requirements.txt`, `runtime.txt`

---

### Step 2: Configure Render Service

#### 2.1 Create Render Account

1. Go to https://render.com
2. Sign up with GitHub account
3. Verify email address

#### 2.2 Connect GitHub Repository

1. Click "New" → "Web Service"
2. Click "Connect GitHub"
3. Authorize Render to access your repositories
4. Select `crop-yield-api` repository
5. Click "Connect"

#### 2.3 Configure Service Settings

Render will auto-detect settings from `render.yaml`:

```yaml
Name: crop-yield-prediction-api
Runtime: Docker
Branch: main
Dockerfile Path: ./Dockerfile
```

**Manual Configuration** (if needed):
- **Name**: `crop-yield-prediction-api`
- **Environment**: Docker
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Build Command**: (handled by Dockerfile)
- **Start Command**: (handled by Dockerfile)

#### 2.4 Set Environment Variables

**Required Variables**:
```env
ENVIRONMENT=production
PYTHONPATH=/app
```

**Optional Variables** (for enhanced features):
```env
# Google Earth Engine (optional)
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_JSON={"type":"service_account",...}

# OpenWeather API (optional)
OPENWEATHER_API_KEY=your-openweather-api-key

# Logging (optional)
LOG_LEVEL=INFO
```

**How to Add Environment Variables**:
1. In Render dashboard, go to your service
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Enter key and value
5. Click "Save Changes"

**For GEE Private Key**:
- Copy entire JSON file content
- Paste as value for `GEE_PRIVATE_KEY_JSON`
- Render will handle file creation automatically

#### 2.5 Configure Health Check

Render auto-configures from `render.yaml`:
```yaml
healthCheckPath: /health
```

**Manual Configuration** (if needed):
- **Health Check Path**: `/health`
- **Health Check Interval**: 30 seconds
- **Health Check Timeout**: 10 seconds

#### 2.6 Select Plan

**Free Tier** (Recommended for testing):
- 750 build hours/month
- 100 GB bandwidth/month
- Auto-sleep after 15 minutes of inactivity
- Cold start: ~30 seconds

**Starter Plan** ($7/month):
- No auto-sleep
- Faster builds
- More resources

**Standard Plan** ($25/month):
- Higher performance
- More memory (up to 4GB)
- Priority support

#### 2.7 Deploy

1. Review all settings
2. Click "Create Web Service"
3. Deployment begins automatically

**Deployment Process**:
- Building Docker image (~10 minutes)
- Installing dependencies (~5 minutes)
- Loading models (~2 minutes)
- Health check validation (~1 minute)
- **Total**: ~15-20 minutes

---

### Step 3: Monitor Deployment

#### 3.1 Watch Build Logs

In Render dashboard:
1. Go to your service
2. Click "Logs" tab
3. Watch for:
   ```
   ✅ Successfully loaded model: bhopal_training_ridge
   ✅ Successfully loaded model: bhopal_training_random_forest
   ...
   ✅ Successfully loaded 15/15 models
   ✅ VarietySelectionService initialized successfully
   ✅ Crop Yield Prediction Service initialized
   ```

#### 3.2 Check Health Status

Once deployed, Render shows:
- **Status**: Live (green)
- **Health Check**: Passing
- **URL**: `https://crop-yield-api-[hash].onrender.com`

#### 3.3 Verify Deployment

```bash
# Replace with your Render URL
export RENDER_URL="https://crop-yield-api-[hash].onrender.com"

# Basic health check
curl $RENDER_URL/health

# Detailed health check
curl $RENDER_URL/health/detailed | jq '.'
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T...",
  "environment": {
    "numpy_version": "2.3.4",
    "sklearn_version": "1.7.2",
    "python_version": "3.11.10"
  },
  "models": {
    "total_loaded": 15,
    "locations": 5,
    "fallback_mode": false
  },
  "services": {
    "variety_selection": "operational",
    "database": "connected"
  },
  "api_version": "6.1.0"
}
```

---

### Step 4: Test Deployed API

#### 4.1 Test Prediction Without Variety (New Feature)

```bash
# Test automatic variety selection
curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "location_name": "Bhopal",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "sowing_date": "2024-06-15",
    "use_real_time_data": false
  }' | jq '.'
```

Expected response:
```json
{
  "prediction_id": "Rice_Bhopal_20251019_...",
  "timestamp": "2025-10-19T...",
  "prediction": {
    "yield_tons_per_hectare": 3.45,
    "variety_used": "IR-64",
    "variety_assumed": true,
    "confidence_score": 0.85
  },
  "factors": {
    "default_variety_selection": {
      "region": "Madhya Pradesh",
      "reason": "global_default",
      "yield_potential": 6.0
    }
  },
  "api_version": "6.1.0"
}
```

#### 4.2 Test Prediction With Variety (Backward Compatibility)

```bash
# Test with explicit variety
curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Wheat",
    "variety_name": "PBW 725",
    "location_name": "Chandigarh",
    "latitude": 30.7333,
    "longitude": 76.7794,
    "sowing_date": "2024-11-15",
    "use_real_time_data": false
  }' | jq '.'
```

Expected response:
```json
{
  "prediction_id": "Wheat_Chandigarh_20251019_...",
  "prediction": {
    "yield_tons_per_hectare": 4.2,
    "variety_used": "PBW 725",
    "variety_assumed": false,
    "confidence_score": 0.88
  },
  "api_version": "6.1.0"
}
```

#### 4.3 Test All Locations

```bash
# Test variety selection for all locations
for location in "Bhopal" "Lucknow" "Chandigarh" "Patna"; do
  echo "Testing $location:"
  curl -s -X POST $RENDER_URL/predict/yield \
    -H "Content-Type: application/json" \
    -d "{
      \"crop_type\": \"Rice\",
      \"location_name\": \"$location\",
      \"latitude\": 25.0,
      \"longitude\": 80.0,
      \"sowing_date\": \"2024-06-15\",
      \"use_real_time_data\": false
    }" | jq '.prediction.variety_used, .factors.default_variety_selection.region'
  echo ""
done
```

#### 4.4 Test Error Handling

```bash
# Test invalid crop type
curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "InvalidCrop",
    "location_name": "Bhopal",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "sowing_date": "2024-06-15"
  }' | jq '.'

# Should return error with clear message
```

#### 4.5 Test API Documentation

```bash
# Access interactive API docs
open $RENDER_URL/docs

# Or visit in browser:
# https://crop-yield-api-[hash].onrender.com/docs
```

---

## Post-Deployment Configuration

### 1. Custom Domain (Optional)

#### 1.1 Add Custom Domain in Render

1. Go to service settings
2. Click "Custom Domains"
3. Click "Add Custom Domain"
4. Enter your domain: `api.yourdomain.com`

#### 1.2 Configure DNS

Add CNAME record in your DNS provider:
```
Type: CNAME
Name: api
Value: crop-yield-api-[hash].onrender.com
TTL: 3600
```

#### 1.3 Verify SSL Certificate

Render automatically provisions SSL certificate (free).
Wait 5-10 minutes for DNS propagation.

### 2. Monitoring Setup

#### 2.1 Enable Render Monitoring

Render provides built-in monitoring:
- CPU usage
- Memory usage
- Request count
- Response times
- Error rates

Access in dashboard: Service → Metrics

#### 2.2 External Monitoring (Optional)

**UptimeRobot** (Free):
1. Sign up at https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(s)
   - URL: `$RENDER_URL/health`
   - Interval: 5 minutes
3. Set up alerts (email/SMS)

**Better Uptime** (Free tier):
1. Sign up at https://betteruptime.com
2. Add monitor with health check endpoint
3. Configure incident notifications

#### 2.3 Log Aggregation (Optional)

**Papertrail** (Free tier):
1. Sign up at https://papertrailapp.com
2. Get log destination URL
3. Add to Render:
   - Service → Settings → Log Streams
   - Add Papertrail destination

### 3. Performance Optimization

#### 3.1 Enable Persistent Disk (Optional)

For faster cold starts:
1. Service → Settings → Disks
2. Add disk: `/app/model_cache`
3. Size: 1GB
4. Mount path: `/app/model_cache`

#### 3.2 Configure Auto-Scaling (Paid Plans)

For high traffic:
1. Service → Settings → Scaling
2. Set min/max instances
3. Configure auto-scale rules

### 4. Security Configuration

#### 4.1 Environment Variables Security

- Never commit API keys to Git
- Use Render's environment variables
- Rotate keys periodically

#### 4.2 API Rate Limiting (Optional)

Add rate limiting middleware in `src/prediction_api.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/predict/yield")
@limiter.limit("100/hour")
async def predict_yield(...):
    ...
```

#### 4.3 CORS Configuration

Already configured in `src/prediction_api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production**: Update `allow_origins` to specific domains.

---

## Troubleshooting

### Issue 1: Build Fails

**Symptoms**:
- Build logs show errors
- Deployment stuck at "Building"

**Solutions**:

1. **Check Dockerfile syntax**:
   ```bash
   # Test locally
   docker build -t crop-yield-api .
   ```

2. **Verify requirements.txt**:
   ```bash
   # Check for conflicts
   pip install -r requirements.txt
   ```

3. **Check build logs** in Render dashboard for specific errors

### Issue 2: Health Check Fails

**Symptoms**:
- Deployment completes but shows "Unhealthy"
- Service keeps restarting

**Solutions**:

1. **Check logs** for startup errors:
   ```
   Service → Logs → Filter by "error"
   ```

2. **Verify health endpoint**:
   ```bash
   # Test locally first
   python run_api.py
   curl http://localhost:8000/health
   ```

3. **Check model loading**:
   - Ensure `models/` directory is in Git
   - Verify all 15 model files exist
   - Check file sizes (should be 1-10 MB each)

### Issue 3: Models Not Loading

**Symptoms**:
- Health check shows `fallback_mode: true`
- Logs show "Failed to load models"

**Solutions**:

1. **Verify models in repository**:
   ```bash
   git ls-files models/
   # Should show 15 .pkl files
   ```

2. **Check model compatibility**:
   - Models must be trained with NumPy 2.x
   - If using old models, retrain:
     ```bash
     python model_trainer.py
     git add models/*.pkl
     git commit -m "Update models for NumPy 2.x"
     git push
     ```

3. **Check environment versions** in logs:
   ```
   NumPy: 2.3.4
   scikit-learn: 1.7.2
   ```

### Issue 4: Slow Response Times

**Symptoms**:
- Predictions take > 2 seconds
- Cold start takes > 60 seconds

**Solutions**:

1. **Upgrade plan**:
   - Free tier has limited resources
   - Starter plan ($7/month) provides better performance

2. **Enable persistent disk**:
   - Caches models between restarts
   - Reduces cold start time

3. **Optimize code**:
   - Profile slow endpoints
   - Add caching for repeated requests

### Issue 5: Variety Selection Errors

**Symptoms**:
- Predictions fail without variety
- Error: "NoVarietiesAvailable"

**Solutions**:

1. **Verify database file**:
   ```bash
   # Check if database exists
   ls -lh data/database/crop_prediction.db
   
   # Verify it's in Git
   git ls-files data/database/
   ```

2. **Check database integrity**:
   ```bash
   # Test locally
   python -c "from src.crop_variety_database import CropVarietyDatabase; db = CropVarietyDatabase(); print(db.get_crop_varieties('Rice', 'Punjab'))"
   ```

3. **Reinitialize database** if corrupted:
   ```bash
   # Backup first
   cp data/database/crop_prediction.db data/database/crop_prediction.db.backup
   
   # Reinitialize
   python -c "from src.crop_variety_database import CropVarietyDatabase; CropVarietyDatabase()"
   ```

### Issue 6: Environment Variable Issues

**Symptoms**:
- API keys not working
- GEE authentication fails

**Solutions**:

1. **Verify variables in Render**:
   - Service → Environment
   - Check all required variables are set
   - No extra spaces in values

2. **Test GEE key format**:
   ```bash
   # Verify JSON is valid
   echo $GEE_PRIVATE_KEY_JSON | jq '.'
   ```

3. **Check service account permissions**:
   - Ensure GEE assets are shared with service account
   - Verify service account has Earth Engine API enabled

---

## Maintenance

### Regular Tasks

#### Weekly
- [ ] Check error logs for anomalies
- [ ] Monitor response times
- [ ] Verify health check status

#### Monthly
- [ ] Review usage metrics
- [ ] Check for dependency updates
- [ ] Rotate API keys (if applicable)
- [ ] Review and optimize costs

#### Quarterly
- [ ] Update dependencies
- [ ] Retrain models with new data
- [ ] Performance audit
- [ ] Security review

### Updating the API

#### Code Updates

```bash
# Make changes locally
git add .
git commit -m "Update: description"
git push origin main

# Render auto-deploys
# Monitor deployment in dashboard
```

#### Model Updates

```bash
# Retrain models
python model_trainer.py

# Commit new models
git add models/*.pkl
git commit -m "Update models with latest data"
git push origin main

# Render will redeploy with new models
```

#### Dependency Updates

```bash
# Update requirements.txt
pip install --upgrade package-name
pip freeze > requirements.txt

# Test locally
python run_api.py
python test_api_startup.py

# Deploy
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### Rollback Procedure

If deployment fails:

1. **Revert to previous version**:
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Or use Render's rollback**:
   - Service → Deploys
   - Find last successful deploy
   - Click "Rollback to this deploy"

3. **Verify rollback**:
   ```bash
   curl $RENDER_URL/health/detailed | jq '.api_version'
   ```

---

## Cost Optimization

### Free Tier Usage

**Limits**:
- 750 build hours/month
- 100 GB bandwidth/month
- Auto-sleep after 15 minutes inactivity

**Optimization**:
- Use persistent disk to reduce build times
- Implement caching to reduce compute
- Monitor bandwidth usage

### Scaling Strategy

**Traffic Levels**:
- **< 1000 requests/day**: Free tier sufficient
- **1000-10000 requests/day**: Starter plan ($7/month)
- **> 10000 requests/day**: Standard plan ($25/month)

**Cost Breakdown**:
```
Free Tier:     $0/month
Starter:       $7/month
Standard:      $25/month
Pro:           $85/month
```

---

## Success Criteria

Deployment is successful when:

- ✅ Build completes without errors
- ✅ Health check returns "healthy" status
- ✅ All 15 models loaded (`fallback_mode: false`)
- ✅ Variety selection works for all locations
- ✅ Predictions return reasonable values
- ✅ Response times < 1 second
- ✅ API documentation accessible at `/docs`
- ✅ No errors in logs for 1 hour
- ✅ API version shows `6.1.0`

---

## Support Resources

### Documentation
- **API Documentation**: `$RENDER_URL/docs`
- **Health Endpoint**: `$RENDER_URL/health/detailed`
- **Local Docs**: `CROP_YIELD_API_DOCUMENTATION.md`

### Render Resources
- **Dashboard**: https://dashboard.render.com
- **Documentation**: https://render.com/docs
- **Status Page**: https://status.render.com
- **Community**: https://community.render.com

### Project Resources
- **GitHub Repository**: Your repository URL
- **Deployment Guide**: This document
- **Model Compatibility**: `MODEL_COMPATIBILITY_DEPLOYMENT_GUIDE.md`
- **Validation Guide**: `VALIDATION_README.md`

---

## Quick Reference

### Essential Commands

```bash
# Health check
curl $RENDER_URL/health

# Detailed health
curl $RENDER_URL/health/detailed | jq '.'

# Test prediction (no variety)
curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{"crop_type":"Rice","location_name":"Bhopal","latitude":23.2599,"longitude":77.4126,"sowing_date":"2024-06-15","use_real_time_data":false}'

# Test prediction (with variety)
curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{"crop_type":"Wheat","variety_name":"PBW 725","location_name":"Chandigarh","latitude":30.7333,"longitude":76.7794,"sowing_date":"2024-11-15","use_real_time_data":false}'

# View logs
# Go to Render dashboard → Service → Logs

# Trigger redeploy
# Push to GitHub or use Render dashboard → Manual Deploy
```

### Environment Variables Template

```env
# Required
ENVIRONMENT=production
PYTHONPATH=/app

# Optional - Google Earth Engine
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_JSON={"type":"service_account",...}

# Optional - OpenWeather
OPENWEATHER_API_KEY=your-api-key

# Optional - Logging
LOG_LEVEL=INFO
```

---

## Conclusion

Your Crop Yield Prediction API v6.1.0 is now deployed on Render with:

✅ **Optional variety selection** - Users can omit variety for automatic selection  
✅ **Regional intelligence** - Varieties selected based on location  
✅ **Backward compatibility** - Existing clients work without changes  
✅ **Robust error handling** - Graceful degradation and clear error messages  
✅ **Production-ready** - Comprehensive testing and validation  

**Next Steps**:
1. Share API URL with users
2. Monitor usage and performance
3. Gather feedback on variety selection
4. Plan for future enhancements

**Questions or Issues?**  
Refer to troubleshooting section or check Render community forums.

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-19  
**API Version**: 6.1.0  
**Author**: Kiro AI Assistant
