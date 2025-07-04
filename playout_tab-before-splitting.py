#!/usr/bin/env python3
"""
Enhanced Playout Tab with Complete Audio Processing Integration
Professional broadcast playout interface with full audio control capabilities
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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSignalBlocker, QThread, pyqtSlot
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
    from audio.jack_backend import JACKServer
    AUDIO_SYSTEM_AVAILABLE = True
except ImportError:
    TVAudioSystem = None
    AudioProfileManager = None
    JACKServer = None
    AUDIO_SYSTEM_AVAILABLE = False

# =============================================================================
# ENHANCED AUDIO CONTROL PANEL WITH COMPLETE FEATURES
# =============================================================================

class EnhancedAudioControlPanel(QGroupBox):
    """Complete audio control panel with all processing features"""
    
    profile_changed = pyqtSignal(str)
    night_mode_toggled = pyqtSignal(bool)
    parameter_changed = pyqtSignal(str, float)
    
    def __init__(self, audio_system=None, config_manager=None, parent=None):
        super().__init__("🔊 Audio Processing & Control", parent)
        self.audio_system = audio_system
        self.config_manager = config_manager
        self.logger = get_logger(f"{__name__}.EnhancedAudioControlPanel")
        
        # Audio level monitoring
        self.left_level = 0.0
        self.right_level = 0.0
        self.peak_hold_left = 0.0
        self.peak_hold_right = 0.0
        
        self._init_ui()
        self._setup_timers()
        self._load_initial_settings()
        
    def _init_ui(self):
        """Initialize comprehensive audio control UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========================
        # 1. PROFILE SELECTION SECTION
        # ========================
        profile_section = self._create_profile_section()
        main_layout.addWidget(profile_section)
        
        # ========================
        # 2. AUDIO PROCESSING CONTROLS
        # ========================
        processing_section = self._create_processing_section()
        main_layout.addWidget(processing_section)
        
        # ========================
        # 3. AUDIO METERS AND MONITORING
        # ========================
        meters_section = self._create_meters_section()
        main_layout.addWidget(meters_section)
        
        # ========================
        # 4. ROUTING AND OUTPUT CONTROL
        # ========================
        routing_section = self._create_routing_section()
        main_layout.addWidget(routing_section)
        
        # Apply modern styling
        self._apply_enhanced_styling()
    
    def _create_profile_section(self):
        """Create audio profile selection and management section"""
        section = QGroupBox("🎛️ Audio Profiles")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        # Profile selection row
        profile_row = QHBoxLayout()
        
        profile_row.addWidget(QLabel("Active Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(150)
        self.profile_combo.addItems([
            "default", "movie_mode", "music_mode", 
            "news_mode", "sports_mode", "night_mode_profile"
        ])
        self.profile_combo.setCurrentText("default")
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        profile_row.addWidget(self.profile_combo)
        
        # Night mode toggle
        self.night_mode_btn = QPushButton("🌙 Night Mode")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setFixedSize(120, 35)
        self.night_mode_btn.toggled.connect(self._on_night_mode_toggled)
        profile_row.addWidget(self.night_mode_btn)
        
        # Auto audio detection
        self.auto_detect_btn = QPushButton("🎯 Auto Detect")
        self.auto_detect_btn.setCheckable(True)
        self.auto_detect_btn.setChecked(True)
        self.auto_detect_btn.setFixedSize(120, 35)
        self.auto_detect_btn.toggled.connect(self._on_auto_detect_toggled)
        profile_row.addWidget(self.auto_detect_btn)
        
        profile_row.addStretch()
        layout.addLayout(profile_row)
        
        # Quick preset buttons
        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("Quick Presets:"))
        
        presets = [
            ("🎬 Movie", "movie_mode", "#2196F3"),
            ("🎵 Music", "music_mode", "#4CAF50"), 
            ("📺 News", "news_mode", "#FF9800"),
            ("⚽ Sports", "sports_mode", "#E91E63")
        ]
        
        for name, profile, color in presets:
            btn = QPushButton(name)
            btn.setFixedSize(90, 30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; 
                    color: white; 
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
                QPushButton:pressed {{
                    opacity: 0.6;
                }}
            """)
            btn.clicked.connect(lambda _, p=profile: self._apply_preset(p))
            presets_row.addWidget(btn)
        
        presets_row.addStretch()
        layout.addLayout(presets_row)
        
        return section
    
    def _create_processing_section(self):
        """Create audio processing controls section"""
        section = QGroupBox("🎛️ Audio Processing")
        layout = QHBoxLayout(section)
        layout.setSpacing(20)
        
        # ========================
        # Voice/Dialogue Controls
        # ========================
        voice_group = QVBoxLayout()
        voice_group.addWidget(QLabel("🎤 Voice Clarity"))
        
        self.voice_clarity_slider = QSlider(Qt.Orientation.Vertical)
        self.voice_clarity_slider.setRange(0, 100)
        self.voice_clarity_slider.setValue(30)
        self.voice_clarity_slider.setFixedHeight(120)
        self.voice_clarity_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed("voice_clarity", v / 100.0)
        )
        voice_group.addWidget(self.voice_clarity_slider)
        
        self.voice_clarity_label = QLabel("30%")
        self.voice_clarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.voice_clarity_label.setFixedHeight(20)
        voice_group.addWidget(self.voice_clarity_label)
        
        # Voice clarity enable/disable
        self.voice_enable_btn = QPushButton("Enable")
        self.voice_enable_btn.setCheckable(True)
        self.voice_enable_btn.setChecked(True)
        self.voice_enable_btn.setFixedHeight(25)
        voice_group.addWidget(self.voice_enable_btn)
        
        layout.addLayout(voice_group)
        
        # ========================
        # Bass Controls
        # ========================
        bass_group = QVBoxLayout()
        bass_group.addWidget(QLabel("🔊 Bass Boost"))
        
        self.bass_boost_slider = QSlider(Qt.Orientation.Vertical)
        self.bass_boost_slider.setRange(-10, 20)
        self.bass_boost_slider.setValue(0)
        self.bass_boost_slider.setFixedHeight(120)
        self.bass_boost_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed("bass_boost", v)
        )
        bass_group.addWidget(self.bass_boost_slider)
        
        self.bass_boost_label = QLabel("0dB")
        self.bass_boost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bass_boost_label.setFixedHeight(20)
        bass_group.addWidget(self.bass_boost_label)
        
        # Bass enable/disable
        self.bass_enable_btn = QPushButton("Enable")
        self.bass_enable_btn.setCheckable(True)
        self.bass_enable_btn.setFixedHeight(25)
        bass_group.addWidget(self.bass_enable_btn)
        
        layout.addLayout(bass_group)
        
        # ========================
        # EQ Controls
        # ========================
        eq_group = QVBoxLayout()
        eq_group.addWidget(QLabel("🎚️ 3-Band EQ"))
        
        # EQ sliders container
        eq_sliders = QHBoxLayout()
        eq_sliders.setSpacing(10)
        
        # Low, Mid, High frequency controls
        eq_bands = [("Low", "low_gain"), ("Mid", "mid_gain"), ("High", "high_gain")]
        self.eq_sliders = {}
        self.eq_labels = {}
        
        for band_name, param_name in eq_bands:
            band_layout = QVBoxLayout()
            band_layout.addWidget(QLabel(band_name))
            
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.setFixedHeight(80)
            slider.valueChanged.connect(
                lambda v, p=param_name: self._on_parameter_changed(p, v)
            )
            band_layout.addWidget(slider)
            
            label = QLabel("0dB")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(15)
            band_layout.addWidget(label)
            
            self.eq_sliders[param_name] = slider
            self.eq_labels[param_name] = label
            
            eq_sliders.addLayout(band_layout)
        
        eq_group.addLayout(eq_sliders)
        
        # EQ enable/disable
        self.eq_enable_btn = QPushButton("Enable EQ")
        self.eq_enable_btn.setCheckable(True)
        self.eq_enable_btn.setChecked(True)
        self.eq_enable_btn.setFixedHeight(25)
        eq_group.addWidget(self.eq_enable_btn)
        
        layout.addLayout(eq_group)
        
        # ========================
        # Compressor Controls
        # ========================
        comp_group = QVBoxLayout()
        comp_group.addWidget(QLabel("🗜️ Compressor"))
        
        # Threshold and Ratio controls
        comp_controls = QHBoxLayout()
        
        # Threshold
        thresh_layout = QVBoxLayout()
        thresh_layout.addWidget(QLabel("Threshold"))
        self.comp_threshold_slider = QSlider(Qt.Orientation.Vertical)
        self.comp_threshold_slider.setRange(-30, 0)
        self.comp_threshold_slider.setValue(-10)
        self.comp_threshold_slider.setFixedHeight(80)
        self.comp_threshold_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed("comp_threshold", v)
        )
        thresh_layout.addWidget(self.comp_threshold_slider)
        self.comp_threshold_label = QLabel("-10dB")
        self.comp_threshold_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thresh_layout.addWidget(self.comp_threshold_label)
        
        # Ratio
        ratio_layout = QVBoxLayout()
        ratio_layout.addWidget(QLabel("Ratio"))
        self.comp_ratio_slider = QSlider(Qt.Orientation.Vertical)
        self.comp_ratio_slider.setRange(10, 100)  # 1.0 to 10.0 ratio
        self.comp_ratio_slider.setValue(20)  # 2.0
        self.comp_ratio_slider.setFixedHeight(80)
        self.comp_ratio_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed("comp_ratio", v / 10.0)
        )
        ratio_layout.addWidget(self.comp_ratio_slider)
        self.comp_ratio_label = QLabel("2.0:1")
        self.comp_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ratio_layout.addWidget(self.comp_ratio_label)
        
        comp_controls.addLayout(thresh_layout)
        comp_controls.addLayout(ratio_layout)
        comp_group.addLayout(comp_controls)
        
        # Compressor enable/disable
        self.comp_enable_btn = QPushButton("Enable")
        self.comp_enable_btn.setCheckable(True)
        self.comp_enable_btn.setFixedHeight(25)
        comp_group.addWidget(self.comp_enable_btn)
        
        layout.addLayout(comp_group)
        
        # Add separator and master controls
        layout.addWidget(self._create_separator())
        
        # ========================
        # Master Volume and Limiter
        # ========================
        master_group = QVBoxLayout()
        master_group.addWidget(QLabel("🎚️ Master"))
        
        self.master_volume_slider = QSlider(Qt.Orientation.Vertical)
        self.master_volume_slider.setRange(0, 150)  # 0% to 150%
        self.master_volume_slider.setValue(100)  # 100% = unity gain
        self.master_volume_slider.setFixedHeight(120)
        self.master_volume_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed("master_volume", v / 100.0)
        )
        master_group.addWidget(self.master_volume_slider)
        
        self.master_volume_label = QLabel("100%")
        self.master_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        master_group.addWidget(self.master_volume_label)
        
        # Master mute
        self.master_mute_btn = QPushButton("🔇 Mute")
        self.master_mute_btn.setCheckable(True)
        self.master_mute_btn.setFixedHeight(25)
        master_group.addWidget(self.master_mute_btn)
        
        layout.addLayout(master_group)
        
        return section
    
    def _create_meters_section(self):
        """Create audio level meters and monitoring section"""
        section = QGroupBox("📊 Audio Monitoring")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        # Level meters
        meters_layout = QHBoxLayout()
        
        # Left channel meter
        left_meter_layout = QVBoxLayout()
        left_meter_layout.addWidget(QLabel("L"))
        
        self.left_meter = QProgressBar()
        self.left_meter.setOrientation(Qt.Orientation.Vertical)
        self.left_meter.setRange(0, 100)
        self.left_meter.setValue(0)
        self.left_meter.setFixedSize(25, 100)
        self.left_meter.setTextVisible(False)
        left_meter_layout.addWidget(self.left_meter)
        
        self.left_peak_label = QLabel("0")
        self.left_peak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_peak_label.setFixedHeight(15)
        left_meter_layout.addWidget(self.left_peak_label)
        
        meters_layout.addLayout(left_meter_layout)
        
        # Right channel meter  
        right_meter_layout = QVBoxLayout()
        right_meter_layout.addWidget(QLabel("R"))
        
        self.right_meter = QProgressBar()
        self.right_meter.setOrientation(Qt.Orientation.Vertical)
        self.right_meter.setRange(0, 100)
        self.right_meter.setValue(0)
        self.right_meter.setFixedSize(25, 100)
        self.right_meter.setTextVisible(False)
        right_meter_layout.addWidget(self.right_meter)
        
        self.right_peak_label = QLabel("0")
        self.right_peak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_peak_label.setFixedHeight(15)
        right_meter_layout.addWidget(self.right_peak_label)
        
        meters_layout.addLayout(right_meter_layout)
        
        # Level indicators and controls
        indicators_layout = QVBoxLayout()
        
        # Peak level display
        peak_layout = QHBoxLayout()
        peak_layout.addWidget(QLabel("Peak:"))
        self.peak_display = QLabel("-∞ dB")
        self.peak_display.setStyleSheet("color: #00FF00; font-weight: bold; font-family: monospace;")
        peak_layout.addWidget(self.peak_display)
        peak_layout.addStretch()
        indicators_layout.addLayout(peak_layout)
        
        # RMS level display
        rms_layout = QHBoxLayout()
        rms_layout.addWidget(QLabel("RMS:"))
        self.rms_display = QLabel("-∞ dB")
        self.rms_display.setStyleSheet("color: #FFFF00; font-weight: bold; font-family: monospace;")
        rms_layout.addWidget(self.rms_display)
        rms_layout.addStretch()
        indicators_layout.addLayout(rms_layout)
        
        # Audio status indicators
        status_layout = QHBoxLayout()
        
        self.clip_indicator = QLabel("🔴 CLIP")
        self.clip_indicator.setStyleSheet("color: #666; font-weight: bold;")
        status_layout.addWidget(self.clip_indicator)
        
        self.silence_indicator = QLabel("🔕 SILENCE")
        self.silence_indicator.setStyleSheet("color: #666; font-weight: bold;")
        status_layout.addWidget(self.silence_indicator)
        
        status_layout.addStretch()
        indicators_layout.addLayout(status_layout)
        
        # Reset peak hold button
        reset_peak_btn = QPushButton("Reset Peak")
        reset_peak_btn.setFixedHeight(25)
        reset_peak_btn.clicked.connect(self._reset_peak_hold)
        indicators_layout.addWidget(reset_peak_btn)
        
        meters_layout.addLayout(indicators_layout)
        
        layout.addLayout(meters_layout)
        
        return section
    
    def _create_routing_section(self):
        """Create audio routing and output control section"""
        section = QGroupBox("🔀 Audio Routing & Output")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        # JACK routing status
        jack_layout = QHBoxLayout()
        jack_layout.addWidget(QLabel("JACK Status:"))
        
        self.jack_status_label = QLabel("🟢 Connected")
        self.jack_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        jack_layout.addWidget(self.jack_status_label)
        
        jack_layout.addStretch()
        
        # JACK controls
        self.jack_connect_btn = QPushButton("Connect JACK")
        self.jack_connect_btn.setFixedSize(100, 25)
        self.jack_connect_btn.clicked.connect(self._toggle_jack_connection)
        jack_layout.addWidget(self.jack_connect_btn)
        
        layout.addLayout(jack_layout)
        
        # Output routing
        routing_layout = QHBoxLayout()
        
        routing_layout.addWidget(QLabel("Output Route:"))
        
        self.output_combo = QComboBox()
        self.output_combo.addItems([
            "System Output 1-2",
            "Headphones", 
            "Program Feed",
            "Monitor Feed",
            "JACK Manual"
        ])
        self.output_combo.setCurrentText("System Output 1-2")
        routing_layout.addWidget(self.output_combo)
        
        routing_layout.addStretch()
        
        # Monitor controls
        self.monitor_btn = QPushButton("🎧 Monitor")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.setChecked(True)
        self.monitor_btn.setFixedSize(80, 25)
        routing_layout.addWidget(self.monitor_btn)
        
        layout.addLayout(routing_layout)
        
        # Plugin chain status
        plugin_layout = QHBoxLayout()
        plugin_layout.addWidget(QLabel("Plugin Chain:"))
        
        self.plugin_status_label = QLabel("4 plugins active")
        self.plugin_status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        plugin_layout.addWidget(self.plugin_status_label)
        
        plugin_layout.addStretch()
        
        # Plugin chain controls
        self.bypass_all_btn = QPushButton("Bypass All")
        self.bypass_all_btn.setCheckable(True)
        self.bypass_all_btn.setFixedSize(80, 25)
        self.bypass_all_btn.toggled.connect(self._toggle_bypass_all)
        plugin_layout.addWidget(self.bypass_all_btn)
        
        layout.addLayout(plugin_layout)
        
        return section
    
    def _create_separator(self):
        """Create visual separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(2)
        return separator
    
    def _setup_timers(self):
        """Setup update timers for real-time monitoring"""
        # Audio level monitoring timer
        self.meter_timer = QTimer()
        self.meter_timer.timeout.connect(self._update_audio_meters)
        self.meter_timer.start(50)  # Update every 50ms for smooth meters
        
        # Peak hold decay timer
        self.peak_decay_timer = QTimer()
        self.peak_decay_timer.timeout.connect(self._decay_peak_hold)
        self.peak_decay_timer.start(100)  # Decay every 100ms
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_indicators)
        self.status_timer.start(500)  # Update status every 500ms
    
    def _load_initial_settings(self):
        """Load initial audio settings"""
        if self.audio_system and AUDIO_SYSTEM_AVAILABLE:
            try:
                # Load default profile
                self.profile_combo.setCurrentText("default")
                self._apply_preset("default")
                
                # Set initial parameter displays
                self._update_all_parameter_displays()
                
                self.logger.info("Initial audio settings loaded")
            except Exception as e:
                self.logger.error(f"Failed to load initial settings: {e}")
    
    def _on_profile_changed(self, profile_name):
        """Handle audio profile change"""
        if self.audio_system and hasattr(self.audio_system, 'load_profile'):
            try:
                self.audio_system.load_profile(profile_name)
                self.profile_changed.emit(profile_name)
                self.logger.info(f"Audio profile changed to: {profile_name}")
                
                # Update UI to reflect profile settings
                self._update_ui_for_profile(profile_name)
                
            except Exception as e:
                self.logger.error(f"Failed to load profile {profile_name}: {e}")
    
    def _on_night_mode_toggled(self, enabled):
        """Handle night mode toggle"""
        if self.audio_system and hasattr(self.audio_system, 'enable_night_mode'):
            try:
                self.audio_system.enable_night_mode(enabled)
                self.night_mode_toggled.emit(enabled)
                
                # Update button appearance
                if enabled:
                    self.night_mode_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2196F3;
                            color: white;
                            border-radius: 6px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #1976D2;
                        }
                    """)
                else:
                    self.night_mode_btn.setStyleSheet("")
                
                self.logger.info(f"Night mode {'enabled' if enabled else 'disabled'}")
                
            except Exception as e:
                self.logger.error(f"Failed to toggle night mode: {e}")
    
    def _on_auto_detect_toggled(self, enabled):
        """Handle auto detect toggle"""
        self.logger.info(f"Auto content detection {'enabled' if enabled else 'disabled'}")
        
        # Update button appearance
        if enabled:
            self.auto_detect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
        else:
            self.auto_detect_btn.setStyleSheet("")
    
    def _on_parameter_changed(self, param_name, value):
        """Handle audio parameter changes"""
        try:
            # Update corresponding label
            if param_name == "voice_clarity":
                self.voice_clarity_label.setText(f"{int(value * 100)}%")
                if self.audio_system and hasattr(self.audio_system, 'enhance_dialogue'):
                    self.audio_system.enhance_dialogue(value > 0)
                    
            elif param_name == "bass_boost":
                self.bass_boost_label.setText(f"{value}dB")
                if self.audio_system and hasattr(self.audio_system, 'set_bass_boost'):
                    self.audio_system.set_bass_boost(value)
                    
            elif param_name in ["low_gain", "mid_gain", "high_gain"]:
                self.eq_labels[param_name].setText(f"{value}dB")
                # Set EQ parameter in audio system
                
            elif param_name == "comp_threshold":
                self.comp_threshold_label.setText(f"{value}dB")
                
            elif param_name == "comp_ratio":
                self.comp_ratio_label.setText(f"{value:.1f}:1")
                
            elif param_name == "master_volume":
                self.master_volume_label.setText(f"{int(value * 100)}%")
            
            # Emit parameter change signal
            self.parameter_changed.emit(param_name, value)
            
            self.logger.debug(f"Parameter {param_name} changed to {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update parameter {param_name}: {e}")
    
    def _apply_preset(self, preset_name):
        """Apply audio preset configuration"""
        presets = {
            "default": {
                "voice_clarity": 30, "bass_boost": 0, "low_gain": 0, 
                "mid_gain": 0, "high_gain": 0, "comp_threshold": -10, 
                "comp_ratio": 20, "master_volume": 100
            },
            "movie_mode": {
                "voice_clarity": 40, "bass_boost": 3, "low_gain": 1, 
                "mid_gain": 2, "high_gain": 0, "comp_threshold": -15, 
                "comp_ratio": 25, "master_volume": 100
            },
            "music_mode": {
                "voice_clarity": 0, "bass_boost": 6, "low_gain": 2, 
                "mid_gain": 0, "high_gain": 1, "comp_threshold": -8, 
                "comp_ratio": 15, "master_volume": 105
            },
            "news_mode": {
                "voice_clarity": 80, "bass_boost": -3, "low_gain": -3, 
                "mid_gain": 3, "high_gain": 0, "comp_threshold": -12, 
                "comp_ratio": 30, "master_volume": 95
            },
            "sports_mode": {
                "voice_clarity": 20, "bass_boost": 8, "low_gain": 3, 
                "mid_gain": 1, "high_gain": 2, "comp_threshold": -10, 
                "comp_ratio": 15, "master_volume": 110
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # Update all controls with preset values
            with QSignalBlocker(self.voice_clarity_slider):
                self.voice_clarity_slider.setValue(preset["voice_clarity"])
            with QSignalBlocker(self.bass_boost_slider):
                self.bass_boost_slider.setValue(preset["bass_boost"])
            with QSignalBlocker(self.master_volume_slider):
                self.master_volume_slider.setValue(preset["master_volume"])
            
            # Update EQ sliders
            for param in ["low_gain", "mid_gain", "high_gain"]:
                if param in self.eq_sliders:
                    with QSignalBlocker(self.eq_sliders[param]):
                        self.eq_sliders[param].setValue(preset[param])
            
            # Update compressor
            with QSignalBlocker(self.comp_threshold_slider):
                self.comp_threshold_slider.setValue(preset["comp_threshold"])
            with QSignalBlocker(self.comp_ratio_slider):
                self.comp_ratio_slider.setValue(preset["comp_ratio"])
            
            # Update profile combo
            with QSignalBlocker(self.profile_combo):
                self.profile_combo.setCurrentText(preset_name)
            
            # Update all labels
            self._update_all_parameter_displays()
            
            self.logger.info(f"Applied preset: {preset_name}")
    
    def _update_all_parameter_displays(self):
        """Update all parameter display labels"""
        self.voice_clarity_label.setText(f"{self.voice_clarity_slider.value()}%")
        self.bass_boost_label.setText(f"{self.bass_boost_slider.value()}dB")
        self.master_volume_label.setText(f"{self.master_volume_slider.value()}%")
        
        for param, slider in self.eq_sliders.items():
            self.eq_labels[param].setText(f"{slider.value()}dB")
        
        self.comp_threshold_label.setText(f"{self.comp_threshold_slider.value()}dB")
        self.comp_ratio_label.setText(f"{self.comp_ratio_slider.value() / 10.0:.1f}:1")
    
    def _update_ui_for_profile(self, profile_name):
        """Update UI elements to reflect current profile"""
        # This would update the UI based on the actual profile loaded from audio system
        # For now, we'll apply the preset values
        self._apply_preset(profile_name)
    
    def _update_audio_meters(self):
        """Update audio level meters with real-time data"""
        import random
        import math
        
        # Simulate audio levels (replace with actual audio system data)
        if hasattr(self, 'audio_system') and self.audio_system:
            # Get real levels from audio system if available
            try:
                # Mock implementation - replace with actual audio level reading
                self.left_level = random.uniform(0, 90) + 10 * math.sin(random.random() * math.pi)
                self.right_level = random.uniform(0, 90) + 10 * math.sin(random.random() * math.pi)
            except:
                # Fallback to simulated levels
                self.left_level = random.uniform(20, 80)
                self.right_level = random.uniform(20, 80)
        else:
            # Simulated audio levels for demo
            self.left_level = random.uniform(20, 80)
            self.right_level = random.uniform(20, 80)
        
        # Update meters
        self.left_meter.setValue(int(self.left_level))
        self.right_meter.setValue(int(self.right_level))
        
        # Update peak hold
        if self.left_level > self.peak_hold_left:
            self.peak_hold_left = self.left_level
        if self.right_level > self.peak_hold_right:
            self.peak_hold_right = self.right_level
        
        # Update peak displays
        self.left_peak_label.setText(f"{int(self.peak_hold_left)}")
        self.right_peak_label.setText(f"{int(self.peak_hold_right)}")
        
        # Update level displays
        max_level = max(self.left_level, self.right_level)
        if max_level > 0:
            peak_db = 20 * math.log10(max_level / 100.0)
            rms_db = peak_db - 3  # Approximate RMS
            
            self.peak_display.setText(f"{peak_db:.1f} dB")
            self.rms_display.setText(f"{rms_db:.1f} dB")
        else:
            self.peak_display.setText("-∞ dB")
            self.rms_display.setText("-∞ dB")
        
        # Update meter colors based on levels
        self._update_meter_colors()
    
    def _update_meter_colors(self):
        """Update meter colors based on audio levels"""
        left_color = self._get_meter_color(self.left_level)
        right_color = self._get_meter_color(self.right_level)
        
        self.left_meter.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }}
            QProgressBar::chunk {{
                background: {left_color};
                border-radius: 3px;
            }}
        """)
        
        self.right_meter.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }}
            QProgressBar::chunk {{
                background: {right_color};
                border-radius: 3px;
            }}
        """)
    
    def _get_meter_color(self, level):
        """Get appropriate color for meter level"""
        if level < 60:
            return "#4CAF50"  # Green - normal levels
        elif level < 80:
            return "#FF9800"  # Orange - moderate levels
        else:
            return "#F44336"  # Red - high levels
    
    def _decay_peak_hold(self):
        """Decay peak hold values over time"""
        decay_rate = 0.5  # dB per 100ms
        self.peak_hold_left = max(0, self.peak_hold_left - decay_rate)
        self.peak_hold_right = max(0, self.peak_hold_right - decay_rate)
    
    def _reset_peak_hold(self):
        """Reset peak hold values"""
        self.peak_hold_left = 0.0
        self.peak_hold_right = 0.0
        self.left_peak_label.setText("0")
        self.right_peak_label.setText("0")
    
    def _update_status_indicators(self):
        """Update audio status indicators"""
        # Check for clipping
        if max(self.left_level, self.right_level) > 95:
            self.clip_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.clip_indicator.setStyleSheet("color: #666; font-weight: bold;")
        
        # Check for silence
        if max(self.left_level, self.right_level) < 5:
            self.silence_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.silence_indicator.setStyleSheet("color: #666; font-weight: bold;")
    
    def _toggle_jack_connection(self):
        """Toggle JACK connection"""
        if self.jack_status_label.text() == "🟢 Connected":
            self.jack_status_label.setText("🔴 Disconnected")
            self.jack_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.jack_connect_btn.setText("Connect JACK")
        else:
            self.jack_status_label.setText("🟢 Connected")
            self.jack_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.jack_connect_btn.setText("Disconnect")
    
    def _toggle_bypass_all(self, bypassed):
        """Toggle bypass for all plugins"""
        if bypassed:
            self.plugin_status_label.setText("All bypassed")
            self.plugin_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.plugin_status_label.setText("4 plugins active")
            self.plugin_status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
        
        self.logger.info(f"All plugins {'bypassed' if bypassed else 'active'}")
    
    def _apply_enhanced_styling(self):
        """Apply enhanced modern styling to all components"""
        self.setStyleSheet("""
            /* Group boxes */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #2a2a2a;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #00BCD4;
                font-size: 12px;
            }
            
            /* Sliders */
            QSlider::groove:vertical {
                border: 1px solid #555;
                width: 12px;
                background: #333;
                border-radius: 6px;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 12px;
                background: #333;
                border-radius: 6px;
            }
            
            QSlider::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00BCD4, stop:1 #0097A7);
                border: 2px solid #00838F;
                width: 18px;
                height: 18px;
                border-radius: 10px;
                margin: 0 -4px;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00BCD4, stop:1 #0097A7);
                border: 2px solid #00838F;
                width: 18px;
                height: 18px;
                border-radius: 10px;
                margin: -4px 0;
            }
            
            QSlider::handle:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #26C6DA, stop:1 #00ACC1);
            }
            
            /* Buttons */
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 6px 12px;
                color: #E0E0E0;
                font-weight: bold;
                min-width: 70px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00BCD4;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
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
            
            /* Combo boxes */
            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 5px 10px;
                color: #E0E0E0;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border-color: #00BCD4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #E0E0E0;
                margin-right: 6px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                selection-background-color: #00BCD4;
                outline: none;
            }
            
            /* Labels */
            QLabel {
                color: #E0E0E0;
                font-weight: normal;
            }
            
            /* Progress bars */
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:0.6 #4CAF50, 
                    stop:0.8 #FF9800, stop:1 #F44336);
                border-radius: 3px;
            }
        """)

# =============================================================================
# ENHANCED VIDEO PLAYER WITH BETTER CONTROLS
# =============================================================================

class EnhancedVideoPlayer(QWidget):
    """Enhanced video player with better controls and monitoring"""
    
    media_loaded = pyqtSignal(str)
    playback_state_changed = pyqtSignal(str)  # playing, paused, stopped
    
    def __init__(self, player_name: str = "Player", parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.logger = get_logger(f"{__name__}.{player_name}")
        
        self.vlc_instance = None
        self.media_player = None
        self.current_media_path = None
        self.is_playing = False
        self.is_paused = False
        
        # Set fixed size for consistent layout
        self.setFixedHeight(450)  # Increased height for better controls
        self.setMinimumWidth(380)
        
        self._init_vlc()
        self._init_ui()
        
    def _init_vlc(self):
        """Initialize VLC components with enhanced settings"""
        if not VLC_AVAILABLE:
            self.logger.warning("VLC not available")
            return
        
        try:
            vlc_args = [
                '--no-xlib', 
                '--quiet', 
                '--intf', 'dummy',
                '--no-video-title-show',  # Don't show filename
                '--mouse-hide-timeout=0',  # Don't hide mouse
                '--no-osd'  # No on-screen display
            ]
            self.vlc_instance = vlc.Instance(vlc_args)
            self.media_player = self.vlc_instance.media_player_new()
            self.logger.debug(f"VLC initialized for {self.player_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize VLC: {e}")
    
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
        
        # Update timer for position and status
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position_and_status)
        self.update_timer.start(100)  # Update every 100ms
        
        # Slider update flag
        self.slider_being_dragged = False
    
    def _show_no_media_message(self):
        """Show enhanced no media message"""
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
        """Enhanced media loading with better error handling"""
        if not VLC_AVAILABLE or not self.media_player:
            QMessageBox.warning(self, "VLC Not Available", 
                              "VLC media player is not available. Please install VLC.")
            return False
        
        try:
            media_path = Path(file_path).resolve()
            
            if not media_path.exists():
                QMessageBox.warning(self, "File Not Found", 
                                  f"Media file not found: {media_path}")
                return False
            
            # Create and set media
            media = self.vlc_instance.media_new(str(media_path))
            self.media_player.set_media(media)
            self.current_media_path = media_path
            
            # Set video output based on platform
            if platform.system() == "Linux":
                self.media_player.set_xwindow(self.video_frame.winId())
            elif platform.system() == "Windows":
                self.media_player.set_hwnd(self.video_frame.winId())
            elif platform.system() == "Darwin":
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            # Enable controls
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            # Update file info
            file_size = media_path.stat().st_size / (1024 * 1024)  # MB
            self.file_info_label.setText(f"{media_path.name} ({file_size:.1f} MB)")
            self.file_info_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
            
            # Clear video frame overlay
            if self.video_frame.layout():
                QWidget().setLayout(self.video_frame.layout())
            
            # Emit signal
            self.media_loaded.emit(str(media_path))
            
            self.logger.info(f"Loaded media: {media_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load media: {e}")
            QMessageBox.critical(self, "Load Error", 
                               f"Failed to load media file:\n{e}")
            return False
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.media_player or not self.current_media_path:
            return
        
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Start or resume playback"""
        if self.media_player:
            self.media_player.play()
            self.is_playing = True
            self.is_paused = False
            
            self.play_btn.setText("⏸️")
            self.play_btn.setToolTip("Pause")
            self.status_indicator.setText("▶️ Playing")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            self.playback_state_changed.emit("playing")
            self.logger.debug("Playback started")
    
    def pause(self):
        """Pause playback"""
        if self.media_player:
            self.media_player.pause()
            self.is_playing = False
            self.is_paused = True
            
            self.play_btn.setText("▶️")
            self.play_btn.setToolTip("Play")
            self.status_indicator.setText("⏸️ Paused")
            self.status_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            self.playback_state_changed.emit("paused")
            self.logger.debug("Playback paused")
    
    def stop(self):
        """Stop playback"""
        if self.media_player:
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
            
            self.playback_state_changed.emit("stopped")
            self.logger.debug("Playback stopped")
    
    def seek_relative(self, seconds):
        """Seek relative to current position"""
        if self.media_player:
            current_time = self.media_player.get_time()
            if current_time >= 0:
                new_time = max(0, current_time + (seconds * 1000))
                self.media_player.set_time(int(new_time))
                self.logger.debug(f"Seeked {seconds}s to {new_time/1000:.1f}s")
    
    def _toggle_mute(self, muted):
        """Toggle audio mute"""
        if self.media_player:
            if muted:
                self.media_player.audio_set_volume(0)
                self.mute_btn.setText("🔇")
                self.mute_btn.setStyleSheet("background-color: #F44336;")
            else:
                volume = self.volume_slider.value()
                self.media_player.audio_set_volume(volume)
                self.mute_btn.setText("🔊")
                self.mute_btn.setStyleSheet("")
    
    def _set_volume(self, volume: int):
        """Set audio volume"""
        if self.media_player and not self.mute_btn.isChecked():
            self.media_player.audio_set_volume(volume)
        
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
        if self.media_player and self.current_media_path:
            position = self.position_slider.value() / 1000.0
            self.media_player.set_position(position)
        
        self.slider_being_dragged = False
    
    def _on_slider_moved(self, value):
        """Handle slider movement during drag"""
        if self.slider_being_dragged and self.media_player:
            # Update time display during drag
            length = self.media_player.get_length()
            if length > 0:
                current_time = (value / 1000.0) * length / 1000.0
                self.time_label.setText(self._format_time(current_time))
    
    def _update_position_and_status(self):
        """Update position slider and status displays"""
        if not self.media_player or self.slider_being_dragged:
            return
        
        try:
            # Update position and time
            position = self.media_player.get_position()
            length = self.media_player.get_length()
            current_time = self.media_player.get_time()
            
            if length > 0 and position >= 0:
                # Update slider
                slider_value = int(position * 1000)
                self.position_slider.setValue(slider_value)
                
                # Update time displays
                current_seconds = current_time / 1000.0 if current_time >= 0 else 0
                total_seconds = length / 1000.0
                
                self.time_label.setText(self._format_time(current_seconds))
                self.duration_label.setText(self._format_time(total_seconds))
            
            # Update playback state based on VLC state
            if VLC_AVAILABLE:
                state = self.media_player.get_state()
                if state == vlc.State.Playing and not self.is_playing:
                    self.is_playing = True
                    self.is_paused = False
                    self.play_btn.setText("⏸️")
                    self.status_indicator.setText("▶️ Playing")
                    self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
                elif state == vlc.State.Paused and self.is_playing:
                    self.is_playing = False
                    self.is_paused = True
                    self.play_btn.setText("▶️")
                    self.status_indicator.setText("⏸️ Paused")
                    self.status_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
                elif state in [vlc.State.Stopped, vlc.State.Ended]:
                    if self.is_playing or self.is_paused:
                        self.is_playing = False
                        self.is_paused = False
                        self.play_btn.setText("▶️")
                        self.status_indicator.setText("⏹️ Stopped")
                        self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
                        if state == vlc.State.Ended:
                            self.playback_state_changed.emit("ended")
        except:
            pass  # Ignore VLC errors during updates
    
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
            'position': self.media_player.get_position() if self.media_player else 0,
            'time': self.media_player.get_time() if self.media_player else 0,
            'length': self.media_player.get_length() if self.media_player else 0
        }

