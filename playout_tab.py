#!/usr/bin/env python3
"""
Enhanced Professional Playout Tab for TV Streaming System
Integrated with complete audio management system and Media Library
"""

import sys
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont

# Import audio system components
try:
    from audio.tv_audio_engine import TVAudioSystem
    from audio.audio_profiles import AudioProfileManager, AudioProfile
    from audio.jack_backend import JackBackend
    from audio.lv2_plugins import LV2PluginManager
    from audio.carla_host import CarlaHost
    AUDIO_SYSTEM_AVAILABLE = True
    print("✅ Audio system components loaded successfully")
except ImportError as e:
    print(f"⚠️ Audio system components not available: {e}")
    AUDIO_SYSTEM_AVAILABLE = False

# Check availability flag
PLAYOUT_TAB_AVAILABLE = True

# Set up basic logging
def get_logger(name):
    return logging.getLogger(name)

# Check VLC availability
VLC_AVAILABLE = False
try:
    import vlc
    VLC_AVAILABLE = True
    print("✅ VLC Python bindings available for playout")
except ImportError:
    print("⚠️ VLC Python bindings not available for playout")


class AudioSystemThread(QThread):
    """Separate thread for audio system operations"""
    audio_levels_updated = pyqtSignal(dict)
    audio_status_changed = pyqtSignal(str, str)
    
    def __init__(self, audio_system):
        super().__init__()
        self.audio_system = audio_system
        self.running = False
        
    def run(self):
        """Monitor audio levels and status"""
        self.running = True
        while self.running:
            try:
                if self.audio_system and AUDIO_SYSTEM_AVAILABLE:
                    # Simulate audio level monitoring
                    levels = {
                        'left': 75 + (time.time() % 10) * 2,
                        'right': 78 + (time.time() % 8) * 1.5,
                        'master': self.audio_system.master_volume * 100
                    }
                    self.audio_levels_updated.emit(levels)
                    
                    # Check audio status
                    if hasattr(self.audio_system, 'jack_server') and self.audio_system.jack_server.is_running:
                        self.audio_status_changed.emit("🟢 Audio Ready", "#4CAF50")
                    else:
                        self.audio_status_changed.emit("🔴 Audio Offline", "#F44336")
                
                self.msleep(100)  # Update every 100ms
                
            except Exception as e:
                logging.error(f"Audio monitoring error: {e}")
                self.msleep(1000)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.wait()


class MediaPlaylist:
    """Enhanced playlist management for media files"""
    
    def __init__(self):
        self.media_files = []
        self.current_index = -1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.auto_advance = True
        
    def load_from_media_library(self, media_files_list):
        """Load playlist from media library"""
        self.media_files = media_files_list.copy()
        self.current_index = 0 if self.media_files else -1
        return len(self.media_files)
    
    def add_media(self, media_file):
        """Add single media file to playlist"""
        self.media_files.append(media_file)
        if self.current_index == -1:
            self.current_index = 0
    
    def clear(self):
        """Clear playlist"""
        self.media_files.clear()
        self.current_index = -1
    
    def get_current(self):
        """Get current media file"""
        if 0 <= self.current_index < len(self.media_files):
            return self.media_files[self.current_index]
        return None
    
    def get_next(self):
        """Get next media file"""
        if not self.media_files:
            return None
            
        if self.current_index + 1 < len(self.media_files):
            return self.media_files[self.current_index + 1]
        elif self.repeat_mode:
            return self.media_files[0]
        return None
    
    def advance_to_next(self):
        """Advance to next media file"""
        if not self.media_files:
            return False
            
        if self.current_index + 1 < len(self.media_files):
            self.current_index += 1
            return True
        elif self.repeat_mode:
            self.current_index = 0
            return True
        return False
    
    def get_previous(self):
        """Get previous media file"""
        if not self.media_files:
            return None
            
        if self.current_index > 0:
            return self.media_files[self.current_index - 1]
        elif self.repeat_mode:
            return self.media_files[-1]
        return None
    
    def advance_to_previous(self):
        """Advance to previous media file"""
        if not self.media_files:
            return False
            
        if self.current_index > 0:
            self.current_index -= 1
            return True
        elif self.repeat_mode:
            self.current_index = len(self.media_files) - 1
            return True
        return False
    
    def get_playlist_info(self):
        """Get playlist information"""
        return {
            'total_files': len(self.media_files),
            'current_position': self.current_index + 1 if self.current_index >= 0 else 0,
            'repeat_mode': self.repeat_mode,
            'shuffle_mode': self.shuffle_mode,
            'auto_advance': self.auto_advance
        }


