# Dockerfile for SenseVoiceSmall-RKNN2
# Speech-to-text model with RKNN2 acceleration

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        wget \
        curl \
        sudo \
        git \
        build-essential \
        ffmpeg \
        libasound2-dev \
        libsndfile1 \
        libdrm2 \
        libdrm-dev \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

# Install RKNPU driver and runtime libraries
RUN cd /tmp \
    && git clone https://github.com/rockchip-linux/rknpu.git \
    && cd rknpu \
    && mkdir -p /usr/lib \
    && cp -r drivers/linux-aarch64/usr/lib/* /usr/lib/ \
    && cp -r rknn/rknn_api/librknn_api/lib/* /usr/lib/ \
    && cp -r rknn/rknn_utils/librknn_utils/lib/* /usr/lib/ \
    && cp -r runtime/Linux/librknn_api/aarch64/* /usr/lib/ || true \
    && ldconfig \
    && cd .. \
    && rm -rf rknpu

WORKDIR /opt/sensevoice

# Copy application files from submodule
COPY submodules/SenseVoiceSmall-RKNN2/*.py /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.onnx /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.rknn /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.model /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.npy /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.mvn /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.yaml /opt/sensevoice/
COPY submodules/SenseVoiceSmall-RKNN2/*.wav /opt/sensevoice/

# Copy API files from main repo
COPY api/ /opt/sensevoice/api/

# Copy requirements.txt from main repo
COPY requirements.txt /opt/sensevoice/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for audio input
RUN mkdir -p /opt/sensevoice/audio

# Set permissions
RUN chmod +x /opt/sensevoice/*.py

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Default command - can be overridden
CMD ["python3", "./sensevoice_rknn.py", "--audio_file", "output.wav"] 