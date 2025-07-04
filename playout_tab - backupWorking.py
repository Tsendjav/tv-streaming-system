#!/usr/bin/env python3
"""
Enhanced Playout Tab with Clean Layout Design
Professional playout control with dual video players and refined styling
"""

import os
import sys
import json
import asyncio
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSignalBlocker
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
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'}
    SUPPORTED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False

# Audio System imports
try:
    from audio.tv_audio_engine import TVAudioSystem
    from audio.audio_profiles import AudioProfileManager
    AUDIO_SYSTEM_AVAILABLE = True
except ImportError:
    TVAudioSystem = None
    AudioProfileManager = None
    AUDIO_SYSTEM_AVAILABLE = False

# AMCP imports
try:
    from ui.tabs.components.amcp_command import AMCPCommand
    from core.amcp_protocol import AMCPProtocol
except ImportError:
    AMCPCommand = None
    AMCPProtocol = None

# =============================================================================
# SIMPLE VIDEO PLAYER WIDGET
# =============================================================================

class SimpleVideoPlayer(QWidget):
    """Simple video player widget for preview/program with fixed dimensions"""
    
    media_loaded = pyqtSignal(str)
    
    def __init__(self, player_name: str = "Player", parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.logger = get_logger(f"{__name__}.{player_name}")
        
        self.vlc_instance = None
        self.media_player = None
        self.current_media_path = None
        
        # Set fixed size for consistent layout
        self.setFixedHeight(380)  # Fixed height for all players
        self.setMinimumWidth(320)  # Minimum width
        
        self._init_vlc()
        self._init_ui()
    
    def _init_vlc(self):
        """Initialize VLC components"""
        if not VLC_AVAILABLE:
            self.logger.warning("VLC not available")
            return
        
        try:
            vlc_args = ['--no-xlib', '--quiet', '--intf', 'dummy']
            self.vlc_instance = vlc.Instance(vlc_args)
            self.media_player = self.vlc_instance.media_player_new()
            self.logger.debug(f"VLC initialized for {self.player_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize VLC: {e}")
    
    def _init_ui(self):
        """Initialize user interface with fixed dimensions"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Video frame with fixed aspect ratio
        self.video_frame = QFrame()
        self.video_frame.setFixedHeight(240)  # Fixed height for video area
        self.video_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e; 
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.video_frame)
        
        # Controls section with fixed height
        controls_widget = QWidget()
        controls_widget.setFixedHeight(135)  # Fixed height for controls
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(5)
        
        # Main control buttons
        main_controls_layout = QHBoxLayout()
        main_controls_layout.setSpacing(5)
        
        load_btn = QPushButton("📁 Load Media")
        load_btn.setFixedHeight(35)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        load_btn.clicked.connect(self.load_media_dialog)
        main_controls_layout.addWidget(load_btn)
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.setFixedHeight(35)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """)
        self.play_btn.clicked.connect(self.play)
        self.play_btn.setEnabled(False)
        main_controls_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setFixedHeight(35)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white; 
                padding: 5px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """)
        self.pause_btn.clicked.connect(self.pause)
        self.pause_btn.setEnabled(False)
        main_controls_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setFixedHeight(35)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336; 
                color: white; 
                padding: 5px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """)
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        main_controls_layout.addWidget(self.stop_btn)
        
        # Volume controls
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(5)
        
        volume_icon = QLabel("🔊")
        volume_icon.setFixedSize(20, 20)
        volume_layout.addWidget(volume_icon)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedHeight(20)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00BCD4;
                border: 1px solid #00BCD4;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
        """)
        self.volume_slider.valueChanged.connect(self._set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        # Audio routing label
        self.audio_label = QLabel("🔗 JACK")
        self.audio_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        self.audio_label.setFixedWidth(60)
        volume_layout.addWidget(self.audio_label)
        
        main_controls_layout.addLayout(volume_layout)
        controls_layout.addLayout(main_controls_layout)
        
        # Position slider and time - fixed height
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #B0BEC5; font-family: monospace;")
        self.time_label.setFixedWidth(100)
        progress_layout.addWidget(self.time_label)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setFixedHeight(20)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00BCD4;
                border: 1px solid #00BCD4;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -6px 0;
            }
        """)
        progress_layout.addWidget(self.position_slider)
        
        controls_layout.addLayout(progress_layout)
        
        layout.addWidget(controls_widget)
        
        # Show no media message
        self._show_no_media_message()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.start(100)
    
    def _show_no_media_message(self):
        """Show no media loaded message with better visibility"""
        # Clear any existing layout
        if self.video_frame.layout():
            QWidget().setLayout(self.video_frame.layout())
        
        overlay_layout = QVBoxLayout(self.video_frame)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setContentsMargins(20, 20, 20, 20)
        
        no_media_label = QLabel("No Media Loaded\nClick 'Load Media' to start")
        no_media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_media_label.setStyleSheet("""
            QLabel {
                color: #B0BEC5; 
                font-size: 14px; 
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        overlay_layout.addWidget(no_media_label)
    
    def load_media_dialog(self):
        """Open file dialog to load media"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Media File",
                "",
                "Video Files (*.mp4 *.avi *.mkv *.mov);;Audio Files (*.mp3 *.wav);;All Files (*)"
            )
            
            if file_path:
                self.load_media(file_path)
        except Exception as e:
            self.logger.error(f"Media dialog error: {e}")
    
    def load_media(self, file_path: Union[str, Path]):
        """Load media file"""
        if not VLC_AVAILABLE or not self.media_player:
            return False
        
        try:
            media_path = Path(file_path).resolve()
            
            if not media_path.exists():
                return False
            
            media = self.vlc_instance.media_new(str(media_path))
            self.media_player.set_media(media)
            self.current_media_path = media_path
            
            # Set video output
            if platform.system() == "Linux":
                self.media_player.set_xwindow(self.video_frame.winId())
            elif platform.system() == "Windows":
                self.media_player.set_hwnd(self.video_frame.winId())
            elif platform.system() == "Darwin":
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            self.media_loaded.emit(str(media_path))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load media: {e}")
            return False
    
    def play(self):
        """Start playback"""
        if self.media_player:
            self.media_player.play()
    
    def pause(self):
        """Pause playback"""
        if self.media_player:
            self.media_player.pause()
    
    def stop(self):
        """Stop playback"""
        if self.media_player:
            self.media_player.stop()
    
    def _set_volume(self, volume: int):
        """Set volume"""
        if self.media_player:
            self.media_player.audio_set_volume(volume)
    
    def _update_position(self):
        """Update position display"""
        if not self.media_player:
            return
        
        try:
            position = self.media_player.get_position()
            length = self.media_player.get_length()
            
            if length > 0:
                self.position_slider.setValue(int(position * 1000))
                current_time = position * length / 1000
                total_time = length / 1000
                time_text = f"{self._format_time(current_time)} / {self._format_time(total_time)}"
                self.time_label.setText(time_text)
        except:
            pass
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS"""
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_file(self) -> Optional[str]:
        """Get current file path"""
        return str(self.current_media_path) if self.current_media_path else None

# =============================================================================
# SIMPLIFIED AUDIO CONTROL PANEL
# =============================================================================

class AudioControlPanel(QGroupBox):
    """Simplified audio control panel with enhanced visuals"""
    
    def __init__(self, audio_system=None, config_manager=None, parent=None):
        super().__init__("🔊 Audio Processing", parent)
        self.audio_system = audio_system
        self.config_manager = config_manager
        self.logger = get_logger(f"{__name__}.AudioControlPanel")
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI with improved styling"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["default", "movie_mode", "music_mode", "news_mode", "sports_mode"])
        self.profile_combo.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5;")
        profile_layout.addWidget(self.profile_combo)
        
        self.night_mode_btn = QPushButton("🌙 Night Mode")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setStyleSheet("background-color: #757575; color: white; padding: 5px;")
        profile_layout.addWidget(self.night_mode_btn)
        
        profile_layout.addStretch()
        layout.addLayout(profile_layout)
        
        # Sliders
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(15)
        
        # Voice Clarity
        voice_group = QVBoxLayout()
        voice_group.addWidget(QLabel("🎤 Voice Clarity"))
        self.voice_clarity_slider = QSlider(Qt.Orientation.Vertical)
        self.voice_clarity_slider.setRange(0, 100)
        self.voice_clarity_slider.setValue(30)
        self.voice_clarity_slider.setMaximumHeight(100)
        self.voice_clarity_slider.setStyleSheet("QSlider::handle:vertical { background: #00BCD4; }")
        voice_group.addWidget(self.voice_clarity_slider)
        self.voice_clarity_label = QLabel("30%")
        self.voice_clarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.voice_clarity_label.setStyleSheet("color: #B0BEC5;")
        voice_group.addWidget(self.voice_clarity_label)
        sliders_layout.addLayout(voice_group)
        
        # Bass Boost
        bass_group = QVBoxLayout()
        bass_group.addWidget(QLabel("🔊 Bass Boost"))
        self.bass_boost_slider = QSlider(Qt.Orientation.Vertical)
        self.bass_boost_slider.setRange(-10, 20)
        self.bass_boost_slider.setValue(0)
        self.bass_boost_slider.setMaximumHeight(100)
        self.bass_boost_slider.setStyleSheet("QSlider::handle:vertical { background: #00BCD4; }")
        bass_group.addWidget(self.bass_boost_slider)
        self.bass_boost_label = QLabel("0dB")
        self.bass_boost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bass_boost_label.setStyleSheet("color: #B0BEC5;")
        bass_group.addWidget(self.bass_boost_label)
        sliders_layout.addLayout(bass_group)
        
        # Audio meters
        meters_group = QVBoxLayout()
        meters_group.addWidget(QLabel("📊 Levels"))
        self.audio_meters = self._create_audio_meters()
        meters_group.addWidget(self.audio_meters)
        sliders_layout.addLayout(meters_group)
        
        sliders_layout.addStretch()
        layout.addLayout(sliders_layout)
        
        # Quick presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Quick Presets:"))
        
        for text, preset in [("Mov", "movie_mode"), ("Mus", "music_mode"), ("New", "news_mode"), ("Spo", "sports_mode")]:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.setStyleSheet("background-color: #757575; color: white; padding: 5px;")
            btn.clicked.connect(lambda _, p=preset: self._apply_preset(p))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        layout.addLayout(presets_layout)
        
        # Connect signals
        self.voice_clarity_slider.valueChanged.connect(self._on_voice_clarity_changed)
        self.bass_boost_slider.valueChanged.connect(self._on_bass_boost_changed)
    
    def _create_audio_meters(self):
        """Create audio level meters with better visuals"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left channel
        layout.addWidget(QLabel("L"))
        self.left_meter = QProgressBar()
        self.left_meter.setRange(0, 100)
        self.left_meter.setMaximumHeight(15)
        self.left_meter.setStyleSheet("QProgressBar::chunk { background: #4CAF50; }")
        self.left_meter.setTextVisible(False)
        layout.addWidget(self.left_meter)
        
        # Right channel
        layout.addWidget(QLabel("R"))
        self.right_meter = QProgressBar()
        self.right_meter.setRange(0, 100)
        self.right_meter.setMaximumHeight(15)
        self.right_meter.setStyleSheet("QProgressBar::chunk { background: #4CAF50; }")
        self.right_meter.setTextVisible(False)
        layout.addWidget(self.right_meter)
        
        # Mock meter updates
        self.meter_timer = QTimer()
        self.meter_timer.timeout.connect(self._update_meters)
        self.meter_timer.start(100)
        
        return widget
    
    def _update_meters(self):
        """Update meters with mock data"""
        import random
        self.left_meter.setValue(random.randint(0, 100))
        self.right_meter.setValue(random.randint(0, 100))
    
    def _on_voice_clarity_changed(self, value):
        """Handle voice clarity change"""
        self.voice_clarity_label.setText(f"{value}%")
    
    def _on_bass_boost_changed(self, value):
        """Handle bass boost change"""
        self.bass_boost_label.setText(f"{value}dB")
    
    def _apply_preset(self, preset_name):
        """Apply audio preset"""
        presets = {
            "movie_mode": {"voice": 40, "bass": 3},
            "music_mode": {"voice": 0, "bass": 6},
            "news_mode": {"voice": 80, "bass": -3},
            "sports_mode": {"voice": 20, "bass": 8}
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.voice_clarity_slider.setValue(preset["voice"])
            self.bass_boost_slider.setValue(preset["bass"])
            self.profile_combo.setCurrentText(preset_name)

# =============================================================================
# MAIN PLAYOUT TAB - SIMPLIFIED LAYOUT
# =============================================================================

class PlayoutTab(QWidget):
    """Main Playout tab with simplified, clean layout and enhanced visuals"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self, config_manager, casparcg_client=None, audio_system=None, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = config_manager
        self.casparcg_client = casparcg_client
        self.audio_system = audio_system
        
        self.preview_player = None
        self.program_player = None
        self.audio_control_panel = None
        
        self.init_ui()
        self._apply_clean_styling()
    
    def init_ui(self):
        """Initialize clean UI layout with improved spacing"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. AMCP Server Control (Top Bar)
        amcp_section = self._create_amcp_section()
        main_layout.addWidget(amcp_section)
        
        # 2. Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Players
        players_widget = self._create_players_section()
        content_splitter.addWidget(players_widget)
        
        # Right side: Controls
        controls_widget = self._create_controls_section()
        content_splitter.addWidget(controls_widget)
        
        # Set splitter proportions (players get more space)
        content_splitter.setSizes([800, 400])
        main_layout.addWidget(content_splitter)
        
        # 3. Bottom: Response log
        log_section = self._create_log_section()
        main_layout.addWidget(log_section)
        
        # Set main layout proportions
        main_layout.setStretchFactor(amcp_section, 0)
        main_layout.setStretchFactor(content_splitter, 1)
        main_layout.setStretchFactor(log_section, 0)
    
    def _create_amcp_section(self):
        """Create AMCP control bar with enhanced styling"""
        section = QGroupBox("🖥️ AMCP Server Control")
        section.setStyleSheet("background-color: #2a2a2a; border: 2px solid #333;")
        layout = QHBoxLayout(section)
        layout.setSpacing(5)
        
        # Connection controls
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        self.connect_btn.clicked.connect(self._connect_amcp)
        layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("background-color: #F44336; color: white; padding: 5px;")
        self.disconnect_btn.clicked.connect(self._disconnect_amcp)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)
        
        self.status_label = QLabel("🔴 Disconnected")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Channel/Layer controls
        layout.addWidget(QLabel("Channel:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5;")
        layout.addWidget(self.channel_spin)
        
        layout.addWidget(QLabel("Layer:"))
        self.layer_spin = QSpinBox()
        self.layer_spin.setRange(1, 20)
        self.layer_spin.setValue(1)
        self.layer_spin.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5;")
        layout.addWidget(self.layer_spin)
        
        layout.addWidget(QLabel("Media:"))
        self.media_combo = QComboBox()
        self.media_combo.setEditable(True)
        self.media_combo.setMinimumWidth(200)
        self.media_combo.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5;")
        layout.addWidget(self.media_combo)
        
        # Action buttons
        load_btn = QPushButton("📥 Load")
        load_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        load_btn.clicked.connect(lambda: self._send_amcp_command("LOAD"))
        layout.addWidget(load_btn)
        
        play_btn = QPushButton("▶️ Play")
        play_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        play_btn.clicked.connect(lambda: self._send_amcp_command("PLAY"))
        layout.addWidget(play_btn)
        
        stop_btn = QPushButton("⏹️ Stop")
        stop_btn.setStyleSheet("background-color: #F44336; color: white; padding: 5px;")
        stop_btn.clicked.connect(lambda: self._send_amcp_command("STOP"))
        layout.addWidget(stop_btn)
        
        console_btn = QPushButton("💻 Console")
        console_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px;")
        console_btn.clicked.connect(self._open_console)
        layout.addWidget(console_btn)
        
        config_btn = QPushButton("⚙️ Configure")
        config_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px;")
        config_btn.clicked.connect(self._configure_server)
        layout.addWidget(config_btn)
        
        return section
    
    def _create_players_section(self):
        """Create players section with equal dimensions for Preview and Program"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main players container
        players_layout = QHBoxLayout()
        players_layout.setSpacing(15)
        
        # =====================
        # PREVIEW PLAYER SECTION
        # =====================
        preview_container = QWidget()
        preview_container.setFixedWidth(350)  # Fixed width
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # Preview header - fixed height
        preview_header = QLabel("🎬 Preview")
        preview_header.setFixedHeight(40)
        preview_header.setStyleSheet("""
            QLabel {
                background: #2196F3; 
                color: white; 
                padding: 8px; 
                font-weight: bold; 
                font-size: 14px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)
        
        # Preview player - will use fixed height from class
        self.preview_player = SimpleVideoPlayer("Preview Player")
        preview_layout.addWidget(self.preview_player)
        
        # Preview controls - fixed height
        preview_controls_widget = QWidget()
        preview_controls_widget.setFixedHeight(50)
        preview_controls_layout = QHBoxLayout(preview_controls_widget)
        preview_controls_layout.setContentsMargins(5, 8, 5, 8)
        preview_controls_layout.setSpacing(8)
        
        cue_btn = QPushButton("🎯 Cue")
        cue_btn.setFixedHeight(35)
        cue_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white; 
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        cue_btn.clicked.connect(self._cue_preview)
        preview_controls_layout.addWidget(cue_btn)
        
        self.auto_audio_btn = QPushButton("🎵 Auto Audio")
        self.auto_audio_btn.setCheckable(True)
        self.auto_audio_btn.setChecked(True)
        self.auto_audio_btn.setFixedHeight(35)
        self.auto_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575; 
                color: white; 
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        preview_controls_layout.addWidget(self.auto_audio_btn)
        
        preview_controls_layout.addStretch()
        preview_layout.addWidget(preview_controls_widget)
        
        players_layout.addWidget(preview_container)
        
        # =====================
        # CENTER CONTROL SECTION
        # =====================
        center_container = QWidget()
        center_container.setFixedWidth(120)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(10, 0, 10, 0)
        center_layout.setSpacing(15)
        
        # Add spacer to center buttons vertically (total height = 40 + 380 + 50 = 470)
        center_layout.addStretch(1)
        
        # Send to Program button
        send_btn = QPushButton("➡️\nSend to\nProgram")
        send_btn.setFixedSize(100, 80)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3; 
                color: white; 
                font-size: 11px; 
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
                border: 2px solid #1976D2;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
        """)
        send_btn.clicked.connect(self._send_to_program)
        center_layout.addWidget(send_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Take to Air button (main action)
        take_btn = QPushButton("📺\nTAKE TO\nAIR")
        take_btn.setFixedSize(100, 90)
        take_btn.setStyleSheet("""
            QPushButton {
                background: #E91E63; 
                color: white; 
                font-size: 12px; 
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
                border: 3px solid #C2185B;
            }
            QPushButton:hover {
                background: #C2185B;
            }
            QPushButton:pressed {
                background: #AD1457;
            }
        """)
        take_btn.clicked.connect(self._take_to_air)
        center_layout.addWidget(take_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Fade button
        fade_btn = QPushButton("🌅\nFade")
        fade_btn.setFixedSize(100, 60)
        fade_btn.setStyleSheet("""
            QPushButton {
                background: #9C27B0; 
                color: white; 
                font-size: 11px; 
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
                border: 2px solid #7B1FA2;
            }
            QPushButton:hover {
                background: #7B1FA2;
            }
            QPushButton:pressed {
                background: #6A1B9A;
            }
        """)
        fade_btn.clicked.connect(self._fade)
        center_layout.addWidget(fade_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        center_layout.addStretch(1)
        
        players_layout.addWidget(center_container)
        
        # =====================
        # PROGRAM PLAYER SECTION  
        # =====================
        program_container = QWidget()
        program_container.setFixedWidth(350)  # Same width as Preview
        program_layout = QVBoxLayout(program_container)
        program_layout.setContentsMargins(0, 0, 0, 0)
        program_layout.setSpacing(0)
        
        # Program header - same height as Preview
        program_header = QLabel("📺 Program")
        program_header.setFixedHeight(40)
        program_header.setStyleSheet("""
            QLabel {
                background: #F44336; 
                color: white; 
                padding: 8px; 
                font-weight: bold; 
                font-size: 14px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        program_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        program_layout.addWidget(program_header)
        
        # Program player - same height as Preview
        self.program_player = SimpleVideoPlayer("Program Player")
        program_layout.addWidget(self.program_player)
        
        # Program status - same height as Preview controls
        program_status_widget = QWidget()
        program_status_widget.setFixedHeight(50)
        program_status_layout = QHBoxLayout(program_status_widget)
        program_status_layout.setContentsMargins(5, 8, 5, 8)
        program_status_layout.setSpacing(8)
        
        # Audio status indicator
        self.audio_status_label = QLabel("🟢 Audio Active")
        self.audio_status_label.setFixedHeight(35)
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50; 
                font-weight: bold; 
                padding: 8px 12px;
                background-color: rgba(76, 175, 80, 0.1);
                border-radius: 4px;
                border: 1px solid #4CAF50;
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
                background-color: rgba(117, 117, 117, 0.1);
                border-radius: 4px;
                border: 1px solid #757575;
            }
        """)
        program_status_layout.addWidget(self.on_air_label)
        
        program_layout.addWidget(program_status_widget)
        
        players_layout.addWidget(program_container)
        
        # Set equal stretch for Preview and Program, minimal for center
        players_layout.setStretchFactor(preview_container, 0)   # Fixed width
        players_layout.setStretchFactor(center_container, 0)    # Fixed width
        players_layout.setStretchFactor(program_container, 0)   # Fixed width
        
        layout.addLayout(players_layout)
        
        return widget
    
    def _create_controls_section(self):
        """Create controls section"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Audio controls
        self.audio_control_panel = AudioControlPanel(self.audio_system, self.config_manager)
        layout.addWidget(self.audio_control_panel)
        
        layout.addStretch()
        return widget
    
    def _create_log_section(self):
        """Create log section with enhanced styling"""
        section = QGroupBox("📋 AMCP Response & System Logs")
        section.setStyleSheet("background-color: #1a1a1a; border: 2px solid #333;")
        layout = QVBoxLayout(section)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #1a1a1a; color: #00FF00; font-family: 'Consolas';")
        layout.addWidget(self.log_text)
        
        self.log_text.append("AMCP Response panel ready...")
        self.log_text.append("✅ Audio system available" if AUDIO_SYSTEM_AVAILABLE else "⚠️ Audio system not available")
        
        return section
    
    def _connect_amcp(self):
        """Connect to AMCP server"""
        try:
            # Mock connection for demo
            self.status_label.setText("🟢 Connected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self._log_response("Connected to AMCP server", "success")
        except Exception as e:
            self._log_response(f"Connection error: {e}", "error")
    
    def _disconnect_amcp(self):
        """Disconnect from AMCP server"""
        self.status_label.setText("🔴 Disconnected")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold; padding: 5px;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self._log_response("Disconnected from AMCP server", "info")
    
    def _send_amcp_command(self, command):
        """Send AMCP command"""
        channel = self.channel_spin.value()
        layer = self.layer_spin.value()
        media = self.media_combo.currentText()
        
        if command == "LOAD" and not media:
            self._log_response("No media selected for LOAD command", "error")
            return
        
        command_str = f"{command} {channel}-{layer}"
        if command == "LOAD":
            command_str += f" {media}"
        
        self._log_response(f"Sent: {command_str}", "info")
    
    def _open_console(self):
        """Open AMCP console"""
        self._log_response("AMCP console opened", "info")
    
    def _configure_server(self):
        """Configure server"""
        self._log_response("Server configuration opened", "info")
    
    def _cue_preview(self):
        """Cue preview"""
        self._log_response("Preview cued to first frame", "info")
    
    def _send_to_program(self):
        """Send preview to program"""
        preview_file = self.preview_player.get_current_file()
        if preview_file:
            self.program_player.load_media(preview_file)
            self._log_response("Preview sent to Program", "success")
        else:
            self._log_response("No media in Preview to send", "warning")
    
    def _take_to_air(self):
        """Take program to air"""
        program_file = self.program_player.get_current_file()
        if program_file:
            # Update audio status
            self.audio_status_label.setText("🔴 LIVE AUDIO")
            self.audio_status_label.setStyleSheet("""
                color: #F44336; 
                font-weight: bold; 
                padding: 8px 12px;
                background-color: rgba(244, 67, 54, 0.1);
                border-radius: 4px;
                border: 2px solid #F44336;
                animation: pulse 2s infinite;
            """)
            
            # Update ON AIR status
            self.on_air_label.setText("🔴 ON AIR")
            self.on_air_label.setStyleSheet("""
                color: #F44336; 
                font-weight: bold; 
                padding: 8px 12px;
                background-color: rgba(244, 67, 54, 0.2);
                border-radius: 4px;
                border: 2px solid #F44336;
            """)
            
            self._log_response("Program taken to air - LIVE", "success")
        else:
            self._log_response("No program content to take to air", "warning")
    
    def _fade(self):
        """Fade program"""
        # Update audio status back to normal
        self.audio_status_label.setText("🟢 Audio Active")
        self.audio_status_label.setStyleSheet("""
            color: #4CAF50; 
            font-weight: bold; 
            padding: 8px 12px;
            background-color: rgba(76, 175, 80, 0.1);
            border-radius: 4px;
            border: 1px solid #4CAF50;
        """)
        
        # Update ON AIR status back to off air
        self.on_air_label.setText("🔴 OFF AIR")
        self.on_air_label.setStyleSheet("""
            color: #757575; 
            font-weight: bold; 
            padding: 8px 12px;
            background-color: rgba(117, 117, 117, 0.1);
            border-radius: 4px;
            border: 1px solid #757575;
        """)
        
        self._log_response("Program faded - OFF AIR", "info")
    
    def _log_response(self, message: str, level: str = "info"):
        """Log response message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"error": "❌", "success": "✅", "warning": "⚠️", "info": "ℹ️"}.get(level, "ℹ️")
        log_message = f"[{timestamp}] {prefix} {message}"
        self.log_text.append(log_message)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _apply_clean_styling(self):
        """Apply clean, modern styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #B0BEC5;
            }
            
            QPushButton:hover {
                opacity: 0.9;
            }
            
            QPushButton:pressed {
                opacity: 0.7;
            }
            
            QPushButton:disabled {
                background: #2a2a2a;
                color: #666666;
            }
            
            QGroupBox {
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            
            QSlider::groove:vertical {
                border: 1px solid #555;
                width: 8px;
                background: #333;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal,
            QSlider::handle:vertical {
                background: #00BCD4;
                border: 1px solid #00BCD4;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            
            QSpinBox, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #B0BEC5;
            }
            
            QSpinBox:focus, QComboBox:focus {
                border-color: #00BCD4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #B0BEC5;
                margin-right: 6px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #555;
                selection-background-color: #00BCD4;
            }
            
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #388E3C);
                border-radius: 3px;
            }
            
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #555;
                border-radius: 5px;
                color: #00FF00;
                font-family: 'Consolas';
            }
            
            QFrame {
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
    
    def cleanup(self):
        """Clean up resources"""
        if self.preview_player:
            try:
                self.preview_player.stop()
            except:
                pass
        
        if self.program_player:
            try:
                self.program_player.stop()
            except:
                pass
        
        if hasattr(self.audio_control_panel, 'meter_timer'):
            self.audio_control_panel.meter_timer.stop()

# =============================================================================
# AMCP CONSOLE DIALOG
# =============================================================================

class AMCPConsoleDialog(QDialog):
    """AMCP Console Dialog for manual command execution with enhanced styling"""
    
    def __init__(self, amcp_client=None, parent=None):
        super().__init__(parent)
        self.amcp_client = amcp_client
        self.logger = get_logger(f"{__name__}.AMCPConsole")
        
        self.setWindowTitle("AMCP Console")
        self.setModal(False)
        self.resize(600, 400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize console UI"""
        layout = QVBoxLayout(self)
        
        # Response display
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setFont(QFont("Consolas", 10))
        self.response_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FF00;
                border: 2px solid #333;
                font-family: 'Consolas';
            }
        """)
        layout.addWidget(self.response_display)
        
        # Command input
        input_layout = QHBoxLayout()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter AMCP command (e.g., INFO, VERSION, PLAY 1-10 video)")
        self.command_input.returnPressed.connect(self._send_command)
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 2px solid #555;
                padding: 8px;
                color: #B0BEC5;
                font-family: 'Consolas';
            }
            QLineEdit:focus {
                border-color: #00BCD4;
            }
        """)
        input_layout.addWidget(self.command_input)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                border: 2px solid #4CAF50;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #757575;
                border: 2px solid #757575;
                padding: 6px 12px;
                color: white;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        clear_btn.clicked.connect(self.response_display.clear)
        controls_layout.addWidget(clear_btn)
        
        # Quick commands
        quick_commands = [
            ("INFO", "INFO"),
            ("VERSION", "VERSION"),
            ("CLS", "CLS"),
            ("TLS", "TLS")
        ]
        
        for name, command in quick_commands:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2a2a2a;
                    border: 2px solid #555;
                    padding: 4px 8px;
                    color: #B0BEC5;
                }
                QPushButton:hover {
                    background: #333;
                    border-color: #00BCD4;
                }
            """)
            btn.clicked.connect(lambda _, cmd=command: self._send_quick_command(cmd))
            controls_layout.addWidget(btn)
        
        controls_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                border: 2px solid #F44336;
                padding: 6px 12px;
                color: white;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        """)
        close_btn.clicked.connect(self.close)
        controls_layout.addWidget(close_btn)
        
        layout.addLayout(controls_layout)
        
        # Initialize console
        self.response_display.append("=== AMCP Console Ready ===")
        self.response_display.append("Enter commands below or use quick command buttons")
        self.response_display.append("Examples: INFO, VERSION, PLAY 1-10 video.mp4")
        self.response_display.append("")
    
    def _send_command(self):
        """Send command via AMCP client"""
        command_text = self.command_input.text().strip()
        if not command_text:
            return
        
        self._log_command(f"> {command_text}")
        
        try:
            if self.amcp_client and hasattr(self.amcp_client, 'send_command'):
                # In a real implementation, this would be async
                response = f"200 OK\n{command_text} command executed successfully"
                self._log_response(f"< {response}")
            else:
                self._log_response("< ERROR: AMCP client not available or not connected")
        except Exception as e:
            self._log_response(f"< ERROR: {e}")
        
        self.command_input.clear()
        self._scroll_to_bottom()
    
    def _send_quick_command(self, command):
        """Send quick command"""
        self.command_input.setText(command)
        self._send_command()
    
    def _log_command(self, message):
        """Log command to display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.response_display.append(f"[{timestamp}] {message}")
    
    def _log_response(self, message):
        """Log response to display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.response_display.append(f"[{timestamp}] {message}")
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of response display"""
        scrollbar = self.response_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

