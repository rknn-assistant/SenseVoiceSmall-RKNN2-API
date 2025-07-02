#!/usr/bin/env python3
"""
SenseVoiceSmall-RKNN2 API Server
Provides REST API endpoints for speech-to-text transcription with RKNN2 acceleration.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import psutil
import prometheus_client
from api.metrics import REQUEST_COUNT, REQUEST_LATENCY, TRANSCRIPTION_DURATION, AUDIO_DURATION, ACTIVE_REQUESTS, MODEL_LOAD_TIME

# Add the submodule path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "submodules" / "SenseVoiceSmall-RKNN2"))

from sensevoice_rknn import SenseVoiceInferenceSession, WavFrontend, FSMNVad

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionConfig:
    """Configuration for transcription features."""
    language: str = "auto"
    use_itn: bool = False
    enable_emotion_detection: bool = True
    enable_language_detection: bool = True
    enable_speaker_diarization: bool = False
    speech_scale: float = 0.5

@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""
    text: str
    language: Optional[str] = None
    emotion: Optional[str] = None
    confidence: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    processing_time: Optional[float] = None

class SenseVoiceAPI:
    """Main API class for SenseVoice transcription."""
    
    def __init__(self, model_path: str = None):
        """Initialize the API with model loading."""
        self.model_path = model_path or str(Path(__file__).parent.parent / "submodules" / "SenseVoiceSmall-RKNN2")
        self.models = {}
        self.lock = threading.Lock()
        
        # Language mapping
        self.languages = {"auto": 0, "zh": 3, "en": 4, "yue": 7, "ja": 11, "ko": 12, "nospeech": 13}
        
        # Load models
        self._load_models()
        
        # Thread pool for batch processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _load_models(self):
        """Load all required models."""
        start_time = time.time()
        
        try:
            logger.info(f"Loading models from {self.model_path}")
            
            # Load frontend
            self.models['frontend'] = WavFrontend(
                os.path.join(self.model_path, "am.mvn")
            )
            
            # Load main model
            self.models['model'] = SenseVoiceInferenceSession(
                os.path.join(self.model_path, "embedding.npy"),
                os.path.join(self.model_path, "sense-voice-encoder.rknn"),
                os.path.join(self.model_path, "chn_jpn_yue_eng_ko_spectok.bpe.model"),
                device_id=-1,  # Use CPU
                intra_op_num_threads=4
            )
            
            # Load VAD model
            self.models['vad'] = FSMNVad(self.model_path)
            
            load_time = time.time() - start_time
            MODEL_LOAD_TIME.observe(load_time)
            logger.info(f"Models loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def transcribe_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int,
        config: TranscriptionConfig
    ) -> List[TranscriptionResult]:
        """Transcribe audio data with specified configuration."""
        
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        try:
            results = []
            
            # Ensure audio is mono and correct sample rate
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert to mono
            
            if sample_rate != 16000:
                logger.warning(f"Resampling from {sample_rate}Hz to 16000Hz")
                # Simple resampling - in production, use librosa or scipy
                audio_data = audio_data[::sample_rate//16000]
                sample_rate = 16000
            
            # Get VAD segments
            segments = self.models['vad'].segments_offline(audio_data)
            
            for segment in segments:
                segment_start = time.time()
                
                # Extract audio segment
                start_frame = segment[0] * 16
                end_frame = segment[1] * 16
                segment_audio = audio_data[start_frame:end_frame]
                
                # Get features
                audio_feats = self.models['frontend'].get_features(segment_audio)
                
                # Perform transcription
                asr_result = self.models['model'](
                    audio_feats[None, ...],
                    language=self.languages[config.language],
                    use_itn=config.use_itn,
                )
                
                # Parse result for additional features
                result = TranscriptionResult(
                    text=asr_result,
                    start_time=segment[0] / 1000.0,
                    end_time=segment[1] / 1000.0,
                    processing_time=time.time() - segment_start
                )
                
                # Extract language and emotion if enabled
                if config.enable_language_detection or config.enable_emotion_detection:
                    self._extract_metadata(asr_result, result, config)
                
                results.append(result)
            
            # Reset VAD for next use
            self.models['vad'].vad.all_reset_detection()
            
            total_time = time.time() - start_time
            TRANSCRIPTION_DURATION.observe(total_time)
            AUDIO_DURATION.observe(len(audio_data) / sample_rate)
            
            return results
            
        finally:
            ACTIVE_REQUESTS.dec()
    
    def _extract_metadata(self, asr_result: str, result: TranscriptionResult, config: TranscriptionConfig):
        """Extract language and emotion metadata from ASR result."""
        # Parse the result format: <|lang|><|emotion|><|type|><|text|>
        parts = asr_result.split('><')
        
        if len(parts) >= 4:
            # Extract language
            if config.enable_language_detection:
                lang_part = parts[0].replace('<|', '').replace('|>', '')
                if lang_part in ['zh', 'en', 'yue', 'ja', 'ko']:
                    result.language = lang_part
            
            # Extract emotion
            if config.enable_emotion_detection:
                emotion_part = parts[1].replace('|>', '')
                if emotion_part in ['NEUTRAL', 'SAD', 'HAPPY', 'ANGRY', 'FEAR', 'SURPRISE']:
                    result.emotion = emotion_part

# Initialize API
api_instance = SenseVoiceAPI()

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    REQUEST_COUNT.labels(endpoint='/health', method='GET').inc()
    
    try:
        # Check if models are loaded
        if not api_instance.models:
            return jsonify({'status': 'unhealthy', 'error': 'Models not loaded'}), 503
        
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return jsonify({
            'status': 'healthy',
            'models_loaded': list(api_instance.models.keys()),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3)
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Single audio transcription endpoint."""
    REQUEST_COUNT.labels(endpoint='/transcribe', method='POST').inc()
    start_time = time.time()
    
    try:
        # Check if audio file was uploaded
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Parse configuration
        config = TranscriptionConfig(
            language=request.form.get('language', 'auto'),
            use_itn=request.form.get('use_itn', 'false').lower() == 'true',
            enable_emotion_detection=request.form.get('enable_emotion_detection', 'true').lower() == 'true',
            enable_language_detection=request.form.get('enable_language_detection', 'true').lower() == 'true',
            enable_speaker_diarization=request.form.get('enable_speaker_diarization', 'false').lower() == 'true',
            speech_scale=float(request.form.get('speech_scale', 0.5))
        )
        
        # Load audio
        audio_data, sample_rate = sf.read(audio_file, dtype='float32')
        
        # Perform transcription
        results = api_instance.transcribe_audio(audio_data, sample_rate, config)
        
        # Format response
        response = {
            'success': True,
            'results': [asdict(result) for result in results],
            'total_segments': len(results),
            'total_processing_time': time.time() - start_time
        }
        
        REQUEST_LATENCY.labels(endpoint='/transcribe').observe(time.time() - start_time)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/batch', methods=['POST'])
