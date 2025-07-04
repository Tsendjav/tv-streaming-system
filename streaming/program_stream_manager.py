"""
TV Stream - Program Stream Manager
Program streaming functionality
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from PyQt6.QtCore import QTimer, QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QTimer, QObject, pyqtSignal

# Safe imports
try:
    from .utils import MediaValidator, LoggerManager, StreamingUtils
except ImportError:
    try:
        from utils import MediaValidator, LoggerManager, StreamingUtils
    except ImportError:
        # Fallback implementations
        import logging
        
        class LoggerManager:
            @classmethod
            def get_logger(cls, name): return logging.getLogger(name)
        
        class MediaValidator:
            @classmethod
            def is_valid_media_file(cls, file_path): return True
        
        class StreamingUtils:
            @staticmethod
            def generate_stream_key(prefix="stream"): 
                return f"{prefix}_{int(time.time())}"


class ProgramStreamManager(QObject):
    """Program streaming management"""
    
    # Signals
    stream_started = pyqtSignal(str, str)
    stream_stopped = pyqtSignal(str, str)
    stream_failed = pyqtSignal(str, str)
    status_changed = pyqtSignal(bool, str)
    
    def __init__(self, parent_tab, stream_manager):
        super().__init__()
        self.parent_tab = parent_tab
        self.stream_manager = stream_manager
        self.logger = LoggerManager.get_logger(__name__)
        self.validator = MediaValidator()
        self.streaming_utils = StreamingUtils()
        
        # State
        self.is_active = False
        self.current_stream_key = None
        self.current_file_path = None
        self.auto_stream_enabled = True
        
        # Monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_streams)
        self.monitor_timer.start(2000)
    
    def start_program_stream(self, file_path: str, options: Dict[str, Any] = None) -> bool:
        """Start program stream"""
        try:
            if not self.validator.is_valid_media_file(file_path):
                raise ValueError(f"Invalid media file: {file_path}")
            
            stream_key = self.streaming_utils.generate_stream_key("program")
            
            # Create mock stream config (replace with actual implementation)
            class MockStreamConfig:
                def __init__(self, stream_key, input_source):
                    self.stream_key = stream_key
                    self.input_source = input_source
            
            config = MockStreamConfig(stream_key, file_path)
            
            if hasattr(self.stream_manager, 'start_stream'):
                success = self.stream_manager.start_stream(config)
                if success:
                    self.current_stream_key = stream_key
                    self.current_file_path = file_path
                    self.is_active = True
                    self.stream_started.emit(stream_key, file_path)
                    self.status_changed.emit(True, stream_key)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start program stream: {e}")
            return False
    
    def stop_program_streams(self) -> int:
        """Stop all program streams"""
        stopped_count = 0
        try:
            if hasattr(self.stream_manager, 'streams'):
                program_streams = [k for k in self.stream_manager.streams.keys() 
                                 if "program" in k.lower()]
                
                for stream_key in program_streams:
                    if hasattr(self.stream_manager, 'stop_stream'):
                        if self.stream_manager.stop_stream(stream_key):
                            stopped_count += 1
            
            if stopped_count > 0:
                self.is_active = False
                self.current_stream_key = None
                self.stream_stopped.emit("all", f"Stopped {stopped_count} streams")
                self.status_changed.emit(False, "")
            
        except Exception as e:
            self.logger.error(f"Failed to stop program streams: {e}")
        
        return stopped_count
    
    def get_program_stream_status(self) -> Dict[str, Any]:
        """Get program stream status"""
        return {
            'is_active': self.is_active,
            'stream_count': 1 if self.is_active else 0,
            'current_file': self.current_file_path,
            'current_key': self.current_stream_key,
            'auto_stream_enabled': self.auto_stream_enabled
        }
    
    def set_auto_stream_enabled(self, enabled: bool):
        """Enable/disable auto streaming"""
        self.auto_stream_enabled = enabled
    
    def connect_to_playout_tab(self, playout_tab) -> bool:
        """Connect to playout tab"""
        try:
            # Connect signals if available
            if hasattr(playout_tab, 'media_taken_to_air'):
                playout_tab.media_taken_to_air.connect(self._on_media_taken_to_air)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to playout tab: {e}")
            return False
    
    def _monitor_streams(self):
        """Monitor stream status"""
        # Basic monitoring implementation
        pass
    
    def _on_media_taken_to_air(self, file_path: str):
        """Handle media taken to air"""
        if self.auto_stream_enabled:
            self.start_program_stream(file_path)