# =============================================================================
# MEDIA LIBRARY DIALOG
# =============================================================================

class MediaLibraryDialog(QDialog):
    """Media Library Management Dialog with enhanced styling"""
    
    media_selected = pyqtSignal(str)  # Emits selected media path
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(f"{__name__}.MediaLibrary")
        
        self.current_media_files = []
        
        self.setWindowTitle("Media Library")
        self.setModal(False)
        self.resize(800, 600)
        
        self._init_ui()
        self._load_media_library()
    
    def _init_ui(self):
        """Initialize media library UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with library path
        header_layout = QHBoxLayout()
        
        self.path_label = QLabel("Media Library:")
        header_layout.addWidget(self.path_label)
        
        self.path_display = QLabel(str(self.config_manager.get_media_library_path()))
        self.path_display.setStyleSheet("color: #00BCD4; font-weight: bold;")
        header_layout.addWidget(self.path_display)
        
        header_layout.addStretch()
        
        browse_path_btn = QPushButton("Change Path")
        browse_path_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px;")
        browse_path_btn.clicked.connect(self._change_library_path)
        header_layout.addWidget(browse_path_btn)
        
        layout.addLayout(header_layout)
        
        # Search and filter
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter media files...")
        self.search_input.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5; border: 2px solid #555;")
        self.search_input.textChanged.connect(self._filter_media_list)
        search_layout.addWidget(self.search_input)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Files", "Video Files", "Audio Files"])
        self.filter_combo.setStyleSheet("background-color: #2a2a2a; color: #B0BEC5;")
        self.filter_combo.currentTextChanged.connect(self._filter_media_list)
        search_layout.addWidget(self.filter_combo)
        
        layout.addLayout(search_layout)
        
        # Media list
        self.media_list = QListWidget()
        self.media_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.media_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.media_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 2px solid #333;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #404040;
            }
            QListWidget::item:selected {
                background-color: #00BCD4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        layout.addWidget(self.media_list)
        
        # File info panel
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("Select a file to see details")
        self.info_label.setStyleSheet("color: #888888; font-style: italic;")
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        self.file_count_label = QLabel("0 files")
        self.file_count_label.setStyleSheet("color: #00BCD4;")
        info_layout.addWidget(self.file_count_label)
        
        layout.addLayout(info_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        import_btn = QPushButton("📁 Import Files")
        import_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        import_btn.clicked.connect(self._import_files)
        buttons_layout.addWidget(import_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px;")
        refresh_btn.clicked.connect(self._load_media_library)
        buttons_layout.addWidget(refresh_btn)
        
        buttons_layout.addStretch()
        
        load_preview_btn = QPushButton("Load to Preview")
        load_preview_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        load_preview_btn.clicked.connect(self._load_to_preview)
        buttons_layout.addWidget(load_preview_btn)
        
        load_program_btn = QPushButton("Load to Program")
        load_program_btn.setStyleSheet("background-color: #E91E63; color: white; padding: 5px;")
        load_program_btn.clicked.connect(self._load_to_program)
        buttons_layout.addWidget(load_program_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #F44336; color: white; padding: 5px;")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connect selection change
        self.media_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _load_media_library(self):
        """Load media files from library path"""
        media_path = self.config_manager.get_media_library_path()
        
        if not media_path.exists():
            self.logger.warning(f"Media library path does not exist: {media_path}")
            self.info_label.setText(f"Library path not found: {media_path}")
            return
        
        self.media_list.clear()
        self.current_media_files.clear()
        
        # Load video files
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            for file_path in media_path.glob(f"*{ext}"):
                self._add_media_file(file_path, "video")
        
        # Load audio files
        for ext in SUPPORTED_AUDIO_EXTENSIONS:
            for file_path in media_path.glob(f"*{ext}"):
                self._add_media_file(file_path, "audio")
        
        self._update_file_count()
        self.logger.info(f"Loaded {len(self.current_media_files)} media files")
    
    def _add_media_file(self, file_path, file_type):
        """Add media file to list"""
        file_info = {
            'path': str(file_path.resolve()),
            'name': file_path.name,
            'type': file_type,
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
        }
        
        self.current_media_files.append(file_info)
        
        # Create list item
        item = QListWidgetItem()
        
        # Set icon based on type
        icon = "🎬" if file_type == "video" else "🎵"
        item.setText(f"{icon} {file_path.name}")
        item.setData(Qt.ItemDataRole.UserRole, file_info)
        
        self.media_list.addItem(item)
    
    def _filter_media_list(self):
        """Filter media list based on search and type"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            file_info = item.data(Qt.ItemDataRole.UserRole)
            
            # Check search text
            name_match = search_text in file_info['name'].lower()
            
            # Check file type filter
            type_match = True
            if filter_type == "Video Files":
                type_match = file_info['type'] == "video"
            elif filter_type == "Audio Files":
                type_match = file_info['type'] == "audio"
            
            item.setHidden(not (name_match and type_match))
    
    def _update_file_count(self):
        """Update file count display"""
        visible_count = sum(1 for i in range(self.media_list.count()) 
                           if not self.media_list.item(i).isHidden())
        total_count = len(self.current_media_files)
        
        if visible_count == total_count:
            self.file_count_label.setText(f"{total_count} files")
        else:
            self.file_count_label.setText(f"{visible_count} of {total_count} files")
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected_items = self.media_list.selectedItems()
        
        if not selected_items:
            self.info_label.setText("Select a file to see details")
            return
        
        if len(selected_items) == 1:
            file_info = selected_items[0].data(Qt.ItemDataRole.UserRole)
            size_mb = file_info['size'] / (1024 * 1024)
            modified_str = file_info['modified'].strftime("%Y-%m-%d %H:%M")
            
            info_text = (f"📄 {file_info['name']} | "
                        f"📊 {size_mb:.1f} MB | "
                        f"📅 {modified_str} | "
                        f"🎯 {file_info['type'].title()}")
            
            self.info_label.setText(info_text)
        else:
            self.info_label.setText(f"{len(selected_items)} files selected")
    
    def _on_item_double_clicked(self, item):
        """Handle double click - load to preview by default"""
        self._load_to_preview()
    
    def _load_to_preview(self):
        """Load selected file to preview"""
        selected_items = self.media_list.selectedItems()
        if selected_items:
            file_info = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.media_selected.emit(f"preview:{file_info['path']}")
    
    def _load_to_program(self):
        """Load selected file to program"""
        selected_items = self.media_list.selectedItems()
        if selected_items:
            file_info = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.media_selected.emit(f"program:{file_info['path']}")
    
    def _change_library_path(self):
        """Change media library path"""
        current_path = self.config_manager.get_media_library_path()
        
        new_path = QFileDialog.getExistingDirectory(
            self,
            "Select Media Library Folder",
            str(current_path)
        )
        
        if new_path:
            self.config_manager.set_media_library_path(Path(new_path))
            self.path_display.setText(new_path)
            self._load_media_library()
            self.logger.info(f"Media library path changed to: {new_path}")
    
    def _import_files(self):
        """Import files to media library"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        # Create filter for supported files
        video_exts = " ".join([f"*{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS])
        audio_exts = " ".join([f"*{ext}" for ext in SUPPORTED_AUDIO_EXTENSIONS])
        all_exts = " ".join([f"*{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS.union(SUPPORTED_AUDIO_EXTENSIONS)])
        
        file_dialog.setNameFilter(
            f"All Media ({all_exts});;Video Files ({video_exts});;Audio Files ({audio_exts});;All Files (*)"
        )
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self._import_selected_files(selected_files)
    
    def _import_selected_files(self, file_paths):
        """Import selected files to library"""
        media_library_path = self.config_manager.get_media_library_path()
        
        if not media_library_path.exists():
            media_library_path.mkdir(parents=True, exist_ok=True)
        
        imported_count = 0
        skipped_count = 0
        
        progress = QProgressDialog("Importing files...", "Cancel", 0, len(file_paths), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        for i, src_path_str in enumerate(file_paths):
            if progress.wasCanceled():
                break
            
            src_path = Path(src_path_str)
            dest_path = media_library_path / src_path.name
            
            progress.setLabelText(f"Importing: {src_path.name}")
            progress.setValue(i)
            
            try:
                if dest_path.exists():
                    reply = QMessageBox.question(
                        self,
                        "File Exists",
                        f"File '{src_path.name}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        skipped_count += 1
                        continue
                
                import shutil
                shutil.copy2(src_path, dest_path)
                imported_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to import {src_path.name}: {e}")
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to import {src_path.name}:\n{e}"
                )
        
        progress.setValue(len(file_paths))
        progress.close()
        
        # Show results
        if imported_count > 0:
            self._load_media_library()  # Refresh the list
            
        message = f"Import completed:\n"
        message += f"• {imported_count} files imported\n"
        if skipped_count > 0:
            message += f"• {skipped_count} files skipped"
        
        QMessageBox.information(self, "Import Results", message)

# =============================================================================
# ENHANCED PLAYOUT TAB WITH MEDIA LIBRARY INTEGRATION
# =============================================================================

def add_media_library_methods_to_playout_tab(playout_tab_instance):
    """Add media library integration methods to PlayoutTab instance"""
    
    def open_media_library(self):
        """Open media library dialog"""
        if not hasattr(self, 'media_library_dialog'):
            self.media_library_dialog = MediaLibraryDialog(self.config_manager, self)
            self.media_library_dialog.media_selected.connect(self._on_media_library_selection)
        
        self.media_library_dialog.show()
        self.media_library_dialog.raise_()
        self.media_library_dialog.activateWindow()
    
    def _on_media_library_selection(self, selection):
        """Handle media selection from library"""
        target, file_path = selection.split(":", 1)
        
        if target == "preview":
            self.preview_player.load_media(file_path)
            self._log_response(f"Loaded to preview: {Path(file_path).name}", "success")
        elif target == "program":
            self.program_player.load_media(file_path)
            self._log_response(f"Loaded to program: {Path(file_path).name}", "success")
    
    # Bind methods to instance
    import types
    playout_tab_instance.open_media_library = types.MethodType(open_media_library, playout_tab_instance)
    playout_tab_instance._on_media_library_selection = types.MethodType(_on_media_library_selection, playout_tab_instance)

# =============================================================================
# PLAYLIST MANAGEMENT
# =============================================================================

class PlaylistManager:
    """Manages playlist operations for playout"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.playlist_items = []
        self.current_index = 0
        self.logger = get_logger(f"{__name__}.PlaylistManager")
    
    def add_item(self, file_path, name=None):
        """Add item to playlist"""
        if name is None:
            name = Path(file_path).name
        
        item = {
            'path': str(file_path),
            'name': name,
            'duration': 0,
            'added_time': datetime.now().isoformat()
        }
        
        self.playlist_items.append(item)
        self.logger.info(f"Added to playlist: {name}")
        return len(self.playlist_items) - 1
    
    def remove_item(self, index):
        """Remove item from playlist"""
        if 0 <= index < len(self.playlist_items):
            removed = self.playlist_items.pop(index)
            self.logger.info(f"Removed from playlist: {removed['name']}")
            
            if self.current_index >= len(self.playlist_items):
                self.current_index = max(0, len(self.playlist_items) - 1)
            
            return removed
        return None
    
    def get_current_item(self):
        """Get current playlist item"""
        if 0 <= self.current_index < len(self.playlist_items):
            return self.playlist_items[self.current_index]
        return None
    
    def advance_to_next(self):
        """Advance to next item in playlist"""
        if self.current_index < len(self.playlist_items) - 1:
            self.current_index += 1
            return self.get_current_item()
        return None
    
    def clear_playlist(self):
        """Clear all playlist items"""
        self.playlist_items.clear()
        self.current_index = 0
        self.logger.info("Playlist cleared")

