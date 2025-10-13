# 🚀 Render Deployment Guide - Crop Yield Prediction API

## Pre-deployment Checklist

### 1. GitHub Repository Setup
- ✅ Code committed with Render configuration files
- 📝 **Create new repository**: `https://github.com/aanandak15-maker/crop-yield-api`
- 📝 **Push code** to new repository

### 2. API Credentials (Required for Production)
- ✅ **Google Earth Engine Account**:
  - Create service account at https://console.cloud.google.com
  - Download private key JSON file
  - Share with Google Earth Engine assets

- ✅ **OpenWeather API**:
  - Sign up at https://openweathermap.org/api
  - Get free API key (1 million calls/month)

## Render Deployment Steps

### Step 1: Create Repository
1. Go to https://github.com and sign in
2. Click "New repository"
3. Name: `crop-yield-api`
4. Make it **public**
5. **Don't initialize with README** (we'll push our own)
6. Click "Create repository"

### Step 2: Push Code to GitHub
```bash
# In terminal - update remote URL to your new repository
git remote set-url origin https://github.com/aanandak15-maker/crop-yield-api.git
git push -u origin main
```

### Step 3: Deploy on Render

#### 3.1 Create Render Account
- Go to https://render.com
- Sign up with GitHub account
- Verify email

#### 3.2 Connect Repository
1. Click "New" → "Web Service"
2. Connect GitHub account
3. Search for `crop-yield-api` repository
4. Click "Connect"

#### 3.3 Configure Service
```yaml
# Render will auto-detect from render.yaml:
Name: crop-yield-prediction-api
Runtime: Python 3
Branch: main
Build Command: pip install -r requirements.txt
Start Command: python run_api.py
```

#### 3.4 Environment Variables
```env
ENVIRONMENT=production
GEE_SERVICE_ACCOUNT=your-gee-service-account-name@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_PATH=/opt/render/project/src/config/gee-auth.json  # Render stores it here
OPENWEATHER_API_KEY=your-openweather-api-key
```

**⚠️ Important**: For GEE private key:
- Copy the JSON content
- Paste as environment variable named `GEE_PRIVATE_KEY_JSON`
- Render will create the auth file automatically

#### 3.5 Deploy
- Click "Create Web Service"
- Deployment takes 10-15 minutes
- You'll get a production URL: `https://crop-yield-api-[hash].onrender.com`

## Post-deployment Verification

### 1. Health Check
```bash
curl https://your-render-url.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "services": {
    "google_earth_engine": "operational",
    "openweather_api": "operational",
    "machine_learning_models": "loaded",
    "database": "connected"
  },
  "version": "1.0.0"
}
```

### 2. Test Prediction
```bash
curl -X POST https://your-render-url.onrender.com/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "variety_name": "C 306",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "sowing_date": "2024-07-21"
  }'
```

### 3. Test Dashboard
- Visit: `https://your-render-url.onrender.com/dashboard`
- Interactive web interface should load

## Production Configuration

### Free Tier Limits (Render)
- 750 build hours/month
- 100 GB bandwidth
- Free custom domain
- Auto SSL certificate

### API Limits
- Google Earth Engine: Check quota dashboard
- OpenWeather: 1,000,000 calls/month (free tier)
- No rate limiting implemented (add if needed)

### Environment Variables (Complete List)
```env
# Required
ENVIRONMENT=production
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_JSON={"type": "service_account", ...}  # Full JSON content
OPENWEATHER_API_KEY=your-openweather-key

# Optional
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
CACHE_EXPIRE_MINUTES=30
```

## Troubleshooting

### Common Issues

**1. Build Failures**
```bash
# Check logs in Render dashboard
2024-10-13T18:47:12+00:00 ERROR: pip install dependency failed
# Solution: Check requirements.txt compatibility
```

**2. API Not Starting**
```bash
# Check environment variables
curl https://your-render-url.onrender.com/health
# Should show healthy status
```

**3. GEE Authentication**
```bash
# Verify key format in environment variables
# Ensure service account has GEE access
```

**4. Memory Issues**
- Render Free tier: 1GB RAM
- If models don't load, may need recurring plan ($7/month)

## Cost Optimization

### Free Tier Usage
- **750 build hours**: ~65 hours/month with tolerance
- **Auto-sleep**: Scales to zero when not used
- **Resume time**: ~30 seconds cold start

### Scaling Options
- **Starter**: $7/month - more build hours
- **Standard**: $25/month - higher performance
- **Up to 4GB RAM**

## Custom Domain (Optional)

1. Go to Render Dashboard → Service Settings
2. Add custom domain
3. Configure DNS records
4. SSL certificate is automatic (free)

## Monitoring & Maintenance

### Logs
- View in Render dashboard
- Automatic retention 30 days

### Health Monitoring
- Set up external uptime monitoring
- Monitor API response times

### Updates
- Push code changes to GitHub
- Render auto-deploys
- Zero-downtime deployments

## Production Checklist

- [ ] GitHub repository created and code pushed
- [ ] Render web service configured
- [ ] Environment variables set (API keys)
- [ ] Health check passing
- [ ] Test prediction working
- [ ] Dashboard accessible
- [ ] Custom domain configured (optional)
- [ ] Monitoring setup
- [ ] Share API documentation with users

---

**Ready for deployment!** 🏆

**Estimated time: 20-30 minutes from repository creation to live API**

**Questions? Refer to CROP_YIELD_API_DOCUMENTATION.md for complete API reference**
