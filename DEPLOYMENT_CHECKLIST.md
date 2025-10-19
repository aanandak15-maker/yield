# 🚀 Render Deployment Checklist

## Pre-Deployment Steps

### 1. Clean Up Repository (Optional but Recommended)

```bash
# Review old model files (180 files, 75 MB)
python cleanup_old_models.py

# Delete old models to reduce repository size
python cleanup_old_models.py --delete
```

**Expected Result**: Only 15 latest model files remain

---

### 2. Run Pre-Deployment Check

```bash
# Automated verification
python pre_deployment_check.py
```

**Expected Output**: 
```
🎉 ALL CHECKS PASSED - READY FOR DEPLOYMENT!
```

**If checks fail**: Review and fix issues before proceeding

---

### 3. Commit All Changes

```bash
# Check status
git status

# Add all files
git add .

# Commit with descriptive message
git commit -m "Deploy v6.1.0 with optional variety feature"

# Verify commit
git log -1
```

**Verify**: All deployment files are committed

---

### 4. Push to GitHub

```bash
# Push to main branch
git push origin main

# Verify push succeeded
git log origin/main -1
```

**Verify**: Latest commit is on GitHub

---

## Render Deployment Steps

### 5. Create Render Account (if needed)

- [ ] Go to https://render.com
- [ ] Sign up with GitHub account
- [ ] Verify email address

---

### 6. Connect GitHub Repository

- [ ] Click "New" → "Web Service"
- [ ] Click "Connect GitHub"
- [ ] Authorize Render
- [ ] Select your repository
- [ ] Click "Connect"

---

### 7. Configure Service

**Auto-detected from render.yaml**:
- [ ] Name: `crop-yield-prediction-api`
- [ ] Runtime: Docker
- [ ] Branch: main
- [ ] Dockerfile Path: `./Dockerfile`
- [ ] Health Check Path: `/health`

**Manual Configuration** (if needed):
- [ ] Plan: Starter ($7/month recommended)
- [ ] Region: Choose closest to users

---

### 8. Set Environment Variables

**Required**:
- [ ] `ENVIRONMENT` = `production`
- [ ] `PYTHONPATH` = `/app`
- [ ] `LOG_LEVEL` = `INFO`

**Optional** (for enhanced features):
- [ ] `GEE_SERVICE_ACCOUNT` = your-service-account@project.iam.gserviceaccount.com
- [ ] `GEE_PRIVATE_KEY_JSON` = {full JSON content}
- [ ] `OPENWEATHER_API_KEY` = your-api-key

**Note**: API works without optional credentials

---

### 9. Deploy

- [ ] Review all settings
- [ ] Click "Create Web Service"
- [ ] Monitor build logs

**Expected Duration**: 15-20 minutes

---

## Post-Deployment Verification

### 10. Monitor Build Progress

Watch for these log messages:
- [ ] `Building Docker image...`
- [ ] `Installing dependencies...`
- [ ] `✅ Successfully loaded model: bhopal_training_ridge`
- [ ] `✅ Successfully loaded 15/15 models`
- [ ] `✅ VarietySelectionService initialized successfully`
- [ ] `✅ Crop Yield Prediction Service initialized`

---

### 11. Check Health Status

```bash
# Set your Render URL
export RENDER_URL="https://crop-yield-api-[hash].onrender.com"

# Basic health check
curl $RENDER_URL/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T...",
  "api_version": "6.1.0"
}
```

- [ ] Status is "healthy"
- [ ] API version is "6.1.0"

---

### 12. Detailed Health Check

```bash
# Detailed health information
curl $RENDER_URL/health/detailed | jq '.'
```

**Verify**:
- [ ] `"total_loaded": 15`
- [ ] `"fallback_mode": false`
- [ ] `"variety_selection": "operational"`
- [ ] `"numpy_version": "2.3.4"`
- [ ] `"sklearn_version": "1.7.2"`

---

### 13. Test Optional Variety Feature

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

**Verify**:
- [ ] Prediction successful
- [ ] `"variety_used"` has a value (e.g., "IR-64")
- [ ] `"variety_assumed": true`
- [ ] `"default_variety_selection"` metadata present

---

### 14. Test Backward Compatibility

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

**Verify**:
- [ ] Prediction successful
- [ ] `"variety_used": "PBW 725"`
- [ ] `"variety_assumed": false`
- [ ] No `default_variety_selection` metadata

---

### 15. Test All Locations

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
    }" | jq '.prediction.variety_used, .prediction.variety_assumed'
  echo ""
done
```

**Verify**:
- [ ] All locations return a variety
- [ ] All show `variety_assumed: true`
- [ ] Different varieties for different locations

---

### 16. Test Error Handling

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
```

**Verify**:
- [ ] Returns error response
- [ ] Error message is clear
- [ ] No server crash

---

### 17. Access API Documentation

```bash
# Open interactive API docs
open $RENDER_URL/docs
```

**Verify**:
- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can test endpoints interactively

---

### 18. Check Response Times

```bash
# Measure response time
time curl -X POST $RENDER_URL/predict/yield \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Rice",
    "location_name": "Bhopal",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "sowing_date": "2024-06-15",
    "use_real_time_data": false
  }' > /dev/null
```

**Verify**:
- [ ] Response time < 2 seconds (first request may be slower)
- [ ] Subsequent requests < 1 second

---

## Post-Deployment Configuration