# =============================================================================
# AUDIO MONITORING
# =============================================================================

class AudioMonitor:
    """Real-time audio monitoring and analysis"""
    
    def __init__(self, audio_system=None):
        self.audio_system = audio_system
        self.logger = get_logger(f"{__name__}.AudioMonitor")
        
        self.is_monitoring = False
        self.peak_levels = {'left': 0.0, 'right': 0.0}
        self.rms_levels = {'left': 0.0, 'right': 0.0}
        
        # Alert thresholds
        self.peak_threshold = -6.0  # dB
        self.silence_threshold = -60.0  # dB
    
    def start_monitoring(self):
        """Start audio level monitoring"""
        self.is_monitoring = True
        self.logger.info("Audio monitoring started")
    
    def stop_monitoring(self):
        """Stop audio level monitoring"""
        self.is_monitoring = False
        self.logger.info("Audio monitoring stopped")
    
    def update_levels(self, left_peak, right_peak, left_rms=None, right_rms=None):
        """Update current audio levels"""
        self.peak_levels['left'] = left_peak
        self.peak_levels['right'] = right_peak
        
        if left_rms is not None:
            self.rms_levels['left'] = left_rms
        if right_rms is not None:
            self.rms_levels['right'] = right_rms
        
        # Check for alerts
        if (left_peak > self.peak_threshold or right_peak > self.peak_threshold):
            self.logger.warning(f"Audio peak alert: L={left_peak:.1f}dB R={right_peak:.1f}dB")
    
    def get_current_levels(self):
        """Get current audio levels"""
        return {
            'peak': self.peak_levels.copy(),
            'rms': self.rms_levels.copy(),
            'monitoring': self.is_monitoring
        }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_time_display(seconds):
    """Format seconds into HH:MM:SS display format"""
    if seconds < 0:
        return "00:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def get_file_duration(file_path):
    """Get duration of media file using VLC"""
    if not VLC_AVAILABLE:
        return 0
    
    try:
        instance = vlc.Instance('--intf', 'dummy')
        media = instance.media_new(str(file_path))
        media.parse()
        duration_ms = media.get_duration()
        instance.release()
        return duration_ms / 1000.0  # Convert to seconds
    except Exception:
        return 0

