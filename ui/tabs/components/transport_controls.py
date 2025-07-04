#!/usr/bin/env python3
"""
Transport Controls Widget
Professional transport controls with keyboard shortcuts and enhanced UI
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class TransportControls(QWidget):
    """Professional transport controls widget with keyboard shortcuts"""
    
    # Signals
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    seek_forward = pyqtSignal()
    seek_backward = pyqtSignal()
    position_changed = pyqtSignal(float)
    volume_changed = pyqtSignal(int)
    
    def __init__(self, label: str = "Transport", parent=None):
        super().__init__(parent)
        self.setMaximumHeight(120)
        self._init_ui(label)
        self._setup_shortcuts()
    
    def _init_ui(self, label: str):
        """Initialize transport controls UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        
        # Title
        title_label = QLabel(label)
        title_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ccc;")
        layout.addWidget(title_label)
        
        # Transport buttons
        buttons_layout = QHBoxLayout()
        
        # Skip backward
        self.skip_back_btn = QPushButton("⏮")
        self.skip_back_btn.setMaximumSize(35, 35)
        self.skip_back_btn.clicked.connect(self.seek_backward.emit)
        self.skip_back_btn.setToolTip("Skip backward 10s (Ctrl+Left)")
        buttons_layout.addWidget(self.skip_back_btn)
        
        # Play
        self.play_btn = QPushButton("▶️")
        self.play_btn.setMaximumSize(40, 40)
        self.play_btn.clicked.connect(self.play_clicked.emit)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(self.play_btn)
        
        # Pause
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setMaximumSize(40, 40)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                border-radius: 20px;
                font-size: 16px;
                color: #212529;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        buttons_layout.addWidget(self.pause_btn)
        
        # Stop
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setMaximumSize(40, 40)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        buttons_layout.addWidget(self.stop_btn)
        
        # Skip forward
        self.skip_forward_btn = QPushButton("⏭")
        self.skip_forward_btn.setMaximumSize(35, 35)
        self.skip_forward_btn.clicked.connect(self.seek_forward.emit)
        self.skip_forward_btn.setToolTip("Skip forward 10s (Ctrl+Right)")
        buttons_layout.addWidget(self.skip_forward_btn)
        
        layout.addLayout(buttons_layout)
        
        # Position slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 10000)
        self.position_slider.sliderPressed.connect(self._on_seek_start)
        self.position_slider.sliderReleased.connect(self._on_seek_end)
        layout.addWidget(self.position_slider)
        
        # Time display
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00:00")
        self.current_time_label.setStyleSheet("font-family: 'Courier New'; font-size: 10px; color: #fff;")
        time_layout.addWidget(self.current_time_label)
        
        time_layout.addStretch()
        
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("font-family: 'Courier New'; font-size: 12px; color: #888;")
        time_layout.addWidget(self.duration_label)
        
        layout.addLayout(time_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔊")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self._update_volume_label)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        self.volume_slider.setMaximumWidth(100)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("80%")
        self.volume_label.setStyleSheet("font-size: 10px; color: #ccc;")
        volume_layout.addWidget(self.volume_label)
        
        # Mute toggle
        self.mute_button = QPushButton("🔇")
        self.mute_button.setMaximumSize(25, 25)
        self.mute_button.setCheckable(True)
        self.mute_button.clicked.connect(self._toggle_mute)
        self.mute_button.setToolTip("Toggle mute (M)")
        volume_layout.addWidget(self.mute_button)
        
        volume_layout.addStretch()
        
        layout.addLayout(volume_layout)
        
        self.seeking = False
        self.is_muted = False
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Space"), self, self._toggle_play_pause)
        QShortcut(QKeySequence("Ctrl+Left"), self, self.seek_backward.emit)
        QShortcut(QKeySequence("Ctrl+Right"), self, self.seek_forward.emit)
        QShortcut(QKeySequence("S"), self, self.stop_clicked.emit)
        QShortcut(QKeySequence("M"), self, self._toggle_mute)
    
    def _toggle_play_pause(self):
        """Toggle play/pause with spacebar"""
        if self.play_btn.isEnabled():
            self.play_clicked.emit()
        else:
            self.pause_clicked.emit()
    
    def _on_seek_start(self):
        """Handle seek start"""
        self.seeking = True
    
    def _on_seek_end(self):
        """Handle seek end"""
        self.seeking = False
        position = self.position_slider.value() / 10000.0
        self.position_changed.emit(position)
    
    def _update_volume_label(self, volume: int):
        """Update volume label"""
        self.volume_label.setText(f"{volume}%")
        self.mute_button.setText("🔇" if volume == 0 or self.is_muted else "🔊")
    
    def _toggle_mute(self):
        """Toggle mute state"""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.volume_slider.setValue(0)
            self.mute_button.setText("🔇")
        else:
            self.volume_slider.setValue(self.current_volume if hasattr(self, 'current_volume') else 80)
            self.mute_button.setText("🔊")
        self.volume_changed.emit(self.volume_slider.value())
    
    def update_position(self, position: float, duration: float):
        """Update position display"""
        if not self.seeking and duration > 0:
            slider_pos = int((position / duration) * 10000)
            self.position_slider.setValue(slider_pos)
        
        self.current_time_label.setText(self._format_time(position))
    
    def update_duration(self, duration: float):
        """Update duration display"""
        self.duration_label.setText(self._format_time(duration))
    
    def update_volume(self, volume: int):
        """Update volume display"""
        self.current_volume = volume
        if not self.is_muted:
            self.volume_slider.setValue(volume)
            self._update_volume_label(volume)
    
    def update_state(self, state: str):
        """Update button states based on playback state"""
        is_playing = (state == "playing")
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)
        self.stop_btn.setEnabled(state != "stopped")
    
    def _format_time(self, seconds: float) -> str:
        """Format time as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
