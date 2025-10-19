# Design Document

## Overview

This design document details the implementation approach for making crop variety selection optional in the prediction API. The feature leverages existing regional prevalence data in the variety database to intelligently select appropriate varieties when users don't specify one. The design maintains backward compatibility while adding transparent default selection logic.

### Key Design Principles

1. **Leverage Existing Data**: Use the variety database's `region_prevalence` field and `yield_potential` metrics
2. **Transparent Defaults**: Always inform users when a default variety was selected
3. **Backward Compatible**: Existing API behavior remains unchanged when variety is specified
4. **Performance Conscious**: Minimize additional latency through efficient queries and caching
5. **Fail Gracefully**: Provide clear error messages when variety selection fails

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Prediction API                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         PredictionRequest (Modified)                    │ │
│  │  - variety_name: Optional[str]                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │    VarietySelectionService (New)                       │ │
│  │  - select_default_variety()                            │ │
│  │  - map_location_to_region()                            │ │
│  │  - get_regional_varieties()                            │ │
│  │  - get_global_default()                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      CropVarietyDatabase (Existing)                    │ │
│  │  - get_crop_varieties(crop_type, region)               │ │
│  │  - get_variety_by_name(crop_type, variety_name)        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request Received**: API receives prediction request with optional variety_name
2. **Variety Check**: If variety_name is missing/null/empty, trigger default selection
3. **Region Mapping**: Map location_name to state/region
4. **Database Query**: Query variety database for regional varieties
5. **Selection Logic**: Select highest yield_potential variety or fallback to global defaults
6. **Validation**: Verify selected variety exists in database
7. **Prediction**: Proceed with normal prediction flow using selected variety
8. **Response Enhancement**: Add variety_assumed and selection metadata to response

## Components and Interfaces

### 1. Modified PredictionRequest Model

**Location**: `src/prediction_api.py`

**Changes**:
```python
class PredictionRequest(BaseModel):
    """Pydantic model for prediction request validation"""

    crop_type: str = Field(
        ..., description="Crop type (Rice, Wheat, Maize)",
        pattern="^(Rice|Wheat|Maize)$"
    )
    variety_name: Optional[str] = Field(
        None, 
        description="Crop variety name (optional - defaults to regional most popular)"
    )
    location_name: str = Field(
        ..., description="Location name (e.g., Bhopal, Lucknow)"
    )
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="Location latitude (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="Location longitude (-180 to 180)"
    )
    sowing_date: str = Field(
        ..., description="Sowing date (YYYY-MM-DD)"
    )
    use_real_time_data: bool = Field(
        default=True, description="Use real-time satellite and weather data"
    )
```

**Key Changes**:
- `variety_name` changed from required (`...`) to optional (`None`)
- Updated description to indicate automatic regional selection
- No validator needed as None/empty string are valid values

### 2. New VarietySelectionService Class

**Location**: `src/variety_selection_service.py` (new file)

**Purpose**: Encapsulate all variety selection logic in a dedicated service class

**Interface**:
```python
class VarietySelectionService:
    """Service for intelligent variety selection based on location and crop type"""
    
    def __init__(self, variety_db: CropVarietyDatabase):
        """
        Initialize variety selection service
        
        Args:
            variety_db: Instance of CropVarietyDatabase
        """
        self.variety_db = variety_db
        self.logger = logging.getLogger(__name__)
        self._location_region_cache = {}
        self._initialize_location_mappings()
    
    def select_default_variety(
        self, 
        crop_type: str, 
        location_name: str
    ) -> Dict[str, Any]:
        """
        Select appropriate default variety based on crop type and location
        
        Args:
            crop_type: Crop type (Rice, Wheat, Maize)
            location_name: Location name (e.g., Bhopal, Lucknow)
        
        Returns:
            Dictionary containing:
            - variety_name: Selected variety name
            - variety_assumed: Always True for this method
            - selection_metadata: Details about selection process
        
        Raises:
            ValueError: If no appropriate variety can be determined
        """
        pass
    
    def map_location_to_region(self, location_name: str) -> str:
        """
        Map location name to state/region
        
        Args:
            location_name: Location name
        
        Returns:
            State/region name (e.g., "Punjab", "Uttar Pradesh")
        """
        pass
    
    def get_regional_varieties(
        self, 
        crop_type: str, 
        region: str
    ) -> pd.DataFrame:
        """
        Get varieties for specific crop type and region
        
        Args:
            crop_type: Crop type
            region: Region/state name
        
        Returns:
            DataFrame of matching varieties sorted by yield_potential (descending)
        """
        pass
    
    def get_global_default(self, crop_type: str) -> str:
        """
        Get global default variety for crop type
        
        Args:
            crop_type: Crop type
        
        Returns:
            Default variety name
        
        Raises:
            ValueError: If crop type is invalid
        """
        pass
```

