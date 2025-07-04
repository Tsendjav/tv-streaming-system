#!/usr/bin/env python3
"""
Professional Audio Control Panel Component
Advanced audio processing and control system
"""

import logging
import threading
import time
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

def get_logger(name):
    return logging.getLogger(name)


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


class ResponsiveAudioControlPanel(QWidget):
    """Responsive professional audio control panel"""
    
    # Signals
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
        self.is_compact = False
        
        # Initialize audio system components
        if AUDIO_SYSTEM_AVAILABLE and not self.audio_system:
            try:
                self.audio_system = TVAudioSystem("playout_audio_client")
                print("🎵 Audio system initialized for playout tab")
            except Exception as e:
                print(f"⚠️ Failed to initialize audio system: {e}")
                self.audio_system = None
        
        # Set minimum size
        self.setMinimumSize(300, 400)
        
        self._init_ui()
        self._start_audio_monitoring()
        
        # Install event filter for responsive behavior
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events for responsive behavior"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle widget resize for responsive behavior"""
        width = size.width()
        height = size.height()
        
        # Determine if compact mode is needed
        is_compact = width < 350 or height < 500
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_layout_for_size()
    
    def _update_layout_for_size(self):
        """Update layout based on size"""
        if self.is_compact:
            # Compact mode - hide some elements, make others smaller
            self._switch_to_compact_mode()
        else:
            # Full mode - show all elements
            self._switch_to_full_mode()
    
    def _switch_to_compact_mode(self):
        """Switch to compact mode layout"""
        # Hide or minimize certain elements
        if hasattr(self, 'eq_group'):
            self.eq_group.setVisible(False)
        if hasattr(self, 'monitoring_group'):
            self.monitoring_group.setMaximumHeight(100)
        
        # Make buttons smaller
        self._update_button_sizes(compact=True)
    
    def _switch_to_full_mode(self):
        """Switch to full mode layout"""
        # Show all elements
        if hasattr(self, 'eq_group'):
            self.eq_group.setVisible(True)
        if hasattr(self, 'monitoring_group'):
            self.monitoring_group.setMaximumHeight(16777215)  # No limit
        
        # Make buttons normal size
        self._update_button_sizes(compact=False)
    
    def _update_button_sizes(self, compact=False):
        """Update button sizes for responsive behavior"""
        if compact:
            height = 30
            font_size = "10px"
        else:
            height = 35
            font_size = "12px"
        
        # Update profile buttons
        if hasattr(self, 'profile_buttons'):
            for btn in self.profile_buttons.values():
                btn.setFixedHeight(height)
                current_style = btn.styleSheet()
                new_style = current_style.replace("font-size: 12px", f"font-size: {font_size}")
                btn.setStyleSheet(new_style)
    
    def _init_ui(self):
        """Initialize user interface"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Header with audio system status
        self._create_header()
        
        # Master Volume Control
        self._create_volume_controls()
        
        # Audio Profiles
        self._create_audio_profiles()
        
        # Special Audio Modes
        self._create_special_modes()
        
        # Real-time Audio Monitoring
        self._create_monitoring()
        
        # Equalizer (will be hidden in compact mode)
        self._create_equalizer()
        
        # Add stretch to fill remaining space
        self.main_layout.addStretch()
    
    def _create_header(self):
        """Create header with audio system status"""
        header_layout = QHBoxLayout()
        
        header = QLabel("🔊 Audio Control")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px; 
                font-weight: bold; 
                color: #00BCD4;
                background-color: #333;
                padding: 8px;
                border-radius: 6px;
            }
        """)
        header_layout.addWidget(header)
        
        # Audio system status
        audio_status = "🟢 Active" if AUDIO_SYSTEM_AVAILABLE and self.audio_system else "🔴 Offline"
        self.audio_system_status = QLabel(audio_status)
        self.audio_system_status.setStyleSheet("""
            QLabel {
                font-size: 10px;
                font-weight: bold;
                color: #4CAF50;
                padding: 6px;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.15);
            }
        """)
        header_layout.addWidget(self.audio_system_status)
        
        self.main_layout.addLayout(header_layout)
    
    def _create_volume_controls(self):
        """Create volume and dynamics controls"""
        self.volume_group = QGroupBox("Master Volume & Dynamics")
        self.volume_group.setStyleSheet(self._get_group_style())
        volume_layout = QVBoxLayout(self.volume_group)
        volume_layout.setSpacing(8)
        volume_layout.setContentsMargins(10, 10, 10, 10)
        
        # Master volume
        master_layout = QHBoxLayout()
        master_label = QLabel("Master Volume:")
        master_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        master_layout.addWidget(master_label)
        
        self.master_slider = QSlider(Qt.Orientation.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(80)
        self.master_slider.setStyleSheet(self._get_slider_style())
        self.master_slider.valueChanged.connect(self._on_volume_changed)
        master_layout.addWidget(self.master_slider)
        
        self.master_label = QLabel("80%")
        self.master_label.setFixedWidth(35)
        self.master_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #00BCD4;")
        master_layout.addWidget(self.master_label)
        volume_layout.addLayout(master_layout)
        
        # Limiter/Compressor controls
        dynamics_layout = QHBoxLayout()
        
        self.limiter_btn = QPushButton("🛡️ Limiter")
        self.limiter_btn.setCheckable(True)
        self.limiter_btn.setFixedHeight(30)
        self.limiter_btn.setStyleSheet(self._get_button_style())
        self.limiter_btn.toggled.connect(self._toggle_limiter)
        dynamics_layout.addWidget(self.limiter_btn)
        
        self.compressor_btn = QPushButton("🎚️ Compressor")
        self.compressor_btn.setCheckable(True)
        self.compressor_btn.setFixedHeight(30)
        self.compressor_btn.setStyleSheet(self._get_button_style())
        self.compressor_btn.toggled.connect(self._toggle_compressor)
        dynamics_layout.addWidget(self.compressor_btn)
        
        volume_layout.addLayout(dynamics_layout)
        self.main_layout.addWidget(self.volume_group)
    
    def _create_audio_profiles(self):
        """Create audio processing profiles"""
        self.profiles_group = QGroupBox("Audio Processing Profiles")
        self.profiles_group.setStyleSheet(self._get_group_style())
        profiles_layout = QVBoxLayout(self.profiles_group)
        profiles_layout.setSpacing(6)
        profiles_layout.setContentsMargins(10, 10, 10, 10)
        
        # Profile buttons
        self.profile_buttons = {}
        profiles = ["Default", "Movie", "Music", "News", "Sports"]
        for profile in profiles:
            btn = QPushButton(f"🎯 {profile}")
            btn.setFixedHeight(30)
            btn.setStyleSheet(self._get_profile_button_style())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=profile: self._apply_preset(p.lower()))
            self.profile_buttons[profile.lower()] = btn
            profiles_layout.addWidget(btn)
        
        # Set default as checked
        self.profile_buttons["default"].setChecked(True)
        self.main_layout.addWidget(self.profiles_group)
    
    def _create_special_modes(self):
        """Create special audio modes"""
        self.special_group = QGroupBox("Special Audio Modes")
        self.special_group.setStyleSheet(self._get_group_style())
        special_layout = QVBoxLayout(self.special_group)
        special_layout.setContentsMargins(10, 10, 10, 10)
        
        special_buttons_layout = QHBoxLayout()
        
        self.night_mode_btn = QPushButton("🌙 Night Mode")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setFixedHeight(35)
        self.night_mode_btn.setStyleSheet(self._get_special_button_style("#9C27B0"))
        self.night_mode_btn.toggled.connect(self._on_night_mode_toggled)
        special_buttons_layout.addWidget(self.night_mode_btn)
        
        self.dialogue_btn = QPushButton("🎙️ Dialogue+")
        self.dialogue_btn.setCheckable(True)
        self.dialogue_btn.setFixedHeight(35)
        self.dialogue_btn.setStyleSheet(self._get_special_button_style("#FF9800"))
        self.dialogue_btn.toggled.connect(self._toggle_dialogue_enhancement)
        special_buttons_layout.addWidget(self.dialogue_btn)
        
        special_layout.addLayout(special_buttons_layout)
        
        # Bass boost control
        bass_layout = QHBoxLayout()
        bass_label = QLabel("Bass Boost:")
        bass_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        bass_layout.addWidget(bass_label)
        
        self.bass_slider = QSlider(Qt.Orientation.Horizontal)
        self.bass_slider.setRange(0, 12)
        self.bass_slider.setValue(0)
        self.bass_slider.setStyleSheet(self._get_slider_style())
        self.bass_slider.valueChanged.connect(self._on_bass_changed)
        bass_layout.addWidget(self.bass_slider)
        
        self.bass_label = QLabel("0dB")
        self.bass_label.setFixedWidth(35)
        self.bass_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #FF9800;")
        bass_layout.addWidget(self.bass_label)
        special_layout.addLayout(bass_layout)
        
        self.main_layout.addWidget(self.special_group)
    
    def _create_monitoring(self):
        """Create real-time audio monitoring"""
        self.monitoring_group = QGroupBox("Audio Monitoring")
        self.monitoring_group.setStyleSheet(self._get_group_style())
        monitoring_layout = QVBoxLayout(self.monitoring_group)
        monitoring_layout.setSpacing(6)
        monitoring_layout.setContentsMargins(10, 10, 10, 10)
        
        # Level meters
        levels_layout = QVBoxLayout()
        
        # Left channel
        left_layout = QHBoxLayout()
        left_label = QLabel("L:")
        left_label.setStyleSheet("font-weight: bold; font-size: 11px; min-width: 15px;")
        left_layout.addWidget(left_label)
        
        self.left_meter = QProgressBar()
        self.left_meter.setRange(0, 100)
        self.left_meter.setValue(75)
        self.left_meter.setFixedHeight(18)
        self.left_meter.setStyleSheet(self._get_meter_style())
        left_layout.addWidget(self.left_meter)
        
        self.left_peak = QLabel("-12dB")
        self.left_peak.setStyleSheet("font-size: 9px; color: #4CAF50; min-width: 40px;")
        left_layout.addWidget(self.left_peak)
        levels_layout.addLayout(left_layout)
        
        # Right channel
        right_layout = QHBoxLayout()
        right_label = QLabel("R:")
        right_label.setStyleSheet("font-weight: bold; font-size: 11px; min-width: 15px;")
        right_layout.addWidget(right_label)
        
        self.right_meter = QProgressBar()
        self.right_meter.setRange(0, 100)
        self.right_meter.setValue(78)
        self.right_meter.setFixedHeight(18)
        self.right_meter.setStyleSheet(self._get_meter_style())
        right_layout.addWidget(self.right_meter)
        
        self.right_peak = QLabel("-9dB")
        self.right_peak.setStyleSheet("font-size: 9px; color: #4CAF50; min-width: 40px;")
        right_layout.addWidget(self.right_peak)
        levels_layout.addLayout(right_layout)
        
        monitoring_layout.addLayout(levels_layout)
        self.main_layout.addWidget(self.monitoring_group)
    
    def _create_equalizer(self):
        """Create professional equalizer"""
        self.eq_group = QGroupBox("Equalizer")
        self.eq_group.setStyleSheet(self._get_group_style())
        eq_layout = QVBoxLayout(self.eq_group)
        eq_layout.setContentsMargins(10, 10, 10, 10)
        
        # EQ controls
        eq_controls_layout = QHBoxLayout()
        
        eq_reset_btn = QPushButton("Reset")
        eq_reset_btn.setFixedHeight(25)
        eq_reset_btn.setStyleSheet(self._get_button_style())
        eq_reset_btn.clicked.connect(self._reset_eq)
        eq_controls_layout.addWidget(eq_reset_btn)
        
        eq_preset_combo = QComboBox()
        eq_preset_combo.addItems(["Flat", "Voice", "Music", "Cinema", "Custom"])
        eq_preset_combo.setFixedHeight(25)
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
            band_label.setStyleSheet("font-size: 8px; color: #AAA;")
            
            band_slider = QSlider(Qt.Orientation.Vertical)
            band_slider.setRange(-12, 12)
            band_slider.setValue(0)
            band_slider.setFixedHeight(50)
            band_slider.setFixedWidth(20)
            band_slider.setStyleSheet(self._get_eq_slider_style())
            band_slider.valueChanged.connect(lambda v, b=band: self._on_eq_changed(b, v))
            self.eq_sliders[band] = band_slider
            
            band_layout.addWidget(band_label)
            band_layout.addWidget(band_slider)
            eq_bands_layout.addLayout(band_layout)
        
        eq_layout.addLayout(eq_bands_layout)
        self.main_layout.addWidget(self.eq_group)
    
    def _get_group_style(self):
        """Get group box style"""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 6px;
                margin-top: 1ex;
                color: #E0E0E0;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px;
            }
        """
    
    def _get_slider_style(self):
        """Get slider style"""
        return """
            QSlider::groove:horizontal {
                border: 2px solid #555;
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00BCD4;
                border: 2px solid #00BCD4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #26C6DA;
            }
        """
    
    def _get_eq_slider_style(self):
        """Get EQ slider style"""
        return """
            QSlider::groove:vertical {
                border: 1px solid #555;
                width: 3px;
                background: #333;
                border-radius: 2px;
            }
            QSlider::handle:vertical {
                background: #00BCD4;
                border: 1px solid #00BCD4;
                height: 8px;
                margin: 0 -3px;
                border-radius: 4px;
            }
        """
    
    def _get_button_style(self):
        """Get button style"""
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border-radius: 4px;
                padding: 6px 8px;
                text-align: center;
                font-weight: bold;
                font-size: 10px;
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
        """Get profile button style"""
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border-radius: 4px;
                padding: 6px 8px;
                text-align: left;
                font-weight: bold;
                font-size: 10px;
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
        """Get special button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
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
        """Get meter style"""
        return """
            QProgressBar {
                border: 2px solid #555;
                border-radius: 3px;
                background-color: #222;
                text-align: center;
                font-weight: bold;
                color: white;
                font-size: 8px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #FFEB3B, stop:1 #F44336);
                border-radius: 2px;
            }
        """
    
    def _get_combo_style(self):
        """Get combo box style"""
        return """
            QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px;
                color: #E0E0E0;
                font-size: 10px;
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
                font-size: 10px;
                font-weight: bold;
                color: {color};
                padding: 6px;
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
        """Get current audio settings"""
        return {
            "profile": self.current_profile,
            "volume": self.current_volume,
            "audio_system_active": AUDIO_SYSTEM_AVAILABLE and self.audio_system is not None
        }


# For backwards compatibility
ProfessionalAudioControlPanel = ResponsiveAudioControlPanel

__all__ = ['ResponsiveAudioControlPanel', 'ProfessionalAudioControlPanel', 'AudioSystemThread']
