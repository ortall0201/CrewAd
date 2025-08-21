"""
Smoke test CLI for CrewAd pipeline
Tests upload → run → status → download flow
"""

import os
import sys
import tempfile
import uuid
import json
import requests
import time
from pathlib import Path
from PIL import Image
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_test_image(path: Path, size=(800, 600), color=(100, 150, 200)):
    """Create a test image"""
    img = Image.new('RGB', size, color)
    img.save(path)
    logger.info(f"Created test image: {path}")

def create_test_brief(path: Path):
    """Create a test brief"""
    brief = """Create an engaging video advertisement for a revolutionary AI tool.

Key Message: Transform your workflow with AI-powered automation
Tone: Confident and innovative
Target: Tech professionals and business owners
CTA: Start your free trial today

Highlights:
- 10x faster processing
- 99% accuracy rate  
- Used by 50,000+ professionals
- Save 20 hours per week"""
    
    with open(path, 'w') as f:
        f.write(brief)
    logger.info(f"Created test brief: {path}")

def test_upload(api_base: str, test_dir: Path):
    """Test file upload"""
    logger.info("=== Testing Upload ===")
    
    # Create test files
    image_path = test_dir / "test_image.jpg"
    logo_path = test_dir / "logo.jpg"
    brief_path = test_dir / "brief.txt"
    
    create_test_image(image_path, size=(800, 600), color=(50, 100, 150))
    create_test_image(logo_path, size=(200, 200), color=(200, 50, 50))
    create_test_brief(brief_path)
    
    # Upload files
    url = f"{api_base}/api/upload"
    files = [
        ('files', ('test_image.jpg', open(image_path, 'rb'), 'image/jpeg')),
        ('files', ('logo.jpg', open(logo_path, 'rb'), 'image/jpeg')),
        ('files', ('brief.txt', open(brief_path, 'rb'), 'text/plain')),
    ]
    
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()
        
        result = response.json()
        run_id = result['run_id']
        logger.info(f"✓ Upload successful: run_id={run_id}")
        logger.info(f"  Files uploaded: {result['total_files']}")
        
        return run_id
        
    except Exception as e:
        logger.error(f"✗ Upload failed: {e}")
        return None
    finally:
        # Close files
        for _, (_, f, _) in files:
            f.close()

def test_pipeline_run(api_base: str, run_id: str):
    """Test pipeline execution"""
    logger.info("=== Testing Pipeline Run ===")
    
    url = f"{api_base}/api/run"
    data = {
        "run_id": run_id,
        "target_length": 10,  # Short video for testing
        "tone": "confident",
        "voice": "default",
        "aspect": "16:9"
    }
    
    try:
        # Test JSON API
        response = requests.post(url, json=data)
        if response.status_code == 422:
            # Fallback to form data if JSON fails
            logger.info("JSON API failed, trying form data...")
            response = requests.post(url, data=data)
            
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"✓ Pipeline started: {result['status']}")
        logger.info(f"  Parameters: {result['parameters']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Pipeline run failed: {e}")
        return False

def test_status_polling(api_base: str, run_id: str, max_wait=60):
    """Test status polling until completion"""
    logger.info("=== Testing Status Polling ===")
    
    url = f"{api_base}/api/status/{run_id}"
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            status = response.json()
            current_step = status.get('current_step', 'unknown')
            overall_status = status.get('overall_status', 'unknown')
            
            logger.info(f"Status: {overall_status} (step: {current_step})")
            
            if overall_status in ['success', 'failed', 'complete']:
                if overall_status == 'success':
                    logger.info("✓ Pipeline completed successfully")
                    return True
                else:
                    logger.error(f"✗ Pipeline failed: {overall_status}")
                    # Log error details
                    if 'steps' in status:
                        for step in status['steps']:
                            if 'error' in step.get('extra', {}):
                                logger.error(f"  Step {step['step']}: {step['extra']['error']}")
                    return False
                    
            time.sleep(2)  # Poll every 2 seconds
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            time.sleep(2)
    
    logger.error("✗ Pipeline timed out")
    return False

def test_download(api_base: str, run_id: str, output_dir: Path):
    """Test video download"""
    logger.info("=== Testing Download ===")
    
    url = f"{api_base}/api/download/{run_id}"
    output_path = output_dir / f"test_output_{run_id}.mp4"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_path)
        logger.info(f"✓ Download successful: {output_path} ({file_size} bytes)")
        
        return file_size > 0
        
    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        return False

def main():
    """Run smoke test"""
    api_base = "http://localhost:8000"
    
    logger.info("🚀 Starting CrewAd Smoke Test")
    logger.info(f"API Base: {api_base}")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_assets"
        output_dir = Path(temp_dir) / "outputs"
        test_dir.mkdir()
        output_dir.mkdir()
        
        # Check API health
        try:
            response = requests.get(f"{api_base}/health")
            response.raise_for_status()
            logger.info("✓ API is healthy")
        except Exception as e:
            logger.error(f"✗ API health check failed: {e}")
            sys.exit(1)
        
        # Run tests
        success = True
        
        # 1. Upload
        run_id = test_upload(api_base, test_dir)
        if not run_id:
            success = False
        
        # 2. Run pipeline
        if success and run_id:
            success = test_pipeline_run(api_base, run_id)
        
        # 3. Poll status
        if success and run_id:
            success = test_status_polling(api_base, run_id)
        
        # 4. Download
        if success and run_id:
            success = test_download(api_base, run_id, output_dir)
        
        # Results
        if success:
            logger.info("🎉 All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some tests failed")
            sys.exit(1)

if __name__ == "__main__":
    main()