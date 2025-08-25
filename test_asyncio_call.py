#!/usr/bin/env python3
"""Test the exact asyncio.to_thread call that fails in the pipeline"""

import asyncio
import os
import json

# Mock the EditTask to isolate the asyncio.to_thread issue
class MockEditTask:
    def __init__(self):
        self.task_name = "Video Rendering"
        
    def execute(self, **kwargs):
        """Simulate the execute method"""
        print(f"MockEditTask.execute() called with kwargs: {list(kwargs.keys())}")
        
        # Create the debug file that should be created in the real execute method
        debug_file = f"C:\\Users\\user\\Desktop\\CrewAd\\mock-execute-debug.txt"
        with open(debug_file, "w") as f:
            f.write(f"MOCK EXECUTE CALLED\n")
            f.write(f"Task: {self.task_name}\n")
            f.write(f"Kwargs: {kwargs}\n")
            
        # Simulate the _run call
        try:
            result = self._run(**kwargs)
            with open(debug_file, "a") as f:
                f.write(f"_run returned: {result}\n")
            return result
        except Exception as e:
            with open(debug_file, "a") as f:
                f.write(f"_run failed with exception: {e}\n")
            raise
            
    def _run(self, run_id: str, shots: dict, wavs: list, aspect: str, run_dir: str) -> str:
        """Mock the _run method"""
        debug_file = f"C:\\Users\\user\\Desktop\\CrewAd\\mock-run-debug.txt"
        with open(debug_file, "w") as f:
            f.write(f"MOCK _RUN CALLED\n")
            f.write(f"run_id: {run_id}\n")
            f.write(f"shots: {type(shots)}\n")
            f.write(f"wavs: {type(wavs)}\n")
            f.write(f"aspect: {aspect}\n")
            f.write(f"run_dir: {run_dir}\n")
            
        # Just return a mock result
        return f"mock_video_path_{run_id}.mp4"

async def test_asyncio_call():
    """Test the exact asyncio.to_thread call pattern used in the pipeline"""
    
    # Set up the same data as the pipeline
    run_id = 'c0e2fe07-5f60-4eda-91de-411f7be4b674'
    run_dir = rf'C:\Users\user\Desktop\CrewAd\folder-in-ad-out\uploads\{run_id}'
    aspect = '16:9'
    
    # Load real shots data
    shots_file = os.path.join(run_dir, 'shots.json')
    with open(shots_file, 'r') as f:
        shots = json.load(f)
    
    # Mock wavs
    wavs = ['file1.wav', 'file2.wav', 'file3.wav']
    
    print(f"Testing asyncio.to_thread with real pipeline parameters...")
    print(f"run_id: {run_id}")
    print(f"shots: {len(shots.get('scenes', []))} scenes")
    print(f"wavs: {len(wavs)} files")
    print(f"aspect: {aspect}")
    print(f"run_dir: {run_dir}")
    
    try:
        # Create mock task (simulating self.tasks["edit"])
        mock_edit_task = MockEditTask()
        
        # Exact same asyncio.to_thread call as in the pipeline
        video_path = await asyncio.to_thread(
            mock_edit_task.execute,
            run_id=run_id,
            shots=shots,
            wavs=wavs,
            aspect=aspect,
            run_dir=run_dir
        )
        
        print(f"asyncio.to_thread returned: {video_path}")
        print("asyncio.to_thread test SUCCESSFUL")
        return video_path
        
    except Exception as e:
        print(f"asyncio.to_thread test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = asyncio.run(test_asyncio_call())
    print(f"Final result: {result}")