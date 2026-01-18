# Recommendation: Dump Logged Data at End of Tests

## Current State

The test suite in `src/factchecker/tests/test_pipeline.py` captures logs using pytest's `caplog` fixture, which is already configured in `src/factchecker/tests/conftest.py` to:
- Include request_id in all log messages
- Set logging level to DEBUG
- Use a custom formatter with timestamp, level, request_id, and message

However, logs are only displayed in the test output if:
1. The test fails
2. The user explicitly requests verbose logging (`pytest -vvv --log-cli-level=DEBUG`)

## Problem

When tests pass, valuable diagnostic information (request IDs, stage transitions, performance data, error context) is discarded. This makes it difficult to:
- Debug intermittent test failures after the fact
- Understand pipeline behavior in passing tests
- Correlate log events with test outcomes

## Recommended Solution

**Use a pytest fixture that dumps `caplog` contents to a file at the end of each test, regardless of pass/fail status.**

This approach:
- ✓ Works with all test outcomes (pass, fail, skip, error)
- ✓ Maintains separation of concerns (logging config stays in conftest)
- ✓ Is easily configurable per test or globally
- ✓ Allows downstream processing of log files
- ✓ Preserves existing caplog behavior
- ✓ Integrates with CI/CD artifact collection

## Implementation Option A: Per-Test Logging (Recommended)

Add this fixture to `src/factchecker/tests/conftest.py`:

```python
import os
from pathlib import Path
from datetime import datetime

@pytest.fixture
def log_dump(caplog):
    """Dump caplog to file after test completes (pass or fail)."""
    test_name = None
    
    def _before_test(request):
        nonlocal test_name
        test_name = request.node.name
    
    request = pytest.request  # Will be set by pytest
    yield caplog
    
    # Dump logs after test completes
    if caplog.records:
        log_dir = Path(".test_logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = log_dir / f"{test_name}_{timestamp}.log"
        
        with open(log_file, "w") as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Records: {len(caplog.records)}\n")
            f.write("=" * 80 + "\n\n")
            for record in caplog.records:
                f.write(caplog.handler.format(record) + "\n")
```

**Usage in test:**
```python
@pytest.mark.asyncio
async def test_pipeline_full_flow_with_mocks(
    pipeline, mock_cache, log_dump, sample_request, sample_extracted_claim
):
    """Test complete pipeline flow with logging dump."""
    # log_dump automatically captures and writes logs
    mock_cache.get.return_value = None
    response = await pipeline.check_claim(sample_request)
    assert isinstance(response, FactCheckResponse)
    # Logs are automatically dumped to .test_logs/{test_name}_{timestamp}.log
```

## Implementation Option B: Global Auto-Dump

Add this to `src/factchecker/tests/conftest.py`:

```python
@pytest.fixture(autouse=True)
def auto_dump_logs(caplog, request):
    """Automatically dump caplog for all tests (pass or fail)."""
    yield
    
    # After test completes
    if caplog.records:
        log_dir = Path(".test_logs")
        log_dir.mkdir(exist_ok=True)
        
        # Use test name and outcome
        test_name = request.node.name
        outcome = "PASS" if request.node.outcome == "passed" else request.node.outcome.upper()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        log_file = log_dir / f"{test_name}_{outcome}_{timestamp}.log"
        
        with open(log_file, "w") as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Status: {outcome}\n")
            f.write(f"Records: {len(caplog.records)}\n")
            f.write("=" * 80 + "\n\n")
            for record in caplog.records:
                f.write(caplog.handler.format(record) + "\n")
```

**Advantages of Option B:**
- No code changes needed in test functions
- Works for all existing and new tests automatically
- Can be toggled with an environment variable

## Configuration

### Option B with Environment Variable Toggle:

```python
@pytest.fixture(autouse=True)
def auto_dump_logs(caplog, request):
    """Automatically dump caplog for all tests (pass or fail)."""
    yield
    
    # Only dump if environment variable is set
    if not os.getenv("PYTEST_DUMP_LOGS", "").lower() in ("1", "true", "yes"):
        return
    
    if caplog.records:
        # ... rest of implementation
```

**Usage:**
```bash
# Run tests with log dumping enabled
PYTEST_DUMP_LOGS=1 pytest src/factchecker/tests/test_pipeline.py -v

# Run tests without log dumping (default)
pytest src/factchecker/tests/test_pipeline.py -v
```

## Additional Enhancements

### 1. Add to .gitignore
```
.test_logs/
```

### 2. Add cleanup fixture (optional)
```python
@pytest.fixture(scope="session", autouse=True)
def cleanup_logs():
    """Clean up old log files before tests run."""
    yield
    # Optionally clean up after session


@pytest.fixture(scope="session", autouse=True)
def archive_logs():
    """Archive logs after session completes."""
    yield
    
    log_dir = Path(".test_logs")
    if log_dir.exists() and list(log_dir.glob("*.log")):
        archive_dir = Path(".test_logs_archive")
        archive_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_archive = archive_dir / f"session_{timestamp}"
        session_archive.mkdir(exist_ok=True)
        
        for log_file in log_dir.glob("*.log"):
            log_file.rename(session_archive / log_file.name)
```

## Recommendation Summary

**Implement Option B (Global Auto-Dump) with Environment Variable Toggle:**

1. **Add to `src/factchecker/tests/conftest.py`**: The auto-dump fixture
2. **Add to `.gitignore`**: Exclude `.test_logs/` directory
3. **Update pytest invocation for CI**: Set `PYTEST_DUMP_LOGS=1` when running tests
4. **No changes needed** to individual test functions

This approach:
- ✓ Captures logs for all tests automatically
- ✓ Can be toggled on/off with environment variable
- ✓ Separates logs by test name, status, and timestamp
- ✓ Maintains current caplog fixture functionality
- ✓ Works with passing and failing tests equally
- ✓ Integrates cleanly with CI/CD pipelines