def transcribe_batch():
    """Batch audio transcription endpoint."""
    REQUEST_COUNT.labels(endpoint='/transcribe/batch', method='POST').inc()
    start_time = time.time()
    
    try:
        # Check if audio files were uploaded
        if 'audio_files' not in request.files:
            return jsonify({'error': 'No audio files provided'}), 400
        
        audio_files = request.files.getlist('audio_files')
        if not audio_files:
            return jsonify({'error': 'No audio files selected'}), 400
        
        # Parse configuration
        config = TranscriptionConfig(
            language=request.form.get('language', 'auto'),
            use_itn=request.form.get('use_itn', 'false').lower() == 'true',
            enable_emotion_detection=request.form.get('enable_emotion_detection', 'true').lower() == 'true',
            enable_language_detection=request.form.get('enable_language_detection', 'true').lower() == 'true',
            enable_speaker_diarization=request.form.get('enable_speaker_diarization', 'false').lower() == 'true',
            speech_scale=float(request.form.get('speech_scale', 0.5))
        )
        
        # Process files in parallel
        futures = []
        for audio_file in audio_files:
            future = api_instance.executor.submit(
                api_instance.transcribe_audio,
                *sf.read(audio_file, dtype='float32'),
                config
            )
            futures.append((audio_file.filename, future))
        
        # Collect results
        batch_results = []
        for filename, future in futures:
            try:
                results = future.result(timeout=300)  # 5 minute timeout
                batch_results.append({
                    'filename': filename,
                    'success': True,
                    'results': [asdict(result) for result in results]
                })
            except Exception as e:
                batch_results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        
        response = {
            'success': True,
            'batch_results': batch_results,
            'total_files': len(audio_files),
            'successful_files': sum(1 for r in batch_results if r['success']),
            'total_processing_time': time.time() - start_time
        }
        
        REQUEST_LATENCY.labels(endpoint='/transcribe/batch').observe(time.time() - start_time)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Batch transcription failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/languages', methods=['GET'])
def get_languages():
    """Get supported languages."""
    REQUEST_COUNT.labels(endpoint='/languages', method='GET').inc()
    
    return jsonify({
        'languages': list(api_instance.languages.keys()),
        'language_codes': api_instance.languages
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration options."""
    REQUEST_COUNT.labels(endpoint='/config', method='GET').inc()
    
    return jsonify({
        'features': {
            'emotion_detection': True,
            'language_detection': True,
            'speaker_diarization': False,  # Not implemented yet
            'inverse_text_normalization': True
        },
        'supported_formats': ['wav', 'flac', 'mp3', 'ogg'],
        'max_file_size_mb': 100,
        'max_batch_size': 10
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    REQUEST_COUNT.labels(endpoint='/metrics', method='GET').inc()
    
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting SenseVoice API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 