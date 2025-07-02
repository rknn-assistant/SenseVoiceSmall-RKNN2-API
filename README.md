# SenseVoiceSmall-RKNN2 Docker API

Docker containerization of the SenseVoiceSmall-RKNN2 model for speech-to-text processing with RKNN2 acceleration.

## Overview

SenseVoice is an audio foundation model with multi-modal capabilities including:
- **Speech Recognition (ASR)** - Multi-language support (Chinese, Cantonese, English, Japanese, Korean)
- **Language Identification (LID)** - Automatic language detection
- **Speech Emotion Recognition (SER)** - Emotion detection in speech
- **Acoustic Event Classification (AEC)** - Sound event detection

### Performance
- **Inference Speed**: ~20x real-time on RK3588 single NPU core (processes 20 seconds of audio per second)
- **Memory Usage**: ~1.1GB
- **Latency**: Extremely low inference delay

## Documentation

This project includes comprehensive documentation available in the [wiki submodule](./wiki/). The wiki contains detailed guides covering:

- **📖 [Quick Start Guide](./wiki/Quick-Start-Guide.md)** - Get up and running in minutes
- **🏗️ [Architecture Guide](./wiki/Architecture.md)** - System design and technical details
- **📋 [API Reference](./wiki/api-reference.md)** - Complete API documentation with examples
- **🔧 [Installation Guide](./wiki/Installation-Guide.md)** - Detailed setup instructions
- **🐳 [Docker Setup](./wiki/Docker-Setup.md)** - Container deployment guide
- **📊 [Monitoring Guide](./wiki/Monitoring.md)** - Metrics and observability
- **🚀 [Deployment Guide](./wiki/Deployment.md)** - Production deployment
- **🔒 [Security Guide](./wiki/Security-Guide.md)** - Security best practices
- **🧪 [Testing Guide](./wiki/testing.md)** - Testing strategies and examples
- **🛠️ [Development Guide](./wiki/Development-Guide.md)** - Contributing and development
- **❓ [Troubleshooting](./wiki/Troubleshooting.md)** - Common issues and solutions

### Accessing the Wiki
The wiki is included as a git submodule. To access it:

```bash
# Clone with submodules (recommended)
git clone --recursive <repository-url>
cd SenseVoiceSmall-RKNN2-API

# Or initialize submodules if already cloned
git submodule update --init --recursive

# View wiki documentation
ls wiki/
```

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- RKNN2-compatible hardware (RK3588, etc.)
- Audio files in WAV format (16kHz, 16-bit, mono preferred)

### 1. Clone Repository with Submodules
```bash
# Clone the repository with submodules
git clone --recursive <repository-url>
cd SenseVoiceSmall-RKNN2-API

# Or if you already cloned without submodules
git submodule update --init --recursive
```

### 2. Build and Run with Docker Compose
```bash
# Build the Docker image
docker compose build

# Run the service
docker compose up -d

# Check logs
docker compose logs -f sensevoice
```

### 3. Test with Sample Audio
```bash
# Place your audio file in the audio directory
cp your_audio.wav audio/input.wav

# Or use the provided test file
ffmpeg -i audio/127389__acclivity__thetimehascome.wav -f wav -acodec pcm_s16le -ac 1 -ar 16000 audio/test.wav

# Run transcription
docker compose exec sensevoice python3 ./sensevoice_rknn.py --audio_file /opt/sensevoice/audio/test.wav
```

## Manual Installation (Bare Metal)

### System Requirements
- Linux ARM64 (tested on RK3588)
- Python 3.8+
- RKNN2 drivers installed

### Installation Steps

1. **Clone the repository with submodules**
   ```bash
   git clone --recursive <repository-url>
   cd SenseVoiceSmall-RKNN2-API
   ```

2. **Install system dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libgomp1 wget curl git build-essential ffmpeg libasound2-dev libsndfile1
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test the installation**
   ```bash
   # Download test audio
   wget https://github.com/voxserv/audio_quality_testing_samples/raw/master/mono_44100/127389__acclivity__thetimehascome.wav
   
   # Convert to required format
   ffmpeg -i 127389__acclivity__thetimehascome.wav -f wav -acodec pcm_s16le -ac 1 -ar 16000 test.wav
   
   # Run transcription
   python3 ./submodules/SenseVoiceSmall-RKNN2/sensevoice_rknn.py --audio_file test.wav
   ```

## Docker Usage

### Building the Image
```bash
docker build -t sensevoice-rknn2 .
```

