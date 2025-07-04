#!/usr/bin/env python3
"""
Enhanced Video Player Component
Professional broadcast video player with VLC integration, thumbnails and preview handling
"""

import os
import sys
import platform
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSignalBlocker, QThread, pyqtSlot, QObject
from PyQt6.QtGui import *

# Fallback imports for missing dependencies
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)

try:
    from core.constants import SUPPORTED_VIDEO_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS
except ImportError:
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v', '.3gp'}
    SUPPORTED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}

try:
    from models.media_metadata import MediaFile
except ImportError:
    # Fallback MediaFile class
    class MediaFile:
        def __init__(self, file_path):
            self.file_path = Path(file_path)
            self.filename = self.file_path.name
            self.display_name = self.filename
            self.media_type = self._detect_type()
        
        def _detect_type(self):
            ext = self.file_path.suffix.lower()
            if ext in SUPPORTED_VIDEO_EXTENSIONS:
                return type('MediaType', (), {'value': 'video'})()
            elif ext in SUPPORTED_AUDIO_EXTENSIONS:
                return type('MediaType', (), {'value': 'audio'})()
            else:
                return type('MediaType', (), {'value': 'unknown'})()
        
        @property
        def is_video(self):
            return self.media_type.value == 'video'
        
        @property
        def is_audio(self):
            return self.media_type.value == 'audio'
        
        @property
        def is_image(self):
            ext = self.file_path.suffix.lower()
            return ext in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        
        def exists(self):
            return self.file_path.exists()

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False


