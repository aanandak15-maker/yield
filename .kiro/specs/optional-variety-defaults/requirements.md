# Requirements Document

## Introduction

This feature enhances the crop yield prediction API by making the variety selection optional. When users don't specify a crop variety, the system will intelligently select the most appropriate variety based on the location and crop type, leveraging existing regional prevalence data in the variety database. This improves user experience by reducing required inputs while maintaining prediction accuracy through smart defaults.

The variety database already contains comprehensive regional prevalence data (e.g., "Punjab,Haryana,UP" for Basmati 370) and yield potential information. This feature surfaces that intelligence to provide sensible defaults when variety information is not available from the user.

## Requirements

### Requirement 1: Optional Variety Field

**User Story:** As an API user, I want to make predictions without specifying a crop variety, so that I can get quick yield estimates when I don't know the specific variety being grown.

#### Acceptance Criteria

1. WHEN a prediction request is submitted WITHOUT a variety_name field THEN the system SHALL accept the request and proceed with default variety selection
2. WHEN a prediction request is submitted WITH a variety_name field THEN the system SHALL use the specified variety as it currently does
3. IF variety_name is provided as null or empty string THEN the system SHALL treat it as missing and apply default selection logic
4. WHEN the API schema is queried THEN variety_name SHALL be documented as optional with a description indicating automatic regional selection

### Requirement 2: Location-to-Region Mapping

**User Story:** As the prediction system, I want to map location names to their corresponding states/regions, so that I can query region-specific variety data from the database.

#### Acceptance Criteria

1. WHEN a location_name is provided (e.g., "Bhopal", "Lucknow", "Chandigarh") THEN the system SHALL map it to the corresponding state (e.g., "Madhya Pradesh", "Uttar Pradesh", "Punjab")
2. IF a location cannot be mapped to a known state THEN the system SHALL use "North India" as a fallback region
3. WHEN mapping locations to regions THEN the system SHALL support all currently available prediction locations (Bhopal, Chandigarh, Lucknow, Patna, North India Regional)
4. IF a location is already a state name THEN the system SHALL use it directly without additional mapping

### Requirement 3: Regional Variety Selection

**User Story:** As the prediction system, I want to select the most appropriate variety based on region and crop type, so that predictions use varieties commonly grown in that area.

#### Acceptance Criteria

1. WHEN variety_name is missing AND location is mapped to a region THEN the system SHALL query the variety database for varieties matching the crop_type and region using `region_prevalence LIKE '%region%'`
2. IF multiple varieties match the region and crop type THEN the system SHALL select the variety with the highest yield_potential value
3. IF no varieties match the specific region THEN the system SHALL query for varieties with region_prevalence containing "All North India"
4. IF no regional varieties are found THEN the system SHALL fall back to a global default variety ranking by crop type
5. WHEN selecting a default variety THEN the system SHALL log the selection decision including region, selected variety, and selection reason

### Requirement 4: Global Default Variety Rankings

**User Story:** As the prediction system, I want to have fallback default varieties for each crop type, so that predictions can proceed even when regional data is unavailable.

#### Acceptance Criteria

1. WHEN no regional variety match is found for Rice THEN the system SHALL use the following priority order: IR-64 → Basmati 370 → Swarna
2. WHEN no regional variety match is found for Wheat THEN the system SHALL use the following priority order: HD 3086 → PBW 725 → C 306
3. WHEN no regional variety match is found for Maize THEN the system SHALL use the following priority order: DHM 117 → HQPM 1 → Baby Corn Hybrid
4. WHEN using a global default THEN the system SHALL log a warning indicating fallback to global defaults

### Requirement 5: Response Transparency

**User Story:** As an API user, I want to know when a default variety was selected and why, so that I can understand the basis of the prediction and provide more specific input if needed.

#### Acceptance Criteria

1. WHEN a default variety is selected THEN the response SHALL include a field `variety_assumed` set to `true` in the prediction section
2. WHEN a user-specified variety is used THEN the response SHALL include a field `variety_assumed` set to `false`
3. WHEN a default variety is selected THEN the response SHALL include a `default_variety_selection` object in the factors section with the following fields:
   - `region`: The region used for selection
   - `reason`: The selection reason (e.g., "regional_highest_yield", "regional_fallback", "global_default")
   - `alternatives`: List of other varieties considered (optional)
4. WHEN the response is returned THEN the `variety_used` field SHALL always contain the actual variety name used for prediction (whether specified or defaulted)

### Requirement 6: Backward Compatibility

**User Story:** As an existing API user, I want my current prediction requests to continue working without modification, so that the new feature doesn't break my existing integration.

#### Acceptance Criteria

1. WHEN an existing prediction request with variety_name is submitted THEN the system SHALL process it exactly as before with no behavioral changes
2. WHEN the API is deployed THEN all existing tests SHALL continue to pass without modification
3. IF variety_name is explicitly provided THEN the system SHALL NOT perform default variety selection logic
4. WHEN API documentation is updated THEN it SHALL clearly indicate that variety_name is now optional while maintaining examples with variety_name for clarity

### Requirement 7: Validation and Error Handling

**User Story:** As the prediction system, I want to validate that selected default varieties exist in the database, so that predictions don't fail due to invalid variety references.

#### Acceptance Criteria

1. WHEN a default variety is selected THEN the system SHALL verify the variety exists in the variety database before proceeding
2. IF a selected default variety is not found in the database THEN the system SHALL try the next variety in the priority list
3. IF no varieties in the priority list are found THEN the system SHALL return an error response with status code 500 and message "Unable to determine appropriate variety for crop type"
4. WHEN variety validation fails THEN the system SHALL log detailed error information including crop type, region, and attempted varieties

### Requirement 8: Performance Considerations

**User Story:** As a system administrator, I want default variety selection to have minimal performance impact, so that API response times remain acceptable.

#### Acceptance Criteria

1. WHEN default variety selection is performed THEN the additional processing time SHALL NOT exceed 50 milliseconds
2. WHEN querying the variety database for regional varieties THEN the system SHALL use indexed queries on crop_type and region_prevalence fields
3. IF variety selection requires multiple database queries THEN the system SHALL cache location-to-region mappings to avoid repeated lookups
4. WHEN the API processes 100 requests with default variety selection THEN the average response time SHALL be within 10% of requests with explicit variety specification