### 3. Location-to-Region Mapping

**Implementation Strategy**: Static mapping with caching

**Mapping Table**:
```python
LOCATION_REGION_MAPPING = {
    # Cities to States
    'bhopal': 'Madhya Pradesh',
    'lucknow': 'Uttar Pradesh',
    'chandigarh': 'Punjab',  # Also Haryana, but Punjab is primary
    'patna': 'Bihar',
    'delhi': 'Delhi',
    'jaipur': 'Rajasthan',
    'amritsar': 'Punjab',
    'ludhiana': 'Punjab',
    'kanpur': 'Uttar Pradesh',
    'agra': 'Uttar Pradesh',
    'varanasi': 'Uttar Pradesh',
    'allahabad': 'Uttar Pradesh',
    'prayagraj': 'Uttar Pradesh',
    'gwalior': 'Madhya Pradesh',
    'indore': 'Madhya Pradesh',
    'jabalpur': 'Madhya Pradesh',
    
    # Regional identifiers
    'north india regional': 'All North India',
    'north india': 'All North India',
    
    # States (pass-through)
    'punjab': 'Punjab',
    'haryana': 'Haryana',
    'uttar pradesh': 'Uttar Pradesh',
    'up': 'Uttar Pradesh',
    'madhya pradesh': 'Madhya Pradesh',
    'mp': 'Madhya Pradesh',
    'bihar': 'Bihar',
    'rajasthan': 'Rajasthan',
    'delhi': 'Delhi'
}

# Fallback region for unmapped locations
DEFAULT_REGION = 'All North India'
```

**Caching Strategy**:
- Cache mappings in memory on first lookup
- No expiration needed (static data)
- Case-insensitive matching

### 4. Regional Variety Selection Logic

**Algorithm**:

```python
def select_default_variety(crop_type: str, location_name: str) -> Dict:
    # Step 1: Map location to region
    region = map_location_to_region(location_name)
    
    # Step 2: Query regional varieties
    regional_varieties = get_regional_varieties(crop_type, region)
    
    # Step 3: Select highest yield potential
    if not regional_varieties.empty:
        selected = regional_varieties.iloc[0]  # Already sorted by yield_potential DESC
        return {
            'variety_name': selected['variety_name'],
            'variety_assumed': True,
            'selection_metadata': {
                'region': region,
                'reason': 'regional_highest_yield',
                'yield_potential': selected['yield_potential'],
                'alternatives': regional_varieties['variety_name'].tolist()[1:4]  # Top 3 alternatives
            }
        }
    
    # Step 4: Try "All North India" fallback
    if region != 'All North India':
        fallback_varieties = get_regional_varieties(crop_type, 'All North India')
        if not fallback_varieties.empty:
            selected = fallback_varieties.iloc[0]
            return {
                'variety_name': selected['variety_name'],
                'variety_assumed': True,
                'selection_metadata': {
                    'region': 'All North India',
                    'reason': 'regional_fallback',
                    'original_region': region,
                    'yield_potential': selected['yield_potential']
                }
            }
    
    # Step 5: Use global defaults
    default_variety = get_global_default(crop_type)
    return {
        'variety_name': default_variety,
        'variety_assumed': True,
        'selection_metadata': {
            'region': region,
            'reason': 'global_default',
            'note': 'No regional varieties found'
        }
    }
```

### 5. Global Default Rankings

**Implementation**: Static dictionary with priority lists

```python
GLOBAL_DEFAULT_VARIETIES = {
    'Rice': ['IR-64', 'Basmati 370', 'Swarna'],
    'Wheat': ['HD 3086', 'PBW 725', 'C 306'],
    'Maize': ['DHM 117', 'HQPM 1', 'Baby Corn Hybrid']
}

def get_global_default(crop_type: str) -> str:
    """Get first available global default variety"""
    if crop_type not in GLOBAL_DEFAULT_VARIETIES:
        raise ValueError(f"Invalid crop type: {crop_type}")
    
    defaults = GLOBAL_DEFAULT_VARIETIES[crop_type]
    
    # Try each default in order, verify it exists in database
    for variety_name in defaults:
        variety_info = variety_db.get_variety_by_name(crop_type, variety_name)
        if variety_info:
            return variety_name
    
    # If none found, raise error
    raise ValueError(f"No default varieties found in database for {crop_type}")
```