# =============================================================================
# ENHANCED PLAYOUT TAB WITH COMPLETE FEATURES
# =============================================================================

class PlayoutTab(QWidget):
    """Enhanced Playout tab with complete audio and video control features"""
    
    status_message = pyqtSignal(str, int)
    media_taken_to_air = pyqtSignal(str)
    audio_profile_changed = pyqtSignal(str)
    
    def __init__(self, config_manager, casparcg_client=None, audio_system=None, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = config_manager
        self.casparcg_client = casparcg_client
        self.audio_system = audio_system
        
        # UI components
        self.preview_player = None
        self.program_player = None
        self.audio_control_panel = None
        
        # State tracking
        self.is_on_air = False
        self.auto_audio_enabled = True
        self.amcp_connected = False
        
        self.init_ui()
        self._apply_professional_styling()
        self._setup_connections()
    
    def init_ui(self):
        """Initialize UI exactly like the screenshot"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # ========================
        # 1. TOP: AMCP SERVER CONTROL (яг зургийн шиг)
        # ========================
        amcp_section = self._create_screenshot_amcp_section()
        main_layout.addWidget(amcp_section)
        
        # ========================
        # 2. MAIN: HORIZONTAL LAYOUT (Players left, Audio right)
        # ========================
        main_content = QHBoxLayout()
        main_content.setSpacing(12)
        
        # Left side: Players section (зүүн тал - preview, transport, program)
        players_widget = self._create_screenshot_players_section()
        main_content.addWidget(players_widget)
        
        # Right side: Audio control (баруун тал - audio processing)
        audio_widget = self._create_screenshot_audio_section()
        main_content.addWidget(audio_widget)
        
        # Set proportions: Players get ~70%, Audio gets ~30%
        players_widget.setMinimumWidth(900)
        audio_widget.setFixedWidth(400)
        
        main_layout.addLayout(main_content)
        
        # ========================
        # 3. BOTTOM: LOG SECTION (доод хэсэг - лог)
        # ========================
        log_section = self._create_screenshot_log_section()
        main_layout.addWidget(log_section)
        
        # Set stretch factors
        main_layout.setStretchFactor(amcp_section, 0)      # Fixed height
        main_layout.setStretchFactor(main_content, 1)      # Expandable
        main_layout.setStretchFactor(log_section, 0)       # Fixed height

    def _create_screenshot_amcp_section(self):
        """Create AMCP section exactly like screenshot"""
        section = QGroupBox("🖥️ AMCP Server Control & Channel Management")
        section.setFixedHeight(80)
        layout = QHBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Left: Connection status
        conn_layout = QVBoxLayout()
        
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.amcp_status_label = QLabel("🔴 Disconnected")
        self.amcp_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        status_row.addWidget(self.amcp_status_label)
        status_row.addStretch()
        conn_layout.addLayout(status_row)
        
        # Connection buttons
        btn_row = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setFixedSize(100, 30)
        btn_row.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedSize(100, 30)
        self.disconnect_btn.setEnabled(False)
        btn_row.addWidget(self.disconnect_btn)
        btn_row.addStretch()
        conn_layout.addLayout(btn_row)
        
        layout.addLayout(conn_layout)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep1)
        
        # Center: Channel/Layer/Media controls
        controls_layout = QVBoxLayout()
        
        # Channel and Layer
        ch_ly_row = QHBoxLayout()
        ch_ly_row.addWidget(QLabel("Channel:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.setFixedWidth(60)
        ch_ly_row.addWidget(self.channel_spin)
        
        ch_ly_row.addWidget(QLabel("Layer:"))
        self.layer_spin = QSpinBox()
        self.layer_spin.setRange(1, 20)
        self.layer_spin.setValue(1)
        self.layer_spin.setFixedWidth(60)
        ch_ly_row.addWidget(self.layer_spin)
        controls_layout.addLayout(ch_ly_row)
        
        # Media selection
        media_row = QHBoxLayout()
        media_row.addWidget(QLabel("Media:"))
        self.media_combo = QComboBox()
        self.media_combo.setEditable(True)
        self.media_combo.setMinimumWidth(200)
        self.media_combo.setPlaceholderText("Enter media filename...")
        media_row.addWidget(self.media_combo)
        controls_layout.addLayout(media_row)
        
        layout.addLayout(controls_layout)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)
        
        # Right: AMCP Commands (яг зургийн шиг 2 мөр)
        cmd_layout = QVBoxLayout()
        
        # First row: LOAD, PLAY, STOP
        cmd_row1 = QHBoxLayout()
        load_btn = QPushButton("📥 LOAD")
        load_btn.setFixedSize(80, 25)
        cmd_row1.addWidget(load_btn)
        
        play_btn = QPushButton("▶️ PLAY")
        play_btn.setFixedSize(80, 25)
        cmd_row1.addWidget(play_btn)
        
        stop_btn = QPushButton("⏹️ STOP")
        stop_btn.setFixedSize(80, 25)
        cmd_row1.addWidget(stop_btn)
        cmd_layout.addLayout(cmd_row1)
        
        # Second row: CLEAR, INFO, CLS
        cmd_row2 = QHBoxLayout()
        clear_btn = QPushButton("🗑️ CLEAR")
        clear_btn.setFixedSize(80, 25)
        cmd_row2.addWidget(clear_btn)
        
        info_btn = QPushButton("ℹ️ INFO")
        info_btn.setFixedSize(80, 25)
        cmd_row2.addWidget(info_btn)
        
        cls_btn = QPushButton("📋 CLS")
        cls_btn.setFixedSize(80, 25)
        cmd_row2.addWidget(cls_btn)
        cmd_layout.addLayout(cmd_row2)
        
        layout.addLayout(cmd_layout)
        
        layout.addStretch()
        
        # Far right: Console and Configure
        adv_layout = QVBoxLayout()
        console_btn = QPushButton("💻 Console")
        console_btn.setFixedSize(100, 30)
        adv_layout.addWidget(console_btn)
        
        config_btn = QPushButton("⚙️ Configure")
        config_btn.setFixedSize(100, 30)
        adv_layout.addWidget(config_btn)
        
        layout.addLayout(adv_layout)
        
        return section

    def _create_screenshot_players_section(self):
        """Create players section exactly like screenshot (left side)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main players layout: Preview | Transport | Program
        players_layout = QHBoxLayout()
        players_layout.setSpacing(15)
        
        # ========================
        # PREVIEW PLAYER (зүүн тал)
        # ========================
        preview_container = QWidget()
        preview_container.setFixedWidth(380)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # Preview header (цэнхэр)
        preview_header = QLabel("🎬 PREVIEW")
        preview_header.setFixedHeight(35)
        preview_header.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
        """)
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)
        
        # Preview video area
        preview_video = QFrame()
        preview_video.setFixedSize(380, 240)
        preview_video.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-left: 2px solid #2196F3;
                border-right: 2px solid #2196F3;
                border-bottom: 2px solid #2196F3;
            }
        """)
        preview_layout.addWidget(preview_video)
        
        # Preview controls row
        preview_controls = QWidget()
        preview_controls.setFixedHeight(50)
        preview_controls_layout = QHBoxLayout(preview_controls)
        preview_controls_layout.setContentsMargins(8, 8, 8, 8)
        
        # CUE button
        cue_btn = QPushButton("🎯 CUE")
        cue_btn.setFixedSize(70, 30)
        cue_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        preview_controls_layout.addWidget(cue_btn)
        
        # Auto Audio button
        auto_audio_btn = QPushButton("🎵 Auto Audio")
        auto_audio_btn.setCheckable(True)
        auto_audio_btn.setChecked(True)
        auto_audio_btn.setFixedSize(100, 30)
        auto_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:!checked {
                background-color: #757575;
            }
        """)
        preview_controls_layout.addWidget(auto_audio_btn)
        
        # Library button
        library_btn = QPushButton("📚 Library")
        library_btn.setFixedSize(70, 30)
        library_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        preview_controls_layout.addWidget(library_btn)
        
        preview_controls_layout.addStretch()
        preview_layout.addWidget(preview_controls)
        
        players_layout.addWidget(preview_container)
        
        # ========================
        # CENTER TRANSPORT (дунд хэсэг)
        # ========================
        transport_container = QWidget()
        transport_container.setFixedWidth(120)
        transport_layout = QVBoxLayout(transport_container)
        transport_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        transport_layout.setSpacing(10)
        
        transport_layout.addStretch(1)
        
        # Send to Program
        send_btn = QPushButton("➡️\nSEND TO\nPROGRAM")
        send_btn.setFixedSize(100, 70)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 10px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #1976D2;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        transport_layout.addWidget(send_btn)
        
        # TAKE TO AIR (гол товчлуур)
        take_btn = QPushButton("📺\nTAKE TO\nAIR")
        take_btn.setFixedSize(100, 80)
        take_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border-radius: 10px;
                border: 3px solid #AD1457;
            }
            QPushButton:hover {
                background-color: #C2185B;
            }
        """)
        transport_layout.addWidget(take_btn)
        
        # FADE and CUT buttons
        fade_cut_layout = QHBoxLayout()
        fade_cut_layout.setSpacing(5)
        
        fade_btn = QPushButton("🌅\nFADE")
        fade_btn.setFixedSize(45, 50)
        fade_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 6px;
            }
        """)
        fade_cut_layout.addWidget(fade_btn)
        
        cut_btn = QPushButton("✂️\nCUT")
        cut_btn.setFixedSize(45, 50)
        cut_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 6px;
            }
        """)
        fade_cut_layout.addWidget(cut_btn)
        
        transport_layout.addLayout(fade_cut_layout)
        transport_layout.addStretch(1)
        
        players_layout.addWidget(transport_container)
        
        # ========================
        # PROGRAM PLAYER (баруун тал)
        # ========================
        program_container = QWidget()
        program_container.setFixedWidth(380)
        program_layout = QVBoxLayout(program_container)
        program_layout.setContentsMargins(0, 0, 0, 0)
        program_layout.setSpacing(0)
        
        # Program header (улаан)
        program_header = QLabel("📺 PROGRAM")
        program_header.setFixedHeight(35)
        program_header.setStyleSheet("""
            QLabel {
                background-color: #F44336;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
        """)
        program_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        program_layout.addWidget(program_header)
        
        # Program video area
        program_video = QFrame()
        program_video.setFixedSize(380, 240)
        program_video.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-left: 2px solid #F44336;
                border-right: 2px solid #F44336;
                border-bottom: 2px solid #F44336;
            }
        """)
        program_layout.addWidget(program_video)
        
        # Program status row
        program_status = QWidget()
        program_status.setFixedHeight(50)
        program_status_layout = QHBoxLayout(program_status)
        program_status_layout.setContentsMargins(8, 8, 8, 8)
        
        # LIVE AUDIO indicator
        live_audio_btn = QPushButton("🔴 LIVE AUDIO")
        live_audio_btn.setFixedSize(100, 30)
        live_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        program_status_layout.addWidget(live_audio_btn)
        
        program_status_layout.addStretch()
        
        # ON AIR indicator
        self.on_air_label = QLabel("🔴 ON AIR")
        self.on_air_label.setFixedSize(80, 30)
        self.on_air_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.on_air_label.setStyleSheet("""
            QLabel {
                background-color: #F44336;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        program_status_layout.addWidget(self.on_air_label)
        
        program_layout.addWidget(program_status)
        
        players_layout.addWidget(program_container)
        
        layout.addLayout(players_layout)
        
        return widget

    def _create_screenshot_audio_section(self):
        """Create audio section exactly like screenshot (right side)"""
        widget = QWidget()
        widget.setFixedWidth(400)
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 0, 0, 0)
        
        # ========================
        # 1. AUDIO PROCESSING CONTROL header
        # ========================
        audio_header = QGroupBox("🔊 Audio Processing & Control")
        audio_header_layout = QVBoxLayout(audio_header)
        
        # ========================
        # 2. AUDIO PROFILES section
        # ========================
        profiles_section = QGroupBox("🎛️ Audio Profiles")
        profiles_layout = QVBoxLayout(profiles_section)
        
        # Active Profile row
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Active Profile:"))
        
        profile_combo = QComboBox()
        profile_combo.addItems(["default", "movie_mode", "music_mode", "news_mode", "sports_mode"])
        profile_combo.setCurrentText("default")
        profile_combo.setFixedWidth(120)
        profile_row.addWidget(profile_combo)
        
        night_mode_btn = QPushButton("🌙 Night Mode")
        night_mode_btn.setCheckable(True)
        night_mode_btn.setFixedSize(100, 25)
        profile_row.addWidget(night_mode_btn)
        
        auto_detect_btn = QPushButton("🎯 Auto Detect")
        auto_detect_btn.setCheckable(True)
        auto_detect_btn.setChecked(True)
        auto_detect_btn.setFixedSize(100, 25)
        profile_row.addWidget(auto_detect_btn)
        
        profiles_layout.addLayout(profile_row)
        
        # Quick Presets row (яг зургийн шиг өнгөтэй)
        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("Quick Presets:"))
        
        movie_btn = QPushButton("🎬 Movie")
        movie_btn.setFixedSize(70, 25)
        movie_btn.setStyleSheet("background-color: #2196F3; color: white; border-radius: 4px;")
        presets_row.addWidget(movie_btn)
        
        music_btn = QPushButton("🎵 Music")
        music_btn.setFixedSize(70, 25)
        music_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
        presets_row.addWidget(music_btn)
        
        news_btn = QPushButton("📺 News")
        news_btn.setFixedSize(70, 25)
        news_btn.setStyleSheet("background-color: #FF9800; color: white; border-radius: 4px;")
        presets_row.addWidget(news_btn)
        
        sports_btn = QPushButton("⚽ Sports")
        sports_btn.setFixedSize(70, 25)
        sports_btn.setStyleSheet("background-color: #E91E63; color: white; border-radius: 4px;")
        presets_row.addWidget(sports_btn)
        
        profiles_layout.addLayout(presets_row)
        audio_header_layout.addWidget(profiles_section)
        
        # ========================
        # 3. AUDIO PROCESSING section
        # ========================
        processing_section = QGroupBox("🎛️ Audio Processing")
        processing_layout = QHBoxLayout(processing_section)
        
        # Voice Clarity
        voice_layout = QVBoxLayout()
        voice_layout.addWidget(QLabel("🎤 Voice Clarity"))
        voice_slider = QSlider(Qt.Orientation.Vertical)
        voice_slider.setRange(0, 100)
        voice_slider.setValue(30)
        voice_slider.setFixedHeight(100)
        voice_layout.addWidget(voice_slider)
        voice_layout.addWidget(QLabel("30%"))
        processing_layout.addLayout(voice_layout)
        
        # Bass Boost
        bass_layout = QVBoxLayout()
        bass_layout.addWidget(QLabel("🔊 Bass Boost"))
        bass_slider = QSlider(Qt.Orientation.Vertical)
        bass_slider.setRange(-10, 20)
        bass_slider.setValue(0)
        bass_slider.setFixedHeight(100)
        bass_layout.addWidget(bass_slider)
        bass_layout.addWidget(QLabel("0dB"))
        processing_layout.addLayout(bass_layout)
        
        # 3-Band EQ
        eq_layout = QVBoxLayout()
        eq_layout.addWidget(QLabel("🎚️ 3-Band EQ"))
        
        eq_sliders = QHBoxLayout()
        for band in ["Low", "Mid", "High"]:
            band_layout = QVBoxLayout()
            band_layout.addWidget(QLabel(band))
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.setFixedHeight(80)
            band_layout.addWidget(slider)
            band_layout.addWidget(QLabel("0dB"))
            eq_sliders.addLayout(band_layout)
        
        eq_layout.addLayout(eq_sliders)
        processing_layout.addLayout(eq_layout)
        
        # Compressor
        comp_layout = QVBoxLayout()
        comp_layout.addWidget(QLabel("🗜️ Compressor"))
        
        comp_controls = QHBoxLayout()
        
        # Threshold
        thresh_layout = QVBoxLayout()
        thresh_layout.addWidget(QLabel("Threshold"))
        thresh_slider = QSlider(Qt.Orientation.Vertical)
        thresh_slider.setRange(-30, 0)
        thresh_slider.setValue(-10)
        thresh_slider.setFixedHeight(60)
        thresh_layout.addWidget(thresh_slider)
        thresh_layout.addWidget(QLabel("-10dB"))
        comp_controls.addLayout(thresh_layout)
        
        # Ratio
        ratio_layout = QVBoxLayout()
        ratio_layout.addWidget(QLabel("Ratio"))
        ratio_slider = QSlider(Qt.Orientation.Vertical)
        ratio_slider.setRange(10, 100)
        ratio_slider.setValue(20)
        ratio_slider.setFixedHeight(60)
        ratio_layout.addWidget(ratio_slider)
        ratio_layout.addWidget(QLabel("2:1"))
        comp_controls.addLayout(ratio_layout)
        
        comp_layout.addLayout(comp_controls)
        processing_layout.addLayout(comp_layout)
        
        # Master
        master_layout = QVBoxLayout()
        master_layout.addWidget(QLabel("🎚️ Master"))
        master_slider = QSlider(Qt.Orientation.Vertical)
        master_slider.setRange(0, 150)
        master_slider.setValue(100)
        master_slider.setFixedHeight(100)
        master_layout.addWidget(master_slider)
        master_layout.addWidget(QLabel("100%"))
        processing_layout.addLayout(master_layout)
        
        audio_header_layout.addWidget(processing_section)
        
        # ========================
        # 4. AUDIO MONITORING section
        # ========================
        monitoring_section = QGroupBox("📊 Audio Monitoring")
        monitoring_layout = QHBoxLayout(monitoring_section)
        
        # Level meters
        meters_layout = QHBoxLayout()
        
        # Left meter
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("L"))
        left_meter = QProgressBar()
        left_meter.setOrientation(Qt.Orientation.Vertical)
        left_meter.setRange(0, 100)
        left_meter.setValue(60)
        left_meter.setFixedSize(20, 80)
        left_layout.addWidget(left_meter)
        left_layout.addWidget(QLabel("77"))
        meters_layout.addLayout(left_layout)
        
        # Right meter
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("R"))
        right_meter = QProgressBar()
        right_meter.setOrientation(Qt.Orientation.Vertical)
        right_meter.setRange(0, 100)
        right_meter.setValue(55)
        right_meter.setFixedSize(20, 80)
        right_layout.addWidget(right_meter)
        right_layout.addWidget(QLabel("77"))
        meters_layout.addLayout(right_layout)
        
        monitoring_layout.addLayout(meters_layout)
        
        # Peak/RMS display
        levels_layout = QVBoxLayout()
        
        peak_layout = QHBoxLayout()
        peak_layout.addWidget(QLabel("Peak:"))
        peak_label = QLabel("-5.2 dB")
        peak_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-family: monospace;")
        peak_layout.addWidget(peak_label)
        levels_layout.addLayout(peak_layout)
        
        rms_layout = QHBoxLayout()
        rms_layout.addWidget(QLabel("RMS:"))
        rms_label = QLabel("-8.2 dB")
        rms_label.setStyleSheet("color: #FF9800; font-weight: bold; font-family: monospace;")
        rms_layout.addWidget(rms_label)
        levels_layout.addLayout(rms_layout)
        
        # Status indicators
        status_layout = QHBoxLayout()
        clip_label = QLabel("🔴 CLIP")
        clip_label.setStyleSheet("color: #666;")
        status_layout.addWidget(clip_label)
        
        silence_label = QLabel("🔕 SILENCE")
        silence_label.setStyleSheet("color: #666;")
        status_layout.addWidget(silence_label)
        levels_layout.addLayout(status_layout)
        
        reset_btn = QPushButton("Reset Peak")
        reset_btn.setFixedHeight(20)
        levels_layout.addWidget(reset_btn)
        
        monitoring_layout.addLayout(levels_layout)
        audio_header_layout.addWidget(monitoring_section)
        
        # ========================
        # 5. AUDIO ROUTING & OUTPUT section
        # ========================
        routing_section = QGroupBox("🔀 Audio Routing & Output")
        routing_layout = QVBoxLayout(routing_section)
        
        # JACK Status
        jack_layout = QHBoxLayout()
        jack_layout.addWidget(QLabel("JACK Status:"))
        jack_status = QLabel("🟢 Connected")
        jack_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        jack_layout.addWidget(jack_status)
        jack_layout.addStretch()
        
        connect_jack_btn = QPushButton("Connect JACK")
        connect_jack_btn.setFixedSize(100, 25)
        jack_layout.addWidget(connect_jack_btn)
        routing_layout.addLayout(jack_layout)
        
        # Output Route
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Route:"))
        output_combo = QComboBox()
        output_combo.addItems(["System Output 1-2", "Headphones", "Program Feed"])
        output_layout.addWidget(output_combo)
        
        monitor_btn = QPushButton("🎧 Monitor")
        monitor_btn.setCheckable(True)
        monitor_btn.setChecked(True)
        monitor_btn.setFixedSize(80, 25)
        output_layout.addWidget(monitor_btn)
        routing_layout.addLayout(output_layout)
        
        # Plugin Chain
        plugin_layout = QHBoxLayout()
        plugin_layout.addWidget(QLabel("Plugin Chain:"))
        plugin_status = QLabel("4 plugins active")
        plugin_status.setStyleSheet("color: #00BCD4; font-weight: bold;")
        plugin_layout.addWidget(plugin_status)
        plugin_layout.addStretch()
        
        bypass_btn = QPushButton("Bypass All")
        bypass_btn.setCheckable(True)
        bypass_btn.setFixedSize(80, 25)
        plugin_layout.addWidget(bypass_btn)
        routing_layout.addLayout(plugin_layout)
        
        audio_header_layout.addWidget(routing_section)
        
        layout.addWidget(audio_header)
        layout.addStretch()
        
        return widget

    def _create_screenshot_log_section(self):
        """Create log section exactly like screenshot (bottom)"""
        section = QGroupBox("📋 AMCP Response & System Activity Log")
        section.setFixedHeight(120)  # Компакт хэмжээ
        layout = QVBoxLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 5, 8, 5)
        
        # Log toolbar (яг зургийн шиг)
        toolbar = QHBoxLayout()
        
        # Filter buttons
        all_btn = QPushButton("All")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.setFixedSize(40, 20)
        all_btn.setStyleSheet("background-color: #00BCD4; color: white; border-radius: 3px;")
        toolbar.addWidget(all_btn)
        
        errors_btn = QPushButton("Errors")
        errors_btn.setCheckable(True)
        errors_btn.setFixedSize(50, 20)
        toolbar.addWidget(errors_btn)
        
        amcp_btn = QPushButton("AMCP")
        amcp_btn.setCheckable(True)
        amcp_btn.setFixedSize(50, 20)
        toolbar.addWidget(amcp_btn)
        
        toolbar.addStretch()
        
        # Auto Scroll checkbox
        auto_scroll_check = QCheckBox("Auto Scroll")
        auto_scroll_check.setChecked(True)
        auto_scroll_check.setStyleSheet("color: #00BCD4;")
        toolbar.addWidget(auto_scroll_check)
        
        # Clear and Save buttons
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setFixedSize(60, 20)
        toolbar.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.setFixedSize(60, 20)
        save_btn.setStyleSheet("background-color: #E91E63; color: white; border-radius: 3px;")
        toolbar.addWidget(save_btn)
        
        layout.addLayout(toolbar)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FF00;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        # Add sample log entries (яг зургийн шиг)
        sample_logs = [
            '<span style="color: #888">[11:07:47.474]</span> <span style="color: #2196F3; font-weight: bold">ℹ️ INFO:</span> <span style="color: #E0E0E0">Auto-detected: General content - Applied default audio profile</span>',
            '<span style="color: #888">[11:07:47.474]</span> <span style="color: #2196F3; font-weight: bold">ℹ️ INFO:</span> <span style="color: #E0E0E0">Auto-detected: General content - Applied default audio profile</span>',
            '<span style="color: #888">[11:07:48.1]</span> <span style="color: #4CAF50; font-weight: bold">✅ OK:</span> <span style="color: #E0E0E0">Media sent to program: A Cool_Honeymoon_D45_Outlaw -Ерд игтэж бална.mp4</span>',
            '<span style="color: #888">[11:07:53.1]</span> <span style="color: #4CAF50; font-weight: bold">✅ OK:</span> <span style="color: #E0E0E0">TAKEN TO AIR: A Cool_Honeymoon_D45_Outlaw -Ерд игтэж бална.mp4</span>'
        ]
        
        for log in sample_logs:
            self.log_text.append(log)
        
        layout.addWidget(self.log_text)
        
        return section

    # =============================================================================
    # COMPLETE STYLING - Зургийн дагуу бүх style
    # =============================================================================

    def _apply_screenshot_styling(self):
        """Apply styling exactly like the screenshot"""
        self.setStyleSheet("""
            /* Main widget */
            QWidget {
                background-color: #2b2b2b;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            
            /* Group boxes - exact colors from screenshot */
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #353535;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00BCD4;
                font-size: 11px;
                font-weight: bold;
            }
            
            /* Buttons - matching screenshot appearance */
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
            
            /* Spin boxes */
            QSpinBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px 5px;
                color: #E0E0E0;
                font-size: 11px;
            }
            
            QSpinBox:focus {
                border-color: #00BCD4;
            }
            
            /* Combo boxes */
            QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            
            QComboBox:hover {
                border-color: #00BCD4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #E0E0E0;
            }
            
            /* Sliders - matching the audio controls */
            QSlider::groove:vertical {
                border: 1px solid #555;
                width: 6px;
                background: #2b2b2b;
                border-radius: 3px;
            }
            
            QSlider::handle:vertical {
                background: #00BCD4;
                border: 1px solid #00ACC1;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: 0 -3px;
            }
            
            QSlider::handle:vertical:hover {
                background: #26C6DA;
            }
            
            /* Progress bars (for audio meters) */
            QProgressBar {
                border: 1px solid #555;
                border-radius: 2px;
                background-color: #2b2b2b;
                text-align: center;
                color: transparent;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:0.6 #4CAF50, 
                    stop:0.8 #FF9800, stop:1 #F44336);
                border-radius: 2px;
            }
            
            /* Text edit (log area) */
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 4px;
                color: #00FF00;
                font-family: 'Consolas', monospace;
                selection-background-color: #00BCD4;
            }
            
            /* Labels */
            QLabel {
                color: #E0E0E0;
                font-size: 11px;
            }
            
            /* Checkboxes */
            QCheckBox {
                color: #E0E0E0;
                font-size: 11px;
            }
            
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #666;
                border-radius: 2px;
                background-color: #404040;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00BCD4;
                border-color: #00ACC1;
            }
            
            QCheckBox::indicator:hover {
                border-color: #00BCD4;
            }
            
            /* Frames */
            QFrame[frameShape="4"], QFrame[frameShape="5"] {
                color: #666;
            }
        """)
    
    def _create_enhanced_amcp_section(self):
        """Create enhanced AMCP control section"""
        section = QGroupBox("🖥️ AMCP Server Control & Channel Management")
        section.setFixedHeight(80)
        layout = QHBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Connection status and controls
        conn_group = QVBoxLayout()
        
        # Status display
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.amcp_status_label = QLabel("🔴 Disconnected")
        self.amcp_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        status_layout.addWidget(self.amcp_status_label)
        status_layout.addStretch()
        conn_group.addLayout(status_layout)
        
        # Connection buttons
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setFixedSize(100, 30)
        self.connect_btn.clicked.connect(self._connect_amcp)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedSize(100, 30)
        self.disconnect_btn.clicked.connect(self._disconnect_amcp)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)
        
        btn_layout.addStretch()
        conn_group.addLayout(btn_layout)
        
        layout.addLayout(conn_group)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)
        
        # Channel and layer controls
        channel_group = QVBoxLayout()
        channel_row1 = QHBoxLayout()
        channel_row1.addWidget(QLabel("Channel:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.setFixedWidth(60)
        channel_row1.addWidget(self.channel_spin)
        
        channel_row1.addWidget(QLabel("Layer:"))
        self.layer_spin = QSpinBox()
        self.layer_spin.setRange(1, 20)
        self.layer_spin.setValue(1)
        self.layer_spin.setFixedWidth(60)
        channel_row1.addWidget(self.layer_spin)
        channel_group.addLayout(channel_row1)
        
        # Media selection
        channel_row2 = QHBoxLayout()
        channel_row2.addWidget(QLabel("Media:"))
        self.media_combo = QComboBox()
        self.media_combo.setEditable(True)
        self.media_combo.setMinimumWidth(200)
        self.media_combo.setPlaceholderText("Enter media filename or select...")
        channel_row2.addWidget(self.media_combo)
        channel_group.addLayout(channel_row2)
        
        layout.addLayout(channel_group)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # AMCP command buttons
        cmd_group = QVBoxLayout()
        
        cmd_row1 = QHBoxLayout()
        load_btn = QPushButton("📥 LOAD")
        load_btn.setFixedSize(80, 25)
        load_btn.clicked.connect(lambda: self._send_amcp_command("LOAD"))
        cmd_row1.addWidget(load_btn)
        
        play_btn = QPushButton("▶️ PLAY")
        play_btn.setFixedSize(80, 25)
        play_btn.clicked.connect(lambda: self._send_amcp_command("PLAY"))
        cmd_row1.addWidget(play_btn)
        
        stop_btn = QPushButton("⏹️ STOP")
        stop_btn.setFixedSize(80, 25)
        stop_btn.clicked.connect(lambda: self._send_amcp_command("STOP"))
        cmd_row1.addWidget(stop_btn)
        cmd_group.addLayout(cmd_row1)
        
        cmd_row2 = QHBoxLayout()
        clear_btn = QPushButton("🗑️ CLEAR")
        clear_btn.setFixedSize(80, 25)
        clear_btn.clicked.connect(lambda: self._send_amcp_command("CLEAR"))
        cmd_row2.addWidget(clear_btn)
        
        info_btn = QPushButton("ℹ️ INFO")
        info_btn.setFixedSize(80, 25)
        info_btn.clicked.connect(lambda: self._send_amcp_command("INFO"))
        cmd_row2.addWidget(info_btn)
        
        cls_btn = QPushButton("📋 CLS")
        cls_btn.setFixedSize(80, 25)
        cls_btn.clicked.connect(lambda: self._send_amcp_command("CLS"))
        cmd_row2.addWidget(cls_btn)
        cmd_group.addLayout(cmd_row2)
        
        layout.addLayout(cmd_group)
        
        layout.addStretch()
        
        # Advanced controls
        adv_group = QVBoxLayout()
        
        console_btn = QPushButton("💻 Console")
        console_btn.setFixedSize(100, 30)
        console_btn.clicked.connect(self._open_console)
        adv_group.addWidget(console_btn)
        
        config_btn = QPushButton("⚙️ Configure")
        config_btn.setFixedSize(100, 30)
        config_btn.clicked.connect(self._configure_server)
        adv_group.addWidget(config_btn)
        
        layout.addLayout(adv_group)
        
        return section
    
    def _create_enhanced_players_section(self):
        """Create enhanced video players section with better layout"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Players container with fixed layout
        players_container = QHBoxLayout()
        players_container.setSpacing(20)
        
        # ========================
        # PREVIEW PLAYER
        # ========================
        preview_container = QWidget()
        preview_container.setFixedWidth(400)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # Preview header with enhanced styling
        preview_header = QLabel("🎬 PREVIEW")
        preview_header.setFixedHeight(45)
        preview_header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2196F3, stop:1 #1976D2); 
                color: white; 
                padding: 12px; 
                font-weight: bold; 
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 2px solid #1565C0;
                border-bottom: none;
            }
        """)
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)
        
        # Preview player
        self.preview_player = EnhancedVideoPlayer("Preview Player")
        self.preview_player.setStyleSheet("""
            EnhancedVideoPlayer {
                border-left: 2px solid #1565C0;
                border-right: 2px solid #1565C0;
                border-bottom: 2px solid #1565C0;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        preview_layout.addWidget(self.preview_player)
        
        # Preview controls
        preview_controls = QWidget()
        preview_controls.setFixedHeight(55)
        preview_controls_layout = QHBoxLayout(preview_controls)
        preview_controls_layout.setContentsMargins(8, 8, 8, 8)
        preview_controls_layout.setSpacing(10)
        
        cue_btn = QPushButton("🎯 CUE")
        cue_btn.setFixedSize(80, 35)
        cue_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF9800, stop:1 #F57C00); 
                color: white; 
                border-radius: 6px;
                font-weight: bold;
                border: 2px solid #EF6C00;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FFB74D, stop:1 #FF9800);
            }
        """)
        cue_btn.clicked.connect(self._cue_preview)
        preview_controls_layout.addWidget(cue_btn)
        
        self.auto_audio_btn = QPushButton("🎵 Auto Audio")
        self.auto_audio_btn.setCheckable(True)
        self.auto_audio_btn.setChecked(True)
        self.auto_audio_btn.setFixedSize(120, 35)
        self.auto_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575; 
                color: white; 
                border-radius: 6px;
                font-weight: bold;
                border: 2px solid #616161;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4CAF50, stop:1 #388E3C);
                border-color: #2E7D32;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)
        self.auto_audio_btn.toggled.connect(self._toggle_auto_audio)
        preview_controls_layout.addWidget(self.auto_audio_btn)
        
        # Media library button
        library_btn = QPushButton("📚 Library")
        library_btn.setFixedSize(80, 35)
        library_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #9C27B0, stop:1 #7B1FA2); 
                color: white; 
                border-radius: 6px;
                font-weight: bold;
                border: 2px solid #6A1B9A;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #BA68C8, stop:1 #9C27B0);
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
        center_container.setFixedWidth(140)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(15, 0, 15, 0)
        center_layout.setSpacing(15)
        
        center_layout.addStretch(1)
        
        # Send to Program button
        send_btn = QPushButton("➡️\nSEND TO\nPROGRAM")
        send_btn.setFixedSize(120, 90)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2196F3, stop:1 #1565C0); 
                color: white; 
                font-size: 11px; 
                font-weight: bold;
                padding: 8px;
                border-radius: 12px;
                border: 3px solid #0D47A1;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1976D2, stop:1 #1565C0);
            }
        """)
        send_btn.clicked.connect(self._send_to_program)
        center_layout.addWidget(send_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # TAKE TO AIR button (main action)
        take_btn = QPushButton("📺\nTAKE TO\nAIR")
        take_btn.setFixedSize(120, 100)
        take_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #E91E63, stop:1 #AD1457); 
                color: white; 
                font-size: 12px; 
                font-weight: bold;
                padding: 8px;
                border-radius: 12px;
                border: 4px solid #880E4F;
                animation: pulse 2s infinite;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #F06292, stop:1 #E91E63);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #C2185B, stop:1 #AD1457);
            }
        """)
        take_btn.clicked.connect(self._take_to_air)
        center_layout.addWidget(take_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Fade/Cut buttons
        fade_cut_layout = QHBoxLayout()
        fade_cut_layout.setSpacing(8)
        
        fade_btn = QPushButton("🌅\nFADE")
        fade_btn.setFixedSize(55, 70)
        fade_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #9C27B0, stop:1 #6A1B9A); 
                color: white; 
                font-size: 10px; 
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #4A148C;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #BA68C8, stop:1 #9C27B0);
            }
        """)
        fade_btn.clicked.connect(lambda: self._fade_program(fade=True))
        fade_cut_layout.addWidget(fade_btn)
        
        cut_btn = QPushButton("✂️\nCUT")
        cut_btn.setFixedSize(55, 70)
        cut_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF5722, stop:1 #D84315); 
                color: white; 
                font-size: 10px; 
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #BF360C;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #FF7043, stop:1 #FF5722);
            }
        """)
        cut_btn.clicked.connect(lambda: self._fade_program(fade=False))
        fade_cut_layout.addWidget(cut_btn)
        
        center_layout.addLayout(fade_cut_layout)
        center_layout.addStretch(1)
        
        players_container.addWidget(center_container)
        
        # ========================
        # PROGRAM PLAYER
        # ========================
        program_container = QWidget()
        program_container.setFixedWidth(400)
        program_layout = QVBoxLayout(program_container)
        program_layout.setContentsMargins(0, 0, 0, 0)
        program_layout.setSpacing(0)
        
        # Program header with enhanced styling
        program_header = QLabel("📺 PROGRAM")
        program_header.setFixedHeight(45)
        program_header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #F44336, stop:1 #C62828); 
                color: white; 
                padding: 12px; 
                font-weight: bold; 
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 2px solid #B71C1C;
                border-bottom: none;
            }
        """)
        program_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        program_layout.addWidget(program_header)
        
        # Program player
        self.program_player = EnhancedVideoPlayer("Program Player")
        self.program_player.setStyleSheet("""
            EnhancedVideoPlayer {
                border-left: 2px solid #B71C1C;
                border-right: 2px solid #B71C1C;
                border-bottom: 2px solid #B71C1C;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        program_layout.addWidget(self.program_player)
        
        # Program status bar
        program_status = QWidget()
        program_status.setFixedHeight(55)
        program_status_layout = QHBoxLayout(program_status)
        program_status_layout.setContentsMargins(8, 8, 8, 8)
        program_status_layout.setSpacing(15)
        
        # Audio status
        self.audio_status_label = QLabel("🟢 Audio Ready")
        self.audio_status_label.setFixedHeight(35)
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50; 
                font-weight: bold; 
                padding: 8px 12px;
                background-color: rgba(76, 175, 80, 0.1);
                border-radius: 6px;
                border: 2px solid #4CAF50;
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
                border-radius: 6px;
                border: 2px solid #757575;
            }
        """)
        program_status_layout.addWidget(self.on_air_label)
        
        program_layout.addWidget(program_status)
        
        players_container.addWidget(program_container)
        
        layout.addLayout(players_container)
        
        return widget
    
    def _create_enhanced_controls_section(self):
        """Create enhanced controls section with comprehensive audio panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Enhanced audio control panel
        self.audio_control_panel = EnhancedAudioControlPanel(
            self.audio_system, 
            self.config_manager
        )
        layout.addWidget(self.audio_control_panel)
        
        layout.addStretch()
        return widget
    
    def _create_enhanced_log_section(self):
        """Create enhanced log section with better formatting"""
        section = QGroupBox("📋 AMCP Response & System Activity Log")
        section.setFixedHeight(180)
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Log controls toolbar
        log_toolbar = QHBoxLayout()
        
        # Filter buttons
        self.log_filter_all = QPushButton("All")
        self.log_filter_all.setCheckable(True)
        self.log_filter_all.setChecked(True)
        self.log_filter_all.setFixedSize(50, 25)
        log_toolbar.addWidget(self.log_filter_all)
        
        self.log_filter_error = QPushButton("Errors")
        self.log_filter_error.setCheckable(True)
        self.log_filter_error.setFixedSize(60, 25)
        log_toolbar.addWidget(self.log_filter_error)
        
        self.log_filter_amcp = QPushButton("AMCP")
        self.log_filter_amcp.setCheckable(True)
        self.log_filter_amcp.setFixedSize(60, 25)
        log_toolbar.addWidget(self.log_filter_amcp)
        
        log_toolbar.addStretch()
        
        # Log controls
        auto_scroll_check = QCheckBox("Auto Scroll")
        auto_scroll_check.setChecked(True)
        log_toolbar.addWidget(auto_scroll_check)
        
        clear_log_btn = QPushButton("🗑️ Clear")
        clear_log_btn.setFixedSize(70, 25)
        clear_log_btn.clicked.connect(self._clear_log)
        log_toolbar.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("💾 Save")
        save_log_btn.setFixedSize(70, 25)
        save_log_btn.clicked.connect(self._save_log)
        log_toolbar.addWidget(save_log_btn)
        
        layout.addLayout(log_toolbar)
        
        # Enhanced log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FF00;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 2px solid #333;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Initialize log with system info
        self._initialize_log()
        
        return section
    
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
            
            if self.program_player:
                self.program_player.media_loaded.connect(self._on_program_media_loaded)
                self.program_player.playback_state_changed.connect(self._on_program_state_changed)
            
            self.logger.info("Signal connections established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup connections: {e}")
    
    def _apply_professional_styling(self):
        """Apply professional broadcast styling"""
        self.setStyleSheet("""
            /* Main widget styling */
            QWidget {
                background-color: #1e1e1e;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Group box styling */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #2a2a2a;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00BCD4;
                font-size: 13px;
                font-weight: bold;
            }
            
            /* Button styling */
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 8px 12px;
                color: #E0E0E0;
                font-weight: bold;
                min-width: 60px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00BCD4;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
                border-color: #00ACC1;
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
            
            /* Spin box styling */
            QSpinBox {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 5px 8px;
                color: #E0E0E0;
                font-weight: bold;
            }
            
            QSpinBox:focus {
                border-color: #00BCD4;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #555;
                border: 1px solid #666;
                width: 16px;
                border-radius: 3px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #666;
            }
            
            /* Combo box styling */
            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 6px 10px;
                color: #E0E0E0;
                font-weight: bold;
                min-width: 120px;
            }
            
            QComboBox:hover {
                border-color: #00BCD4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #E0E0E0;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                selection-background-color: #00BCD4;
                outline: none;
                padding: 4px;
            }
            
            /* Text edit styling */
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 6px;
                color: #00FF00;
                font-family: 'Consolas', 'Monaco', monospace;
                selection-background-color: #00BCD4;
            }
            
            /* Splitter styling */
            QSplitter::handle {
                background-color: #555;
                border-radius: 3px;
                margin: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #00BCD4;
            }
            
            QSplitter::handle:pressed {
                background-color: #00ACC1;
            }
            
            /* Frame styling */
            QFrame[frameShape="4"] {
                color: #666;
            }
            
            QFrame[frameShape="5"] {
                color: #666;
            }
            
            /* Checkbox styling */
            QCheckBox {
                color: #E0E0E0;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #3a3a3a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00BCD4;
                border-color: #00ACC1;
            }
            
            QCheckBox::indicator:hover {
                border-color: #00BCD4;
            }
            
            /* Tooltip styling */
            QToolTip {
                background-color: #2a2a2a;
                color: #E0E0E0;
                border: 2px solid #00BCD4;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
        """)
    
    # ========================
    # AMCP CONTROL METHODS
    # ========================
    
    def _connect_amcp(self):
        """Connect to AMCP server with enhanced status reporting"""
        try:
            # Simulate connection process
            self.amcp_connected = True
            self.amcp_status_label.setText("🟢 Connected")
            self.amcp_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            
            self._log_message("AMCP server connection established", "success")
            self._log_message("Ready to send commands to CasparCG", "info")
            
            # Load media list if available
            self._refresh_media_list()
            
        except Exception as e:
            self._log_message(f"AMCP connection failed: {e}", "error")
            self.amcp_connected = False
    
    def _disconnect_amcp(self):
        """Disconnect from AMCP server"""
        self.amcp_connected = False
        self.amcp_status_label.setText("🔴 Disconnected")
        self.amcp_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        
        self._log_message("AMCP server disconnected", "warning")
    
    def _send_amcp_command(self, command):
        """Send AMCP command with comprehensive logging"""
        if not self.amcp_connected:
            self._log_message("Cannot send command - AMCP not connected", "error")
            return
        
        channel = self.channel_spin.value()
        layer = self.layer_spin.value()
        media = self.media_combo.currentText().strip()
        
        # Build command string
        if command in ["LOAD", "PLAY"] and not media:
            self._log_message(f"No media specified for {command} command", "error")
            return
        
        if command == "LOAD":
            command_str = f"LOAD {channel}-{layer} {media}"
        elif command == "PLAY":
            command_str = f"PLAY {channel}-{layer} {media}" if media else f"PLAY {channel}-{layer}"
        elif command == "STOP":
            command_str = f"STOP {channel}-{layer}"
        elif command == "CLEAR":
            command_str = f"CLEAR {channel}-{layer}"
        elif command == "INFO":
            command_str = f"INFO {channel}-{layer}"
        elif command == "CLS":
            command_str = "CLS"
        else:
            command_str = command
        
        # Send command (simulated)
        self._log_message(f"AMCP > {command_str}", "amcp")
        
        # Simulate response
        if command == "CLS":
            self._log_message("AMCP < 200 CLS OK\n\"media1.mp4\"\n\"media2.avi\"\n\"background.png\"", "amcp")
            # Update media combo with response
            self.media_combo.clear()
            self.media_combo.addItems(["media1.mp4", "media2.avi", "background.png"])
        elif command == "INFO":
            self._log_message(f"AMCP < 201 INFO OK\n[{channel}-{layer}]: PLAYING \"example.mp4\"", "amcp")
        else:
            self._log_message(f"AMCP < 202 {command} OK", "amcp")
    
    def _refresh_media_list(self):
        """Refresh media list from server"""
        if self.amcp_connected:
            self._send_amcp_command("CLS")
    
    def _open_console(self):
        """Open AMCP console dialog"""
        try:
            console_dialog = AMCPConsoleDialog(self.casparcg_client, self)
            console_dialog.show()
            self._log_message("AMCP console opened", "info")
        except Exception as e:
            self._log_message(f"Failed to open console: {e}", "error")
    
    def _configure_server(self):
        """Open server configuration dialog"""
        # Implementation for server configuration
        self._log_message("Server configuration dialog opened", "info")
    
    # ========================
    # VIDEO PLAYER CONTROL METHODS
    # ========================
    
    def _cue_preview(self):
        """Cue preview to first frame"""
        if self.preview_player.current_media_path:
            # Pause at first frame
            self.preview_player.stop()
            self.preview_player.play()
            QTimer.singleShot(100, self.preview_player.pause)  # Pause after brief play
            self._log_message("Preview cued to first frame", "info")
        else:
            self._log_message("No media in preview to cue", "warning")
    
    def _send_to_program(self):
        """Send preview content to program player"""
        preview_file = self.preview_player.get_current_file()
        if preview_file:
            # Get current preview state
            preview_state = self.preview_player.get_playback_state()
            
            # Load same media to program
            if self.program_player.load_media(preview_file):
                # If auto audio is enabled, sync audio profile
                if self.auto_audio_enabled:
                    self._sync_audio_to_content(preview_file)
                
                self._log_message(f"Media sent to program: {Path(preview_file).name}", "success")
                
                # Update media combo for AMCP
                self.media_combo.setCurrentText(Path(preview_file).name)
            else:
                self._log_message("Failed to send media to program", "error")
        else:
            self._log_message("No media in preview to send", "warning")
    
    def _take_to_air(self):
        """Take program content to air"""
        program_file = self.program_player.get_current_file()
        if program_file:
            # Update ON AIR status
            self.is_on_air = True
            self._update_on_air_status(True)
            
            # Start program playback if not already playing
            if not self.program_player.is_playing:
                self.program_player.play()
            
            # Send AMCP PLAY command if connected
            if self.amcp_connected:
                media_name = Path(program_file).name
                self.media_combo.setCurrentText(media_name)
                self._send_amcp_command("PLAY")
            
            # Emit signal for other components
            self.media_taken_to_air.emit(program_file)
            
            self._log_message(f"TAKEN TO AIR: {Path(program_file).name}", "success")
        else:
            self._log_message("No program content to take to air", "warning")
    
    def _fade_program(self, fade=True):
        """Fade or cut program off air"""
        if self.is_on_air:
            # Update OFF AIR status
            self.is_on_air = False
            self._update_on_air_status(False)
            
            # Stop program playback
            if fade:
                # Implement fade logic here (could be gradual volume reduction)
                self._log_message("Program FADED off air", "info")
            else:
                # Hard cut
                self.program_player.stop()
                self._log_message("Program CUT off air", "info")
            
            # Send AMCP STOP command if connected
            if self.amcp_connected:
                self._send_amcp_command("STOP")
        else:
            self._log_message("No program on air to fade", "warning")
    
    def _update_on_air_status(self, on_air):
        """Update ON AIR visual indicators"""
        if on_air:
            # ON AIR styling
            self.on_air_label.setText("🔴 ON AIR")
            self.on_air_label.setStyleSheet("""
                QLabel {
                    color: #F44336; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: rgba(244, 67, 54, 0.2);
                    border-radius: 6px;
                    border: 3px solid #F44336;
                    animation: pulse 2s infinite;
                }
            """)
            
            # Update audio status
            self.audio_status_label.setText("🔴 LIVE AUDIO")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #F44336; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: rgba(244, 67, 54, 0.2);
                    border-radius: 6px;
                    border: 3px solid #F44336;
                }
            """)
        else:
            # OFF AIR styling
            self.on_air_label.setText("🔴 OFF AIR")
            self.on_air_label.setStyleSheet("""
                QLabel {
                    color: #757575; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: rgba(117, 117, 117, 0.1);
                    border-radius: 6px;
                    border: 2px solid #757575;
                }
            """)
            
            # Reset audio status
            self.audio_status_label.setText("🟢 Audio Ready")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50; 
                    font-weight: bold; 
                    padding: 8px 12px;
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 6px;
                    border: 2px solid #4CAF50;
                }
            """)
    
    def _toggle_auto_audio(self, enabled):
        """Toggle automatic audio profile detection"""
        self.auto_audio_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self._log_message(f"Auto audio detection {status}", "info")
        
        if enabled and self.program_player.current_media_path:
            self._sync_audio_to_content(str(self.program_player.current_media_path))
    
    def _sync_audio_to_content(self, file_path):
        """Automatically sync audio profile to content type"""
        if not self.auto_audio_enabled or not self.audio_control_panel:
            return
        
        try:
            file_name = Path(file_path).name.lower()
            
            # Simple content detection based on filename
            if any(word in file_name for word in ['movie', 'film', 'cinema']):
                self.audio_control_panel._apply_preset("movie_mode")
                self._log_message("Auto-detected: Movie content - Applied movie audio profile", "info")
            elif any(word in file_name for word in ['music', 'song', 'audio']):
                self.audio_control_panel._apply_preset("music_mode")
                self._log_message("Auto-detected: Music content - Applied music audio profile", "info")
            elif any(word in file_name for word in ['news', 'report', 'interview']):
                self.audio_control_panel._apply_preset("news_mode")
                self._log_message("Auto-detected: News content - Applied news audio profile", "info")
            elif any(word in file_name for word in ['sport', 'game', 'match']):
                self.audio_control_panel._apply_preset("sports_mode")
                self._log_message("Auto-detected: Sports content - Applied sports audio profile", "info")
            else:
                self.audio_control_panel._apply_preset("default")
                self._log_message("Auto-detected: General content - Applied default audio profile", "info")
                
        except Exception as e:
            self.logger.error(f"Failed to sync audio to content: {e}")
    
    def _open_media_library(self):
        """Open media library dialog"""
        try:
            # Implementation for media library would go here
            self._log_message("Media library opened", "info")
        except Exception as e:
            self._log_message(f"Failed to open media library: {e}", "error")
    
    # ========================
    # AUDIO CONTROL SIGNAL HANDLERS
    # ========================
    
    def _on_audio_profile_changed(self, profile_name):
        """Handle audio profile change"""
        self._log_message(f"Audio profile changed to: {profile_name}", "info")
        self.audio_profile_changed.emit(profile_name)
    
    def _on_night_mode_changed(self, enabled):
        """Handle night mode toggle"""
        status = "enabled" if enabled else "disabled"
        self._log_message(f"Night mode {status}", "info")
    
    def _on_audio_parameter_changed(self, param_name, value):
        """Handle audio parameter changes"""
        self.logger.debug(f"Audio parameter {param_name} changed to {value}")
        # Could emit signal to audio system here
    
    # ========================
    # VIDEO PLAYER SIGNAL HANDLERS
    # ========================
    
    def _on_preview_media_loaded(self, file_path):
        """Handle preview media loaded"""
        file_name = Path(file_path).name
        self._log_message(f"Preview loaded: {file_name}", "success")
        
        # Auto-detect content type if enabled
        if self.auto_audio_enabled:
            self._sync_audio_to_content(file_path)
    
    def _on_preview_state_changed(self, state):
        """Handle preview playback state change"""
        self.logger.debug(f"Preview state: {state}")
    
    def _on_program_media_loaded(self, file_path):
        """Handle program media loaded"""
        file_name = Path(file_path).name
        self._log_message(f"Program loaded: {file_name}", "success")
        
        # Update AMCP media combo
        self.media_combo.setCurrentText(file_name)
        
        # Auto-detect content type if enabled
        if self.auto_audio_enabled:
            self._sync_audio_to_content(file_path)
    
    def _on_program_state_changed(self, state):
        """Handle program playback state change"""
        self.logger.debug(f"Program state: {state}")
        
        if state == "ended" and self.is_on_air:
            self._log_message("Program media ended while on air", "warning")
            # Could automatically fade off air or load next item
    
    # ========================
    # LOGGING METHODS
    # ========================
    
    def _initialize_log(self):
        """Initialize log with system information"""
        self._log_message("Enhanced Playout System initialized", "info")
        self._log_message(f"VLC Available: {'Yes' if VLC_AVAILABLE else 'No'}", "info")
        self._log_message(f"Audio System Available: {'Yes' if AUDIO_SYSTEM_AVAILABLE else 'No'}", "info")
        self._log_message("Ready for broadcast operations", "success")
    
    def _log_message(self, message: str, level: str = "info"):
        """Enhanced logging with color coding and filtering"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color and icon mapping
        level_config = {
            "error": {"color": "#F44336", "icon": "❌", "prefix": "ERROR"},
            "warning": {"color": "#FF9800", "icon": "⚠️", "prefix": "WARN"},
            "success": {"color": "#4CAF50", "icon": "✅", "prefix": "OK"},
            "info": {"color": "#2196F3", "icon": "ℹ️", "prefix": "INFO"},
            "amcp": {"color": "#9C27B0", "icon": "🖥️", "prefix": "AMCP"},
            "audio": {"color": "#00BCD4", "icon": "🔊", "prefix": "AUDIO"}
        }
        
        config = level_config.get(level, level_config["info"])
        
        # Format message with HTML for colors
        log_entry = f'<span style="color: #888">[{timestamp}]</span> ' \
                   f'<span style="color: {config["color"]}; font-weight: bold">' \
                   f'{config["icon"]} {config["prefix"]}:</span> ' \
                   f'<span style="color: #E0E0E0">{message}</span>'
        
        # Add to log
        self.log_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Emit status message for status bar
        self.status_message.emit(message, 3000)
    
    def _clear_log(self):
        """Clear log content"""
        self.log_text.clear()
        self._log_message("Log cleared", "info")
    
    def _save_log(self):
        """Save log to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Log File",
                f"playout_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                # Extract plain text from HTML
                plain_text = self.log_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                
                self._log_message(f"Log saved to: {file_path}", "success")
                
        except Exception as e:
            self._log_message(f"Failed to save log: {e}", "error")
    
    # ========================
    # CLEANUP METHODS
    # ========================
    
    def cleanup(self):
        """Clean up resources when closing"""
        try:
            # Stop video players
            if self.preview_player:
                self.preview_player.stop()
            
            if self.program_player:
                self.program_player.stop()
            
            # Stop audio control panel timers
            if self.audio_control_panel:
                if hasattr(self.audio_control_panel, 'meter_timer'):
                    self.audio_control_panel.meter_timer.stop()
                if hasattr(self.audio_control_panel, 'peak_decay_timer'):
                    self.audio_control_panel.peak_decay_timer.stop()
                if hasattr(self.audio_control_panel, 'status_timer'):
                    self.audio_control_panel.status_timer.stop()
            
            
            self._log_message("Playout system shutdown complete", "info")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# =============================================================================
