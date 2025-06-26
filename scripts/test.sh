#!/bin/bash

# Test script for SenseVoiceSmall-RKNN2 Docker setup
set -e

echo "🎤 SenseVoiceSmall-RKNN2 Docker Test Script"
echo "==========================================="

# Configuration
AUDIO_DIR="./audio"
TEST_AUDIO="test.wav"
CONTAINER_NAME="sensevoice-test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_status "Docker is installed"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_status "Docker Compose is installed"

# Check if running on ARM64
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]] && [[ "$ARCH" != "arm64" ]]; then
    print_warning "Not running on ARM64 architecture ($ARCH). RKNN2 acceleration may not work."
fi

# Create audio directory if it doesn't exist
mkdir -p "$AUDIO_DIR"
print_status "Audio directory created/verified"

# Download test audio if it doesn't exist
if [ ! -f "$AUDIO_DIR/127389__acclivity__thetimehascome.wav" ]; then
    echo "Downloading test audio file..."
    wget -O "$AUDIO_DIR/127389__acclivity__thetimehascome.wav" \
         "https://github.com/voxserv/audio_quality_testing_samples/raw/master/mono_44100/127389__acclivity__thetimehascome.wav"
    print_status "Test audio downloaded"
fi

# Convert audio to required format
if [ ! -f "$AUDIO_DIR/$TEST_AUDIO" ]; then
    echo "Converting audio to required format..."
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -i "$AUDIO_DIR/127389__acclivity__thetimehascome.wav" \
               -f wav -acodec pcm_s16le -ac 1 -ar 16000 \
               "$AUDIO_DIR/$TEST_AUDIO" -y
        print_status "Audio converted successfully"
    else
        print_error "FFmpeg not found. Please install it or manually convert the audio file."
        exit 1
    fi
fi

# Build Docker image
echo "Building Docker image..."
docker-compose build
print_status "Docker image built successfully"

# Test the container
echo "Testing the container..."
docker-compose run --rm --name "$CONTAINER_NAME" sensevoice \
    python3 ./sensevoice_rknn.py --audio_file "/opt/sensevoice/audio/$TEST_AUDIO"

if [ $? -eq 0 ]; then
    print_status "Container test completed successfully!"
else
    print_error "Container test failed!"
    exit 1
fi

# Cleanup
echo "Cleaning up test resources..."
docker-compose down
print_status "Cleanup completed"

echo ""
echo "🎉 All tests passed! Your SenseVoice Docker setup is ready to use."
echo ""
echo "Usage examples:"
echo "  docker-compose up -d                    # Start the service"
echo "  docker-compose exec sensevoice python3 ./sensevoice_rknn.py --audio_file /opt/sensevoice/audio/your_file.wav"
echo "  docker-compose logs -f                  # View logs"
echo "  docker-compose down                     # Stop the service" 