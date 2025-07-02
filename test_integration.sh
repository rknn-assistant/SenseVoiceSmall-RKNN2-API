#!/bin/bash

# Integration test script for SenseVoiceSmall-RKNN2-API
# This script automates the testing process

set -e

echo "🚀 SenseVoiceSmall-RKNN2-API Integration Test Runner"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    print_status "Docker is running"
}

# Check if container is running
check_container() {
    if docker compose ps | grep -q "sensevoice-rknn2.*Up"; then
        print_status "Container is already running"
        return 0
    else
        print_warning "Container is not running, starting..."
        return 1
    fi
}

# Start container
start_container() {
    print_status "Starting Docker container..."
    docker compose up -d
    sleep 10
}

# Wait for API to be ready
wait_for_api() {
    print_status "Waiting for API to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8081/health > /dev/null 2>&1; then
            local status=$(curl -s http://localhost:8081/health | jq -r '.status' 2>/dev/null || echo "unknown")
            if [ "$status" = "healthy" ]; then
                print_status "API is ready!"
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "API failed to become ready within timeout"
    return 1
}

# Test health endpoint
test_health() {
    print_status "Testing health endpoint..."
    local response=$(curl -s http://localhost:8081/health)
    local status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" = "healthy" ]; then
        print_status "Health check passed"
        echo "$response" | jq '.'
    else
        print_error "Health check failed"
        echo "$response"
        return 1
    fi
}

# Test config endpoint
test_config() {
    print_status "Testing config endpoint..."
    local response=$(curl -s http://localhost:8081/config)
    
    if echo "$response" | jq -e '.features' > /dev/null; then
        print_status "Config endpoint passed"
        echo "$response" | jq '.'
    else
        print_error "Config endpoint failed"
        echo "$response"
        return 1
    fi
}

# Test languages endpoint
test_languages() {
    print_status "Testing languages endpoint..."
    local response=$(curl -s http://localhost:8081/languages)
    
    if echo "$response" | jq -e '.languages' > /dev/null; then
        print_status "Languages endpoint passed"
        echo "$response" | jq '.'
    else
        print_error "Languages endpoint failed"
        echo "$response"
        return 1
    fi
}

# Test transcription endpoint
test_transcription() {
    print_status "Testing transcription endpoint..."
    
    if [ ! -f "audio/test.wav" ]; then
        print_error "Test audio file not found: audio/test.wav"
        return 1
    fi
    
    local response=$(curl -s -X POST -F 'audio=@audio/test.wav' http://localhost:8081/transcribe)
    local success=$(echo "$response" | jq -r '.success')
    
    if [ "$success" = "true" ]; then
        print_status "Transcription endpoint passed"
        local segments=$(echo "$response" | jq -r '.total_segments')
        local time=$(echo "$response" | jq -r '.total_processing_time')
        echo "Processed $segments segments in ${time}s"
    else
        print_error "Transcription endpoint failed"
        echo "$response"
        return 1
    fi
}

# Test batch transcription
test_batch_transcription() {
    print_status "Testing batch transcription endpoint..."
    
    if [ ! -f "audio/test.wav" ] || [ ! -f "audio/127389__acclivity__thetimehascome.wav" ]; then
        print_error "Test audio files not found"
        return 1
    fi
    
    local response=$(curl -s -X POST \
        -F 'audio_files=@audio/test.wav' \
        -F 'audio_files=@audio/127389__acclivity__thetimehascome.wav' \
        http://localhost:8081/transcribe/batch)
    
    local success=$(echo "$response" | jq -r '.success')
    local total_files=$(echo "$response" | jq -r '.total_files')
    local successful_files=$(echo "$response" | jq -r '.successful_files')
    
    if [ "$success" = "true" ]; then
        print_status "Batch transcription endpoint passed"
        echo "Processed $successful_files/$total_files files successfully"
    else
        print_error "Batch transcription endpoint failed"
        echo "$response"
        return 1
    fi
}

# Test metrics endpoint
test_metrics() {
    print_status "Testing metrics endpoint..."
    local response=$(curl -s http://localhost:8081/metrics)
    
    if echo "$response" | grep -q "sensevoice_requests_total"; then
        print_status "Metrics endpoint passed"
        echo "Metrics collected successfully"
    else
        print_error "Metrics endpoint failed"
        return 1
    fi
}

# Run performance tests
test_performance() {
    print_status "Running performance tests..."
    
    # Make multiple requests to test performance
    for i in {1..3}; do
        echo "  Request $i..."
        curl -s -X POST -F 'audio=@audio/test.wav' http://localhost:8081/transcribe > /dev/null
    done
    
    # Check final metrics
    local metrics=$(curl -s http://localhost:8081/metrics)
    local request_count=$(echo "$metrics" | grep "sensevoice_requests_total" | grep -v "#" | wc -l)
    
    print_status "Performance tests completed"
    echo "Total requests tracked: $request_count"
}

# Main test execution
main() {
    local failed_tests=0
    
    # Check prerequisites
    check_docker
    
    # Start container if needed
    if ! check_container; then
        start_container
    fi
    
    # Wait for API
    if ! wait_for_api; then
        exit 1
    fi
    
    # Run tests
    echo ""
    echo "🧪 Running Integration Tests..."
    echo "================================"
    
    # Test 1: Health
    if ! test_health; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 2: Config
    if ! test_config; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 3: Languages
    if ! test_languages; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 4: Transcription
    if ! test_transcription; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 5: Batch Transcription
    if ! test_batch_transcription; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 6: Metrics
    if ! test_metrics; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 7: Performance
    if ! test_performance; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Summary
    echo ""
    echo "📊 Test Summary"
    echo "==============="
    
    if [ $failed_tests -eq 0 ]; then
        print_status "All tests passed! 🎉"
        exit 0
    else
        print_error "$failed_tests test(s) failed"
        exit 1
    fi
}

# Run main function
main "$@" 