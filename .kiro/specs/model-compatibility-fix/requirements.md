# Requirements Document

## Introduction

The crop yield prediction API is failing to load trained machine learning models due to NumPy version incompatibility. Models were trained with NumPy 1.24.3 and scikit-learn 1.6.0, but the current environment has NumPy 2.3.3 and scikit-learn 1.7.2. The `numpy._core` module referenced in the pickled models doesn't exist in NumPy 2.x, causing all 14 models to fail loading, leaving only 1 fallback model operational.

## Requirements

### Requirement 1: Model Retraining with Current Dependencies

**User Story:** As a system administrator, I want all ML models retrained with the current NumPy 2.x and scikit-learn 1.7.x versions, so that models load successfully without compatibility errors.

#### Acceptance Criteria

1. WHEN the model training script is executed THEN it SHALL use the currently installed versions of NumPy (2.3.3) and scikit-learn (1.7.2)
2. WHEN models are saved THEN they SHALL be serialized using joblib with the current dependency versions
3. WHEN the API starts THEN it SHALL successfully load all 15 models (5 locations × 3 algorithms) without NumPy compatibility errors
4. WHEN model loading completes THEN the logs SHALL show "✅ Successfully loaded model" for all 15 models instead of compatibility warnings

### Requirement 2: Dependency Version Alignment

**User Story:** As a developer, I want the requirements.txt file to reflect the actual installed versions, so that there are no version mismatches between specification and runtime.

#### Acceptance Criteria

1. WHEN requirements.txt is updated THEN it SHALL specify NumPy 2.3.3 or compatible 2.x version
2. WHEN requirements.txt is updated THEN it SHALL specify scikit-learn 1.7.2 or compatible 1.7.x version
3. WHEN requirements.txt is updated THEN it SHALL specify joblib 1.5.2 or compatible version
4. WHEN pip install is run with updated requirements THEN it SHALL install versions matching the current environment

### Requirement 3: Model Loading Robustness

**User Story:** As a system operator, I want the model loading process to handle version mismatches gracefully, so that the API can provide informative error messages and fallback behavior.

#### Acceptance Criteria

1. WHEN a model fails to load due to version mismatch THEN the system SHALL log the specific incompatibility issue with library versions
2. WHEN model loading fails THEN the system SHALL provide a clear error message indicating which models failed and why
3. WHEN all models fail to load THEN the system SHALL fall back to the existing fallback models and log a warning
4. WHEN the API health check is called THEN it SHALL report the number of successfully loaded models and any compatibility issues

### Requirement 4: Validation and Testing

**User Story:** As a quality assurance engineer, I want to verify that retrained models produce predictions comparable to the original models, so that we maintain prediction accuracy.

#### Acceptance Criteria

1. WHEN models are retrained THEN the system SHALL generate a comparison report showing R² scores and RMSE for old vs new models
2. WHEN model performance is evaluated THEN new models SHALL achieve R² scores within 5% of original models
3. WHEN the API makes predictions THEN it SHALL successfully use the newly trained models without errors
4. WHEN a test prediction request is made THEN the API SHALL return valid predictions with confidence scores
