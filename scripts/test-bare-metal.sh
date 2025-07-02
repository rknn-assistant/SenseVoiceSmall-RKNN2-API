#!/bin/bash

# Test script for SenseVoiceSmall-RKNN2 on bare metal
set -e

echo "🎤 SenseVoiceSmall-RKNN2 Bare Metal Test Script"
echo "=============================================="

# Configuration
AUDIO_DIR="./audio"
TEST_AUDIO="test.wav"

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

if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi
print_status "Python3 is installed"

if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    print_error "pip is not installed"
    exit 1
fi
print_status "pip is installed"

# Check if running on ARM64
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
    print_status "Running on ARM64 architecture - RKNN2 acceleration available"
else
    print_warning "Not running on ARM64 architecture ($ARCH). RKNN2 acceleration may not work."
fi

# Check for RKNN runtime
if [ -f "/usr/lib/librknnrt.so" ]; then
    print_status "RKNN runtime library found"
else
    print_warning "RKNN runtime library not found at /usr/lib/librknnrt.so"
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

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi
print_status "Python dependencies installed"

# Test the application
echo "Testing SenseVoice..."
python3 ./sensevoice_rknn.py --audio_file "$AUDIO_DIR/$TEST_AUDIO"

if [ $? -eq 0 ]; then
    print_status "SenseVoice test completed successfully!"
else
    print_error "SenseVoice test failed!"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Ensure RKNN2 drivers are properly installed"
    echo "2. Check if you have the required hardware (RK3588, etc.)"
    echo "3. Verify the audio file format is correct"
    echo "4. Try adjusting SPEECH_SCALE environment variable"
    exit 1
fi

echo ""
echo "🎉 Bare metal test completed!"
echo ""
echo "Usage examples:"
echo "  python3 ./sensevoice_rknn.py --audio_file audio/your_file.wav"
echo "  SPEECH_SCALE=0.3 python3 ./sensevoice_rknn.py --audio_file audio/your_file.wav" 