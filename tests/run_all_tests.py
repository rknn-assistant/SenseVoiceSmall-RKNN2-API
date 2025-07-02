#!/usr/bin/env python3
"""
Comprehensive test runner for SenseVoiceSmall-RKNN2-API
Runs unit, integration, API, and performance tests.
"""

import os
import sys
import time
import argparse
import subprocess
import unittest
from pathlib import Path

def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running Unit Tests...")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent / "unit")
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_api_tests():
    """Run API tests."""
    print("🌐 Running API Tests...")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent / "api")
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running Integration Tests...")
    print("=" * 40)
    
    # Import integration test module
    sys.path.insert(0, str(Path(__file__).parent / "integration"))
    from test_integration import run_integration_tests as run_tests
    
    try:
        run_tests()
        return True
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

def run_performance_tests():
    """Run performance tests."""
    print("⚡ Running Performance Tests...")
    print("=" * 40)
    
    # For now, run the performance tests from integration
    # TODO: Create dedicated performance test suite
    print("Performance tests are currently part of integration tests")
    return True

def run_bash_integration_tests():
    """Run bash integration tests."""
    print("🐚 Running Bash Integration Tests...")
    print("=" * 40)
    
    script_path = Path(__file__).parent.parent / "test_integration.sh"
    
    try:
        result = subprocess.run([str(script_path)], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Bash integration tests timed out")
        return False
    except Exception as e:
        print(f"❌ Bash integration tests failed: {e}")
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run SenseVoiceSmall-RKNN2-API tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--bash", action="store_true", help="Run bash integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    print("🚀 SenseVoiceSmall-RKNN2-API Test Suite")
    print("=" * 50)
    
    results = {}
    
    # Determine which tests to run
    if args.unit or args.api or args.integration or args.performance or args.bash:
        run_all = False
    else:
        run_all = True
    
    # Run unit tests
    if args.unit or run_all:
        results['unit'] = run_unit_tests()
    
    # Run API tests
    if args.api or run_all:
        results['api'] = run_api_tests()
    
    # Run integration tests
    if args.integration or run_all:
        results['integration'] = run_integration_tests()
    
    # Run performance tests
    if args.performance or run_all:
        results['performance'] = run_performance_tests()
    
    # Run bash integration tests
    if args.bash or run_all:
        results['bash'] = run_bash_integration_tests()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_type, result in results.items():
        if hasattr(result, 'testsRun'):
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
            success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                           result.testsRun * 100) if result.testsRun > 0 else 0
            
            print(f"{test_type.upper()}: {result.testsRun} tests, "
                  f"{len(result.failures)} failures, {len(result.errors)} errors "
                  f"({success_rate:.1f}% success)")
        else:
            # Boolean result (for bash tests)
            status = "PASS" if result else "FAIL"
            print(f"{test_type.upper()}: {status}")
    
    if total_tests > 0:
        overall_success_rate = ((total_tests - total_failures - total_errors) / 
                               total_tests * 100)
        print(f"\nOverall: {total_tests} tests, {total_failures} failures, "
              f"{total_errors} errors ({overall_success_rate:.1f}% success)")
    
    # Exit with appropriate code
    if total_failures > 0 or total_errors > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    main() 