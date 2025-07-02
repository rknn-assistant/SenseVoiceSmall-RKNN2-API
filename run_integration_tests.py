#!/usr/bin/env python3
"""
Integration test runner for SenseVoiceSmall-RKNN2-API
Automates the complete integration testing process.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_docker_running():
    """Check if Docker container is running."""
    try:
        result = subprocess.run(['docker', 'compose', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        return 'sensevoice-rknn2' in result.stdout and 'Up' in result.stdout
    except Exception:
        return False

def start_docker_container():
    """Start the Docker container if not running."""
    print("🐳 Starting Docker container...")
    try:
        subprocess.run(['docker', 'compose', 'up', '-d'], 
                      check=True, timeout=60)
        print("✅ Docker container started")
        return True
    except subprocess.TimeoutExpired:
        print("❌ Docker container startup timed out")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker container: {e}")
        return False

def wait_for_api_ready(max_wait=60):
    """Wait for API to be ready."""
    import requests
    
    print("⏳ Waiting for API to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get('http://localhost:8081/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    print("✅ API is ready!")
                    return True
        except Exception:
            pass
        
        time.sleep(2)
    
    print("❌ API failed to become ready within timeout")
    return False

def run_integration_tests():
    """Run the integration tests."""
    print("🧪 Running integration tests...")
    
    # Add tests directory to Python path
    tests_dir = Path(__file__).parent / "tests"
    sys.path.insert(0, str(tests_dir))
    
    # Import and run integration tests
    from test_integration import run_integration_tests as run_tests
    run_tests()

def main():
    """Main function to orchestrate the integration testing."""
    print("🚀 SenseVoiceSmall-RKNN2-API Integration Test Runner")
    print("=" * 60)
    
    # Check if Docker is running
    if not check_docker_running():
        print("🐳 Docker container not running, starting...")
        if not start_docker_container():
            print("❌ Failed to start Docker container")
            sys.exit(1)
    
    # Wait for API to be ready
    if not wait_for_api_ready():
        print("❌ API failed to become ready")
        sys.exit(1)
    
    # Run integration tests
    try:
        run_integration_tests()
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 