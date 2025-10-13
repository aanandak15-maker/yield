# 🔑 Railway Environment Variables Setup

## Required Environment Variables

Set these in Railway dashboard under your project > Variables:

### Core Variables
```env
ENVIRONMENT=production
```

### Google Earth Engine (GEE)
```env
# Service Account Email (from GEE setup)
GEE_SERVICE_ACCOUNT=crop-yield-api@your-project.iam.gserviceaccount.com

# Private Key JSON Content (paste entire JSON file content)
GEE_PRIVATE_KEY_JSON={"type": "service_account", "project_id": "...", "private_key": "-----BEGIN PRIVATE KEY-----\n...", "..."}
```

**Note:** Railway has a 5KB limit per environment variable. If your GEE private key JSON is too large:
- Option 1: Store in Railway filesystem (mount as file)
- Option 2: Use Railway secrets storage
- Option 3: Compress/compress JSON content

### OpenWeather API
```env
OPENWEATHER_API_KEY=7ff2c5b7b2d42e3f5e8c4a9d6b1234f
```

## Optional Variables

### Logging & Debugging
```env
PYTHONUNBUFFERED=1          # Force stdout/stderr flushing
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
SOURCE_COMMIT=41dd69e82ca945f34053e7fed0ae774dcbd1b1b4  # Git commit ID
```

### Model Configuration
```env
MODEL_CACHE_SIZE=8          # Number of cached models
DEFAULT_MODEL_REGION=north_india_regional
```

### API Limits & Rates
```env
MAX_REQUEST_SIZE=1048576    # Max request size in bytes (1MB)
RATE_LIMIT_PER_MINUTE=60    # API rate limiting
CACHE_TTL_SECONDS=300       # Cache expiration time
```

## Railway Setup Steps

1. **Access Variables:**
   - Railway Dashboard → Your Project → Variables tab

2. **Add Variables:**
   - Click "Add Variable"
   - Enter KEY (exact name) and VALUE
   - Required variables marked with ⭐
   - Sensitive variables (API keys) marked with 🔐

3. **Required Variables Table:**

| Variable | Value/Format | Required | Sensitive |
|----------|-------------|----------|-----------|
| `ENVIRONMENT` | `production` | ✅ | ❌ |
| `GEE_SERVICE_ACCOUNT` | `email@project.iam.gserviceaccount.com` | ✅ | ❌ |
| `GEE_PRIVATE_KEY_JSON` | `{json_content}` | ✅ | 🔐 |
| `OPENWEATHER_API_KEY` | `32char_hex_key` | ✅ | 🔐 |
| `PYTHONUNBUFFERED` | `1` | ❌ | ❌ |
| `LOG_LEVEL` | `INFO` | ❌ | ❌ |

4. **Redeploy:**
   - After adding variables, Railway automatically redeploys
   - Monitor deployment in dashboard

## ⚠️ Important Notes

### Security
- **Never commit API keys to GitHub**
- **Never share GEE private key JSON**
- Use Railway's variable management - it's encrypted

### Variable Names
- Must match exactly (case-sensitive)
- No spaces or special characters
- Some frameworks expect specific casing

### Deployment Impact
- Environment variables are available at runtime
- Changing them triggers redeploy
- No app downtime during redeploy

### Validation
- Railway doesn't validate values (only presence)
- Test endpoints after setting variables
- Check health endpoint for component status

## 🚨 If GEE JSON Key is Too Large (>5KB)

Railway limits environment variables to 5KB. For large GEE keys:

### Option 1: Environment File Upload
```bash
# Upload as file (recommended)
1. Use Railway's file mount feature
2. Upload ge_credentials.json as /opt/render/project/ge_credentials.json
3. Set GEE_PRIVATE_KEY_PATH=/opt/render/project/ge_credentials.json
```

### Option 2: Railway Secrets
```bash
# Use Railway CLI
railway secrets set GEE_PRIVATE_KEY_JSON="$(cat your-key.json)"
```

## 🧪 Testing Variables

After deployment:

```bash
# Check health to see if services are ready
curl https://your-app.up.railway.app/health
```

Expected response for working setup:
```json
{
  "status": "healthy",
  "components": {
    "gee_client": "ready",
    "weather_client": "ready",
    "models_loaded": 5
  }
}
```

If `unavailable`, check your API keys and GEE setup!