### Running the Container
```bash
# Basic usage
docker run --privileged --device=/dev/dri:/dev/dri \
  -v $(pwd)/audio:/opt/sensevoice/audio \
  sensevoice-rknn2 python3 ./sensevoice_rknn.py --audio_file /opt/sensevoice/audio/input.wav

# With custom environment variables
docker run --privileged --device=/dev/dri:/dev/dri \
  -e SPEECH_SCALE=0.3 \
  -v $(pwd)/audio:/opt/sensevoice/audio \
  sensevoice-rknn2 python3 ./sensevoice_rknn.py --audio_file /opt/sensevoice/audio/input.wav
```

## Configuration

### Environment Variables
- `SPEECH_SCALE`: Input data scaling ratio (default: 0.5, set lower if getting inf values)
- `PYTHONUNBUFFERED`: Set to 1 for immediate output

### Audio Format Requirements
For optimal performance, audio files should be:
- **Format**: WAV
- **Sample Rate**: 16kHz
- **Bit Depth**: 16-bit
- **Channels**: Mono (1 channel)

### Format Conversion
```bash
# Convert any audio file to required format
ffmpeg -i input_audio.mp3 -f wav -acodec pcm_s16le -ac 1 -ar 16000 output.wav
```

## API Usage

The application can be extended to provide REST API endpoints. See the `submodules/SenseVoiceSmall-RKNN2/sensevoice_rknn.py` file for implementation details.

### Command Line Options
```bash
python3 ./submodules/SenseVoiceSmall-RKNN2/sensevoice_rknn.py --audio_file path/to/audio.wav [options]
```

## Troubleshooting

### Common Issues

1. **Overflow errors (inf values)**
   - Set `SPEECH_SCALE` to a smaller value (e.g., 0.3)
   - Check audio file format and quality

2. **RKNN driver issues**
   - Ensure RKNN2 drivers are properly installed
   - Check device permissions (`/dev/dri`)
   - Run container with `--privileged` flag

3. **Audio format issues**
   - Convert audio to 16kHz, 16-bit, mono WAV format
   - Check file corruption with `ffprobe`

4. **Memory issues**
   - Ensure sufficient system memory (>2GB recommended)
   - Monitor memory usage during inference

5. **Submodule issues**
   - If you get errors about missing files, ensure submodules are initialized:
     ```bash
     git submodule update --init --recursive
     ```

### Debug Mode
```bash
# Enable verbose logging
docker compose exec sensevoice python3 ./sensevoice_rknn.py --audio_file /opt/sensevoice/audio/test.wav --verbose
```

## Development

### Project Structure
```
.
├── Dockerfile              # Main Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── audio/                  # Audio files directory
├── models/                 # Model files directory
├── scripts/                # Utility scripts
├── submodules/             # Git submodules
│   └── SenseVoiceSmall-RKNN2/  # Original SenseVoice model files
│       ├── sensevoice_rknn.py  # Main application
│       ├── convert_rknn.py     # RKNN model conversion script
│       └── ...                 # Other model files
├── wiki/                   # 📚 Documentation wiki (git submodule)
│   ├── README.md           # Wiki home page
│   ├── Quick-Start-Guide.md # Getting started guide
│   ├── Architecture.md     # System architecture
│   ├── api-reference.md    # API documentation
│   └── ...                 # Additional documentation
└── tests/                  # Test files and test data
```

### Updating Submodules
To update to the latest version of the SenseVoice model:
```bash
# Update the submodule to the latest commit
git submodule update --remote submodules/SenseVoiceSmall-RKNN2

# Commit the update
git add submodules/SenseVoiceSmall-RKNN2
git commit -m "Update SenseVoice submodule to latest version"
```

To update the documentation wiki:
```bash
# Update wiki submodule
git submodule update --remote wiki

# Commit the wiki update
git add wiki
git commit -m "Update documentation wiki"
```

### Building from Source
1. Download ONNX model from [lovemefan/SenseVoice-onnx](https://huggingface.co/lovemefan/SenseVoice-onnx)
2. Convert to RKNN format using `submodules/SenseVoiceSmall-RKNN2/convert_rknn.py`
3. Test with sample audio

## References

- [SenseVoice Original Repository](https://github.com/FunAudioLLM/SenseVoice)
- [SenseVoice-ONNX Models](https://huggingface.co/lovemefan/SenseVoice-onnx)
- [SenseVoiceSmall-RKNN2 Model](https://huggingface.co/happyme531/SenseVoiceSmall-RKNN2)
- [RKNN2 Documentation](https://github.com/rockchip-linux/rknpu)

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- Create an issue in this repository
- Check the [comprehensive documentation in the wiki](./wiki/)
- Review the [original SenseVoice documentation](https://huggingface.co/happyme531/SenseVoiceSmall-RKNN2)
- Review RKNN2 driver documentation
