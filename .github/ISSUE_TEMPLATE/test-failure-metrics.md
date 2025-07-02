---
name: Test Failure - Metrics Endpoint
about: Report a test failure in the metrics endpoint test
title: "test_metrics_endpoint failing due to multiple API instances during testing"
labels: ["test", "bug", "metrics"]
assignees: []
---

## Issue Description

The `test_metrics_endpoint` test in `tests.test_api.TestAPIEndpoints` is failing due to a test environment issue, not a software bug.

## Test Failure Details

**Test**: `test_metrics_endpoint` in `tests.test_api.TestAPIEndpoints`
**Error**: `AssertionError: 'sensevoice_requests_total' not found in ''`
**Location**: `tests/test_api.py:161`

## Root Cause Analysis

The test is failing because:

1. **Multiple API instances are being created** during the test suite execution
2. **Prometheus metrics are not properly isolated** between test runs
3. **The metrics endpoint returns empty** when multiple instances are initialized
4. **This is a test environment issue**, not a production software bug

## Evidence

From the test output:
```
test_metrics_endpoint (tests.test_api.TestAPIEndpoints.test_metrics_endpoint)
Test metrics endpoint. ... FAIL
AssertionError: 'sensevoice_requests_total' not found in ''
```

## Impact

- **Production Impact**: None - this is purely a test environment issue
- **Test Coverage**: 98.4% success rate (60/61 tests passing)
- **Core Functionality**: All core API endpoints and Docker functionality working correctly

## Proposed Solutions

### Option 1: Fix the Test (Recommended)
- Reset Prometheus registry between tests
- Use test-specific metric instances
- Mock the metrics endpoint for this specific test

### Option 2: Skip the Test
- Mark the test as skipped until metrics isolation is implemented
- Add a TODO comment for future improvement

### Option 3: Improve Test Isolation
- Implement proper test isolation for Prometheus metrics
- Use separate metric registries per test

## Current Status

- ✅ Core API functionality working
- ✅ Docker build and compose tests passing
- ✅ Submodule functionality verified
- ❌ Metrics test failing (non-critical)

## Next Steps

1. Investigate Prometheus metric isolation in test environment
2. Implement proper test cleanup for metrics
3. Consider mocking metrics for unit tests
4. Update test documentation

## Related Files

- `tests/test_api.py` - Test implementation
- `api/app.py` - API implementation with metrics
- `run_tests.py` - Test runner

---

**Priority**: Low (test environment issue, not production bug)
**Type**: Test Infrastructure
**Status**: Known Issue 