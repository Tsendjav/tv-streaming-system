#!/usr/bin/env python3
"""
core/integration/shared_data.py
Хуваалцсан өгөгдлийн удирдлага - табуудын хооронд өгөгдөл хуваалцах
"""

import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class MediaInfo:
    """Shared media information"""
    file_path: str
    title: Optional[str] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    resolution: Optional[tuple] = None
    file_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StreamInfo:
    """Shared stream information"""
    stream_key: str
    server_name: str
    quality: str
    status: str
    bitrate: str
    fps: float
    uptime: str
    viewer_count: Optional[int] = None

@dataclass
class PlayoutState:
    """Shared playout state"""
    preview_media: Optional[MediaInfo] = None
    program_media: Optional[MediaInfo] = None
    is_live: bool = False
    preview_position: float = 0.0
    program_position: float = 0.0
    audio_levels: Dict[str, float] = field(default_factory=dict)

# =============================================================================
# SHARED DATA MANAGER
# =============================================================================

class SharedDataManager(QObject):
    """Manages shared data between tabs"""
    
    # Signals for data changes
    media_library_updated = pyqtSignal()
    current_media_changed = pyqtSignal(object)
    playout_state_changed = pyqtSignal(object)
    stream_status_changed = pyqtSignal(object)
    audio_state_changed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        
        # Shared data stores
        self.media_library: List[MediaInfo] = []
        self.current_media: Optional[MediaInfo] = None
        self.playout_state = PlayoutState()
        self.active_streams: Dict[str, StreamInfo] = {}
        self.audio_state: Dict[str, Any] = {
            "profile": "default",
            "levels": {"left": 0.0, "right": 0.0},
            "muted": False,
            "voice_clarity": 30,
            "bass_boost": 0
        }
        
        # Configuration cache
        self.config_cache: Dict[str, Any] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        self.logger = self._get_logger()
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    # Media Library Management
    def update_media_library(self, media_files: List[MediaInfo]):
        """Update shared media library"""
        with self._lock:
            self.media_library = media_files.copy()
            self.media_library_updated.emit()
            self.logger.debug(f"Media library updated: {len(media_files)} files")
    
    def get_media_library(self) -> List[MediaInfo]:
        """Get current media library"""
        with self._lock:
            return self.media_library.copy()
    
    def add_media_file(self, media_info: MediaInfo):
        """Add single media file"""
        with self._lock:
            self.media_library.append(media_info)
            self.media_library_updated.emit()
    
    def set_current_media(self, media_info: Optional[MediaInfo]):
        """Set currently selected media"""
        with self._lock:
            self.current_media = media_info
            self.current_media_changed.emit(media_info)
            self.logger.debug(f"Current media changed: {media_info.title if media_info else None}")
    
    def get_current_media(self) -> Optional[MediaInfo]:
        """Get currently selected media"""
        with self._lock:
            return self.current_media
    
    # Playout State Management
    def update_playout_state(self, **kwargs):
        """Update playout state"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.playout_state, key):
                    setattr(self.playout_state, key, value)
            
            self.playout_state_changed.emit(self.playout_state)
            self.logger.debug(f"Playout state updated: {kwargs}")
    
    def get_playout_state(self) -> PlayoutState:
        """Get current playout state"""
        with self._lock:
            return self.playout_state
    
    # Stream Management
    def update_stream_info(self, stream_key: str, stream_info: StreamInfo):
        """Update stream information"""
        with self._lock:
            self.active_streams[stream_key] = stream_info
            self.stream_status_changed.emit(self.active_streams.copy())
    
    def remove_stream_info(self, stream_key: str):
        """Remove stream information"""
        with self._lock:
            if stream_key in self.active_streams:
                del self.active_streams[stream_key]
                self.stream_status_changed.emit(self.active_streams.copy())
    
    def get_active_streams(self) -> Dict[str, StreamInfo]:
        """Get all active streams"""
        with self._lock:
            return self.active_streams.copy()
    
    # Audio State Management
    def update_audio_state(self, **kwargs):
        """Update audio state"""
        with self._lock:
            self.audio_state.update(kwargs)
            self.audio_state_changed.emit(self.audio_state.copy())
            self.logger.debug(f"Audio state updated: {kwargs}")
    
    def get_audio_state(self) -> Dict[str, Any]:
        """Get current audio state"""
        with self._lock:
            return self.audio_state.copy()
    
    # Configuration Management
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        with self._lock:
            self.config_cache[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self._lock:
            return self.config_cache.get(key, default)

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'MediaInfo',
    'StreamInfo', 
    'PlayoutState',
    'SharedDataManager'
]