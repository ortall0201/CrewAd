#!/usr/bin/env python3
import sys
import os
import json

# Add the backend src to Python path
backend_src = os.path.join(os.path.dirname(__file__), 'folder-in-ad-out', 'backend', 'src')
sys.path.insert(0, backend_src)

from crew.tasks import EditTask

def test_edit_task():
    # Test EditTask directly with real parameters
    run_id = 'c0e2fe07-5f60-4eda-91de-411f7be4b674'
    base_dir = r'C:\Users\user\Desktop\CrewAd\folder-in-ad-out\uploads'
    run_dir = os.path.join(base_dir, run_id)
    aspect = '16:9'

    print(f'Testing EditTask.execute() directly...')
    print(f'run_id: {run_id}')
    print(f'run_dir: {run_dir}')

    # Load actual shots data
    shots_file = os.path.join(run_dir, 'shots.json')
    with open(shots_file, 'r') as f:
        shots = json.load(f)

    # Mock wavs data based on actual temp_audio structure
    wavs = [
        os.path.join(run_dir, 'temp_audio', 'line_01_silent.wav'),
        os.path.join(run_dir, 'temp_audio', 'line_02_silent.wav'),
        os.path.join(run_dir, 'temp_audio', 'line_03_silent.wav')
    ]

    print(f'shots: {len(shots.get("scenes", []))} scenes')
    print(f'wavs: {len(wavs)} audio files')
    print(f'aspect: {aspect}')

    try:
        edit_task = EditTask()
        print(f'EditTask created: {edit_task.task_name}')
        
        result = edit_task.execute(
            run_id=run_id,
            shots=shots,
            wavs=wavs,
            aspect=aspect,
            run_dir=run_dir
        )
        print(f'EditTask.execute() returned: "{result}"')
        print('Direct EditTask test SUCCESSFUL')
        return result
        
    except Exception as e:
        print(f'Direct EditTask test FAILED: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_edit_task()