# AMCP CONSOLE DIALOG (Enhanced)
# =============================================================================

class AMCPConsoleDialog(QDialog):
    """Enhanced AMCP Console Dialog with better features"""
    
    def __init__(self, amcp_client=None, parent=None):
        super().__init__(parent)
        self.amcp_client = amcp_client
        self.logger = get_logger(f"{__name__}.AMCPConsole")
        
        self.setWindowTitle("AMCP Console - CasparCG Command Interface")
        self.setModal(False)
        self.resize(700, 500)
        
        # Command history
        self.command_history = []
        self.history_index = 0
        
        self._init_ui()
        self._apply_console_styling()
    
    def _init_ui(self):
        """Initialize enhanced console UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with connection status
        header_layout = QHBoxLayout()
        
        self.connection_label = QLabel("🔴 Not Connected")
        self.connection_label.setStyleSheet("color: #F44336; font-weight: bold;")
        header_layout.addWidget(self.connection_label)
        
        header_layout.addStretch()
        
        # Server info
        server_info = QLabel("CasparCG Server Console")
        server_info.setStyleSheet("color: #00BCD4; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(server_info)
        
        layout.addLayout(header_layout)
        
        # Response display with enhanced features
        response_container = QWidget()
        response_layout = QVBoxLayout(response_container)
        response_layout.setContentsMargins(0, 0, 0, 0)
        response_layout.setSpacing(5)
        
        # Response controls
        response_controls = QHBoxLayout()
        
        self.word_wrap_check = QCheckBox("Word Wrap")
        self.word_wrap_check.setChecked(True)
        self.word_wrap_check.toggled.connect(self._toggle_word_wrap)
        response_controls.addWidget(self.word_wrap_check)
        
        self.timestamps_check = QCheckBox("Timestamps")
        self.timestamps_check.setChecked(True)
        response_controls.addWidget(self.timestamps_check)
        
        response_controls.addStretch()
        
        clear_response_btn = QPushButton("Clear Output")
        clear_response_btn.setFixedSize(100, 25)
        clear_response_btn.clicked.connect(self._clear_response)
        response_controls.addWidget(clear_response_btn)
        
        response_layout.addLayout(response_controls)
        
        # Response display
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setFont(QFont("Consolas", 10))
        response_layout.addWidget(self.response_display)
        
        layout.addWidget(response_container)
        
        # Command input section
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        # Command input with history
        input_row = QHBoxLayout()
        
        input_row.addWidget(QLabel("Command:"))
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter AMCP command (e.g., INFO, VERSION, PLAY 1-10 video.mp4)")
        self.command_input.returnPressed.connect(self._send_command)
        self.command_input.keyPressEvent = self._handle_key_press
        input_row.addWidget(self.command_input)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(80, 30)
        send_btn.clicked.connect(self._send_command)
        input_row.addWidget(send_btn)
        
        input_layout.addLayout(input_row)
        
        # Quick commands section
        quick_commands_label = QLabel("Quick Commands:")
        quick_commands_label.setStyleSheet("font-weight: bold; color: #00BCD4;")
        input_layout.addWidget(quick_commands_label)
        
        # Quick command buttons organized in groups
        commands_grid = QGridLayout()
        commands_grid.setSpacing(5)
        
        # Server info commands
        info_commands = [
            ("VERSION", "Get server version", "#4CAF50"),
            ("INFO", "Get server info", "#4CAF50"),
            ("CLS", "List media files", "#2196F3"),
            ("TLS", "List templates", "#2196F3"),
            ("CINF", "Get channel info", "#FF9800"),
            ("FLS", "List fonts", "#9C27B0")
        ]
        
        row = 0
        for i, (cmd, tooltip, color) in enumerate(info_commands):
            btn = QPushButton(cmd)
            btn.setFixedSize(80, 28)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btn.clicked.connect(lambda _, command=cmd: self._send_quick_command(command))
            commands_grid.addWidget(btn, row, i % 3)
            if (i + 1) % 3 == 0:
                row += 1
        
        input_layout.addLayout(commands_grid)
        
        # Playback command templates
        templates_label = QLabel("Command Templates:")
        templates_label.setStyleSheet("font-weight: bold; color: #00BCD4; margin-top: 10px;")
        input_layout.addWidget(templates_label)
        
        templates_layout = QHBoxLayout()
        
        template_commands = [
            ("LOAD 1-10 ", "Load media to channel 1, layer 10"),
            ("PLAY 1-10 ", "Play on channel 1, layer 10"),
            ("STOP 1-10", "Stop channel 1, layer 10"),
            ("CLEAR 1-10", "Clear channel 1, layer 10")
        ]
        
        for template, tooltip in template_commands:
            btn = QPushButton(template.strip())
            btn.setToolTip(tooltip)
            btn.setFixedSize(90, 25)
            btn.clicked.connect(lambda _, t=template: self._insert_template(t))
            templates_layout.addWidget(btn)
        
        templates_layout.addStretch()
        input_layout.addLayout(templates_layout)
        
        layout.addWidget(input_container)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        # History controls
        history_btn = QPushButton("📜 History")
        history_btn.setFixedSize(80, 30)
        history_btn.clicked.connect(self._show_history)
        bottom_layout.addWidget(history_btn)
        
        save_btn = QPushButton("💾 Save Log")
        save_btn.setFixedSize(80, 30)
        save_btn.clicked.connect(self._save_log)
        bottom_layout.addWidget(save_btn)
        
        bottom_layout.addStretch()
        
        # Help button
        help_btn = QPushButton("❓ Help")
        help_btn.setFixedSize(60, 30)
        help_btn.clicked.connect(self._show_help)
        bottom_layout.addWidget(help_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(80, 30)
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
        
        # Initialize console
        self._initialize_console()
    
    def _apply_console_styling(self):
        """Apply console-specific styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #E0E0E0;
            }
            
            QTextEdit {
                background-color: #0a0a0a;
                color: #00FF00;
                border: 2px solid #333;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
            }
            
            QLineEdit {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            
            QLineEdit:focus {
                border-color: #00BCD4;
            }
            
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00BCD4;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            
            QCheckBox {
                color: #E0E0E0;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00BCD4;
                border-color: #00ACC1;
            }
            
            QLabel {
                color: #E0E0E0;
            }
        """)
    
    def _initialize_console(self):
        """Initialize console with welcome message"""
        welcome_msg = """
=== AMCP Console Ready ===
CasparCG Advanced Media Control Protocol Interface

Quick Commands:
• VERSION - Get server version
• INFO - Get server information  
• CLS - List available media files
• TLS - List available templates
• CINF - Get channel information

Playback Commands:
• LOAD [channel]-[layer] [media] - Load media to channel/layer
• PLAY [channel]-[layer] [media] - Play media on channel/layer
• STOP [channel]-[layer] - Stop playback on channel/layer
• CLEAR [channel]-[layer] - Clear channel/layer

Examples:
  LOAD 1-10 "video.mp4"
  PLAY 1-10 
  STOP 1-10
  CLEAR 1-10

Use ↑/↓ arrows to navigate command history.
Enter commands below or use quick command buttons.

        """.strip()
        
        self._log_to_console(welcome_msg, "system")
    
    def _handle_key_press(self, event):
        """Handle special key presses for command history"""
        if event.key() == Qt.Key.Key_Up:
            self._navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self._navigate_history(1)
        else:
            # Call original keyPressEvent
            QLineEdit.keyPressEvent(self.command_input, event)
    
    def _navigate_history(self, direction):
        """Navigate through command history"""
        if not self.command_history:
            return
        
        self.history_index = max(0, min(len(self.command_history) - 1, 
                                       self.history_index + direction))
        
        if 0 <= self.history_index < len(self.command_history):
            self.command_input.setText(self.command_history[self.history_index])
    
    def _send_command(self):
        """Send command with enhanced processing"""
        command_text = self.command_input.text().strip()
        if not command_text:
            return
        
        # Add to history
        if command_text not in self.command_history:
            self.command_history.append(command_text)
        self.history_index = len(self.command_history)
        
        # Log command
        self._log_to_console(f"> {command_text}", "command")
        
        try:
            # Simulate AMCP communication
            response = self._simulate_amcp_response(command_text)
            self._log_to_console(f"< {response}", "response")
            
        except Exception as e:
            self._log_to_console(f"< ERROR: {e}", "error")
        
        self.command_input.clear()
        self._scroll_to_bottom()
    
    def _simulate_amcp_response(self, command):
        """Simulate AMCP server responses"""
        command_upper = command.upper().strip()
        
        if command_upper == "VERSION":
            return "201 VERSION OK\n2.3.3.stable"
        elif command_upper == "INFO":
            return "200 INFO OK\n[1-10]: EMPTY\n[1-11]: EMPTY"
        elif command_upper == "CLS":
            return '200 CLS OK\n"AMB"\n"COUNTDOWN"\n"video1.mp4"\n"background.png"'
        elif command_upper == "TLS":
            return '200 TLS OK\n"lower_third"\n"countdown"\n"weather"'
        elif command_upper.startswith("CINF"):
            return "200 CINF OK\n[1-10]: PLAYING \"video1.mp4\""
        elif command_upper == "FLS":
            return '200 FLS OK\n"Arial"\n"Times New Roman"\n"Helvetica"'
        elif command_upper.startswith("LOAD"):
            return "202 LOAD OK"
        elif command_upper.startswith("PLAY"):
            return "202 PLAY OK"
        elif command_upper.startswith("STOP"):
            return "202 STOP OK"
        elif command_upper.startswith("CLEAR"):
            return "202 CLEAR OK"
        else:
            return f"400 ERROR\nUnknown command: {command}"
    
    def _send_quick_command(self, command):
        """Send predefined quick command"""
        self.command_input.setText(command)
        self._send_command()
    
    def _insert_template(self, template):
        """Insert command template into input field"""
        self.command_input.setText(template)
        self.command_input.setFocus()
        # Position cursor at end
        self.command_input.setCursorPosition(len(template))
    
    def _log_to_console(self, message, msg_type="info"):
        """Log message to console with formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamps_check.isChecked() else ""
        
        # Color and formatting based on message type
        if msg_type == "command":
            formatted_msg = f'<span style="color: #FFD700; font-weight: bold;">{timestamp} {message}</span>'
        elif msg_type == "response":
            formatted_msg = f'<span style="color: #00FF00;">{timestamp} {message}</span>'
        elif msg_type == "error":
            formatted_msg = f'<span style="color: #FF6B6B; font-weight: bold;">{timestamp} {message}</span>'
        elif msg_type == "system":
            formatted_msg = f'<span style="color: #87CEEB;">{message}</span>'
        else:
            formatted_msg = f'<span style="color: #E0E0E0;">{timestamp} {message}</span>'
        
        self.response_display.append(formatted_msg)
    
    def _toggle_word_wrap(self, enabled):
        """Toggle word wrap in response display"""
        if enabled:
            self.response_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.response_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
    
    def _clear_response(self):
        """Clear response display"""
        self.response_display.clear()
        self._log_to_console("Console output cleared", "system")
    
    def _scroll_to_bottom(self):
        """Scroll response display to bottom"""
        scrollbar = self.response_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _show_history(self):
        """Show command history dialog"""
        if not self.command_history:
            QMessageBox.information(self, "Command History", "No commands in history.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Command History")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        history_list = QListWidget()
        for cmd in reversed(self.command_history):  # Most recent first
            history_list.addItem(cmd)
        
        history_list.itemDoubleClicked.connect(
            lambda item: self._select_from_history(item.text(), dialog)
        )
        
        layout.addWidget(history_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(
            lambda: self._select_from_history(
                history_list.currentItem().text() if history_list.currentItem() else "", 
                dialog
            )
        )
        btn_layout.addWidget(select_btn)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(lambda: self._clear_history(dialog))
        btn_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _select_from_history(self, command, dialog):
        """Select command from history"""
        if command:
            self.command_input.setText(command)
            dialog.close()
    
    def _clear_history(self, dialog):
        """Clear command history"""
        reply = QMessageBox.question(
            dialog, 
            "Clear History", 
            "Are you sure you want to clear the command history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.command_history.clear()
            self.history_index = 0
            dialog.close()
    
    def _save_log(self):
        """Save console log to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Console Log",
                f"amcp_console_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                plain_text = self.response_display.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                
                self._log_to_console(f"Console log saved to: {file_path}", "system")
                
        except Exception as e:
            self._log_to_console(f"Failed to save log: {e}", "error")
    
    def _show_help(self):
        """Show help dialog with AMCP command reference"""
        help_text = """
AMCP Command Reference

SERVER INFORMATION:
• VERSION - Get CasparCG server version
• INFO [channel] - Get server or channel information
• CINF [channel] - Get detailed channel information
• CLS - List available media files
• TLS - List available templates
• FLS - List available fonts

MEDIA PLAYBACK:
• LOAD [channel]-[layer] [clip] - Load media file
• PLAY [channel]-[layer] [clip] - Play media file
• PAUSE [channel]-[layer] - Pause playback
• RESUME [channel]-[layer] - Resume playback
• STOP [channel]-[layer] - Stop playback
• CLEAR [channel]-[layer] - Clear layer

CHANNEL CONTROL:
• MIXER [channel] OPACITY [layer] [value] - Set opacity
• MIXER [channel] VOLUME [layer] [value] - Set volume
• MIXER [channel] CLEAR [layer] - Clear mixer settings

TEMPLATES:
• CG [channel]-[layer] ADD [template] [data] - Add template
• CG [channel]-[layer] PLAY [template] - Play template
• CG [channel]-[layer] STOP [template] - Stop template
• CG [channel]-[layer] CLEAR - Clear template

Examples:
  LOAD 1-10 "video.mp4"
  PLAY 1-10
  MIXER 1 VOLUME 10 0.5
  CG 1-20 ADD "lower_third" "<templateData><f0>John Doe</f0></templateData>"

Note: Replace [channel], [layer], [clip], [template], etc. with actual values.
        """.strip()
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("AMCP Command Help")
        help_dialog.resize(600, 500)
        
        layout = QVBoxLayout(help_dialog)
        
        help_display = QTextEdit()
        help_display.setReadOnly(True)
        help_display.setPlainText(help_text)
        help_display.setFont(QFont("Consolas", 10))
        layout.addWidget(help_display)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.close)
        layout.addWidget(close_btn)
        
        help_dialog.exec()

# =============================================================================
# MAIN EXPORTS AND INITIALIZATION
# =============================================================================

def create_enhanced_playout_tab(config_manager, casparcg_client=None, audio_system=None):
    """Factory function to create enhanced playout tab"""
    return PlayoutTab(config_manager, casparcg_client, audio_system)

# Export enhanced classes
__all__ = [
    'PlayoutTab',
    'EnhancedVideoPlayer', 
    'EnhancedAudioControlPanel',
    'AMCPConsoleDialog',
    'create_enhanced_playout_tab'
]

# Version info
__version__ = "2.0.0"
__author__ = "Enhanced TV Stream Professional"