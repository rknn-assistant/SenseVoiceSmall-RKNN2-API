#!/usr/bin/env python3
"""
Test cases for Docker functionality
"""

import os
import sys
import time
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests

class TestDockerBuild(unittest.TestCase):
    """Test cases for Docker build functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.dockerfile_path = self.project_root / "Dockerfile"
        self.docker_compose_path = self.project_root / "docker-compose.yml"
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        self.assertTrue(self.dockerfile_path.exists(), "Dockerfile not found")
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        self.assertTrue(self.docker_compose_path.exists(), "docker-compose.yml not found")
    
    def test_dockerfile_content(self):
        """Test Dockerfile content."""
        with open(self.dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for required components
        self.assertIn('FROM python:3.11-slim', content)
        self.assertIn('submodules/SenseVoiceSmall-RKNN2', content)
        self.assertIn('requirements.txt', content)
        self.assertIn('EXPOSE 8080', content)
    
    def test_docker_compose_content(self):
        """Test docker-compose.yml content."""
        with open(self.docker_compose_path, 'r') as f:
            content = f.read()
        
        # Check for required components
        self.assertIn('sensevoice:', content)
        self.assertIn('build:', content)
        self.assertIn('ports:', content)
        self.assertIn('volumes:', content)
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_BUILD'), "Docker build test disabled")
    def test_docker_build(self):
        """Test Docker image build."""
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', 'sensevoice-test', '.'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"Docker build failed: {result.stderr}")
            
            self.assertEqual(result.returncode, 0, "Docker build failed")
            
        except subprocess.TimeoutExpired:
            self.fail("Docker build timed out")
        except FileNotFoundError:
            self.skipTest("Docker not available")

class TestDockerCompose(unittest.TestCase):
    """Test cases for Docker Compose functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_COMPOSE'), "Docker Compose test disabled")
    def test_docker_compose_build(self):
        """Test Docker Compose build."""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'build'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"Docker Compose build failed: {result.stderr}")
            
            self.assertEqual(result.returncode, 0, "Docker Compose build failed")
            
        except subprocess.TimeoutExpired:
            self.fail("Docker Compose build timed out")
        except FileNotFoundError:
            self.skipTest("Docker Compose not available")
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_COMPOSE'), "Docker Compose test disabled")
    def test_docker_compose_up_down(self):
        """Test Docker Compose up and down."""
        try:
            # Start services
            up_result = subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.assertEqual(up_result.returncode, 0, "Docker Compose up failed")
            
            # Wait for service to be ready
            time.sleep(10)
            
            # Check if service is running
            ps_result = subprocess.run(
                ['docker', 'compose', 'ps'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            self.assertIn('sensevoice-rknn2', ps_result.stdout)
            
            # Stop services
            down_result = subprocess.run(
                ['docker', 'compose', 'down'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.assertEqual(down_result.returncode, 0, "Docker Compose down failed")
            
        except subprocess.TimeoutExpired:
            self.fail("Docker Compose operation timed out")
        except FileNotFoundError:
            self.skipTest("Docker Compose not available")

class TestDockerAPI(unittest.TestCase):
    """Test cases for API running in Docker."""
    
    def setUp(self):
        """Set up test environment."""
        self.api_url = "http://localhost:8081"
        self.timeout = 30
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_API'), "Docker API test disabled")
    def test_docker_api_health(self):
        """Test API health endpoint in Docker."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"API health check failed: {e}")
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_API'), "Docker API test disabled")
    def test_docker_api_languages(self):
        """Test API languages endpoint in Docker."""
        try:
            response = requests.get(f"{self.api_url}/languages", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('languages', data)
            self.assertIn('language_codes', data)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"API languages check failed: {e}")
    
    @unittest.skipUnless(os.environ.get('TEST_DOCKER_API'), "Docker API test disabled")
    def test_docker_api_config(self):
        """Test API config endpoint in Docker."""
        try:
            response = requests.get(f"{self.api_url}/config", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('features', data)
            self.assertIn('supported_formats', data)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"API config check failed: {e}")

class TestSubmoduleFunctionality(unittest.TestCase):
    """Test cases for submodule functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.submodule_path = self.project_root / "submodules" / "SenseVoiceSmall-RKNN2"
    
    def test_submodule_exists(self):
        """Test that submodule directory exists."""
        self.assertTrue(self.submodule_path.exists(), "Submodule directory not found")
    
    def test_submodule_files(self):
        """Test that required submodule files exist."""
        required_files = [
            "sensevoice_rknn.py",
            "convert_rknn.py",
            "embedding.npy",
            "sense-voice-encoder.rknn",
            "chn_jpn_yue_eng_ko_spectok.bpe.model",
            "am.mvn",
            "fsmnvad-offline.onnx",
            "fsmn-config.yaml"
        ]
        
        for file_name in required_files:
            file_path = self.submodule_path / file_name
            self.assertTrue(file_path.exists(), f"Required file {file_name} not found in submodule")
    
    def test_gitmodules_file(self):
        """Test that .gitmodules file exists and is correct."""
        gitmodules_path = self.project_root / ".gitmodules"
        self.assertTrue(gitmodules_path.exists(), ".gitmodules file not found")
        
        with open(gitmodules_path, 'r') as f:
            content = f.read()
        
        self.assertIn("SenseVoiceSmall-RKNN2", content)
        self.assertIn("huggingface.co", content)

class TestRequirements(unittest.TestCase):
    """Test cases for requirements.txt."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.requirements_path = self.project_root / "requirements.txt"
    
    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        self.assertTrue(self.requirements_path.exists(), "requirements.txt not found")
    
    def test_requirements_content(self):
        """Test requirements.txt content."""
        with open(self.requirements_path, 'r') as f:
            content = f.read()
        
        # Check for required packages
        required_packages = [
            "numpy",
            "soundfile",
            "onnxruntime",
            "rknn-toolkit-lite2",
            "flask",
            "flask-cors",
            "prometheus-client"
        ]
        
        for package in required_packages:
            self.assertIn(package, content, f"Required package {package} not found in requirements.txt")

if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    os.makedirs('tests', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2) 