class MediaPreviewHandler(QObject):
    """Handles media file previews and thumbnails"""
    
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str, int)
    thumbnail_generated = pyqtSignal(str)  # thumbnail path
    
    def __init__(self, preview_label, parent=None):
        super().__init__(parent)
        self.preview_label = preview_label
        self.logger = get_logger(__name__)
        
        # VLC components
        self.vlc_instance = None
        self.media_player = None
        self.vlc_available = VLC_AVAILABLE
        
        if self.vlc_available:
            self._init_vlc()
    
    def _init_vlc(self):
        """Initialize VLC components"""
        try:
            self.vlc_instance = vlc.Instance([
                '--no-xlib',
                '--intf', 'dummy',
                '--no-video-title-show',
                '--no-metadata-network-access',
                '--quiet'
            ])
            self.media_player = self.vlc_instance.media_player_new()
            self.logger.debug("VLC preview handler initialized successfully")
        except Exception as e:
            self.vlc_available = False
            self.logger.warning(f"VLC preview initialization failed: {e}")
    
    def update_preview(self, media_file: MediaFile):
        """Update preview area with media file"""
        try:
            if media_file.is_image:
                self._load_image_preview(media_file)
            elif media_file.is_video:
                self._load_video_thumbnail(media_file)
            else:
                file_type = media_file.media_type.value.title()
                self.preview_label.setText(f"🎵 {file_type} File\n\n{media_file.filename}\n\nClick 'Play' to preview")
                self.preview_label.setPixmap(QPixmap())  # Clear any existing pixmap
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
            self.preview_label.setText("❌ Preview error")
    
    def _load_image_preview(self, media_file: MediaFile):
        """Load image preview"""
        try:
            if not media_file.exists():
                self.preview_label.setText("❌ File not found")
                return
                
            pixmap = QPixmap(str(media_file.file_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")  # Clear text when showing image
            else:
                self.preview_label.setText("❌ Cannot load image")
                self.preview_label.setPixmap(QPixmap())
        except Exception as e:
            self.logger.error(f"Error loading image preview: {e}")
            self.preview_label.setText("❌ Preview error")
            self.preview_label.setPixmap(QPixmap())
    
    def _load_video_thumbnail(self, media_file: MediaFile):
        """Load video thumbnail"""
        try:
            if not media_file.exists():
                self.preview_label.setText("❌ File not found")
                return
            
            # Try to generate thumbnail with FFmpeg
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                output_path = temp_file.name
            
            try:
                # Generate thumbnail at 1 second mark
                cmd = [
                    "ffmpeg", "-i", str(media_file.file_path), 
                    "-ss", "1", "-vframes", "1", 
                    "-vf", "scale=320:240:force_original_aspect_ratio=decrease",
                    "-y", output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    pixmap = QPixmap(output_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.preview_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.preview_label.setPixmap(scaled_pixmap)
                        self.preview_label.setText("")  # Clear text when showing image
                        self.thumbnail_generated.emit(output_path)
                    else:
                        raise Exception("Generated thumbnail is invalid")
                else:
                    raise Exception("FFmpeg failed to generate thumbnail")
                    
            finally:
                # Clean up temporary file
                if os.path.exists(output_path):
                    QTimer.singleShot(5000, lambda: self._cleanup_temp_file(output_path))
                        
        except subprocess.TimeoutExpired:
            self.logger.warning("Thumbnail generation timed out")
            self.preview_label.setText(f"🎬 Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
        except FileNotFoundError:
            self.logger.debug("FFmpeg not found for thumbnail generation")
            self.preview_label.setText(f"🎬 Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
        except Exception as e:
            self.logger.error(f"Error loading video thumbnail: {e}")
            self.preview_label.setText(f"🎬 Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
    
    def _cleanup_temp_file(self, file_path):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
    
    def clear_preview(self):
        """Clear preview area"""
        self.preview_label.setText("📺 No media selected")
        self.preview_label.setPixmap(QPixmap())


class EnhancedMediaPlayer(QObject):
    """Enhanced media player with VLC backend and improved state management"""
    
    # Signals
    position_changed = pyqtSignal(float)  # position in seconds
    duration_changed = pyqtSignal(float)  # duration in seconds
    state_changed = pyqtSignal(str)       # playing, paused, stopped, ended, error
    volume_changed = pyqtSignal(int)      # volume 0-100
    error_occurred = pyqtSignal(str)      # error messages
    
    def __init__(self, video_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.video_widget = video_widget
        
        # VLC setup
        if VLC_AVAILABLE:
            self.vlc_instance = vlc.Instance([
                '--no-xlib',
                '--intf', 'dummy',
                '--no-video-title-show',
                '--no-metadata-network-access',
                '--quiet'
            ])
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Set video output
            if video_widget:
                if sys.platform.startswith('win'):
                    self.vlc_player.set_hwnd(video_widget.winId())
                elif sys.platform.startswith('linux'):
                    self.vlc_player.set_xwindow(video_widget.winId())
                elif sys.platform == 'darwin':
                    self.vlc_player.set_nsobject(int(video_widget.winId()))
            
            # Setup event manager
            self.event_manager = self.vlc_player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self._on_duration_changed)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_ended)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
            
        else:
            self.vlc_instance = None
            self.vlc_player = None
            self.logger.warning("VLC not available - media player disabled")
        
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
    
    def validate_media(self, file_path) -> bool:
        """Validate media file before loading"""
        path = Path(file_path)
        if not path.exists():
            self.error_occurred.emit(f"Media file not found: {path}")
            return False
        
        supported_extensions = SUPPORTED_VIDEO_EXTENSIONS.union(SUPPORTED_AUDIO_EXTENSIONS)
        if path.suffix.lower() not in supported_extensions:
            self.error_occurred.emit(f"Unsupported file format: {path.suffix}")
            return False
        
        return True
    
    def load_media(self, file_path) -> bool:
        """Load media file with validation"""
        if not VLC_AVAILABLE or not self.vlc_player:
            self.error_occurred.emit("VLC not available")
            return False
        
        if not self.validate_media(file_path):
            return False
        
        try:
            # Create VLC media
            media = self.vlc_instance.media_new(str(Path(file_path).resolve()))
            
            if not media:
                self.error_occurred.emit(f"Failed to create VLC media for: {file_path}")
                return False
            
            # Set media to player
            self.vlc_player.set_media(media)
            
            self.current_media = file_path
            self.current_state = "stopped"
            
            self.logger.info(f"Loaded media: {Path(file_path).name}")
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
    
    def _on_ended(self, event):
        """Handle VLC end reached event"""
        self.current_state = "ended"
        self.state_changed.emit("ended")
        self.position_timer.stop()
    
    def _on_error(self, event):
        """Handle VLC error event"""
        self.error_occurred.emit("Media playback error occurred")
        self.current_state = "error"
        self.state_changed.emit("error")
    
    def cleanup(self):
        """Cleanup VLC resources"""
        try:
            self.position_timer.stop()
            if VLC_AVAILABLE and self.vlc_player:
                self.vlc_player.stop()
                self.vlc_player.release()
            if VLC_AVAILABLE and self.vlc_instance:
                self.vlc_instance.release()
            self.logger.debug("MediaPlayer cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during MediaPlayer cleanup: {e}")


class EnhancedVideoPlayer(QWidget):
    """Enhanced video player with better controls, thumbnails and monitoring"""
    
    media_loaded = pyqtSignal(str)
    playback_state_changed = pyqtSignal(str)  # playing, paused, stopped, ended, error
    error_occurred = pyqtSignal(str)
    
    def __init__(self, player_name: str = "Player", parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.logger = get_logger(f"{__name__}.{player_name}")
        
        self.current_media_path = None
        self.is_playing = False
        self.is_paused = False
        
        # Set fixed size for consistent layout
        self.setFixedHeight(450)  # Increased height for better controls
        self.setMinimumWidth(380)
        
        self._init_ui()
        self._init_media_components()
        
    def _init_ui(self):
        """Initialize enhanced user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Video frame with enhanced styling
        self.video_frame = QFrame()
        self.video_frame.setFixedHeight(280)  # Increased video area
        self.video_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a; 
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.video_frame)
        
        # Enhanced controls section
        controls_widget = QWidget()
        controls_widget.setFixedHeight(165)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)
        
        # Transport controls row
        transport_layout = QHBoxLayout()
        transport_layout.setSpacing(8)
        
        # Media loading
        load_btn = QPushButton("📁")
        load_btn.setFixedSize(40, 40)
        load_btn.setToolTip("Load Media File")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        load_btn.clicked.connect(self.load_media_dialog)
        transport_layout.addWidget(load_btn)
        
        # Playback controls
        self.play_btn = QPushButton("▶️")
        self.play_btn.setFixedSize(50, 40)
        self.play_btn.setToolTip("Play")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #757575;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.play_btn.setEnabled(False)
        transport_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336; 
                color: white; 
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #757575;
            }
        """)
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        transport_layout.addWidget(self.stop_btn)
        
        # Seek controls
        seek_back_btn = QPushButton("⏪")
        seek_back_btn.setFixedSize(35, 40)
        seek_back_btn.setToolTip("Seek -10s")
        seek_back_btn.clicked.connect(lambda: self.seek_relative(-10))
        transport_layout.addWidget(seek_back_btn)
        
        seek_fwd_btn = QPushButton("⏩")
        seek_fwd_btn.setFixedSize(35, 40)
        seek_fwd_btn.setToolTip("Seek +10s")
        seek_fwd_btn.clicked.connect(lambda: self.seek_relative(10))
        transport_layout.addWidget(seek_fwd_btn)
        
        transport_layout.addStretch()
        
        # Volume controls
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(30, 30)
        self.mute_btn.setCheckable(True)
        self.mute_btn.toggled.connect(self._toggle_mute)
        volume_layout.addWidget(self.mute_btn)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setFixedHeight(25)
        self.volume_slider.valueChanged.connect(self._set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("80%")
        self.volume_label.setFixedWidth(35)
        self.volume_label.setStyleSheet("color: #B0BEC5; font-weight: bold;")
        volume_layout.addWidget(self.volume_label)
        
        transport_layout.addLayout(volume_layout)
        controls_layout.addLayout(transport_layout)
        
        # Progress bar and time display
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        
        # Time display
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("color: #E0E0E0; font-family: monospace; font-weight: bold;")
        self.time_label.setFixedWidth(70)
        time_layout.addWidget(self.time_label)
        
        time_layout.addStretch()
        
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("color: #B0BEC5; font-family: monospace;")
        self.duration_label.setFixedWidth(70)
        time_layout.addWidget(self.duration_label)
        
        progress_layout.addLayout(time_layout)
        
        # Position slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setValue(0)
        self.position_slider.setFixedHeight(25)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_moved)
        progress_layout.addWidget(self.position_slider)
        
        controls_layout.addLayout(progress_layout)
        
        # Status and info row
        status_layout = QHBoxLayout()
        
        # File info
        self.file_info_label = QLabel("No media loaded")
        self.file_info_label.setStyleSheet("color: #888; font-style: italic;")
        status_layout.addWidget(self.file_info_label)
        
        status_layout.addStretch()
        
        # Playback status
        self.status_indicator = QLabel("⏹️ Stopped")
        self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
        status_layout.addWidget(self.status_indicator)
        
        controls_layout.addLayout(status_layout)
        
        layout.addWidget(controls_widget)
        
        # Show no media message initially
        self._show_no_media_message()
        
        # Slider update flag
        self.slider_being_dragged = False
    
    def _init_media_components(self):
        """Initialize media player and preview handler"""
        # Create media player
        self.media_player = EnhancedMediaPlayer(self.video_frame, self)
        
        # Create preview handler with a label for the video frame
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #888; font-size: 14px;")
        
        self.preview_handler = MediaPreviewHandler(self.preview_label, self)
        
        # Connect signals
        self.media_player.state_changed.connect(self._on_media_state_changed)
        self.media_player.position_changed.connect(self._on_position_changed)
        self.media_player.duration_changed.connect(self._on_duration_changed)
        self.media_player.volume_changed.connect(self._on_volume_changed)
        self.media_player.error_occurred.connect(self._on_media_error)
        
        self.preview_handler.error_occurred.connect(self._on_preview_error)
        self.preview_handler.status_message.connect(self._on_status_message)
    
    def _show_no_media_message(self):
        """Show enhanced no media message with preview functionality"""
        if self.video_frame.layout():
            QWidget().setLayout(self.video_frame.layout())
        
        overlay_layout = QVBoxLayout(self.video_frame)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setContentsMargins(20, 20, 20, 20)
        
        # Large media icon
        icon_label = QLabel("🎬")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; color: #555;")
        overlay_layout.addWidget(icon_label)
        
        # Message text
        message_label = QLabel(f"{self.player_name}\nNo Media Loaded")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #888; 
                font-size: 14px; 
                font-weight: bold;
                line-height: 1.5;
            }
        """)
        overlay_layout.addWidget(message_label)
        
        # VLC status
        vlc_status = QLabel(f"VLC: {'Available' if VLC_AVAILABLE else 'Not Available'}")
        vlc_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlc_color = "#4CAF50" if VLC_AVAILABLE else "#F44336"
        vlc_status.setStyleSheet(f"color: {vlc_color}; font-size: 10px;")
        overlay_layout.addWidget(vlc_status)
        
        # Load button
        load_hint = QLabel("Click 📁 to load media")
        load_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        load_hint.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        overlay_layout.addWidget(load_hint)
    
    def load_media_dialog(self):
        """Enhanced media loading dialog"""
        try:
            # Create enhanced file dialog
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setViewMode(QFileDialog.ViewMode.Detail)
            dialog.setWindowTitle(f"Load Media for {self.player_name}")
            
            # Set file filters
            video_filter = "Video Files (" + " ".join([f"*{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS]) + ")"
            audio_filter = "Audio Files (" + " ".join([f"*{ext}" for ext in SUPPORTED_AUDIO_EXTENSIONS]) + ")"
            all_media_filter = "All Media Files (" + " ".join([f"*{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS.union(SUPPORTED_AUDIO_EXTENSIONS)]) + ")"
            
            dialog.setNameFilter(f"{all_media_filter};;{video_filter};;{audio_filter};;All Files (*)")
            
            if dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected_files = dialog.selectedFiles()
                if selected_files:
                    self.load_media(selected_files[0])
                    
        except Exception as e:
            self.logger.error(f"Media dialog error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open media dialog: {e}")
    
    def load_media(self, file_path: Union[str, Path]):
        """Enhanced media loading with preview and error handling"""
        try:
            media_path = Path(file_path).resolve()
            
            if not media_path.exists():
                QMessageBox.warning(self, "File Not Found", 
                                  f"Media file not found: {media_path}")
                return False
            
            # Load media into player
            if self.media_player.load_media(str(media_path)):
                self.current_media_path = media_path
                
                # Enable controls
                self.play_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                
                # Update file info
                file_size = media_path.stat().st_size / (1024 * 1024)  # MB
                self.file_info_label.setText(f"{media_path.name} ({file_size:.1f} MB)")
                self.file_info_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
                
                # Create MediaFile for preview
                media_file = MediaFile(media_path)
                
                # Update preview in video frame
                if media_file.is_video or media_file.is_image:
                    # Clear existing layout
                    if self.video_frame.layout():
                        QWidget().setLayout(self.video_frame.layout())
                    
                    # Add preview label to video frame
                    frame_layout = QVBoxLayout(self.video_frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.addWidget(self.preview_label)
                    
                    # Update preview
                    self.preview_handler.update_preview(media_file)
                
                # Emit signal
                self.media_loaded.emit(str(media_path))
                
                self.logger.info(f"Loaded media: {media_path.name}")
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to load media: {e}")
            QMessageBox.critical(self, "Load Error", 
                               f"Failed to load media file:\n{e}")
            return False
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Start or resume playback"""
        if self.media_player.play():
            self.is_playing = True
            self.is_paused = False
            
            self.play_btn.setText("⏸️")
            self.play_btn.setToolTip("Pause")
            self.status_indicator.setText("▶️ Playing")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Clear preview when playing video
            if VLC_AVAILABLE and self.current_media_path:
                media_file = MediaFile(self.current_media_path)
                if media_file.is_video:
                    # Clear preview label to show VLC video output
                    if self.video_frame.layout():
                        QWidget().setLayout(self.video_frame.layout())
            
            self.logger.debug("Playback started")
    
    def pause(self):
        """Pause playback"""
        self.media_player.pause()
        self.is_playing = False
        self.is_paused = True
        
        self.play_btn.setText("▶️")
        self.play_btn.setToolTip("Play")
        self.status_indicator.setText("⏸️ Paused")
        self.status_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
        
        self.logger.debug("Playback paused")
    
    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.is_playing = False
        self.is_paused = False
        
        self.play_btn.setText("▶️")
        self.play_btn.setToolTip("Play")
        self.status_indicator.setText("⏹️ Stopped")
        self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
        
        # Reset position
        self.position_slider.setValue(0)
        self.time_label.setText("00:00:00")
        
        # Show preview again after stopping
        if self.current_media_path:
            media_file = MediaFile(self.current_media_path)
            if media_file.is_video:
                # Recreate preview
                if self.video_frame.layout():
                    QWidget().setLayout(self.video_frame.layout())
                
                frame_layout = QVBoxLayout(self.video_frame)
                frame_layout.setContentsMargins(0, 0, 0, 0)
                frame_layout.addWidget(self.preview_label)
                
                self.preview_handler.update_preview(media_file)
        
        self.logger.debug("Playback stopped")
    
    def seek_relative(self, seconds):
        """Seek relative to current position"""
        current_time = self.media_player.get_time()
        if current_time >= 0:
            new_time = max(0, current_time + (seconds * 1000))
            self.media_player.seek_time(int(new_time))
            self.logger.debug(f"Seeked {seconds}s to {new_time/1000:.1f}s")
    
    def _toggle_mute(self, muted):
        """Toggle audio mute"""
        if muted:
            self.media_player.set_volume(0)
            self.mute_btn.setText("🔇")
            self.mute_btn.setStyleSheet("background-color: #F44336;")
        else:
            volume = self.volume_slider.value()
            self.media_player.set_volume(volume)
            self.mute_btn.setText("🔊")
            self.mute_btn.setStyleSheet("")
    
    def _set_volume(self, volume: int):
        """Set audio volume"""
        if not self.mute_btn.isChecked():
            self.media_player.set_volume(volume)
        
        self.volume_label.setText(f"{volume}%")
        
        # Update mute button if volume is 0
        if volume == 0:
            self.mute_btn.setChecked(True)
        elif self.mute_btn.isChecked() and volume > 0:
            self.mute_btn.setChecked(False)
    
    def _on_slider_pressed(self):
        """Handle slider press - pause updates"""
        self.slider_being_dragged = True
    
    def _on_slider_released(self):
        """Handle slider release - seek to position"""
        if self.current_media_path:
            position = self.position_slider.value() / 1000.0
            self.media_player.seek(position)
        
        self.slider_being_dragged = False
    
    def _on_slider_moved(self, value):
        """Handle slider movement during drag"""
        if self.slider_being_dragged:
            # Update time display during drag
            duration_ms = self.media_player.get_duration()
            if duration_ms > 0:
                current_time = (value / 1000.0) * duration_ms / 1000.0
                self.time_label.setText(self._format_time(current_time))
    
    def _on_media_state_changed(self, state):
        """Handle media player state changes"""
        self.playback_state_changed.emit(state)
        
        if state == "ended":
            self.is_playing = False
            self.is_paused = False
            self.play_btn.setText("▶️")
            self.status_indicator.setText("⏹️ Ended")
            self.status_indicator.setStyleSheet("color: #9E9E9E; font-weight: bold;")
            
            # Show preview again after ending
            self.stop()
    
    def _on_position_changed(self, position_seconds):
        """Handle position changes from media player"""
        if not self.slider_being_dragged:
            duration_ms = self.media_player.get_duration()
            if duration_ms > 0:
                position = (position_seconds * 1000.0) / duration_ms
                slider_value = int(position * 1000)
                self.position_slider.setValue(slider_value)
            
            self.time_label.setText(self._format_time(position_seconds))
    
    def _on_duration_changed(self, duration_seconds):
        """Handle duration changes from media player"""
        self.duration_label.setText(self._format_time(duration_seconds))
    
    def _on_volume_changed(self, volume):
        """Handle volume changes from media player"""
        self.volume_slider.setValue(volume)
        self.volume_label.setText(f"{volume}%")
    
    def _on_media_error(self, error_message):
        """Handle media player errors"""
        self.error_occurred.emit(error_message)
        self.logger.error(f"Media error: {error_message}")
    
    def _on_preview_error(self, error_message):
        """Handle preview errors"""
        self.logger.warning(f"Preview error: {error_message}")
    
    def _on_status_message(self, message, timeout):
        """Handle status messages from preview"""
        self.logger.debug(f"Preview status: {message}")
    
    def _format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS"""
        if seconds < 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_current_file(self) -> Optional[str]:
        """Get current file path"""
        return str(self.current_media_path) if self.current_media_path else None
    
    def get_playback_state(self) -> dict:
        """Get current playback state"""
        return {
            'file': self.get_current_file(),
            'playing': self.is_playing,
            'paused': self.is_paused,
            'position': self.media_player.get_position(),
            'time': self.media_player.get_time(),
            'length': self.media_player.get_duration()
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.media_player:
                self.media_player.cleanup()
            
            self.logger.debug("Enhanced video player cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Export
__all__ = ['EnhancedVideoPlayer', 'VLC_AVAILABLE', 'EnhancedMediaPlayer', 'MediaPreviewHandler']