### 6. Modified Prediction Flow

**Location**: `src/prediction_api.py` - `CropYieldPredictionService.predict_yield()`

**Changes**:

```python
def predict_yield(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main prediction function with optional variety support"""
    
    # NEW: Check if variety needs to be selected
    variety_assumed = False
    selection_metadata = None
    
    if not request_data.get('variety_name'):
        # Select default variety
        selection_result = self.variety_selector.select_default_variety(
            request_data['crop_type'],
            request_data['location_name']
        )
        request_data['variety_name'] = selection_result['variety_name']
        variety_assumed = True
        selection_metadata = selection_result['selection_metadata']
        
        self.logger.info(
            f"🔄 Auto-selected variety: {request_data['variety_name']} "
            f"(reason: {selection_metadata['reason']})"
        )
    
    # EXISTING: Validate variety exists
    variety_info = self.variety_db.get_variety_by_name(
        request_data['crop_type'],
        request_data['variety_name']
    )
    
    if not variety_info:
        return self._error_response(
            "InvalidInput",
            f"Variety '{request_data['variety_name']}' not found for crop '{request_data['crop_type']}'",
            variety_found=False
        )
    
    # ... rest of existing prediction logic ...
    
    # MODIFIED: Enhanced response with variety selection metadata
    response = {
        # ... existing response fields ...
        'prediction': {
            'yield_tons_per_hectare': round(float(model_result['prediction']), 2),
            'variety_used': request_data['variety_name'],  # NEW
            'variety_assumed': variety_assumed,  # NEW
            # ... other prediction fields ...
        },
        'factors': {
            # ... existing factors ...
        }
    }
    
    # NEW: Add selection metadata if variety was assumed
    if variety_assumed and selection_metadata:
        response['factors']['default_variety_selection'] = selection_metadata
    
    return response
```

## Data Models

### Enhanced Prediction Response

```json
{
  "prediction_id": "Rice_Bhopal_20251019_143022",
  "timestamp": "2025-10-19T14:30:22",
  
  "input": {
    "crop_type": "Rice",
    "variety_name": null,
    "location": {
      "name": "Bhopal",
      "latitude": 23.2599,
      "longitude": 77.4126
    },
    "sowing_date": "2024-06-15",
    "growth_days": 127,
    "use_real_time_data": true
  },
  
  "prediction": {
    "yield_tons_per_hectare": 5.8,
    "variety_used": "Swarna",
    "variety_assumed": true,
    "lower_bound": 5.2,
    "upper_bound": 6.4,
    "confidence_score": 0.85,
    "variety_adjusted_yield": 5.9
  },
  
  "model": {
    "location_used": "bhopal_training",
    "algorithm": "gradient_boosting",
    "model_timestamp": "20251019_120000",
    "feature_count": 15
  },
  
  "factors": {
    "variety_characteristics": {
      "maturity_days": 140,
      "yield_potential": 5.8,
      "drought_tolerance": "Medium"
    },
    "default_variety_selection": {
      "region": "Madhya Pradesh",
      "reason": "regional_highest_yield",
      "yield_potential": 5.8,
      "alternatives": ["IR-64", "Basmati 370"]
    },
    "environmental_adjustments": {
      "heat_stress_penalty": 0.05,
      "drought_penalty": 0.02,
      "cold_stress_penalty": 0.0,
      "optimal_temp_bonus": 0.15
    },
    "data_quality": 0.92
  },
  
  "data_sources": {
    "satellite_data_points": 30,
    "weather_data_points": 56,
    "data_freshness_hours": 24
  },
  
  "processing_time_seconds": 2.34,
  "api_version": "6.1.0"
}
```

### Selection Metadata Schema

```python
SelectionMetadata = {
    'region': str,  # Region used for selection
    'reason': str,  # One of: 'regional_highest_yield', 'regional_fallback', 'global_default'
    'yield_potential': float,  # Optional: yield potential of selected variety
    'alternatives': List[str],  # Optional: other varieties considered
    'original_region': str,  # Optional: for fallback scenarios
    'note': str  # Optional: additional context
}
```

