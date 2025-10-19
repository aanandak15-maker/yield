# Implementation Plan

- [x] 1. Create VarietySelectionService class with core selection logic
  - Create new file `src/variety_selection_service.py`
  - Implement `__init__` method with variety database dependency injection
  - Implement location-to-region mapping with static dictionary and caching
  - Implement `map_location_to_region()` method with case-insensitive matching
  - Implement `get_regional_varieties()` method to query database by crop type and region
  - Implement `get_global_default()` method with priority lists for Rice, Wheat, and Maize
  - Implement `select_default_variety()` method orchestrating the full selection flow
  - Add comprehensive logging for selection decisions, fallbacks, and errors
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3, 7.4_

- [x] 2. Update PredictionRequest model to make variety optional
  - Modify `variety_name` field in `PredictionRequest` class from required to Optional[str]
  - Update field description to indicate automatic regional selection
  - Update field default value to None
  - Verify Pydantic validation accepts None, null, and empty string values
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Integrate VarietySelectionService into CropYieldPredictionService
  - Import VarietySelectionService in `src/prediction_api.py`
  - Initialize VarietySelectionService instance in `_initialize_components()` method
  - Pass variety_db instance to VarietySelectionService constructor
  - Add error handling for VarietySelectionService initialization failures
  - _Requirements: 1.1, 7.1_

- [x] 4. Modify predict_yield method to handle optional variety
  - Add variety selection logic at start of `predict_yield()` method
  - Check if `variety_name` is None, null, or empty string
  - Call `variety_selector.select_default_variety()` when variety is missing
  - Store selection result including variety_name and metadata
  - Update request_data with selected variety_name
  - Add logging for variety selection with reason and selected variety
  - Preserve existing behavior when variety_name is provided
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Enhance prediction response with variety selection metadata
  - Add `variety_used` field to prediction section of response
  - Add `variety_assumed` boolean field to prediction section
  - Add `default_variety_selection` object to factors section when variety was assumed
  - Include region, reason, yield_potential, and alternatives in selection metadata
  - Ensure metadata is only added when variety was actually selected by system
  - Update API version number to 6.1.0
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Add database indexes for variety queries
  - Create database migration script or update `_setup_database()` in CropVarietyDatabase
  - Add index on `crop_type` column in crop_varieties table
  - Add index on `region_prevalence` column in crop_varieties table
  - Add composite index on (crop_type, region_prevalence) for optimal query performance
  - Verify indexes are created successfully on service startup
  - _Requirements: 8.2_

- [x] 7. Write unit tests for VarietySelectionService
  - Create `test_variety_selection_service.py` test file
  - Write test for location-to-region mapping with known cities
  - Write test for location-to-region mapping with unknown locations (fallback)
  - Write test for case-insensitive location mapping
  - Write test for get_regional_varieties with matching varieties
  - Write test for get_regional_varieties with no matches
  - Write test for select_default_variety with regional success
  - Write test for select_default_variety with fallback to "All North India"
  - Write test for select_default_variety using global defaults
  - Write test for get_global_default with valid crop types
  - Write test for get_global_default with invalid crop type (error case)
  - Write test for location mapping caching behavior
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 7.1, 7.2, 7.3_

- [x] 8. Write integration tests for optional variety feature
  - Create `test_optional_variety_integration.py` test file
  - Write test for prediction without variety for Bhopal + Rice
  - Write test for prediction without variety for Chandigarh + Wheat
  - Write test for prediction without variety for Lucknow + Maize
  - Write test for prediction with variety (verify unchanged behavior)
  - Write test for prediction with variety_name=null (treated as missing)
  - Write test for prediction with variety_name="" (treated as missing)
  - Write test verifying response includes variety_assumed=true when variety selected
  - Write test verifying response includes variety_assumed=false when variety provided
  - Write test verifying response includes selection_metadata when variety assumed
  - Write test for backward compatibility with existing request format
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4_

- [x] 9. Write performance tests for variety selection
  - Create `test_variety_selection_performance.py` test file
  - Write test measuring variety selection latency (must be < 50ms)
  - Write test measuring cached location mapping performance
  - Write test processing 100 requests with variety selection
  - Write test comparing response times with and without variety specification
  - Verify average response time increase is within 10% threshold
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 10. Add error handling and validation
  - Add try-catch blocks around variety selection logic in predict_yield
  - Create error response for "NoVarietiesAvailable" scenario
  - Create error response for database query failures
  - Add input sanitization for location_name before database queries
  - Add validation that selected variety exists in database before proceeding
  - Implement fallback chain: regional → All North India → global defaults → error
  - Add detailed error logging with crop type, region, and attempted varieties
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 11. Update API documentation
  - Update API endpoint documentation to mark variety_name as optional
  - Add description explaining automatic variety selection behavior
  - Add example request without variety_name field
  - Add example response showing variety_assumed=true and selection metadata
  - Update existing examples to show both with-variety and without-variety cases
  - Document selection logic: regional → fallback → global defaults
  - Document response fields: variety_used, variety_assumed, default_variety_selection
  - Update API version to 6.1.0 in documentation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.4_

- [x] 12. Verify backward compatibility
  - Run all existing prediction tests without modifications
  - Verify all tests pass with no changes to test code
  - Test existing client requests with variety_name specified
  - Verify response format is unchanged when variety is provided
  - Verify variety_assumed=false when variety is explicitly provided
  - Confirm no breaking changes to API contract
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 13. Add monitoring and logging
  - Add INFO-level logging for successful variety selections with reason
  - Add WARNING-level logging for fallback scenarios (regional → North India)
  - Add WARNING-level logging for global default usage
  - Add ERROR-level logging for variety selection failures
  - Log selection metadata: crop type, region, selected variety, reason, yield potential
  - Add performance timing logs for variety selection operations
  - Ensure no sensitive user data is logged
  - _Requirements: 3.5, 7.4_

- [x] 14. Create end-to-end validation test
  - Create `test_optional_variety_e2e.py` test file
  - Write test simulating full prediction flow without variety for each location
  - Verify correct variety selected for each region (Bhopal→MP, Lucknow→UP, etc.)
  - Verify prediction completes successfully with selected variety
  - Verify response includes all required metadata fields
  - Test error scenarios: invalid crop type, unknown location, database unavailable
  - Verify graceful degradation when variety database is empty
  - _Requirements: 1.1, 2.1, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3, 7.1, 7.2, 7.3, 7.4_