### 19. Set Up Monitoring (Optional)

**UptimeRobot** (Free):
- [ ] Sign up at https://uptimerobot.com
- [ ] Add HTTP(s) monitor
- [ ] URL: `$RENDER_URL/health`
- [ ] Interval: 5 minutes
- [ ] Set up email alerts

**Better Uptime** (Free tier):
- [ ] Sign up at https://betteruptime.com
- [ ] Add monitor
- [ ] Configure notifications

---

### 20. Configure Custom Domain (Optional)

**In Render Dashboard**:
- [ ] Go to Service → Settings → Custom Domains
- [ ] Add custom domain (e.g., `api.yourdomain.com`)
- [ ] Configure DNS CNAME record
- [ ] Wait for SSL certificate (automatic)

**DNS Configuration**:
```
Type: CNAME
Name: api
Value: crop-yield-api-[hash].onrender.com
TTL: 3600
```

---

### 21. Enable Log Aggregation (Optional)

**Papertrail** (Free tier):
- [ ] Sign up at https://papertrailapp.com
- [ ] Get log destination URL
- [ ] Add to Render: Service → Settings → Log Streams
- [ ] Verify logs are flowing

---

### 22. Document Production URL

- [ ] Update README.md with production URL
- [ ] Share URL with team/users
- [ ] Update any client applications
- [ ] Update documentation

---

## Success Criteria

Deployment is successful when ALL of these are true:

- [ ] ✅ Health check returns `"status": "healthy"`
- [ ] ✅ API version shows `"6.1.0"`
- [ ] ✅ All 15 models loaded (`"total_loaded": 15`)
- [ ] ✅ Fallback mode is false (`"fallback_mode": false`)
- [ ] ✅ Variety selection works for all locations
- [ ] ✅ Predictions return reasonable values (0-10 tons/ha)
- [ ] ✅ Response times < 1 second
- [ ] ✅ Backward compatibility maintained
- [ ] ✅ Error handling works correctly
- [ ] ✅ API documentation accessible
- [ ] ✅ No errors in logs for 1 hour

---

## Rollback Plan (If Needed)

### Option 1: Render Dashboard Rollback

1. Go to Render dashboard → Service → Deploys
2. Find last successful deploy
3. Click "Rollback to this deploy"
4. Wait for rollback to complete
5. Verify health check

### Option 2: Git Revert

```bash
# Revert last commit
git revert HEAD

# Push to trigger redeploy
git push origin main

# Monitor deployment
```

### Option 3: Emergency Fallback

The API includes automatic fallback system:
- If models fail to load, fallback models activate
- Service continues with reduced accuracy
- No manual intervention needed

---

## Troubleshooting

### Build Fails

**Check**:
- [ ] Review build logs in Render dashboard
- [ ] Verify Dockerfile syntax
- [ ] Check requirements.txt for conflicts

**Fix**:
```bash
# Test locally
docker build -t crop-yield-api .
```

### Models Not Loading

**Check**:
- [ ] Verify models/ directory in Git
- [ ] Check all 15 .pkl files exist
- [ ] Review model loading logs

**Fix**:
```bash
# Verify models
ls -lh models/*.pkl | wc -l
# Should show 15

# If needed, retrain
python model_trainer.py
```

### Variety Selection Errors

**Check**:
- [ ] Verify database file exists
- [ ] Check database integrity
- [ ] Review variety selection logs

**Fix**:
```bash
# Test database locally
python -c "from src.crop_variety_database import CropVarietyDatabase; db = CropVarietyDatabase(); print(db.get_crop_varieties('Rice', 'Punjab'))"
```

### Slow Response Times

**Check**:
- [ ] Monitor Render metrics
- [ ] Check if on Free tier (auto-sleep)
- [ ] Review logs for bottlenecks

**Fix**:
- Upgrade to Starter plan ($7/month)
- Enable persistent disk
- Optimize code

---

## Maintenance Schedule

### Daily
- [ ] Check Render dashboard for errors
- [ ] Monitor response times
- [ ] Verify health check status

### Weekly
- [ ] Review error logs
- [ ] Check variety selection patterns
- [ ] Monitor API usage

### Monthly
- [ ] Review performance metrics
- [ ] Update dependencies if needed
- [ ] Rotate API keys (if using external services)
- [ ] Review and optimize costs

---

## Support Resources

### Documentation
- **Deployment Guide**: `RENDER_DEPLOYMENT_GUIDE.md`
- **API Documentation**: `CROP_YIELD_API_DOCUMENTATION.md`
- **Quick Reference**: `DEPLOYMENT_READY_SUMMARY.md`

### Tools
- **Pre-deployment Check**: `python pre_deployment_check.py`
- **Model Cleanup**: `python cleanup_old_models.py`
- **End-to-End Tests**: `python test_optional_variety_e2e.py`

### External
- **Render Dashboard**: https://dashboard.render.com
- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Render Community**: https://community.render.com

---

## Completion

Once all checklist items are complete:

- [ ] ✅ All pre-deployment steps completed
- [ ] ✅ Deployment successful
- [ ] ✅ All verification tests passed
- [ ] ✅ Monitoring configured
- [ ] ✅ Documentation updated
- [ ] ✅ Team/users notified

**Congratulations! Your API is now live in production! 🎉**

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-19  
**API Version**: 6.1.0  
**Status**: READY FOR USE ✅
