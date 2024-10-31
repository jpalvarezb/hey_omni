import os
from pathlib import Path

def verify_structure():
    expected_structure = {
        'core': {
            'files': ['__init__.py', 'app.py', 'config.py', 'state.py', 'exceptions.py'],
            'dirs': []
        },
        'services': {
            'files': ['__init__.py'],
            'dirs': ['speech', 'intent', 'edge', 'cloud']
        },
        'services/speech': {
            'files': ['__init__.py'],
            'dirs': ['recognition', 'synthesis', 'wake_word']
        },
        'services/speech/recognition': {
            'files': ['__init__.py', 'base.py', 'vosk.py', 'whisper.py'],
            'dirs': []
        },
        'services/speech/synthesis': {
            'files': ['__init__.py', 'base.py', 'local_tts.py', 'espeak.py'],
            'dirs': []
        },
        'services/speech/wake_word': {
            'files': ['__init__.py', 'base.py', 'porcupine.py'],
            'dirs': []
        },
        'services/intent': {
            'files': ['__init__.py', 'engine.py', 'local_sti.py'],
            'dirs': ['handlers']
        },
        'services/edge': {
            'files': ['__init__.py', 'processor.py'],
            'dirs': ['cache']
        },
        'services/edge/cache': {
            'files': ['__init__.py', 'base.py', 'memory_cache.py'],
            'dirs': []
        },
        'services/cloud': {
            'files': ['__init__.py', 'llm.py'],
            'dirs': ['api']
        },
        'services/cloud/api': {
            'files': ['__init__.py'],
            'dirs': []
        },
        'models': {
            'files': ['__init__.py', 'intent.py', 'command.py', 'response.py'],
            'dirs': []
        },
        'utils': {
            'files': ['__init__.py', 'async_utils.py', 'logging.py', 'validators.py'],
            'dirs': []
        }
    }

    base_path = Path('omni')
    missing_files = []
    missing_dirs = []

    for path, expected in expected_structure.items():
        full_path = base_path / path
        
        # Check if directory exists
        if not full_path.exists():
            missing_dirs.append(path)
            continue

        # Check files
        for file in expected['files']:
            if not (full_path / file).exists():
                missing_files.append(f"{path}/{file}")

        # Check subdirectories
        for dir in expected['dirs']:
            if not (full_path / dir).exists():
                missing_dirs.append(f"{path}/{dir}")

    return missing_files, missing_dirs

missing_files, missing_dirs = verify_structure()

if not missing_files and not missing_dirs:
    print("✅ All directories and files are present!")
else:
    if missing_dirs:
        print("❌ Missing directories:")
        for d in missing_dirs:
            print(f"  - {d}")
    if missing_files:
        print("❌ Missing files:")
        for f in missing_files:
            print(f"  - {f}") 