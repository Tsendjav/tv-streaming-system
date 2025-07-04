#!/usr/bin/env python3
"""
Media Player Module
Enhanced VLC-based media player with state management and error handling
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QWidget
from models.media_metadata import MediaFile, MediaType

# Core imports with fallbacks
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# VLC import with fallback
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False


class MediaPlayer(QObject):
    """Enhanced media player with VLC backend and improved state management"""
    
    # Signals
    position_changed = pyqtSignal(float)  # position in seconds
    duration_changed = pyqtSignal(float)  # duration in seconds
    state_changed = pyqtSignal(str)       # playing, paused, stopped
    volume_changed = pyqtSignal(int)      # volume 0-100
    error_occurred = pyqtSignal(str)      # error messages
    
    def __init__(self, video_widget: QWidget = None):
        super().__init__()
        self.logger = get_logger(__name__)
        self.video_widget = video_widget
        
        # VLC setup
        if VLC_AVAILABLE:
            self.vlc_instance = vlc.Instance([
                '--no-xlib',
                '--intf', 'dummy',
                '--no-video-title-show',
                '--no-metadata-network-access'
            ])
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Set video output
            if video_widget and sys.platform.startswith('win'):
                self.vlc_player.set_hwnd(video_widget.winId())
            elif video_widget and sys.platform.startswith('linux'):
                self.vlc_player.set_xwindow(video_widget.winId())
            elif video_widget and sys.platform == 'darwin':
                self.vlc_player.set_nsobject(int(video_widget.winId()))
            
            # Setup event manager
            self.event_manager = self.vlc_player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self._on_duration_changed)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
            
        else:
            self.vlc_instance = None
            self.vlc_player = None
            self.logger.warning("VLC not available - preview disabled")
        
        # State
        self.current_media = None
        self.current_state = "stopped"
        self.current_position = 0.0
        self.current_duration = 0.0
        self.current_volume = 80
        
        # Timer for position updates
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(100)  # Update every 100ms
    
    def validate_media(self, media_file) -> bool:
        """Validate media file before loading"""
        if not media_file.file_path.exists():
            self.error_occurred.emit(f"Media file not found: {media_file.file_path}")
            return False
        
        supported_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', 
                              '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        if media_file.file_path.suffix.lower() not in supported_extensions:
            self.error_occurred.emit(f"Unsupported file format: {media_file.file_path.suffix}")
            return False
        
        return True
    
    def load_media(self, media_file) -> bool:
        """Load media file with validation"""
        if not VLC_AVAILABLE or not self.vlc_player:
            self.error_occurred.emit("VLC not available")
            return False
        
        if not self.validate_media(media_file):
            return False
        
        try:
            # Create VLC media
            media = self.vlc_instance.media_new(str(media_file.file_path))
            
            if not media:
                self.error_occurred.emit(f"Failed to create VLC media for: {media_file.file_path}")
                return False
            
            # Set media to player
            self.vlc_player.set_media(media)
            
            self.current_media = media_file
            self.current_state = "stopped"
            
            self.logger.info(f"Loaded media: {media_file.display_name}")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error loading media: {str(e)}")
            return False
    
    def play(self) -> bool:
        """Start playback"""
        if not VLC_AVAILABLE or not self.vlc_player:
            self.error_occurred.emit("VLC not available")
            return False
        
        try:
            result = self.vlc_player.play()
            if result == 0:  # Success
                self.position_timer.start()
                return True
            else:
                self.error_occurred.emit("VLC play() failed")
                return False
        except Exception as e:
            self.error_occurred.emit(f"Error starting playback: {str(e)}")
            return False
    
    def pause(self):
        """Pause playback"""
        if VLC_AVAILABLE and self.vlc_player:
            self.vlc_player.pause()
    
    def stop(self):
        """Stop playback"""
        if VLC_AVAILABLE and self.vlc_player:
            self.vlc_player.stop()
            self.position_timer.stop()
            self.current_position = 0.0
            self.position_changed.emit(0.0)
    
    def seek(self, position: float):
        """Seek to position (0.0 - 1.0)"""
        if VLC_AVAILABLE and self.vlc_player:
            position = max(0.0, min(1.0, position))
            self.vlc_player.set_position(position)
    
    def seek_time(self, time_ms: int):
        """Seek to specific time in milliseconds"""
        if VLC_AVAILABLE and self.vlc_player:
            duration_ms = self.get_duration()
            time_ms = max(0, min(time_ms, duration_ms))
            self.vlc_player.set_time(time_ms)
    
    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        if VLC_AVAILABLE and self.vlc_player:
            volume = max(0, min(100, volume))
            self.vlc_player.audio_set_volume(volume)
            self.current_volume = volume
            self.volume_changed.emit(volume)
    
    def get_position(self) -> float:
        """Get current position (0.0 - 1.0)"""
        if VLC_AVAILABLE and self.vlc_player:
            return self.vlc_player.get_position()
        return 0.0
    
    def get_time(self) -> int:
        """Get current time in milliseconds"""
        if VLC_AVAILABLE and self.vlc_player:
            return self.vlc_player.get_time()
        return 0
    
    def get_duration(self) -> int:
        """Get duration in milliseconds"""
        if VLC_AVAILABLE and self.vlc_player:
            return self.vlc_player.get_length()
        return 0
    
    def is_playing(self) -> bool:
        """Check if currently playing"""
        if VLC_AVAILABLE and self.vlc_player:
            return self.vlc_player.is_playing()
        return False
    
    def _update_position(self):
        """Update position from VLC"""
        if VLC_AVAILABLE and self.vlc_player and self.vlc_player.is_playing():
            time_ms = self.vlc_player.get_time()
            if time_ms >= 0:
                self.current_position = time_ms / 1000.0
                self.position_changed.emit(self.current_position)
    
    def _on_duration_changed(self, event):
        """Handle VLC duration change event"""
        if VLC_AVAILABLE and self.vlc_player:
            duration_ms = self.vlc_player.get_length()
            if duration_ms > 0:
                self.current_duration = duration_ms / 1000.0
                self.duration_changed.emit(self.current_duration)
    
    def _on_playing(self, event):
        """Handle VLC playing event"""
        self.current_state = "playing"
        self.state_changed.emit("playing")
    
    def _on_paused(self, event):
        """Handle VLC paused event"""
        self.current_state = "paused"
        self.state_changed.emit("paused")
    
    def _on_stopped(self, event):
        """Handle VLC stopped event"""
        self.current_state = "stopped"
        self.state_changed.emit("stopped")
        self.position_timer.stop()
    
    def _on_error(self, event):
        """Handle VLC error event"""
        self.error_occurred.emit("Media playback error occurred")
        self.current_state = "error"
        self.state_changed.emit("error")
    
    def cleanup(self):
        """Cleanup VLC resources"""
        try:
            if VLC_AVAILABLE and self.vlc_player:
                self.vlc_player.stop()
                self.vlc_player.release()
            if VLC_AVAILABLE and self.vlc_instance:
                self.vlc_instance.release()
            self.logger.debug("MediaPlayer cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during MediaPlayer cleanup: {e}")
