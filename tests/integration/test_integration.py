#!/usr/bin/env python3
"""
Integration tests for SenseVoiceSmall-RKNN2-API
Tests the complete API functionality including transcription, batch processing, and monitoring.
"""

import os
import sys
import time
import json
import requests
import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional

class IntegrationTestSuite(unittest.TestCase):
    """Comprehensive integration tests for the API."""
    
    def setUp(self):
        """Set up test environment."""
        self.base_url = os.environ.get('API_BASE_URL', 'http://localhost:8081')
        self.timeout = int(os.environ.get('API_TIMEOUT', '30'))
        self.test_results = []
        
        # Test audio files
        self.audio_dir = Path(__file__).parent.parent / "audio"
        self.test_audio = self.audio_dir / "test.wav"
        self.long_audio = self.audio_dir / "127389__acclivity__thetimehascome.wav"
        
        # Ensure test audio files exist
        if not self.test_audio.exists():
            self.skipTest(f"Test audio file not found: {self.test_audio}")
        if not self.long_audio.exists():
            self.skipTest(f"Long audio file not found: {self.long_audio}")
    
    def _test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Optional[Dict[str, Any]] = None, files: Any = None, 
                     expected_status: int = 200) -> Dict[str, Any]:
        """Test an API endpoint and return results."""
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(f'{self.base_url}{endpoint}', timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(f'{self.base_url}{endpoint}', 
                                       data=data, files=files, timeout=self.timeout)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == expected_status
            result = {
                'name': name,
                'status': 'PASS' if success else 'FAIL',
                'status_code': response.status_code,
                'response_time': response_time,
                'expected_status': expected_status
            }
            
            if success:
                try:
                    result['response_data'] = response.json()
                except json.JSONDecodeError:
                    result['response_data'] = response.text
            else:
                result['error'] = response.text
            
            self.test_results.append(result)
            
            if success:
                print(f'✅ {name}: {response.status_code} ({response_time:.3f}s)')
            else:
                print(f'❌ {name}: {response.status_code} - {response.text}')
            
            return result
            
        except Exception as e:
            result = {
                'name': name,
                'status': 'ERROR',
                'error': str(e)
            }
            self.test_results.append(result)
            print(f'❌ {name}: ERROR - {e}')
            return result
    
    def test_01_health_check(self):
        """Test API health endpoint."""
        result = self._test_endpoint('Health Check', 'GET', '/health')
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'healthy')
            self.assertIn('models_loaded', data)
            self.assertIn('system', data)
    
    def test_02_config_endpoint(self):
        """Test API configuration endpoint."""
        result = self._test_endpoint('Config Endpoint', 'GET', '/config')
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('features', data)
            self.assertIn('supported_formats', data)
            self.assertIn('supported_languages', data)
    
    def test_03_languages_endpoint(self):
        """Test API languages endpoint."""
        result = self.test_endpoint('Languages Endpoint', 'GET', '/languages')
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('languages', data)
            self.assertIn('language_codes', data)
            self.assertIn('auto', data['language_codes'])
    
    def test_04_single_transcription(self):
        """Test single audio transcription."""
        with open(self.test_audio, 'rb') as f:
            files = {'audio': ('test.wav', f, 'audio/wav')}
            result = self.test_endpoint('Single Transcription', 'POST', '/transcribe', files=files)
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('success', data)
            self.assertTrue(data['success'])
            self.assertIn('results', data)
            self.assertIn('total_processing_time', data)
            self.assertIn('total_segments', data)
            
            # Verify transcription results
            results = data['results']
            self.assertGreater(len(results), 0)
            
            for segment in results:
                self.assertIn('text', segment)
                self.assertIn('start_time', segment)
                self.assertIn('end_time', segment)
                self.assertIn('processing_time', segment)
    
    def test_05_batch_transcription(self):
        """Test batch audio transcription."""
        with open(self.test_audio, 'rb') as f1, open(self.long_audio, 'rb') as f2:
            files = [
                ('audio_files', ('test1.wav', f1, 'audio/wav')),
                ('audio_files', ('test2.wav', f2, 'audio/wav'))
            ]
            result = self.test_endpoint('Batch Transcription', 'POST', '/transcribe/batch', files=files)
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('success', data)
            self.assertTrue(data['success'])
            self.assertIn('batch_results', data)
            self.assertIn('total_files', data)
            self.assertIn('successful_files', data)
            self.assertIn('total_processing_time', data)
            
            # Verify batch results
            self.assertEqual(data['total_files'], 2)
            self.assertEqual(data['successful_files'], 2)
            self.assertGreater(len(data['batch_results']), 0)
    
    def test_06_metrics_endpoint(self):
        """Test metrics endpoint."""
        result = self.test_endpoint('Metrics Endpoint', 'GET', '/metrics')
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            metrics_text = result['response_data']
            self.assertIn('sensevoice_requests_total', metrics_text)
            self.assertIn('sensevoice_transcription_duration_seconds', metrics_text)
            self.assertIn('sensevoice_audio_duration_seconds', metrics_text)
    
    def test_07_transcription_with_config(self):
        """Test transcription with custom configuration."""
        with open(self.test_audio, 'rb') as f:
            files = {'audio': ('test.wav', f, 'audio/wav')}
            data = {
                'language': 'en',
                'use_itn': 'true',
                'enable_emotion_detection': 'true',
                'enable_language_detection': 'true',
                'speech_scale': '0.5'
            }
            result = self.test_endpoint('Transcription with Config', 'POST', '/transcribe', 
                                       data=data, files=files)
        
        self.assertEqual(result['status'], 'PASS')
        if result['status'] == 'PASS':
            data = result['response_data']
            self.assertIn('success', data)
            self.assertTrue(data['success'])
    
    def test_08_error_handling(self):
        """Test error handling for invalid requests."""
        # Test missing audio file
        result = self.test_endpoint('Error - No Audio', 'POST', '/transcribe', 
                                   expected_status=400)
        self.assertEqual(result['status'], 'PASS')
        
        # Test invalid endpoint
        result = self.test_endpoint('Error - Invalid Endpoint', 'GET', '/invalid', 
                                   expected_status=404)
        self.assertEqual(result['status'], 'PASS')
    
    def test_09_performance_metrics(self):
        """Test performance metrics collection."""
        # Make a few requests to generate metrics
        for i in range(3):
            with open(self.test_audio, 'rb') as f:
                files = {'audio': (f'test_{i}.wav', f, 'audio/wav')}
                self.test_endpoint(f'Performance Test {i+1}', 'POST', '/transcribe', files=files)
        
        # Check metrics
        result = self.test_endpoint('Performance Metrics', 'GET', '/metrics')
        self.assertEqual(result['status'], 'PASS')
    
    def test_10_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                with open(self.test_audio, 'rb') as f:
                    files = {'audio': ('concurrent_test.wav', f, 'audio/wav')}
                    response = requests.post(f'{self.base_url}/transcribe', 
                                           files=files, timeout=self.timeout)
                    results.append(response.status_code == 200)
            except Exception as e:
                errors.append(str(e))
        
        # Start 3 concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(results), 3)
        self.assertTrue(all(results), f"Some concurrent requests failed: {results}")
        self.assertEqual(len(errors), 0, f"Concurrent requests had errors: {errors}")
        
        print(f'✅ Concurrent Requests: All {len(results)} requests successful')
    
    def tearDown(self):
        """Generate test summary."""
        if hasattr(self, 'test_results') and self.test_results:
            passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
            total = len(self.test_results)
            success_rate = (passed / total * 100) if total > 0 else 0
            
            response_times = [r.get('response_time', 0) for r in self.test_results 
                            if 'response_time' in r]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            print(f'\n📊 Integration Test Summary:')
            print(f'Tests run: {total}')
            print(f'Passed: {passed}')
            print(f'Failed: {total - passed}')
            print(f'Success rate: {success_rate:.1f}%')
            print(f'Average response time: {avg_response_time:.3f}s')
            
            # Store results for CI/CD
            summary = {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'results': self.test_results
            }
            
            # Write to file for CI/CD systems
            with open('integration_test_results.json', 'w') as f:
                json.dump(summary, f, indent=2)


def run_integration_tests():
    """Run the integration test suite."""
    print('🚀 Running SenseVoiceSmall-RKNN2-API Integration Tests...')
    print('=' * 60)
    
    # Set up test environment
    os.environ['TEST_DOCKER_API'] = '1'
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(IntegrationTestSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print('\n' + '=' * 60)
    print('🎯 Final Test Results:')
    print('=' * 60)
    print(f'Tests run: {result.testsRun}')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                       result.testsRun * 100)
        print(f'Success rate: {success_rate:.1f}%')
    else:
        print('Success rate: N/A')
    
    # Exit with appropriate code for CI/CD
    if result.failures or result.errors:
        print('\n❌ Integration tests failed!')
        sys.exit(1)
    else:
        print('\n✅ All integration tests passed!')
        sys.exit(0)


if __name__ == '__main__':
    run_integration_tests() 