## Error Handling

### Error Scenarios and Responses

#### 1. No Varieties Found for Crop Type

**Scenario**: Database has no varieties for the requested crop type

**Response**:
```json
{
  "error": {
    "code": "NoVarietiesAvailable",
    "message": "Unable to determine appropriate variety for crop type 'Rice'",
    "details": {
      "crop_type": "Rice",
      "region_attempted": "Madhya Pradesh",
      "fallback_attempted": "All North India",
      "global_defaults_attempted": ["IR-64", "Basmati 370", "Swarna"]
    }
  },
  "status": 500
}
```

#### 2. Invalid Location Mapping

**Scenario**: Location cannot be mapped to a region (handled gracefully)

**Behavior**: Use "All North India" as fallback region, log warning

**Log Message**:
```
⚠️  Unknown location 'XYZ', using fallback region 'All North India'
```

#### 3. Database Query Failure

**Scenario**: Variety database query fails

**Response**:
```json
{
  "error": {
    "code": "DatabaseError",
    "message": "Failed to query variety database",
    "details": {
      "operation": "get_regional_varieties",
      "crop_type": "Rice",
      "region": "Punjab"
    }
  },
  "status": 500
}
```

## Testing Strategy

### Unit Tests

**File**: `test_variety_selection_service.py`

**Test Cases**:
1. `test_location_to_region_mapping_known_cities`
2. `test_location_to_region_mapping_unknown_location`
3. `test_location_to_region_mapping_case_insensitive`
4. `test_get_regional_varieties_with_matches`
5. `test_get_regional_varieties_no_matches`
6. `test_select_default_variety_regional_success`
7. `test_select_default_variety_fallback_to_north_india`
8. `test_select_default_variety_global_default`
9. `test_get_global_default_valid_crop`
10. `test_get_global_default_invalid_crop`
11. `test_variety_selection_caching`

### Integration Tests

**File**: `test_optional_variety_integration.py`

**Test Cases**:
1. `test_prediction_without_variety_bhopal_rice`
2. `test_prediction_without_variety_chandigarh_wheat`
3. `test_prediction_without_variety_lucknow_maize`
4. `test_prediction_with_variety_unchanged_behavior`
5. `test_prediction_variety_null_treated_as_missing`
6. `test_prediction_variety_empty_string_treated_as_missing`
7. `test_response_includes_variety_assumed_true`
8. `test_response_includes_variety_assumed_false`
9. `test_response_includes_selection_metadata`
10. `test_backward_compatibility_existing_requests`

### Performance Tests

**File**: `test_variety_selection_performance.py`

**Test Cases**:
1. `test_variety_selection_latency_under_50ms`
2. `test_cached_location_mapping_performance`
3. `test_100_requests_with_variety_selection`
4. `test_response_time_comparison_with_without_variety`

## Performance Considerations

### Query Optimization

**Database Indexes**:
```sql
-- Ensure these indexes exist for optimal performance
CREATE INDEX IF NOT EXISTS idx_crop_varieties_crop_type 
    ON crop_varieties(crop_type);

CREATE INDEX IF NOT EXISTS idx_crop_varieties_region 
    ON crop_varieties(region_prevalence);

CREATE INDEX IF NOT EXISTS idx_crop_varieties_crop_region 
    ON crop_varieties(crop_type, region_prevalence);
```

### Caching Strategy

**Location-to-Region Cache**:
- In-memory dictionary
- Populated on first service initialization
- No expiration (static data)
- Estimated memory: < 10KB

**Regional Varieties Cache** (Optional Enhancement):
- Cache query results for (crop_type, region) pairs
- TTL: 1 hour (varieties rarely change)
- Max size: 100 entries
- Estimated memory: < 1MB

### Expected Performance Impact

- **Without caching**: +30-50ms per request
- **With caching**: +5-10ms per request
- **Database query time**: 10-20ms (with indexes)
- **Selection logic time**: < 5ms

## Security Considerations

### Input Validation

- Location names sanitized before database queries (prevent SQL injection)
- Crop type validated against whitelist (Rice, Wheat, Maize)
- No user-provided SQL in variety queries

### Logging

- Log variety selection decisions (audit trail)
- Do not log sensitive user data
- Log level: INFO for selections, WARNING for fallbacks, ERROR for failures

