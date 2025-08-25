#!/usr/bin/env python3
"""Test the real EditTask with extensive exception handling"""

import asyncio
import os
import json
import sys

# Change to the backend directory to avoid import issues
backend_dir = os.path.join(os.path.dirname(__file__), 'folder-in-ad-out', 'backend')
original_cwd = os.getcwd()
os.chdir(backend_dir)
sys.path.insert(0, os.path.join(backend_dir, 'src'))

from crew.run_crew import AdCreationPipeline

async def test_real_edit_task():
    """Test the real EditTask with the exact same pattern as the pipeline"""
    
    # Set up the same data as the pipeline
    run_id = 'c0e2fe07-5f60-4eda-91de-411f7be4b674'
    base_uploads = os.path.abspath('../../folder-in-ad-out/uploads')
    run_dir = os.path.join(base_uploads, run_id)
    aspect = '16:9'
    
    print(f"Testing REAL EditTask with pipeline parameters...")
    print(f"run_id: {run_id}")
    print(f"run_dir: {run_dir}")
    print(f"aspect: {aspect}")
    
    # Load real shots data
    shots_file = os.path.join(run_dir, 'shots.json')
    with open(shots_file, 'r') as f:
        shots = json.load(f)
    
    # Use the real wavs that the pipeline would generate
    temp_audio_dir = os.path.join(run_dir, 'temp_audio')
    wavs = []
    if os.path.exists(temp_audio_dir):
        for scene in shots.get('scenes', []):
            scene_id = scene.get('id', 1)
            wav_file = os.path.join(temp_audio_dir, f'line_{scene_id:02d}_silent.wav')
            if os.path.exists(wav_file):
                wavs.append(wav_file)
    
    print(f"shots: {len(shots.get('scenes', []))} scenes")
    print(f"wavs: {len(wavs)} files")
    
    try:
        # Create real pipeline and get the real EditTask
        pipeline = AdCreationPipeline()
        real_edit_task = pipeline.tasks["edit"]
        
        print(f"Real EditTask created: {real_edit_task.task_name}")
        
        # Write pre-execution debug file
        debug_file = f"C:\\Users\\user\\Desktop\\CrewAd\\real-edit-pre-debug.txt"
        with open(debug_file, "w") as f:
            f.write(f"BEFORE asyncio.to_thread\\n")
            f.write(f"EditTask type: {type(real_edit_task)}\\n")
            f.write(f"Execute method: {real_edit_task.execute}\\n")
            f.write(f"Parameters ready\\n")
            
        print("About to call asyncio.to_thread with REAL EditTask...")
        
        # Exact same asyncio.to_thread call as in the pipeline with extra error handling
        try:
            video_path = await asyncio.to_thread(
                real_edit_task.execute,
                run_id=run_id,
                shots=shots,
                wavs=wavs,
                aspect=aspect,
                run_dir=run_dir
            )
            
            # Write success debug
            with open(debug_file, "a") as f:
                f.write(f"asyncio.to_thread SUCCEEDED\\n")
                f.write(f"Returned: {video_path}\\n")
                
            print(f"asyncio.to_thread returned: '{video_path}'")
            print("Real EditTask test SUCCESSFUL")
            return video_path
            
        except Exception as async_e:
            # Write async failure debug  
            with open(debug_file, "a") as f:
                f.write(f"asyncio.to_thread FAILED\\n")
                f.write(f"Exception: {async_e}\\n")
                f.write(f"Exception type: {type(async_e)}\\n")
                
            print(f"asyncio.to_thread FAILED: {async_e}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"Setup FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = asyncio.run(test_real_edit_task())
    print(f"Final result: {result}")