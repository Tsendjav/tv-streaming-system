"""
TV Streaming System - Modular Streaming Components
Safe import system with path management
"""

import sys
import os
from pathlib import Path

# Add streaming directory to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Ensure paths are in sys.path
paths_to_add = [str(current_dir), str(project_root)]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Safe imports with error handling
def safe_import(module_name, class_name=None):
    """Safely import module or class"""
    try:
        if class_name:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            return __import__(module_name)
    except ImportError as e:
        print(f"⚠️ Failed to import {module_name}: {e}")
        return None

# Core module availability
_MODULES = {
    'utils': safe_import('utils'),
    'ui_helpers': safe_import('ui_helpers'),
    'server_management': safe_import('server_management'),
    'program_stream_manager': safe_import('program_stream_manager'),
    'ffmpeg_builder': safe_import('ffmpeg_builder'),
    'refactored_streaming_tab': safe_import('refactored_streaming_tab'),
    'integration': safe_import('integration')
}

# Export available modules
available_modules = [name for name, module in _MODULES.items() if module is not None]
print(f"✅ Streaming modules loaded: {', '.join(available_modules)}")

__all__ = available_modules
