# Test Suite for SenseVoiceSmall-RKNN2-API

This directory contains the comprehensive test suite for the SenseVoiceSmall-RKNN2-API project.

## 📁 Test Organization

```
tests/
├── unit/           # Unit tests for individual components
├── api/            # API endpoint tests
├── integration/    # Integration tests (end-to-end)
├── performance/    # Performance and load tests
├── run_all_tests.py # Main test runner
└── README.md       # This file
```

## 🧪 Test Categories

### Unit Tests (`unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Docker configuration, file structure, dependencies
- **Files**: `test_docker.py`
- **Dependencies**: None (no Docker required)

### API Tests (`api/`)
- **Purpose**: Test API endpoints and functionality
- **Scope**: Individual endpoint testing, request/response validation
- **Files**: `test_api.py`
- **Dependencies**: Running API server

### Integration Tests (`integration/`)
- **Purpose**: End-to-end testing of the complete system
- **Scope**: Full workflow testing, Docker container integration
- **Files**: `test_integration.py`
- **Dependencies**: Docker container running

### Performance Tests (`performance/`)
- **Purpose**: Performance benchmarking and load testing
- **Scope**: Response times, throughput, concurrent requests
- **Files**: Currently part of integration tests
- **Dependencies**: Running API server

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
python3 tests/run_all_tests.py

# Run specific test categories
python3 tests/run_all_tests.py --unit
python3 tests/run_all_tests.py --api
python3 tests/run_all_tests.py --integration
python3 tests/run_all_tests.py --performance
python3 tests/run_all_tests.py --bash
```

### Individual Test Files
```bash
# Unit tests
python3 -m unittest discover tests/unit

# API tests
python3 -m unittest discover tests/api

# Integration tests
python3 tests/integration/test_integration.py

# Bash integration tests
./test_integration.sh
```

### CI/CD Integration
```bash
# GitHub Actions automatically runs integration tests
# See .github/workflows/integration-tests.yml
```

## 📊 Test Coverage

### Unit Tests
- ✅ Dockerfile validation
- ✅ Docker Compose configuration
- ✅ Submodule functionality
- ✅ Requirements validation
- ✅ File structure verification

### API Tests
- ✅ Health endpoint (`/health`)
- ✅ Configuration endpoint (`/config`)
- ✅ Languages endpoint (`/languages`)
- ✅ Transcription endpoint (`/transcribe`)
- ✅ Batch transcription (`/transcribe/batch`)
- ✅ Metrics endpoint (`/metrics`)
- ✅ Error handling
- ✅ Request validation

### Integration Tests
- ✅ Docker container startup/shutdown
- ✅ API server initialization
- ✅ Model loading verification
- ✅ End-to-end transcription workflow
- ✅ Batch processing
- ✅ Performance metrics collection
- ✅ Concurrent request handling
- ✅ Error recovery

### Performance Tests
- ✅ Response time measurement
- ✅ Throughput testing
- ✅ Concurrent request handling
- ✅ Memory usage monitoring
- ✅ CPU utilization tracking

## 🔧 Test Configuration

### Environment Variables
```bash
# API configuration
export API_BASE_URL="http://localhost:8081"
export API_TIMEOUT="30"

# Test flags
export TEST_DOCKER_API="1"
export TEST_DOCKER_BUILD="1"
export TEST_DOCKER_COMPOSE="1"
```

### Test Data
- **Audio files**: Located in `audio/` directory
- **Test files**: `test.wav`, `127389__acclivity__thetimehascome.wav`
- **Expected results**: Validated against known transcription outputs

## 📈 Test Results

### Success Criteria
- **Unit Tests**: 100% pass rate
- **API Tests**: 100% pass rate (excluding known issues)
- **Integration Tests**: 100% pass rate
- **Performance Tests**: Meet performance benchmarks

### Known Issues
- **Metrics Test**: May fail due to multiple API instances during testing
  - **Status**: Documented in GitHub issue
  - **Impact**: Non-critical (test infrastructure issue)
  - **Workaround**: Run tests individually

### Performance Benchmarks
- **Response Time**: < 3 seconds for transcription
- **Throughput**: > 10 requests/minute
- **Memory Usage**: < 2GB for API server
- **CPU Usage**: < 50% during normal operation

## 🛠️ Adding New Tests

### Unit Tests
```python
# tests/unit/test_new_component.py
import unittest

class TestNewComponent(unittest.TestCase):
    def test_specific_functionality(self):
        # Test implementation
        self.assertTrue(True)
```

### API Tests
```python
# tests/api/test_new_endpoint.py
import unittest
import requests

class TestNewEndpoint(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8081"
    
    def test_new_endpoint(self):
        response = requests.get(f"{self.base_url}/new-endpoint")
        self.assertEqual(response.status_code, 200)
```

### Integration Tests
```python
# tests/integration/test_new_workflow.py
# Add to existing test_integration.py or create new file
```

## 🔍 Debugging Tests

### Common Issues
1. **Docker not running**: Start Docker service
2. **API not ready**: Wait for container startup (30-60 seconds)
3. **Audio files missing**: Ensure test audio files exist
4. **Port conflicts**: Check if port 8081 is available

### Debug Commands
```bash
# Check Docker status
docker compose ps

# View container logs
docker compose logs sensevoice

# Test API manually
curl http://localhost:8081/health

# Run tests with verbose output
python3 tests/run_all_tests.py --integration -v
```

## 📝 Test Documentation

For detailed testing documentation, see:
- [Testing Guide](../wiki/testing.md)
- [API Reference](../wiki/api-reference.md)
- [Development Guide](../wiki/Development-Guide.md)

## 🤝 Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate docstrings
3. Include error handling
4. Update this README if needed
5. Ensure tests pass before submitting PR

## 📞 Support

For test-related issues:
1. Check the troubleshooting guide
2. Review known issues above
3. Create a GitHub issue with test output
4. Include environment details and error messages 