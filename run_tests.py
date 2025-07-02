#!/usr/bin/env python3
"""
Test runner for SenseVoiceSmall-RKNN2-API
Runs all test suites and provides a comprehensive report.
"""

import os
import sys
import time
import subprocess
import unittest
from pathlib import Path
from datetime import datetime

def run_unit_tests():
    """Run unit tests."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    # Add tests directory to path
    tests_dir = Path(__file__).parent / "tests"
    sys.path.insert(0, str(tests_dir))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_docker_tests():
    """Run Docker-specific tests."""
    print("\n" + "=" * 60)
    print("RUNNING DOCKER TESTS")
    print("=" * 60)
    
    # Set environment variable to enable Docker tests
    os.environ['TEST_DOCKER_BUILD'] = '1'
    os.environ['TEST_DOCKER_COMPOSE'] = '1'
    
    # Import and run Docker tests
    import tests.test_docker
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(tests.test_docker.TestDockerBuild)
    suite.addTests(loader.loadTestsFromTestCase(tests.test_docker.TestDockerCompose))
    suite.addTests(loader.loadTestsFromTestCase(tests.test_docker.TestSubmoduleFunctionality))
    suite.addTests(loader.loadTestsFromTestCase(tests.test_docker.TestRequirements))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_api_tests():
    """Run API tests."""
    print("\n" + "=" * 60)
    print("RUNNING API TESTS")
    print("=" * 60)
    
    # Import and run API tests
    import tests.test_api
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(tests.test_api.TestTranscriptionConfig)
    suite.addTests(loader.loadTestsFromTestCase(tests.test_api.TestTranscriptionResult))
    suite.addTests(loader.loadTestsFromTestCase(tests.test_api.TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(tests.test_api.TestAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(tests.test_api.TestPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_integration_tests():
    """Run integration tests with actual API server."""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Check if API server is running
    try:
        import requests
        response = requests.get("http://localhost:8081/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running, running integration tests...")
            
            # Set environment variable to enable Docker API tests
            os.environ['TEST_DOCKER_API'] = '1'
            
            from tests.test_docker import TestDockerAPI
            
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(tests.test_docker.TestDockerAPI)
            
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            return result
        else:
            print("⚠️  API server is not responding correctly")
            return None
    except requests.exceptions.RequestException:
        print("⚠️  API server is not running, skipping integration tests")
        print("   To run integration tests, start the API server first:")
        print("   docker compose up -d")
        return None

def run_manual_tests():
    """Run manual tests that require user interaction."""
    print("\n" + "=" * 60)
    print("MANUAL TESTS")
    print("=" * 60)
    
    print("The following tests require manual verification:")
    print()
    print("1. Docker Build Test:")
    print("   docker build -t sensevoice-test .")
    print()
    print("2. Docker Compose Test:")
    print("   docker compose up -d")
    print("   curl http://localhost:8081/health")
    print("   docker compose down")
    print()
    print("3. API Functionality Test:")
    print("   curl -X POST -F 'audio=@audio/test.wav' http://localhost:8081/transcribe")
    print()
    print("4. Performance Test:")
    print("   curl http://localhost:8081/metrics")
    print()

def generate_report(results):
    """Generate a test report."""
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for name, result in results.items():
        if result:
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            total_skipped += len(result.skipped)
            
            print(f"\n{name}:")
            print(f"  Tests run: {result.testsRun}")
            print(f"  Failures: {len(result.failures)}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Skipped: {len(result.skipped)}")
            
            if result.failures:
                print("  Failures:")
                for test, traceback in result.failures:
                    print(f"    - {test}: {traceback.split('AssertionError:')[-1].strip()}")
            
            if result.errors:
                print("  Errors:")
                for test, traceback in result.errors:
                    print(f"    - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print(f"\nSUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Total failures: {total_failures}")
    print(f"  Total errors: {total_errors}")
    print(f"  Total skipped: {total_skipped}")
    print(f"  Success rate: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%" if total_tests > 0 else "N/A")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total_failures + total_errors} TESTS FAILED")

def main():
    """Main test runner."""
    print("SenseVoiceSmall-RKNN2-API Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    try:
        # Run unit tests
        results['Unit Tests'] = run_unit_tests()
        
        # Run API tests
        results['API Tests'] = run_api_tests()
        
        # Run Docker tests
        results['Docker Tests'] = run_docker_tests()
        
        # Run integration tests
        results['Integration Tests'] = run_integration_tests()
        
        # Show manual tests
        run_manual_tests()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        return 1
    
    # Generate report
    generate_report(results)
    
    # Return appropriate exit code
    total_failures = sum(len(result.failures) if result else 0 for result in results.values())
    total_errors = sum(len(result.errors) if result else 0 for result in results.values())
    
    return 0 if total_failures == 0 and total_errors == 0 else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 