## Deployment Strategy

### Phase 1: Code Deployment

1. Deploy `VarietySelectionService` class
2. Update `PredictionRequest` model
3. Modify `predict_yield()` method
4. Deploy without enabling feature (variety still required)

### Phase 2: Database Verification

1. Verify all default varieties exist in database
2. Verify region_prevalence data is accurate
3. Create database indexes if missing

### Phase 3: Feature Enablement

1. Make variety_name optional in API schema
2. Enable variety selection logic
3. Monitor logs for selection patterns

### Phase 4: Documentation Update

1. Update API documentation
2. Add examples with and without variety
3. Update client SDKs (if applicable)

## Rollback Plan

If issues arise:

1. **Immediate**: Revert `PredictionRequest` to require variety_name
2. **Code Rollback**: Revert to previous API version
3. **Database**: No database changes needed (backward compatible)
4. **Monitoring**: Check for increased error rates or latency

## Future Enhancements

### 1. Machine Learning-Based Selection

Use historical prediction accuracy to select varieties:
- Track which varieties produce most accurate predictions per region
- Weight selection by prediction accuracy, not just yield potential

### 2. Seasonal Variety Selection

Consider sowing date to select season-appropriate varieties:
- Kharif varieties for June-July sowing
- Rabi varieties for October-November sowing

### 3. User Preference Learning

Allow users to provide feedback on variety selections:
- Track which varieties users override
- Adjust defaults based on user patterns

### 4. Multi-Region Varieties

Handle varieties prevalent in multiple regions:
- Consider distance from location to region centers
- Weight by regional adoption rates

## Monitoring and Metrics

### Key Metrics to Track

1. **Variety Selection Rate**: % of requests without variety_name
2. **Selection Reason Distribution**: regional_highest_yield vs fallback vs global_default
3. **Selection Latency**: Time spent in variety selection logic
4. **Selection Failures**: Requests that fail due to variety selection errors
5. **Override Rate**: Users who specify variety after seeing default (future)

### Logging Examples

```python
# Successful regional selection
logger.info(
    f"✅ Selected variety '{variety_name}' for {crop_type} in {region} "
    f"(yield potential: {yield_potential} t/ha, reason: regional_highest_yield)"
)

# Fallback to North India
logger.warning(
    f"⚠️  No varieties found for {crop_type} in {region}, "
    f"falling back to 'All North India' region"
)

# Global default used
logger.warning(
    f"⚠️  Using global default '{variety_name}' for {crop_type} "
    f"(no regional varieties found)"
)

# Selection failure
logger.error(
    f"❌ Failed to select variety for {crop_type} in {region}: "
    f"no varieties available in database"
)
```

## Documentation Updates

### API Documentation Changes

**Before**:
```
POST /predict/yield

Required Parameters:
- crop_type: string (Rice, Wheat, Maize)
- variety_name: string
- location_name: string
- latitude: float
- longitude: float
- sowing_date: string (YYYY-MM-DD)
```

**After**:
```
POST /predict/yield

Required Parameters:
- crop_type: string (Rice, Wheat, Maize)
- location_name: string
- latitude: float
- longitude: float
- sowing_date: string (YYYY-MM-DD)

Optional Parameters:
- variety_name: string (if not provided, system selects most appropriate 
  variety based on location and crop type)
```

### Example Requests

**With Variety (Existing)**:
```json
{
  "crop_type": "Rice",
  "variety_name": "Basmati 370",
  "location_name": "Bhopal",
  "latitude": 23.2599,
  "longitude": 77.4126,
  "sowing_date": "2024-06-15"
}
```

**Without Variety (New)**:
```json
{
  "crop_type": "Rice",
  "location_name": "Bhopal",
  "latitude": 23.2599,
  "longitude": 77.4126,
  "sowing_date": "2024-06-15"
}
```

## Success Criteria

The design is considered successful when:

1. ✅ Variety selection adds < 50ms latency
2. ✅ 95%+ of requests without variety successfully select a default
3. ✅ All existing tests pass without modification
4. ✅ Regional varieties selected 80%+ of the time (vs global defaults)
5. ✅ Zero SQL injection vulnerabilities
6. ✅ Clear logging of all selection decisions
7. ✅ Response transparency: users always know when variety was assumed
8. ✅ Backward compatibility: existing integrations work unchanged

