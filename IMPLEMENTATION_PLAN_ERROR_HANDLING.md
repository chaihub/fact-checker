# IMPLEMENTATION PLAN: Enhanced Error Context Tracking

## 1. **Data Model Changes**

### 1.1 New Model: ErrorDetails (src/factchecker/core/models.py)
**Create new model to store detailed error information:**

```python
class ErrorDetails(BaseModel):
    """Detailed error information for debugging."""
    
    failed_stage: str
    failed_function: str
    error_type: str
    error_message: str
    input_parameters: dict
    traceback_summary: str
    timestamp: datetime
```

**Fields:**
- `failed_stage`: Pipeline stage name (e.g., "Cache Lookup", "Claim Extraction")
- `failed_function`: Full function name/path (e.g., "_check_cache", "cache.get")
- `error_type`: Exception type (e.g., "Exception", "ValueError")
- `error_message`: Exception message
- `input_parameters`: Dict of input params to failed function (sanitized for sensitive data)
- `traceback_summary`: Condensed traceback showing call chain
- `timestamp`: When error occurred

### 1.2 VerdictEnum (UNCHANGED)
**Add:**
- `ERROR = "error"`

### 1.3 FactCheckResponse (UPDATED)
**Add error details field:**
- Change `evidence: List[Evidence]` → `evidence: Optional[List[Evidence]] = None`
- Change `references: List[Reference]` → `references: Optional[List[Reference]] = None`
- Change `search_queries_used: List[str]` → `search_queries_used: Optional[List[str]] = None`
- **Add NEW:** `error_details: Optional[ErrorDetails] = None`

---

## 2. **Exception Context Capture Architecture**

### 2.1 New Custom Exception Class (src/factchecker/pipeline/factcheck_pipeline.py)
**Create wrapper exception to carry context:**

```python
class PipelineExecutionError(Exception):
    """Exception with pipeline execution context."""
    
    def __init__(
        self,
        message: str,
        stage_name: str,
        function_name: str,
        input_params: dict,
        original_exception: Exception,
    ):
        self.message = message
        self.stage_name = stage_name
        self.function_name = function_name
        self.input_params = input_params
        self.original_exception = original_exception
        super().__init__(message)
```

### 2.2 Context Variable for Error Tracking (src/factchecker/logging_config.py)
**Add new context variable:**

```python
error_context_var = ContextVar('error_context', default=None)
```

**Purpose:** Store current error context during execution for retrieval at top level

---

## 3. **Pipeline Implementation Changes**

### 3.1 Enhanced log_stage Decorator (src/factchecker/logging_config.py)
**Modify to capture and wrap exceptions with context.**

### 3.2 New Helper Function: _extract_params (src/factchecker/logging_config.py)
**Sanitize and extract input parameters:**
- Skip 'self' parameter for methods
- Sanitize bytes to avoid logging sensitive data
- Mask image_data, passwords, tokens, etc.

### 3.3 Enhanced check_claim Method (src/factchecker/pipeline/factcheck_pipeline.py)
**Modify exception handling to return error responses instead of raising.**

### 3.4 Updated _generate_error_response Method (src/factchecker/pipeline/factcheck_pipeline.py)
**Create ErrorDetails object and populate error response with rich context.**

### 3.5 Traceback Extraction Helper (src/factchecker/pipeline/factcheck_pipeline.py)
**New method to create debugging-friendly traceback summary.**

---

## 4. **Test Changes**

### 4.1 test_error_propagation_through_pipeline
- Remove `pytest.raises(Exception)`
- Assert error response structure
- Verify error_details are captured with stage name, function name, error type

### 4.2 test_full_pipeline_response_structure_validation
- Update type expectations to allow None for optional fields
- Add error_details to type checks

### 4.3 test_pipeline_response_has_all_required_fields
- Update field validation logic to allow None for optional fields

### 4.4 NEW test_error_details_capture_cache_error
- Test cache stage error context capture

### 4.5 NEW test_error_details_capture_extraction_error
- Test extraction stage error context capture

### 4.6 NEW test_error_response_includes_debugging_info
- Comprehensive test for all debugging information fields

### 4.7 NEW test_error_parameters_sanitization
- Verify sensitive data is not leaked in error parameters

---

## 5. **Logging Configuration Changes**

### 5.1 Enhanced log_stage decorator
- Add exception wrapping logic
- Add parameter extraction and sanitization
- Store error context in context variable

### 5.2 New helper functions
- `_extract_params()` - Extract and sanitize parameters
- `_sanitize_value()` - Remove sensitive data
- `_is_sensitive()` - Detect sensitive field names

### 5.3 New context variable
```python
error_context_var = ContextVar('error_context', default=None)
```

---

## 6. **Implementation Sequence**

1. Update models.py: Add ErrorDetails, update VerdictEnum, update FactCheckResponse
2. Update logging_config.py: Add context variable, helper functions, enhance decorator
3. Update pipeline.py: Add PipelineExecutionError, enhance check_claim, add _generate_error_response
4. Update test_pipeline.py: Update existing tests, add new error handling tests

---

## 7. **Files to Modify**

- `src/factchecker/core/models.py`
- `src/factchecker/logging_config.py`
- `src/factchecker/pipeline/factcheck_pipeline.py`
- `src/factchecker/tests/test_pipeline.py`

---

## 8. **Backward Compatibility Notes**

- **Breaking changes:** 
  - `evidence`, `references`, `search_queries_used` now Optional
  - New VerdictEnum.ERROR value
  - FactCheckResponse now has `error_details` field

- **Callers must:**
  - Handle Optional fields with null checks
  - Handle VerdictEnum.ERROR verdict
  - Use `response.error_details` when verdict is ERROR

- **Debugging benefits:**
  - Full error context in response (no need to check logs separately)
  - Input parameters included for root cause analysis
  - Traceback summary for stack trace context
  - Stage and function names for precise fault localization

---

Generated: December 2, 2025
Status: Ready for Implementation