class EnhancedVideoPlayer(QWidget):
    """Enhanced video player with VLC support and playlist integration"""
    media_loaded = pyqtSignal(str)
    playback_state_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    media_ended = pyqtSignal()  # NEW: Signal when media ends
    
    def __init__(self, player_name="Player", parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.current_media_path = None
        self.is_playing = False
        self.vlc_instance = None
        self.vlc_player = None
        
        # Playlist integration
        self.playlist = MediaPlaylist()
        self.playlist_enabled = False
        
        self.setFixedHeight(480)
        self.setMinimumWidth(500)
        self._init_ui()
        self._init_vlc()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Video display area
        self.video_frame = QFrame()
        self.video_frame.setFixedHeight(350)
        self.video_frame.setStyleSheet("""
            QFrame {
                background: #1a1a1a; 
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        
        frame_layout = QVBoxLayout(self.video_frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("📹")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px; color: #555;")
        frame_layout.addWidget(icon)
        
        message = QLabel(f"{self.player_name}")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
        frame_layout.addWidget(message)
        
        vlc_status = QLabel(f"VLC: {'Available' if VLC_AVAILABLE else 'Not Available'}")
        vlc_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlc_color = "#4CAF50" if VLC_AVAILABLE else "#F44336"
        vlc_status.setStyleSheet(f"color: {vlc_color}; font-size: 10px;")
        frame_layout.addWidget(vlc_status)
        
        layout.addWidget(self.video_frame)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Load from Media Library button - ENHANCED
        load_btn = QPushButton("📚 Load from Library")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        load_btn.clicked.connect(self.load_from_media_library)
        controls_layout.addWidget(load_btn)
        
        # Original load button
        load_file_btn = QPushButton("📁 Load File")
        load_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        load_file_btn.clicked.connect(self.load_media_dialog)
        controls_layout.addWidget(load_file_btn)
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
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
        controls_layout.addWidget(self.play_btn)
        
        stop_btn = QPushButton("⏹️ Stop")
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        stop_btn.clicked.connect(self.stop)
        controls_layout.addWidget(stop_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Playlist controls - NEW
        playlist_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⏮️ Previous")
        self.prev_btn.setFixedSize(80, 30)
        self.prev_btn.clicked.connect(self.play_previous)
        self.prev_btn.setEnabled(False)
        playlist_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("⏭️ Next")
        self.next_btn.setFixedSize(80, 30)
        self.next_btn.clicked.connect(self.play_next)
        self.next_btn.setEnabled(False)
        playlist_layout.addWidget(self.next_btn)
        
        self.repeat_btn = QPushButton("🔁 Repeat")
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setFixedSize(80, 30)
        self.repeat_btn.toggled.connect(self._toggle_repeat)
        playlist_layout.addWidget(self.repeat_btn)
        
        self.auto_advance_btn = QPushButton("🚀 Auto")
        self.auto_advance_btn.setCheckable(True)
        self.auto_advance_btn.setChecked(True)
        self.auto_advance_btn.setFixedSize(80, 30)
        self.auto_advance_btn.toggled.connect(self._toggle_auto_advance)
        playlist_layout.addWidget(self.auto_advance_btn)
        
        playlist_layout.addStretch()
        
        # Playlist info
        self.playlist_info_label = QLabel("Playlist: 0/0")
        self.playlist_info_label.setStyleSheet("font-size: 10px; color: #888;")
        playlist_layout.addWidget(self.playlist_info_label)
        
        layout.addLayout(playlist_layout)
        
        # Status
        self.status_label = QLabel(f"{self.player_name} - Ready")
        self.status_label.setStyleSheet("color: #E0E0E0; font-size: 12px; padding: 8px;")
        layout.addWidget(self.status_label)
    
    def _init_vlc(self):
        """Initialize VLC if available"""
        if VLC_AVAILABLE:
            try:
                self.vlc_instance = vlc.Instance('--no-xlib')
                self.vlc_player = self.vlc_instance.media_player_new()
                
                # Set up event handling for media end
                if self.vlc_player:
                    event_manager = self.vlc_player.event_manager()
                    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end)
                
                if sys.platform.startswith('linux'):
                    self.vlc_player.set_xwindow(self.video_frame.winId())
                elif sys.platform == "win32":
                    self.vlc_player.set_hwnd(self.video_frame.winId())
                elif sys.platform == "darwin":
                    self.vlc_player.set_nsobject(int(self.video_frame.winId()))
                
                print(f"✅ VLC initialized for {self.player_name}")
            except Exception as e:
                print(f"❌ Failed to initialize VLC: {e}")
                self.vlc_instance = None
                self.vlc_player = None
    
    def _on_media_end(self, event):
        """Handle media end event"""
        self.media_ended.emit()
        if self.playlist.auto_advance and self.playlist_enabled:
            QTimer.singleShot(500, self.play_next)  # Small delay before advancing
    
    def load_from_media_library(self):
        """Load media files from Media Library - NEW"""
        # This will be connected to main window to get media library files
        self.media_library_requested.emit()
    
    # Add signal for requesting media library
    media_library_requested = pyqtSignal()
    
    def set_media_library_files(self, media_files):
        """Set media files from media library - NEW"""
        if not media_files:
            self.status_label.setText("No media files available in library")
            return
            
        count = self.playlist.load_from_media_library(media_files)
        self.playlist_enabled = True
        self._update_playlist_controls()
        self._update_playlist_info()
        
        # Load first file
        current_media = self.playlist.get_current()
        if current_media:
            self.load_media(str(current_media.file_path))
            self.status_label.setText(f"Loaded playlist with {count} files")
    
    def play_next(self):
        """Play next media in playlist - NEW"""
        if not self.playlist_enabled or not self.playlist.advance_to_next():
            self.status_label.setText("End of playlist reached")
            return
            
        current_media = self.playlist.get_current()
        if current_media:
            self.load_media(str(current_media.file_path))
            if self.is_playing:
                self.play()
            self._update_playlist_info()
    
    def play_previous(self):
        """Play previous media in playlist - NEW"""
        if not self.playlist_enabled or not self.playlist.advance_to_previous():
            self.status_label.setText("At beginning of playlist")
            return
            
        current_media = self.playlist.get_current()
        if current_media:
            self.load_media(str(current_media.file_path))
            if self.is_playing:
                self.play()
            self._update_playlist_info()
    
    def _toggle_repeat(self, enabled):
        """Toggle repeat mode - NEW"""
        self.playlist.repeat_mode = enabled
        status = "enabled" if enabled else "disabled"
        self.status_label.setText(f"Repeat mode {status}")
    
    def _toggle_auto_advance(self, enabled):
        """Toggle auto advance mode - NEW"""
        self.playlist.auto_advance = enabled
        status = "enabled" if enabled else "disabled"
        self.status_label.setText(f"Auto advance {status}")
    
    def _update_playlist_controls(self):
        """Update playlist control buttons - NEW"""
        has_playlist = self.playlist_enabled and len(self.playlist.media_files) > 0
        
        self.prev_btn.setEnabled(has_playlist)
        self.next_btn.setEnabled(has_playlist)
        self.repeat_btn.setEnabled(has_playlist)
        self.auto_advance_btn.setEnabled(has_playlist)
    
    def _update_playlist_info(self):
        """Update playlist information display - NEW"""
        if self.playlist_enabled:
            info = self.playlist.get_playlist_info()
            self.playlist_info_label.setText(
                f"Playlist: {info['current_position']}/{info['total_files']}"
            )
        else:
            self.playlist_info_label.setText("Playlist: 0/0")
    
    def load_media_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Load Media for {self.player_name}",
            "", "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flv *.wmv);;All Files (*)"
        )
        if file_path:
            # Disable playlist when loading single file
            self.playlist_enabled = False
            self._update_playlist_controls()
            self._update_playlist_info()
            self.load_media(file_path)
    
    def load_media(self, file_path):
        self.current_media_path = Path(file_path)
        self.play_btn.setEnabled(True)
        self.status_label.setText(f"Loaded: {self.current_media_path.name}")
        
        # Load in VLC if available
        if self.vlc_player:
            try:
                media = self.vlc_instance.media_new(str(file_path))
                self.vlc_player.set_media(media)
                print(f"✅ Media loaded in VLC: {self.current_media_path.name}")
            except Exception as e:
                print(f"❌ Failed to load media in VLC: {e}")
        
        self.media_loaded.emit(str(file_path))
        return True
    
    def toggle_play_pause(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        self.is_playing = True
        self.play_btn.setText("⏸️ Pause")
        if self.current_media_path:
            self.status_label.setText(f"Playing: {self.current_media_path.name}")
        
        # Play in VLC if available
        if self.vlc_player:
            self.vlc_player.play()
        
        self.playback_state_changed.emit("playing")
    
    def pause(self):
        self.is_playing = False
        self.play_btn.setText("▶️ Play")
        if self.current_media_path:
            self.status_label.setText(f"Paused: {self.current_media_path.name}")
        
        # Pause in VLC if available
        if self.vlc_player:
            self.vlc_player.pause()
        
        self.playback_state_changed.emit("paused")
    
    def stop(self):
        self.is_playing = False
        self.play_btn.setText("▶️ Play")
        self.status_label.setText("Stopped")
        
        # Stop in VLC if available
        if self.vlc_player:
            self.vlc_player.stop()
        
        self.playback_state_changed.emit("stopped")
    
    def get_current_file(self):
        return str(self.current_media_path) if self.current_media_path else None
    
    def get_playback_state(self):
        return {"file": self.get_current_file(), "playing": self.is_playing}
    
    def cleanup(self):
        if self.vlc_player:
            self.vlc_player.stop()


class ProfessionalAudioControlPanel(QWidget):
    """Professional audio control panel with integrated audio system"""
    profile_changed = pyqtSignal(str)
    night_mode_toggled = pyqtSignal(bool)
    parameter_changed = pyqtSignal(str, object)
    
    def __init__(self, audio_system=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.audio_system = audio_system
        self.config_manager = config_manager
        self.current_profile = "default"
        self.current_volume = 80
        self.audio_monitor_thread = None
        
        # Initialize audio system components
        if AUDIO_SYSTEM_AVAILABLE and not self.audio_system:
            try:
                self.audio_system = TVAudioSystem("playout_audio_client")
                print("🎵 Audio system initialized for playout tab")
            except Exception as e:
                print(f"⚠️ Failed to initialize audio system: {e}")
                self.audio_system = None
        
        self._init_ui()
        self._start_audio_monitoring()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with audio system status
        header_layout = QHBoxLayout()
        header = QLabel("🔊 Professional Audio Control")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: bold; 
                color: #00BCD4;
                background-color: #333;
                padding: 12px;
                border-radius: 6px;
            }
        """)
        header_layout.addWidget(header)
        
        # Audio system status
        audio_status = "🟢 Active" if AUDIO_SYSTEM_AVAILABLE and self.audio_system else "🔴 Offline"
        self.audio_system_status = QLabel(audio_status)
        self.audio_system_status.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4CAF50;
                padding: 8px;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.15);
            }
        """)
        header_layout.addWidget(self.audio_system_status)
        
        layout.addLayout(header_layout)
        
        # Master Volume Control
        volume_group = QGroupBox("Master Volume & Dynamics")
        volume_group.setStyleSheet(self._get_group_style())
        volume_layout = QVBoxLayout(volume_group)
        volume_layout.setSpacing(10)
        volume_layout.setContentsMargins(15, 15, 15, 15)
        
        # Master volume
        master_layout = QHBoxLayout()
        master_label = QLabel("Master Volume:")
        master_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        master_layout.addWidget(master_label)
        
        self.master_slider = QSlider(Qt.Orientation.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(80)
        self.master_slider.setStyleSheet(self._get_slider_style())
        self.master_slider.valueChanged.connect(self._on_volume_changed)
        master_layout.addWidget(self.master_slider)
        
        self.master_label = QLabel("80%")
        self.master_label.setFixedWidth(40)
        self.master_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00BCD4;")
        master_layout.addWidget(self.master_label)
        volume_layout.addLayout(master_layout)
        
        # Limiter/Compressor controls
        dynamics_layout = QHBoxLayout()
        
        self.limiter_btn = QPushButton("🛡️ Limiter")
        self.limiter_btn.setCheckable(True)
        self.limiter_btn.setStyleSheet(self._get_button_style())
        self.limiter_btn.toggled.connect(self._toggle_limiter)
        dynamics_layout.addWidget(self.limiter_btn)
        
        self.compressor_btn = QPushButton("🎚️ Compressor")
        self.compressor_btn.setCheckable(True)
        self.compressor_btn.setStyleSheet(self._get_button_style())
        self.compressor_btn.toggled.connect(self._toggle_compressor)
        dynamics_layout.addWidget(self.compressor_btn)
        
        volume_layout.addLayout(dynamics_layout)
        layout.addWidget(volume_group)
        
        # Audio Profiles
        profiles_group = QGroupBox("Audio Processing Profiles")
        profiles_group.setStyleSheet(self._get_group_style())
        profiles_layout = QVBoxLayout(profiles_group)
        profiles_layout.setSpacing(8)
        profiles_layout.setContentsMargins(15, 15, 15, 15)
        
        # Profile buttons
        self.profile_buttons = {}
        profiles = ["Default", "Movie", "Music", "News", "Sports"]
        for profile in profiles:
            btn = QPushButton(f"🎯 {profile}")
            btn.setFixedHeight(35)
            btn.setStyleSheet(self._get_profile_button_style())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=profile: self._apply_preset(p.lower()))
            self.profile_buttons[profile.lower()] = btn
            profiles_layout.addWidget(btn)
        
        # Set default as checked
        self.profile_buttons["default"].setChecked(True)
        layout.addWidget(profiles_group)
        
        # Special Audio Modes
        special_group = QGroupBox("Special Audio Modes")
        special_group.setStyleSheet(self._get_group_style())
        special_layout = QVBoxLayout(special_group)
        special_layout.setContentsMargins(15, 15, 15, 15)
        
        special_buttons_layout = QHBoxLayout()
        
        self.night_mode_btn = QPushButton("🌙 Night Mode")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setFixedHeight(40)
        self.night_mode_btn.setStyleSheet(self._get_special_button_style("#9C27B0"))
        self.night_mode_btn.toggled.connect(self._on_night_mode_toggled)
        special_buttons_layout.addWidget(self.night_mode_btn)
        
        self.dialogue_btn = QPushButton("🎙️ Dialogue+")
        self.dialogue_btn.setCheckable(True)
        self.dialogue_btn.setFixedHeight(40)
        self.dialogue_btn.setStyleSheet(self._get_special_button_style("#FF9800"))
        self.dialogue_btn.toggled.connect(self._toggle_dialogue_enhancement)
        special_buttons_layout.addWidget(self.dialogue_btn)
        
        special_layout.addLayout(special_buttons_layout)
        
        # Bass boost control
        bass_layout = QHBoxLayout()
        bass_label = QLabel("Bass Boost:")
        bass_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        bass_layout.addWidget(bass_label)
        
        self.bass_slider = QSlider(Qt.Orientation.Horizontal)
        self.bass_slider.setRange(0, 12)
        self.bass_slider.setValue(0)
        self.bass_slider.setStyleSheet(self._get_slider_style())
        self.bass_slider.valueChanged.connect(self._on_bass_changed)
        bass_layout.addWidget(self.bass_slider)
        
        self.bass_label = QLabel("0dB")
        self.bass_label.setFixedWidth(40)
        self.bass_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FF9800;")
        bass_layout.addWidget(self.bass_label)
        special_layout.addLayout(bass_layout)
        
        layout.addWidget(special_group)
        
        # Real-time Audio Monitoring
        monitoring_group = QGroupBox("Real-time Audio Monitoring")
        monitoring_group.setStyleSheet(self._get_group_style())
        monitoring_layout = QVBoxLayout(monitoring_group)
        monitoring_layout.setSpacing(8)
        monitoring_layout.setContentsMargins(15, 15, 15, 15)
        
        # Level meters
        levels_layout = QVBoxLayout()
        
        # Left channel
        left_layout = QHBoxLayout()
        left_label = QLabel("L:")
        left_label.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 20px;")
        left_layout.addWidget(left_label)
        
        self.left_meter = QProgressBar()
        self.left_meter.setRange(0, 100)
        self.left_meter.setValue(75)
        self.left_meter.setFixedHeight(20)
        self.left_meter.setStyleSheet(self._get_meter_style())
        left_layout.addWidget(self.left_meter)
        
        self.left_peak = QLabel("-12dB")
        self.left_peak.setStyleSheet("font-size: 10px; color: #4CAF50; min-width: 50px;")
        left_layout.addWidget(self.left_peak)
        levels_layout.addLayout(left_layout)
        
        # Right channel
        right_layout = QHBoxLayout()
        right_label = QLabel("R:")
        right_label.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 20px;")
        right_layout.addWidget(right_label)
        
        self.right_meter = QProgressBar()
        self.right_meter.setRange(0, 100)
        self.right_meter.setValue(78)
        self.right_meter.setFixedHeight(20)
        self.right_meter.setStyleSheet(self._get_meter_style())
        right_layout.addWidget(self.right_meter)
        
        self.right_peak = QLabel("-9dB")
        self.right_peak.setStyleSheet("font-size: 10px; color: #4CAF50; min-width: 50px;")
        right_layout.addWidget(self.right_peak)
        levels_layout.addLayout(right_layout)
        
        monitoring_layout.addLayout(levels_layout)
        layout.addWidget(monitoring_group)
        
        # Equalizer
        eq_group = QGroupBox("Professional Equalizer")
        eq_group.setStyleSheet(self._get_group_style())
        eq_layout = QVBoxLayout(eq_group)
        eq_layout.setContentsMargins(15, 15, 15, 15)
        
        # EQ controls
        eq_controls_layout = QHBoxLayout()
        
        eq_reset_btn = QPushButton("Reset EQ")
        eq_reset_btn.setStyleSheet(self._get_button_style())
        eq_reset_btn.clicked.connect(self._reset_eq)
        eq_controls_layout.addWidget(eq_reset_btn)
        
        eq_preset_combo = QComboBox()
        eq_preset_combo.addItems(["Flat", "Voice", "Music", "Cinema", "Custom"])
        eq_preset_combo.setStyleSheet(self._get_combo_style())
        eq_preset_combo.currentTextChanged.connect(self._apply_eq_preset)
        eq_controls_layout.addWidget(eq_preset_combo)
        
        eq_controls_layout.addStretch()
        eq_layout.addLayout(eq_controls_layout)
        
        # EQ bands
        eq_bands_layout = QHBoxLayout()
        eq_bands = ["60Hz", "170Hz", "310Hz", "600Hz", "1kHz", "3kHz", "6kHz", "12kHz"]
        self.eq_sliders = {}
        
        for band in eq_bands:
            band_layout = QVBoxLayout()
            band_layout.setSpacing(2)
            
            band_label = QLabel(band)
            band_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            band_label.setStyleSheet("font-size: 9px; color: #AAA;")
            
            band_slider = QSlider(Qt.Orientation.Vertical)
            band_slider.setRange(-12, 12)
            band_slider.setValue(0)
            band_slider.setFixedHeight(60)
            band_slider.setFixedWidth(25)
            band_slider.setStyleSheet(self._get_eq_slider_style())
            band_slider.valueChanged.connect(lambda v, b=band: self._on_eq_changed(b, v))
            self.eq_sliders[band] = band_slider
            
            band_layout.addWidget(band_label)
            band_layout.addWidget(band_slider)
            eq_bands_layout.addLayout(band_layout)
        
        eq_layout.addLayout(eq_bands_layout)
        layout.addWidget(eq_group)
        
        # Add stretch to fill remaining space
        layout.addStretch()
    
    def _get_group_style(self):
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 8px;
                margin-top: 1ex;
                color: #E0E0E0;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
            }
        """
    
    def _get_slider_style(self):
        return """
            QSlider::groove:horizontal {
                border: 2px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00BCD4;
                border: 2px solid #00BCD4;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #26C6DA;
            }
        """
    
    def _get_eq_slider_style(self):
        return """
            QSlider::groove:vertical {
                border: 1px solid #555;
                width: 4px;
                background: #333;
                border-radius: 2px;
            }
            QSlider::handle:vertical {
                background: #00BCD4;
                border: 1px solid #00BCD4;
                height: 10px;
                margin: 0 -4px;
                border-radius: 5px;
            }
        """
    
    def _get_button_style(self):
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:checked {
                background-color: #00BCD4;
                border: 2px solid #26C6DA;
            }
        """
    
    def _get_profile_button_style(self):
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:checked {
                background-color: #00BCD4;
                border: 2px solid #26C6DA;
            }
        """
    
    def _get_special_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:checked {{
                background-color: {color};
                border: 2px solid #FFF;
                opacity: 0.8;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
    
    def _get_meter_style(self):
        return """
            QProgressBar {
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #222;
                text-align: center;
                font-weight: bold;
                color: white;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #FFEB3B, stop:1 #F44336);
                border-radius: 2px;
            }
        """
    
    def _get_combo_style(self):
        return """
            QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
                color: #E0E0E0;
            }
        """
    
    def _start_audio_monitoring(self):
        """Start audio monitoring thread"""
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            self.audio_monitor_thread = AudioSystemThread(self.audio_system)
            self.audio_monitor_thread.audio_levels_updated.connect(self._update_audio_levels)
            self.audio_monitor_thread.audio_status_changed.connect(self._update_audio_status)
            self.audio_monitor_thread.start()
    
    def _update_audio_levels(self, levels):
        """Update audio level meters"""
        try:
            if 'left' in levels:
                self.left_meter.setValue(int(min(100, max(0, levels['left']))))
                self.left_peak.setText(f"{levels['left']:.0f}dB")
            
            if 'right' in levels:
                self.right_meter.setValue(int(min(100, max(0, levels['right']))))
                self.right_peak.setText(f"{levels['right']:.0f}dB")
        except Exception as e:
            logging.error(f"Error updating audio levels: {e}")
    
    def _update_audio_status(self, status_text, color):
        """Update audio system status"""
        self.audio_system_status.setText(status_text)
        self.audio_system_status.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color};
                padding: 8px;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.15);
            }}
        """)
    
    def _on_volume_changed(self, value):
        """Handle master volume change"""
        self.current_volume = value
        self.master_label.setText(f"{value}%")
        
        # Update audio system
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                self.audio_system.set_master_volume(value / 100.0)
                print(f"🔊 Master volume set to {value}%")
            except Exception as e:
                logging.error(f"Failed to set master volume: {e}")
        
        self.parameter_changed.emit("volume", value)
    
    def _on_bass_changed(self, value):
        """Handle bass boost change"""
        self.bass_label.setText(f"{value}dB")
        
        # Update audio system
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                self.audio_system.set_bass_boost(value)
                print(f"🎵 Bass boost set to {value}dB")
            except Exception as e:
                logging.error(f"Failed to set bass boost: {e}")
    
    def _apply_preset(self, preset_name):
        """Apply audio profile preset"""
        # Uncheck all buttons
        for btn in self.profile_buttons.values():
            btn.setChecked(False)
        
        # Check the selected button
        if preset_name in self.profile_buttons:
            self.profile_buttons[preset_name].setChecked(True)
        
        self.current_profile = preset_name
        
        # Apply to audio system
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                if preset_name == "movie":
                    self.audio_system.set_content_type("movie")
                elif preset_name == "music":
                    self.audio_system.set_content_type("music")
                elif preset_name == "news":
                    self.audio_system.set_content_type("news")
                elif preset_name == "sports":
                    self.audio_system.set_content_type("sports")
                else:
                    self.audio_system.load_profile("default")
                
                print(f"🎯 Applied audio profile: {preset_name}")
            except Exception as e:
                logging.error(f"Failed to apply audio profile: {e}")
        
        self.profile_changed.emit(preset_name)
    
    def _on_night_mode_toggled(self, enabled):
        """Handle night mode toggle"""
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                self.audio_system.enable_night_mode(enabled)
                print(f"🌙 Night mode {'enabled' if enabled else 'disabled'}")
            except Exception as e:
                logging.error(f"Failed to toggle night mode: {e}")
        
        self.night_mode_toggled.emit(enabled)
    
    def _toggle_dialogue_enhancement(self, enabled):
        """Toggle dialogue enhancement"""
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                self.audio_system.enhance_dialogue(enabled)
                print(f"🎙️ Dialogue enhancement {'enabled' if enabled else 'disabled'}")
            except Exception as e:
                logging.error(f"Failed to toggle dialogue enhancement: {e}")
    
    def _toggle_limiter(self, enabled):
        """Toggle audio limiter"""
        print(f"🛡️ Limiter {'enabled' if enabled else 'disabled'}")
        # Implementation would set limiter parameters in audio system
    
    def _toggle_compressor(self, enabled):
        """Toggle audio compressor"""
        print(f"🎚️ Compressor {'enabled' if enabled else 'disabled'}")
        # Implementation would set compressor parameters in audio system
    
    def _on_eq_changed(self, band, value):
        """Handle EQ band change"""
        print(f"🎛️ EQ {band}: {value}dB")
        # Implementation would update EQ plugin parameters
    
    def _reset_eq(self):
        """Reset all EQ bands to 0"""
        for slider in self.eq_sliders.values():
            slider.setValue(0)
        print("🎛️ EQ reset to flat")
    
    def _apply_eq_preset(self, preset_name):
        """Apply EQ preset"""
        print(f"🎛️ Applied EQ preset: {preset_name}")
        # Implementation would load EQ preset values
    
    def cleanup(self):
        """Cleanup audio monitoring"""
        if self.audio_monitor_thread:
            self.audio_monitor_thread.stop()
        
        if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
            try:
                self.audio_system.deactivate()
            except Exception as e:
                logging.error(f"Error during audio cleanup: {e}")
    
    def get_current_settings(self):
        return {
            "profile": self.current_profile,
            "volume": self.current_volume,
            "audio_system_active": AUDIO_SYSTEM_AVAILABLE and self.audio_system is not None
        }


class PlayoutTab(QWidget):
    """Enhanced Professional Playout tab with Media Library integration"""
    
    # Signals for main window integration
    status_message = pyqtSignal(str, int)
    media_taken_to_air = pyqtSignal(str)
    audio_profile_changed = pyqtSignal(str)
    media_loaded = pyqtSignal(str)
    server_config_requested = pyqtSignal()
    media_library_requested = pyqtSignal()  # NEW: Request media library files
    stream_program_requested = pyqtSignal(str)  # Request to stream program content
    stream_status_changed = pyqtSignal(bool, str)  # Streaming status change
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = config_manager
        
        # Initialize audio system first
        self.audio_system = None
        if AUDIO_SYSTEM_AVAILABLE:
            try:
                self.audio_system = TVAudioSystem("playout_main_client")
                self.logger.info("Audio system initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize audio system: {e}")
                self.audio_system = None
        
        # Component references
        self.preview_player = None
        self.program_player = None
        self.audio_control_panel = None
        self.amcp_status_label = None
        self.on_air_label = None
        self.auto_audio_btn = None
        self.log_text = None
        self.connect_btn = None
        self.disconnect_btn = None
        self.channel_spin = None
        self.layer_spin = None
        self.media_combo = None
        self.audio_status_label = None
        
        # State tracking
        self.is_on_air = False
        self.auto_audio_enabled = True
        self.amcp_connected = False
        
        # Media Library Integration - NEW
        self.media_library_tab = None  # Will be set by main window
        
        self.init_ui()
        self._apply_professional_styling()
        self._setup_connections()
        self._initialize_log()
        self._initialize_audio_system()
    
    def set_media_library_tab(self, media_library_tab):
        """Set reference to media library tab - NEW"""
        self.media_library_tab = media_library_tab
        self.logger.info("Media library tab reference set")
    
    def _initialize_audio_system(self):
        """Initialize and start audio system"""
        if self.audio_system:
            try:
                # Start audio system
                if hasattr(self.audio_system, 'jack_server'):
                    self.audio_system.jack_server.start()
                self.audio_system.activate()
                
                self._add_log_entry("AUDIO", "Professional audio system initialized", "#00BCD4")
                self._add_log_entry("AUDIO", f"JACK Backend: {'Active' if self.audio_system.jack_server.is_running else 'Inactive'}", "#00BCD4")
                self._add_log_entry("AUDIO", f"Plugin Host: {'Ready' if self.audio_system.carla_host else 'Not Available'}", "#00BCD4")
                
            except Exception as e:
                self.logger.error(f"Failed to start audio system: {e}")
                self._add_log_entry("ERROR", f"Audio system initialization failed: {e}", "#F44336")
    
    def init_ui(self):
        """Initialize separated UI layout with independent sections"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========================
        # LEFT SECTION: VIDEO PLAYERS & AMCP CONTROL
        # ========================
        left_section = QWidget()
        left_section.setMinimumWidth(1150)
        left_layout = QVBoxLayout(left_section)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. AMCP Server Control (top)
        amcp_section = self._create_compact_amcp_section()
        left_layout.addWidget(amcp_section)
        
        # 2. Video Players Section (main)
        players_section = self._create_enhanced_players_section()
        left_layout.addWidget(players_section)
        
        # 3. Log Section (bottom)
        log_section = self._create_compact_log_section()
        left_layout.addWidget(log_section)
        
        # Set stretch factors for left section
        left_layout.setStretchFactor(amcp_section, 0)
        left_layout.setStretchFactor(players_section, 1)
        left_layout.setStretchFactor(log_section, 0)
        
        main_layout.addWidget(left_section)
        
        # ========================
        # RIGHT SECTION: PROFESSIONAL AUDIO CONTROLLER
        # ========================
        right_section = QWidget()
        right_section.setFixedWidth(400)  # Increased width for professional controls
        right_layout = QVBoxLayout(right_section)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        # Professional audio control panel
        self.audio_control_panel = ProfessionalAudioControlPanel(
            audio_system=self.audio_system,
            config_manager=self.config_manager
        )
        right_layout.addWidget(self.audio_control_panel)
        
        main_layout.addWidget(right_section)
        
        # Set stretch factors for main layout
        main_layout.setStretchFactor(left_section, 1)
        main_layout.setStretchFactor(right_section, 0)

    def _create_compact_amcp_section(self):
        """Create compact AMCP control section"""
        section = QGroupBox("🖥️ AMCP Server Control & Channel Management")
        section.setFixedHeight(70)
        layout = QHBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Connection status
        self.amcp_status_label = QLabel("🔴 Disconnected")
        self.amcp_status_label.setStyleSheet("color: #F44336; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.amcp_status_label)
        
        # Connect/Disconnect buttons
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setFixedSize(90, 35)
        self.connect_btn.clicked.connect(self._connect_amcp)
        layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedSize(90, 35)
        self.disconnect_btn.clicked.connect(self._disconnect_amcp)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)
        
        # Channel/layer controls
        layout.addWidget(QLabel("Channel:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.setFixedWidth(60)
        layout.addWidget(self.channel_spin)
        
        layout.addWidget(QLabel("Layer:"))
        self.layer_spin = QSpinBox()
        self.layer_spin.setRange(1, 20)
        self.layer_spin.setValue(1)
        self.layer_spin.setFixedWidth(60)
        layout.addWidget(self.layer_spin)
        
        # Media combo
        layout.addWidget(QLabel("Media:"))
        self.media_combo = QComboBox()
        self.media_combo.setEditable(True)
        self.media_combo.setMinimumWidth(180)
        self.media_combo.setPlaceholderText("Media file...")
        layout.addWidget(self.media_combo)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # AMCP commands
        commands_layout = QHBoxLayout()
        commands_layout.setSpacing(5)
        
        load_btn = QPushButton("LOAD")
        load_btn.setFixedSize(60, 35)
        load_btn.clicked.connect(lambda: self._send_amcp_command("LOAD"))
        commands_layout.addWidget(load_btn)
        
        play_btn = QPushButton("PLAY")
        play_btn.setFixedSize(60, 35)
        play_btn.clicked.connect(lambda: self._send_amcp_command("PLAY"))
        commands_layout.addWidget(play_btn)
        
        stop_btn = QPushButton("STOP")
        stop_btn.setFixedSize(60, 35)
        stop_btn.clicked.connect(lambda: self._send_amcp_command("STOP"))
        commands_layout.addWidget(stop_btn)
        
        info_btn = QPushButton("INFO")
        info_btn.setFixedSize(60, 35)
        info_btn.clicked.connect(lambda: self._send_amcp_command("INFO"))
        commands_layout.addWidget(info_btn)
        
        layout.addLayout(commands_layout)
        layout.addStretch()
        
        # Console button
        console_btn = QPushButton("💻 Console")
        console_btn.setFixedSize(90, 35)
        console_btn.clicked.connect(self._open_console)
        layout.addWidget(console_btn)
        
        return section

    def _create_enhanced_players_section(self):
        """Create enhanced players section with better layout"""
        section = QGroupBox("📺 Video Players & Transport Control")
        section_layout = QVBoxLayout(section)
        section_layout.setSpacing(8)
        section_layout.setContentsMargins(10, 15, 10, 8)
        
        # Players container
        players_container = QHBoxLayout()
        players_container.setSpacing(5)
        
        # ========================
        # PREVIEW PLAYER
        # ========================
        preview_container = QWidget()
        preview_container.setFixedWidth(520)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(3)
        
        # Preview header
        preview_header = QLabel("🎬 PREVIEW")
        preview_header.setFixedHeight(40)
        preview_header.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px 8px 0 0;
            }
        """)
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)
        
        # Preview player
        self.preview_player = EnhancedVideoPlayer("Preview Player")
        self.preview_player.setStyleSheet("""
            EnhancedVideoPlayer {
                border-left: 3px solid #2196F3;
                border-right: 3px solid #2196F3;
                border-bottom: 3px solid #2196F3;
                border-radius: 0 0 8px 8px;
            }
        """)
        preview_layout.addWidget(self.preview_player)
        
        # Preview controls
        preview_controls = QWidget()
        preview_controls.setFixedHeight(50)
        preview_controls_layout = QHBoxLayout(preview_controls)
        preview_controls_layout.setContentsMargins(8, 15, 8, 5)
        preview_controls_layout.setSpacing(8)
        
        cue_btn = QPushButton("🎯 CUE")
        cue_btn.setFixedSize(70, 35)
        cue_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        cue_btn.clicked.connect(self._cue_preview)
        preview_controls_layout.addWidget(cue_btn)
        
        self.auto_audio_btn = QPushButton("🎵 Auto Audio")
        self.auto_audio_btn.setCheckable(True)
        self.auto_audio_btn.setChecked(True)
        self.auto_audio_btn.setFixedSize(110, 35)
        self.auto_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        self.auto_audio_btn.toggled.connect(self._toggle_auto_audio)
        preview_controls_layout.addWidget(self.auto_audio_btn)
        
        library_btn = QPushButton("📚 Library")
        library_btn.setFixedSize(80, 35)
        library_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #AB47BC;
            }
        """)
        library_btn.clicked.connect(self._open_media_library)
        preview_controls_layout.addWidget(library_btn)
        
        preview_controls_layout.addStretch()
        preview_layout.addWidget(preview_controls)
        
        players_container.addWidget(preview_container)
        
        # ========================
        # CENTER TRANSPORT CONTROLS
        # ========================
        center_container = QWidget()
        center_container.setFixedWidth(80)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(5, 0, 5, 0)
        center_layout.setSpacing(8)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_layout.addStretch(1)
        
        # Send to Program
        send_btn = QPushButton("➡️\nSEND TO\nPROGRAM")
        send_btn.setFixedSize(70, 55)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #1976D2;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        send_btn.clicked.connect(self._send_to_program)
        center_layout.addWidget(send_btn)
        
        # TAKE TO AIR (main button)
        take_btn = QPushButton("📺\nTAKE TO\nAIR")
        take_btn.setFixedSize(70, 65)
        take_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 10px;
                border: 3px solid #AD1457;
            }
            QPushButton:hover {
                background-color: #C2185B;
            }
        """)
        take_btn.clicked.connect(self._take_to_air)
        center_layout.addWidget(take_btn)
        
        # Fade/Cut buttons
        fade_cut_layout = QHBoxLayout()
        fade_cut_layout.setSpacing(4)
        
        fade_btn = QPushButton("🌅\nFADE")
        fade_btn.setFixedSize(32, 40)
        fade_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #AB47BC;
            }
        """)
        fade_btn.clicked.connect(lambda: self._fade_program(fade=True))
        fade_cut_layout.addWidget(fade_btn)
        
        cut_btn = QPushButton("✂️\nCUT")
        cut_btn.setFixedSize(32, 40)
        cut_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F4511E;
            }
        """)
        cut_btn.clicked.connect(lambda: self._fade_program(fade=False))
        fade_cut_layout.addWidget(cut_btn)
        
        center_layout.addLayout(fade_cut_layout)
        center_layout.addStretch(2)
        
        players_container.addWidget(center_container)
        
        # ========================
        # PROGRAM PLAYER
        # ========================
        program_container = QWidget()
        program_container.setFixedWidth(520)
        program_layout = QVBoxLayout(program_container)
        program_layout.setContentsMargins(0, 0, 0, 0)
        program_layout.setSpacing(3)
        
        # Program header
        program_header = QLabel("📺 PROGRAM")
        program_header.setFixedHeight(40)
        program_header.setStyleSheet("""
            QLabel {
                background-color: #F44336;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px 8px 0 0;
            }
        """)
        program_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        program_layout.addWidget(program_header)
        
        # Program player
        self.program_player = EnhancedVideoPlayer("Program Player")
        self.program_player.setStyleSheet("""
            EnhancedVideoPlayer {
                border-left: 3px solid #F44336;
                border-right: 3px solid #F44336;
                border-bottom: 3px solid #F44336;
                border-radius: 0 0 8px 8px;
            }
        """)
        program_layout.addWidget(self.program_player)
        
        # Program status
        program_status = QWidget()
        program_status.setFixedHeight(50)
        program_status_layout = QHBoxLayout(program_status)
        program_status_layout.setContentsMargins(8, 15, 8, 5)
        program_status_layout.setSpacing(12)
        
        # Audio status
        self.audio_status_label = QLabel("🟢 Audio Ready")
        self.audio_status_label.setFixedHeight(35)
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                padding: 8px 12px;
                background-color: rgba(76, 175, 80, 0.15);
                border-radius: 6px;
                border: 2px solid #4CAF50;
                font-size: 11px;
            }
        """)
        program_status_layout.addWidget(self.audio_status_label)
        
        program_status_layout.addStretch()
        
        # ON AIR indicator
        self.on_air_label = QLabel("🔴 OFF AIR")
        self.on_air_label.setFixedHeight(35)
        self.on_air_label.setStyleSheet("""
            QLabel {
                color: #757575; 
                font-weight: bold; 
                padding: 8px 12px;
                background-color: rgba(117, 117, 117, 0.15);
                border-radius: 6px;
                border: 2px solid #757575;
                font-size: 11px;
            }
        """)
        program_status_layout.addWidget(self.on_air_label)
        
        program_layout.addWidget(program_status)
        
        players_container.addWidget(program_container)
        
        section_layout.addLayout(players_container)
        
        return section

    def _create_compact_log_section(self):
        """Create compact log section"""
        section = QGroupBox("📋 Professional System Activity Log")
        section.setFixedHeight(140)
        layout = QVBoxLayout(section)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 3, 8, 3)
        
        # Log controls
        log_toolbar = QHBoxLayout()
        log_toolbar.setSpacing(5)
        
        # Filter buttons
        self.log_filter_all = QPushButton("All")
        self.log_filter_all.setCheckable(True)
        self.log_filter_all.setChecked(True)
        self.log_filter_all.setFixedSize(35, 20)
        self.log_filter_all.setStyleSheet("font-size: 9px; padding: 2px;")
        log_toolbar.addWidget(self.log_filter_all)
        
        self.log_filter_error = QPushButton("Err")
        self.log_filter_error.setCheckable(True)
        self.log_filter_error.setFixedSize(35, 20)
        self.log_filter_error.setStyleSheet("font-size: 9px; padding: 2px;")
        log_toolbar.addWidget(self.log_filter_error)
        
        self.log_filter_amcp = QPushButton("AMCP")
        self.log_filter_amcp.setCheckable(True)
        self.log_filter_amcp.setFixedSize(45, 20)
        self.log_filter_amcp.setStyleSheet("font-size: 9px; padding: 2px;")
        log_toolbar.addWidget(self.log_filter_amcp)
        
        self.log_filter_audio = QPushButton("AUDIO")
        self.log_filter_audio.setCheckable(True)
        self.log_filter_audio.setFixedSize(50, 20)
        self.log_filter_audio.setStyleSheet("font-size: 9px; padding: 2px;")
        log_toolbar.addWidget(self.log_filter_audio)
        
        log_toolbar.addStretch()
        
        # Clear and save
        clear_log_btn = QPushButton("Clear")
        clear_log_btn.setFixedSize(45, 20)
        clear_log_btn.setStyleSheet("font-size: 9px; padding: 2px;")
        clear_log_btn.clicked.connect(self._clear_log)
        log_toolbar.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("Save")
        save_log_btn.setFixedSize(40, 20)
        save_log_btn.setStyleSheet("font-size: 9px; padding: 2px;")
        save_log_btn.clicked.connect(self._save_log)
        log_toolbar.addWidget(save_log_btn)
        
        layout.addLayout(log_toolbar)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FF00;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 3px;
            }
        """)
        layout.addWidget(self.log_text)
        
        return section
    
    def _apply_professional_styling(self):
        """Apply professional broadcast styling"""
        self.setStyleSheet("""
            /* Main widget styling */
            QWidget {
                background-color: #2b2b2b;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            
            /* Button styling */
            QPushButton {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-weight: bold;
                font-size: 10px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00BCD4;
            }
            
            QPushButton:pressed {
                background-color: #353535;
            }
            
            QPushButton:checked {
                background-color: #00BCD4;
                border-color: #00ACC1;
                color: white;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                border-color: #333;
                color: #666;
            }
            
            /* Labels */
            QLabel {
                color: #E0E0E0;
                font-size: 11px;
            }
            
            /* Group boxes */
            QGroupBox {
                background-color: #333;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #00BCD4;
            }
            
            /* ComboBox */
            QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
                color: #E0E0E0;
            }
            
            QComboBox:hover {
                border-color: #00BCD4;
            }
            
            /* LineEdit */
            QLineEdit {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
                color: #E0E0E0;
            }
            
            QLineEdit:hover {
                border-color: #00BCD4;
            }
            
            QLineEdit:focus {
                border-color: #00BCD4;
            }
        """)
    
    def _setup_connections(self):
        """Setup signal connections between components"""
        try:
            # Audio control panel connections
            if self.audio_control_panel:
                self.audio_control_panel.profile_changed.connect(self._on_audio_profile_changed)
                self.audio_control_panel.night_mode_toggled.connect(self._on_night_mode_changed)
                self.audio_control_panel.parameter_changed.connect(self._on_audio_parameter_changed)
            
            # Video player connections
            if self.preview_player:
                self.preview_player.media_loaded.connect(self._on_preview_media_loaded)
                self.preview_player.playback_state_changed.connect(self._on_preview_state_changed)
                self.preview_player.error_occurred.connect(self._on_player_error)
                # NEW: Connect media library request signal
                self.preview_player.media_library_requested.connect(self._handle_media_library_request)
            
            if self.program_player:
                self.program_player.media_loaded.connect(self._on_program_media_loaded)
                self.program_player.playback_state_changed.connect(self._on_program_state_changed)
                self.program_player.error_occurred.connect(self._on_player_error)
                # NEW: Connect media library request signal  
                self.program_player.media_library_requested.connect(self._handle_media_library_request)
            
            # External signals
            if self.preview_player:
                self.preview_player.media_loaded.connect(self.media_loaded.emit)
            if self.program_player:
                self.program_player.media_loaded.connect(self.media_loaded.emit)
            
            self.logger.info("Signal connections established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup connections: {e}")
    
    def _handle_media_library_request(self):
        """Handle request for media library files - NEW"""
        try:
            if self.media_library_tab and hasattr(self.media_library_tab, 'media_library'):
                # Get current filtered files from media library
                current_search = ""
                current_filters = {}
                
                # Try to get current search text
                if hasattr(self.media_library_tab, 'search_input') and self.media_library_tab.search_input:
                    current_search = self.media_library_tab.search_input.text().strip()
                
                # Try to get current category filter
                if hasattr(self.media_library_tab, 'category_list') and self.media_library_tab.category_list:
                    current_item = self.media_library_tab.category_list.currentItem()
                    if current_item and current_item.text() != "Бүх медиа":
                        current_filters["category"] = current_item.text()
                
                # Try to get current type filter
                if hasattr(self.media_library_tab, 'type_combo') and self.media_library_tab.type_combo:
                    type_filter = self.media_library_tab.type_combo.currentText()
                    if type_filter != "Бүх төрөл":
                        from media_library_tab import MediaType
                        type_map = {
                            "Видео": MediaType.VIDEO,
                            "Аудио": MediaType.AUDIO,
                            "Зураг": MediaType.IMAGE
                        }
                        if type_filter in type_map:
                            current_filters["media_type"] = type_map[type_filter]
                
                # Get filtered media files
                media_files = self.media_library_tab.media_library.search_media(
                    current_search, current_filters
                )
                
                # Send to the requesting player
                sender = self.sender()
                if sender:
                    sender.set_media_library_files(media_files)
                    self._add_log_entry("LIBRARY", f"Loaded {len(media_files)} files from Media Library", "#9C27B0")
                else:
                    self._add_log_entry("WARNING", "Could not identify requesting player", "#FF9800")
                    
            else:
                self._add_log_entry("ERROR", "Media Library not available", "#F44336")
                
        except Exception as e:
            self.logger.error(f"Failed to handle media library request: {e}")
            self._add_log_entry("ERROR", f"Media Library request failed: {e}", "#F44336")
    
    def _initialize_log(self):
        """Initialize the system log"""
        if self.log_text:
            self._add_log_entry("SYSTEM", "Enhanced Professional Playout System initialized", "#00BCD4")
            self._add_log_entry("SYSTEM", f"VLC Available: {'Yes' if VLC_AVAILABLE else 'No'}", "#00BCD4")
            self._add_log_entry("SYSTEM", f"Audio System: {'Active' if AUDIO_SYSTEM_AVAILABLE and self.audio_system else 'Unavailable'}", "#00BCD4")
            self._add_log_entry("SYSTEM", "Ready for professional broadcast operations", "#00BCD4")
            self._add_log_entry("LIBRARY", "Media Library integration enabled", "#9C27B0")
    
    # ========================
    # PLAYER CONTROL METHODS
    # ========================
    
    def _cue_preview(self):
        """Cue preview to first frame"""
        if self.preview_player and self.preview_player.current_media_path:
            self.preview_player.stop()
            self._add_log_entry("SYSTEM", "Preview cued to first frame", "#00BCD4")
        else:
            self._add_log_entry("WARNING", "No media in preview to cue", "#FF9800")
    
    def _send_to_program(self):
        """Send preview content to program player"""
        if not self.preview_player or not self.program_player:
            return
            
        preview_file = self.preview_player.get_current_file()
        if preview_file:
            if self.program_player.load_media(preview_file):
                if self.auto_audio_enabled:
                    self._sync_audio_to_content(preview_file)
                
                self._add_log_entry("SUCCESS", f"Media sent to program: {Path(preview_file).name}", "#4CAF50")
                
                # Update media combo
                if self.media_combo:
                    self.media_combo.setCurrentText(Path(preview_file).name)
            else:
                self._add_log_entry("ERROR", "Failed to send media to program", "#F44336")
        else:
            self._add_log_entry("WARNING", "No media in preview to send", "#FF9800")
    
    def _take_to_air(self):
        """Take program content to air"""
        if not self.program_player:
            return
            
        program_file = self.program_player.get_current_file()
        if program_file:
            self.is_on_air = True
            self._update_on_air_status(True)
            
            if not self.program_player.is_playing:
                self.program_player.play()
            
            if self.amcp_connected:
                self._send_amcp_command("PLAY")
            
            self.media_taken_to_air.emit(program_file)
            self._add_log_entry("SUCCESS", f"🚨 TAKEN TO AIR: {Path(program_file).name}", "#E91E63")
        else:
            self._add_log_entry("WARNING", "No program content to take to air", "#FF9800")
    
    def _fade_program(self, fade=True):
        """Fade or cut program off air"""
        if self.is_on_air:
            self.is_on_air = False
            self._update_on_air_status(False)
            
            if fade:
                self._add_log_entry("SYSTEM", "Program FADED off air", "#9C27B0")
            else:
                if self.program_player:
                    self.program_player.stop()
                self._add_log_entry("SYSTEM", "Program CUT off air", "#FF5722")
            
            if self.amcp_connected:
                self._send_amcp_command("STOP")
        else:
            self._add_log_entry("WARNING", "No program on air to fade", "#FF9800")
    
    def _update_on_air_status(self, on_air):
        """Update ON AIR visual indicators"""
        if not self.on_air_label:
            return
            
        if on_air:
            self.on_air_label.setText("🔴 ON AIR")
            self.on_air_label.setStyleSheet("""
                QLabel {
                    color: white; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: #F44336;
                    border-radius: 6px;
                    border: 2px solid #F44336;
                    font-size: 11px;
                }
            """)
        else:
            self.on_air_label.setText("🔴 OFF AIR")
            self.on_air_label.setStyleSheet("""
                QLabel {
                    color: #757575; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: rgba(117, 117, 117, 0.15);
                    border-radius: 6px;
                    border: 2px solid #757575;
                    font-size: 11px;
                }
            """)
    
    def _toggle_auto_audio(self, enabled):
        """Toggle automatic audio profile detection"""
        self.auto_audio_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self._add_log_entry("AUDIO", f"Auto audio detection {status}", "#9C27B0")
        
        if enabled and self.program_player and self.program_player.current_media_path:
            self._sync_audio_to_content(str(self.program_player.current_media_path))
    
    def _sync_audio_to_content(self, file_path):
        """Automatically sync audio profile to content type"""
        if not self.auto_audio_enabled or not self.audio_control_panel:
            return
        
        try:
            file_name = Path(file_path).name.lower()
            
            if any(word in file_name for word in ['movie', 'film', 'cinema']):
                self.audio_control_panel._apply_preset("movie")
                self._add_log_entry("AUDIO", "Auto-detected: Movie content - Applied movie audio profile", "#9C27B0")
            elif any(word in file_name for word in ['music', 'song', 'audio']):
                self.audio_control_panel._apply_preset("music")
                self._add_log_entry("AUDIO", "Auto-detected: Music content - Applied music audio profile", "#9C27B0")
            elif any(word in file_name for word in ['news', 'report', 'interview']):
                self.audio_control_panel._apply_preset("news")
                self._add_log_entry("AUDIO", "Auto-detected: News content - Applied news audio profile", "#9C27B0")
            elif any(word in file_name for word in ['sport', 'game', 'match']):
                self.audio_control_panel._apply_preset("sports")
                self._add_log_entry("AUDIO", "Auto-detected: Sports content - Applied sports audio profile", "#9C27B0")
            else:
                self.audio_control_panel._apply_preset("default")
                self._add_log_entry("AUDIO", "Auto-detected: General content - Applied default audio profile", "#9C27B0")
                
        except Exception as e:
            self.logger.error(f"Failed to sync audio to content: {e}")
    
    def _open_media_library(self):
        """Open media library dialog - ENHANCED"""
        try:
            if self.media_library_tab:
                self._add_log_entry("LIBRARY", "Requesting files from Media Library", "#9C27B0")
                self._handle_media_library_request()
            else:
                # Fallback to file dialog
                self._add_log_entry("SYSTEM", "Media library opened (file dialog fallback)", "#00BCD4")
                
                file_dialog = QFileDialog(self)
                file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
                file_dialog.setWindowTitle("Select Media File")
                
                video_exts = "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.m4v"
                audio_exts = "*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma"
                all_media = f"{video_exts} {audio_exts}"
                
                file_dialog.setNameFilter(f"All Media ({all_media});;Video Files ({video_exts});;Audio Files ({audio_exts})")
                
                if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                    selected_files = file_dialog.selectedFiles()
                    if selected_files and self.preview_player:
                        self.preview_player.load_media(selected_files[0])
                        
        except Exception as e:
            self._add_log_entry("ERROR", f"Failed to open media library: {e}", "#F44336")
    
    # ========================
    # AMCP CONTROL METHODS
    # ========================
    
    def _connect_amcp(self):
        """Connect to AMCP server"""
        self.amcp_connected = True
        if self.amcp_status_label:
            self.amcp_status_label.setText("🟢 Connected")
            self.amcp_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        
        if self.connect_btn:
            self.connect_btn.setEnabled(False)
        if self.disconnect_btn:
            self.disconnect_btn.setEnabled(True)
        
        self._add_log_entry("AMCP", "Connected to AMCP server", "#2196F3")
    
    def _disconnect_amcp(self):
        """Disconnect from AMCP server"""
        self.amcp_connected = False
        if self.amcp_status_label:
            self.amcp_status_label.setText("🔴 Disconnected")
            self.amcp_status_label.setStyleSheet("color: #F44336; font-weight: bold; font-size: 12px;")
        
        if self.connect_btn:
            self.connect_btn.setEnabled(True)
        if self.disconnect_btn:
            self.disconnect_btn.setEnabled(False)
        
        self._add_log_entry("AMCP", "Disconnected from AMCP server", "#2196F3")
    
    def _send_amcp_command(self, command):
        """Send AMCP command"""
        if self.amcp_connected:
            channel = self.channel_spin.value() if self.channel_spin else 1
            layer = self.layer_spin.value() if self.layer_spin else 1
            media = self.media_combo.currentText() if self.media_combo else ""
            
            if command == "LOAD" and media:
                full_command = f"LOAD {channel}-{layer} {media}"
            elif command == "PLAY":
                full_command = f"PLAY {channel}-{layer}"
            elif command == "STOP":
                full_command = f"STOP {channel}-{layer}"
            elif command == "INFO":
                full_command = f"INFO {channel}-{layer}"
            else:
                full_command = command
            
            self._add_log_entry("AMCP", f"SENT: {full_command}", "#2196F3")
        else:
            self._add_log_entry("ERROR", "Not connected to AMCP server", "#F44336")
    
    def _open_console(self):
        """Open AMCP console dialog"""
        self._add_log_entry("SYSTEM", "AMCP console opened", "#00BCD4")
    
    # ========================
    # LOG METHODS
    # ========================
    
    def _add_log_entry(self, level, message, color="#E0E0E0"):
        """Add entry to log"""
        if not self.log_text:
            return
            
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format with color
        formatted_entry = f'<span style="color: {color};">[{timestamp}] {level}:</span> {message}'
        self.log_text.append(formatted_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _clear_log(self):
        """Clear log"""
        if self.log_text:
            self.log_text.clear()
            self._add_log_entry("SYSTEM", "Log cleared", "#00BCD4")
    
    def _save_log(self):
        """Save log to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Log", "", "Text Files (*.txt);;All Files (*)"
            )
            if file_path and self.log_text:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self._add_log_entry("SYSTEM", f"Log saved to: {file_path}", "#00BCD4")
        except Exception as e:
            self._add_log_entry("ERROR", f"Failed to save log: {e}", "#F44336")
    
    # ========================
    # SIGNAL HANDLERS
    # ========================
    
    def _on_audio_profile_changed(self, profile_name):
        """Handle audio profile change"""
        self._add_log_entry("AUDIO", f"Audio profile changed to: {profile_name}", "#9C27B0")
        self.audio_profile_changed.emit(profile_name)
    
    def _on_night_mode_changed(self, enabled):
        """Handle night mode toggle"""
        status = "enabled" if enabled else "disabled"
        self._add_log_entry("AUDIO", f"Night mode {status}", "#9C27B0")
    
    def _on_audio_parameter_changed(self, param_name, value):
        """Handle audio parameter changes"""
        self.logger.debug(f"Audio parameter {param_name} changed to {value}")
    
    def _on_preview_media_loaded(self, file_path):
        """Handle preview media loaded"""
        file_name = Path(file_path).name
        self._add_log_entry("SUCCESS", f"Preview loaded: {file_name}", "#4CAF50")
        
        if self.auto_audio_enabled:
            self._sync_audio_to_content(file_path)
    
    def _on_preview_state_changed(self, state):
        """Handle preview playback state change"""
        self.logger.debug(f"Preview state: {state}")
    
    def _on_program_media_loaded(self, file_path):
        """Handle program media loaded"""
        file_name = Path(file_path).name
        self._add_log_entry("SUCCESS", f"Program loaded: {file_name}", "#4CAF50")
        
        # Update media combo
        if self.media_combo:
            self.media_combo.setCurrentText(file_name)
        
        if self.auto_audio_enabled:
            self._sync_audio_to_content(file_path)
    
    def _on_program_state_changed(self, state):
        """Handle program playback state change"""
        self.logger.debug(f"Program state: {state}")
        
        if state == "ended" and self.is_on_air:
            self._add_log_entry("WARNING", "⚠️ Program media ended while on air", "#FF9800")
            self.is_on_air = False
            self._update_on_air_status(False)
    
    def _on_player_error(self, error_message):
        """Handle player errors"""
        self._add_log_entry("ERROR", f"Player error: {error_message}", "#F44336")
    
    # ========================
    # PUBLIC INTERFACE METHODS
    # ========================
    
    def get_current_state(self):
        """Get current playout state"""
        return {
            'on_air': self.is_on_air,
            'auto_audio': self.auto_audio_enabled,
            'preview': self.preview_player.get_playback_state() if self.preview_player else None,
            'program': self.program_player.get_playback_state() if self.program_player else None,
            'amcp_connected': self.amcp_connected,
            'audio_settings': self.audio_control_panel.get_current_settings() if self.audio_control_panel else None,
            'audio_system_active': AUDIO_SYSTEM_AVAILABLE and self.audio_system is not None,
            'media_library_integration': self.media_library_tab is not None
        }
    
    def load_preview_media(self, file_path):
        """Load media to preview player"""
        if self.preview_player:
            return self.preview_player.load_media(file_path)
        return False
    
    def load_program_media(self, file_path):
        """Load media to program player"""
        if self.program_player:
            return self.program_player.load_media(file_path)
        return False
    
    def emergency_stop(self):
        """Emergency stop - immediately cut all output"""
        try:
            if self.preview_player:
                self.preview_player.stop()
            if self.program_player:
                self.program_player.stop()
            
            self.is_on_air = False
            self._update_on_air_status(False)
            
            if self.amcp_connected:
                self._send_amcp_command("STOP")
            
            # Stop audio system
            if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
                self.audio_system.set_master_volume(0.0)
            
            self._add_log_entry("ERROR", "🚨 EMERGENCY STOP executed", "#F44336")
            self.logger.warning("Emergency stop executed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def cleanup(self):
        """Clean up resources when closing"""
        try:
            if self.preview_player:
                self.preview_player.stop()
                self.preview_player.cleanup()
            
            if self.program_player:
                self.program_player.stop()
                self.program_player.cleanup()
            
            if self.audio_control_panel:
                self.audio_control_panel.cleanup()
            
            if self.amcp_connected:
                self._disconnect_amcp()
            
            # Cleanup audio system
            if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
                try:
                    self.audio_system.deactivate()
                    if hasattr(self.audio_system, 'jack_server'):
                        self.audio_system.jack_server.stop()
                except Exception as e:
                    self.logger.error(f"Error cleaning up audio system: {e}")
            
            self._add_log_entry("SYSTEM", "Professional playout system shutdown complete", "#00BCD4")
            self.logger.info("Enhanced professional playout tab cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def refresh(self):
        """Refresh tab"""
        self._add_log_entry("SYSTEM", "Professional playout tab refreshed", "#00BCD4")
    
    def get_tab_name(self):
        """Get tab name for integration"""
        return "playout"
    
    def get_tab_status(self):
        """Get enhanced tab status"""
        return {
            "name": "playout",
            "status": "ready",
            "on_air": self.is_on_air,
            "vlc_available": VLC_AVAILABLE,
            "audio_system_available": AUDIO_SYSTEM_AVAILABLE,
            "audio_control": True,
            "amcp_available": True,
            "professional_features": True,
            "media_library_integration": self.media_library_tab is not None,
            "playlist_support": True
        }
    
    def execute_command(self, command, params=None):
        """Execute tab-specific command"""
        try:
            if command == "take_to_air":
                self._take_to_air()
                return {"status": "success", "message": "Media taken to air"}
            elif command == "emergency_stop":
                self.emergency_stop()
                return {"status": "success", "message": "Emergency stop executed"}
            elif command == "send_to_program":
                self._send_to_program()
                return {"status": "success", "message": "Media sent to program"}
            elif command == "load_preview" and params and "file_path" in params:
                success = self.load_preview_media(params["file_path"])
                return {"status": "success" if success else "error", "message": f"Preview load {'successful' if success else 'failed'}"}
            elif command == "load_program" and params and "file_path" in params:
                success = self.load_program_media(params["file_path"])
                return {"status": "success" if success else "error", "message": f"Program load {'successful' if success else 'failed'}"}
            elif command == "set_audio_profile" and params and "profile" in params:
                if self.audio_control_panel:
                    self.audio_control_panel._apply_preset(params["profile"])
                return {"status": "success", "message": f"Audio profile set to {params['profile']}"}
            elif command == "set_master_volume" and params and "volume" in params:
                if self.audio_control_panel:
                    self.audio_control_panel._on_volume_changed(params["volume"])
                return {"status": "success", "message": f"Master volume set to {params['volume']}%"}
            elif command == "load_media_library_playlist":
                self._handle_media_library_request()
                return {"status": "success", "message": "Media library playlist loaded"}
            elif command == "play_next" and params and "player" in params:
                player = self.preview_player if params["player"] == "preview" else self.program_player
                if player and hasattr(player, 'play_next'):
                    player.play_next()
                    return {"status": "success", "message": "Advanced to next media"}
                return {"status": "error", "message": "Player not found or no playlist"}
            elif command == "play_previous" and params and "player" in params:
                player = self.preview_player if params["player"] == "preview" else self.program_player
                if player and hasattr(player, 'play_previous'):
                    player.play_previous()
                    return {"status": "success", "message": "Advanced to previous media"}
                return {"status": "error", "message": "Player not found or no playlist"}
            else:
                return {"error": f"Unknown command: {command}"}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}"}
    
    def handle_system_event(self, event):
        """Handle incoming system event"""
        try:
            if hasattr(event, 'event_type') and hasattr(event, 'data'):
                if event.event_type == "media_loaded":
                    if event.data.get("file_path") and not self.preview_player.current_media_path:
                        self.load_preview_media(event.data["file_path"])
                elif event.event_type == "stream_started":
                    self._add_log_entry("SYSTEM", "External stream started", "#00BCD4")
                elif event.event_type == "emergency_stop":
                    self.emergency_stop()
                elif event.event_type == "audio_profile_change":
                    if self.audio_control_panel and event.data.get("profile"):
                        self.audio_control_panel._apply_preset(event.data["profile"])
                elif event.event_type == "media_library_updated":
                    self._add_log_entry("LIBRARY", "Media library updated", "#9C27B0")
        except Exception as e:
            self.logger.error(f"Error handling system event: {e}")

    def _stream_program_content(self):
        """Stream current program content to streaming tab"""
        try:
            if not self.program_player or not self.program_player.current_media_path:
                self._add_log_entry("ERROR", "No program content to stream", "#F44336")
                return False
                
            program_file = str(self.program_player.current_media_path)
            
            # Check if file exists
            if not Path(program_file).exists():
                self._add_log_entry("ERROR", f"Program file not found: {program_file}", "#F44336")
                return False
            
            # Signal to main window to start streaming with this file
            self.stream_program_requested.emit(program_file)
            
            self._add_log_entry("SUCCESS", f"🚀 Streaming program content: {Path(program_file).name}", "#00BCD4")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stream program content: {e}")
            self._add_log_entry("ERROR", f"Streaming failed: {e}", "#F44336")
            return False

    def _stream_current_program_auto(self):
        """Automatically stream current program content when on air"""
        try:
            if not self.is_on_air:
                return False
                
            return self._stream_program_content()
            
        except Exception as e:
            self.logger.error(f"Auto streaming failed: {e}")
            return False

    def _stop_program_streaming(self):
        """Stop streaming program content"""
        try:
            # Signal to main window to stop streaming
            self.stream_status_changed.emit(False, "Program streaming stopped")
            self._add_log_entry("SYSTEM", "🛑 Program streaming stopped", "#FF5722")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
            return False

    # ========================
    # MODIFIED TAKE TO AIR FUNCTION
    # ========================

    def _take_to_air(self):
        """Take program content to air and start streaming automatically"""
        if not self.program_player:
            self._add_log_entry("ERROR", "Program player not available", "#F44336")
            return
            
        program_file = self.program_player.get_current_file()
        if program_file:
            # Set on air status
            self.is_on_air = True
            self._update_on_air_status(True)
            
            # Start playing if not already playing
            if not self.program_player.is_playing:
                self.program_player.play()
            
            # Automatically start streaming the program content
            streaming_success = self._stream_program_content()
            
            # Send AMCP command if connected
            if self.amcp_connected:
                self._send_amcp_command("PLAY")
            
            # Emit signals
            self.media_taken_to_air.emit(program_file)
            
            # Log with streaming status
            if streaming_success:
                self._add_log_entry("SUCCESS", f"🚨 TAKEN TO AIR & STREAMING: {Path(program_file).name}", "#E91E63")
            else:
                self._add_log_entry("WARNING", f"🚨 TAKEN TO AIR (Streaming failed): {Path(program_file).name}", "#FF9800")
        else:
            self._add_log_entry("WARNING", "No program content to take to air", "#FF9800")

    # ========================
    # MODIFIED FADE PROGRAM FUNCTION
    # ========================

    def _fade_program(self, fade=True):
        """Fade or cut program off air and stop streaming"""
        if self.is_on_air:
            self.is_on_air = False
            self._update_on_air_status(False)
            
            # Stop streaming
            self._stop_program_streaming()
            
            if fade:
                self._add_log_entry("SYSTEM", "Program FADED off air & streaming stopped", "#9C27B0")
            else:
                if self.program_player:
                    self.program_player.stop()
                self._add_log_entry("SYSTEM", "Program CUT off air & streaming stopped", "#FF5722")
            
            if self.amcp_connected:
                self._send_amcp_command("STOP")
        else:
            self._add_log_entry("WARNING", "No program on air to fade", "#FF9800")

    # ========================
    # UI MODIFICATIONS - CENTER TRANSPORT CONTROLS SECTION
    # ========================

    def _create_enhanced_center_controls(self):
        """Create enhanced center controls with streaming support"""
        center_container = QWidget()
        center_container.setFixedWidth(80)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(5, 0, 5, 0)
        center_layout.setSpacing(6)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_layout.addStretch(1)
        
        # Send to Program
        send_btn = QPushButton("➡️\nSEND TO\nPROGRAM")
        send_btn.setFixedSize(70, 45)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 6px;
                border: 2px solid #1976D2;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        send_btn.clicked.connect(self._send_to_program)
        center_layout.addWidget(send_btn)
        
        # Stream Program Button - НЭМ
        stream_btn = QPushButton("📡\nSTREAM\nPROGRAM")
        stream_btn.setFixedSize(70, 45)
        stream_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 6px;
                border: 2px solid #7B1FA2;
            }
            QPushButton:hover {
                background-color: #AB47BC;
            }
        """)
        stream_btn.clicked.connect(self._stream_program_content)
        center_layout.addWidget(stream_btn)
        
        # TAKE TO AIR (main button) - ENHANCED
        take_btn = QPushButton("📺\nTAKE TO AIR\n& STREAM")
        take_btn.setFixedSize(70, 65)
        take_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 10px;
                border: 3px solid #AD1457;
            }
            QPushButton:hover {
                background-color: #C2185B;
            }
        """)
        take_btn.clicked.connect(self._take_to_air)
        center_layout.addWidget(take_btn)
        
        # Fade/Cut buttons - ENHANCED
        fade_cut_layout = QHBoxLayout()
        fade_cut_layout.setSpacing(4)
        
        fade_btn = QPushButton("🌅\nFADE\n& STOP")
        fade_btn.setFixedSize(32, 40)
        fade_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 7px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #AB47BC;
            }
        """)
        fade_btn.clicked.connect(lambda: self._fade_program(fade=True))
        fade_cut_layout.addWidget(fade_btn)
        
        cut_btn = QPushButton("✂️\nCUT\n& STOP")
        cut_btn.setFixedSize(32, 40)
        cut_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-size: 7px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F4511E;
            }
        """)
        cut_btn.clicked.connect(lambda: self._fade_program(fade=False))
        fade_cut_layout.addWidget(cut_btn)
        
        center_layout.addLayout(fade_cut_layout)
        center_layout.addStretch(2)
        
        return center_container

    # ========================
    # PROGRAM STATUS ENHANCEMENT WITH STREAMING INFO
    # ========================

    def _create_enhanced_program_status(self):
        """Create enhanced program status with streaming information"""
        program_status = QWidget()
        program_status.setFixedHeight(50)
        program_status_layout = QHBoxLayout(program_status)
        program_status_layout.setContentsMargins(8, 15, 8, 5)
        program_status_layout.setSpacing(8)
        
        # Audio status
        self.audio_status_label = QLabel("🟢 Audio Ready")
        self.audio_status_label.setFixedHeight(35)
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                padding: 6px 10px;
                background-color: rgba(76, 175, 80, 0.15);
                border-radius: 6px;
                border: 2px solid #4CAF50;
                font-size: 10px;
            }
        """)
        program_status_layout.addWidget(self.audio_status_label)
        
        # Streaming status - НЭМ
        self.streaming_status_label = QLabel("🔴 Not Streaming")
        self.streaming_status_label.setFixedHeight(35)
        self.streaming_status_label.setStyleSheet("""
            QLabel {
                color: #757575;
                font-weight: bold;
                padding: 6px 10px;
                background-color: rgba(117, 117, 117, 0.15);
                border-radius: 6px;
                border: 2px solid #757575;
                font-size: 10px;
            }
        """)
        program_status_layout.addWidget(self.streaming_status_label)
        
        program_status_layout.addStretch()
        
        # ON AIR indicator
        self.on_air_label = QLabel("🔴 OFF AIR")
        self.on_air_label.setFixedHeight(35)
        self.on_air_label.setStyleSheet("""
            QLabel {
                color: #757575; 
                font-weight: bold; 
                padding: 6px 10px;
                background-color: rgba(117, 117, 117, 0.15);
                border-radius: 6px;
                border: 2px solid #757575;
                font-size: 10px;
            }
        """)
        program_status_layout.addWidget(self.on_air_label)
        
        return program_status

    # ========================
    # STREAMING STATUS UPDATE FUNCTIONS
    # ========================

    def _update_streaming_status(self, is_streaming, message=""):
        """Update streaming status display"""
        if not hasattr(self, 'streaming_status_label') or not self.streaming_status_label:
            return
            
        if is_streaming:
            self.streaming_status_label.setText("🟢 Streaming")
            self.streaming_status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 6px 10px;
                    background-color: rgba(76, 175, 80, 0.15);
                    border-radius: 6px;
                    border: 2px solid #4CAF50;
                    font-size: 10px;
                }
            """)
        else:
            self.streaming_status_label.setText("🔴 Not Streaming")
            self.streaming_status_label.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-weight: bold;
                    padding: 6px 10px;
                    background-color: rgba(117, 117, 117, 0.15);
                    border-radius: 6px;
                    border: 2px solid #757575;
                    font-size: 10px;
                }
            """)

    def _on_streaming_status_changed(self, is_streaming, stream_key=""):
        """Handle streaming status change from main window"""
        self._update_streaming_status(is_streaming)
        
        if is_streaming:
            self._add_log_entry("SUCCESS", f"🚀 Program streaming started: {stream_key}", "#9C27B0")
        else:
            self._add_log_entry("SYSTEM", "🛑 Program streaming stopped", "#FF5722")

    # ========================
    # EMERGENCY STOP WITH STREAMING
    # ========================

    def emergency_stop(self):
        """Emergency stop - immediately cut all output including streaming"""
        try:
            # Stop players
            if self.preview_player:
                self.preview_player.stop()
            if self.program_player:
                self.program_player.stop()
            
            # Stop streaming
            self._stop_program_streaming()
            
            # Update status
            self.is_on_air = False
            self._update_on_air_status(False)
            self._update_streaming_status(False)
            
            # AMCP stop
            if self.amcp_connected:
                self._send_amcp_command("STOP")
            
            # Audio system stop
            if AUDIO_SYSTEM_AVAILABLE and self.audio_system:
                self.audio_system.set_master_volume(0.0)
            
            self._add_log_entry("ERROR", "🚨 EMERGENCY STOP executed - All output stopped", "#F44336")
            self.logger.warning("Emergency stop executed with streaming")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")

    # ========================
    # COMMAND EXECUTION ENHANCEMENT
    # ========================

    def execute_command(self, command, params=None):
        """Execute tab-specific command with streaming support"""
        try:
            if command == "take_to_air":
                self._take_to_air()
                return {"status": "success", "message": "Media taken to air and streaming started"}
            elif command == "stream_program":
                success = self._stream_program_content()
                return {"status": "success" if success else "error", "message": f"Program streaming {'started' if success else 'failed'}"}
            elif command == "stop_streaming":
                success = self._stop_program_streaming()
                return {"status": "success" if success else "error", "message": f"Streaming {'stopped' if success else 'stop failed'}"}
            elif command == "emergency_stop":
                self.emergency_stop()
                return {"status": "success", "message": "Emergency stop executed with streaming"}
            # ... existing commands ...
            else:
                return {"error": f"Unknown command: {command}"}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}"}

    # ========================
    # INTEGRATION FUNCTIONS FOR MAIN WINDOW
    # ========================

    def connect_to_streaming_tab(self, streaming_tab):
        """Connect playout tab to streaming tab for integration"""
        try:
            if hasattr(self, 'stream_program_requested'):
                self.stream_program_requested.connect(
                    lambda file_path: streaming_tab.load_and_start_stream(file_path)
                )
            
            if hasattr(streaming_tab, 'stream_status_changed'):
                streaming_tab.stream_status_changed.connect(self._on_streaming_status_changed)
            
            self._add_log_entry("SYSTEM", "🔗 Connected to streaming tab", "#00BCD4")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to streaming tab: {e}")
            return False


# Export classes for main window
__all__ = ['PlayoutTab', 'PLAYOUT_TAB_AVAILABLE', 'ProfessionalAudioControlPanel', 'EnhancedVideoPlayer', 'MediaPlaylist']