def validate_media_file(file_path):
    """Validate if file is a supported media file"""
    path = Path(file_path)
    
    if not path.exists():
        return False, "File does not exist"
    
    extension = path.suffix.lower()
    
    if extension in SUPPORTED_VIDEO_EXTENSIONS:
        return True, "Video file"
    elif extension in SUPPORTED_AUDIO_EXTENSIONS:
        return True, "Audio file"
    else:
        return False, f"Unsupported file type: {extension}"

# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

def initialize_playout_system(config_manager, audio_system=None, casparcg_client=None):
    """Initialize complete playout system with all components"""
    
    # Create main playout tab
    playout_tab = PlayoutTab(config_manager, casparcg_client, audio_system)
    
    # Add media library integration
    add_media_library_methods_to_playout_tab(playout_tab)
    
    # Create playlist manager
    playlist_manager = PlaylistManager(config_manager)
    playout_tab.playlist_manager = playlist_manager
    
    # Create audio monitor
    playout_tab.audio_monitor = AudioMonitor(audio_system)
    
    return playout_tab

# =============================================================================
# VERSION AND EXPORTS
# =============================================================================

__version__ = "1.0.1"
__author__ = "TV Stream Professional"

# Export main classes and functions
__all__ = [
    'PlayoutTab',
    'SimpleVideoPlayer', 
    'AudioControlPanel',
    'AMCPConsoleDialog',
    'MediaLibraryDialog',
    'PlaylistManager',
    'AudioMonitor',
    'add_media_library_methods_to_playout_tab',
    'initialize_playout_system',
    'format_time_display',
    'get_file_duration',
    'validate_media_file'
]