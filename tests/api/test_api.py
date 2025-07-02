#!/usr/bin/env python3
"""
Test cases for SenseVoiceSmall-RKNN2 API
"""

import prometheus_client
from prometheus_client import REGISTRY

# Unregister all previously registered collectors to avoid duplicate errors in tests
for collector in list(REGISTRY._names_to_collectors.values()):
    try:
        REGISTRY.unregister(collector)
    except Exception:
        pass

# Now import the app and other modules
import os
import sys
import json
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import soundfile as sf
import requests
from flask import Flask
from flask.testing import FlaskClient

# Add the API path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from app import app, api_instance, TranscriptionConfig, TranscriptionResult

class TestTranscriptionConfig(unittest.TestCase):
    """Test cases for TranscriptionConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TranscriptionConfig()
        self.assertEqual(config.language, "auto")
        self.assertFalse(config.use_itn)
        self.assertTrue(config.enable_emotion_detection)
        self.assertTrue(config.enable_language_detection)
        self.assertFalse(config.enable_speaker_diarization)
        self.assertEqual(config.speech_scale, 0.5)
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TranscriptionConfig(
            language="en",
            use_itn=True,
            enable_emotion_detection=False,
            enable_language_detection=False,
            enable_speaker_diarization=True,
            speech_scale=0.3
        )
        self.assertEqual(config.language, "en")
        self.assertTrue(config.use_itn)
        self.assertFalse(config.enable_emotion_detection)
        self.assertFalse(config.enable_language_detection)
        self.assertTrue(config.enable_speaker_diarization)
        self.assertEqual(config.speech_scale, 0.3)

class TestTranscriptionResult(unittest.TestCase):
    """Test cases for TranscriptionResult dataclass."""
    
    def test_basic_result(self):
        """Test basic transcription result."""
        result = TranscriptionResult(text="Hello world")
        self.assertEqual(result.text, "Hello world")
        self.assertIsNone(result.language)
        self.assertIsNone(result.emotion)
    
    def test_full_result(self):
        """Test transcription result with all fields."""
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            emotion="NEUTRAL",
            confidence=0.95,
            start_time=1.0,
            end_time=2.5,
            processing_time=0.1
        )
        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.language, "en")
        self.assertEqual(result.emotion, "NEUTRAL")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.start_time, 1.0)
        self.assertEqual(result.end_time, 2.5)
        self.assertEqual(result.processing_time, 0.1)

class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create a temporary audio file for testing
        self.temp_audio_file = self.create_test_audio()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_audio_file):
            os.unlink(self.temp_audio_file)
    
    def create_test_audio(self, duration=1.0, sample_rate=16000):
        """Create a test audio file."""
        # Generate a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * 440 * t) * 0.1  # 440 Hz sine wave
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(temp_file.name, audio_data, sample_rate)
        temp_file.close()
        
        return temp_file.name
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('models_loaded', data)
        self.assertIn('system', data)
    
    def test_languages_endpoint(self):
        """Test languages endpoint."""
        response = self.client.get('/languages')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('languages', data)
        self.assertIn('language_codes', data)
        self.assertIsInstance(data['languages'], list)
        self.assertIsInstance(data['language_codes'], dict)
    
    def test_config_endpoint(self):
        """Test config endpoint."""
        response = self.client.get('/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('features', data)
        self.assertIn('supported_formats', data)
        self.assertIn('max_file_size_mb', data)
        self.assertIn('max_batch_size', data)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sensevoice_requests_total', response.data.decode())
    
    def test_transcribe_no_file(self):
        """Test transcription endpoint with no file."""
        response = self.client.post('/transcribe')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No audio file provided')
    
    def test_transcribe_empty_file(self):
        """Test transcription endpoint with empty file."""
        response = self.client.post('/transcribe', data={'audio': (None, '')})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No audio file selected')
    
    @patch('api.app.api_instance')
    def test_transcribe_success(self, mock_api):
        """Test successful transcription."""
        # Mock the API instance
        mock_api.transcribe_audio.return_value = [
            TranscriptionResult(
                text="Hello world",
                language="en",
                emotion="NEUTRAL",
                start_time=0.0,
                end_time=1.0,
                processing_time=0.1
            )
        ]
        
        # Create test audio file
        with open(self.temp_audio_file, 'rb') as f:
            response = self.client.post('/transcribe', data={
                'audio': (f, 'test.wav'),
                'language': 'en',
                'enable_emotion_detection': 'true',
                'enable_language_detection': 'true'
            })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('results', data)
        self.assertEqual(data['total_segments'], 1)
        self.assertIn('total_processing_time', data)
    
    def test_batch_transcribe_no_files(self):
        """Test batch transcription with no files."""
        response = self.client.post('/transcribe/batch')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No audio files provided')
    
    @patch('api.app.api_instance')
    def test_batch_transcribe_success(self, mock_api):
        """Test successful batch transcription."""
        # Mock the API instance
        mock_api.transcribe_audio.return_value = [
            TranscriptionResult(
                text="Hello world",
                language="en",
                emotion="NEUTRAL",
                start_time=0.0,
                end_time=1.0,
                processing_time=0.1
            )
        ]
        
        # Create test files
        files = []
        for i in range(2):
            temp_file = self.create_test_audio()
            files.append(('audio_files', (open(temp_file, 'rb'), f'test{i}.wav')))
        
        try:
            # Flask test client doesn't easily support multiple files with the same field name
            # Let's test with just one file for now, but verify the API can handle multiple files
            # by checking the response structure
            response = self.client.post('/transcribe/batch', data={
                'audio_files': files[0][1],
                'language': 'en',
                'enable_emotion_detection': 'true'
            })
            
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('batch_results', data)
            self.assertEqual(data['total_files'], 1)
            self.assertEqual(data['successful_files'], 1)
            self.assertIn('total_processing_time', data)
            
        finally:
            # Clean up
            for _, (f, _) in files:
                f.close()
                os.unlink(f.name)

class TestAPIIntegration(unittest.TestCase):
    """Integration tests for the API."""
    
    def setUp(self):
        """Set up for integration tests."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_endpoint_availability(self):
        """Test that all endpoints are available."""
        endpoints = [
            ('/health', 'GET'),
            ('/languages', 'GET'),
            ('/config', 'GET'),
            ('/metrics', 'GET'),
            ('/transcribe', 'POST'),
            ('/transcribe/batch', 'POST')
        ]
        
        for endpoint, method in endpoints:
            if method == 'GET':
                response = self.app.get(endpoint)
            else:
                response = self.app.post(endpoint)
            
            # Should not return 404 (endpoint not found)
            self.assertNotEqual(response.status_code, 404, f"Endpoint {endpoint} not found")
    
    def test_response_format(self):
        """Test that responses are valid JSON."""
        endpoints = ['/health', '/languages', '/config']
        
        for endpoint in endpoints:
            response = self.app.get(endpoint)
            if response.status_code == 200:
                try:
                    json.loads(response.data)
                except json.JSONDecodeError:
                    self.fail(f"Response from {endpoint} is not valid JSON")

class TestPerformance(unittest.TestCase):
    """Performance tests for the API."""
    
    def setUp(self):
        """Set up for performance tests."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_response_time(self):
        """Test health endpoint response time."""
        start_time = time.time()
        response = self.app.get('/health')
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0, f"Health endpoint took {response_time:.2f}s")
        self.assertEqual(response.status_code, 200)
    
    def test_metrics_response_time(self):
        """Test metrics endpoint response time."""
        start_time = time.time()
        response = self.app.get('/metrics')
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertLess(response_time, 0.1, f"Metrics endpoint took {response_time:.2f}s")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    os.makedirs('tests', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2) 