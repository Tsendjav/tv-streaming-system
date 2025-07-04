#!/usr/bin/env python3
"""
UI Components for Playout Tab
Responsive UI components and layout helpers
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional, List


class ResponsiveGroupBox(QGroupBox):
    """Responsive group box that adapts to screen size"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.original_title = title
        self.is_compact = False
        
        # Install event filter for resize detection
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle resize for responsive behavior"""
        width = size.width()
        is_compact = width < 300
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_for_size()
    
    def _update_for_size(self):
        """Update styling for size"""
        if self.is_compact:
            # Compact mode - shorter title
            words = self.original_title.split()
            if len(words) > 2:
                self.setTitle(' '.join(words[:2]) + '...')
            
            # Smaller font
            self.setStyleSheet("""
                QGroupBox {
                    font-size: 10px;
                    font-weight: bold;
                    border: 1px solid #666;
                    border-radius: 4px;
                    margin-top: 1ex;
                    color: #E0E0E0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 4px;
                }
            """)
        else:
            # Full mode - full title
            self.setTitle(self.original_title)
            
            # Normal font
            self.setStyleSheet("""
                QGroupBox {
                    font-size: 12px;
                    font-weight: bold;
                    border: 2px solid #666;
                    border-radius: 6px;
                    margin-top: 1ex;
                    color: #E0E0E0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 6px;
                }
            """)


class ResponsiveLayout:
    """Helper class for creating responsive layouts"""
    
    @staticmethod
    def create_button_layout(buttons: List[tuple], parent=None, compact_threshold=400):
        """Create responsive button layout"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Add buttons
        for text, callback, style in buttons:
            btn = QPushButton(text)
            if style:
                btn.setStyleSheet(style)
            if callback:
                btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        layout.addStretch()
        return widget
    
    @staticmethod
    def create_control_section(title: str, controls: List[QWidget], parent=None):
        """Create responsive control section"""
        group = ResponsiveGroupBox(title, parent)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        for control in controls:
            layout.addWidget(control)
        
        return group
    
    @staticmethod
    def create_status_bar(initial_text: str = "Ready", parent=None):
        """Create responsive status bar"""
        status_label = QLabel(initial_text)
        status_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 10px;
                padding: 4px;
                background-color: #333;
                border-radius: 4px;
            }
        """)
        return status_label


class ResponsiveButton(QPushButton):
    """Responsive button that adapts its size and text"""
    
    def __init__(self, full_text: str, compact_text: str = None, parent=None):
        super().__init__(full_text, parent)
        self.full_text = full_text
        self.compact_text = compact_text or full_text.split()[0]  # Use first word as compact
        self.is_compact = False
        
        # Install event filter
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle resize for responsive behavior"""
        width = size.width()
        is_compact = width < 80
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_for_size()
    
    def _update_for_size(self):
        """Update button for size"""
        if self.is_compact:
            self.setText(self.compact_text)
            self.setMaximumWidth(60)
        else:
            self.setText(self.full_text)
            self.setMaximumWidth(16777215)


class AMCPControlSection(QWidget):
    """Responsive AMCP control section"""
    
    # Signals
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()
    command_requested = pyqtSignal(str)
    console_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.amcp_connected = False
        self.is_compact = False
        
        # Set minimum height
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        
        self._init_ui()
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle resize for responsive behavior"""
        width = size.width()
        is_compact = width < 800
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_layout_for_size()
    
    def _init_ui(self):
        """Initialize UI"""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Connection status
        self.status_label = QLabel("🔴 Disconnected")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold; font-size: 11px;")
        self.main_layout.addWidget(self.status_label)
        
        # Connection buttons
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setFixedSize(80, 30)
        self.connect_btn.clicked.connect(self.connect_requested.emit)
        self.main_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedSize(80, 30)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_btn.setEnabled(False)
        self.main_layout.addWidget(self.disconnect_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(separator1)
        
        # Channel/layer controls
        self.main_layout.addWidget(QLabel("Ch:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.setFixedWidth(50)
        self.main_layout.addWidget(self.channel_spin)
        
        self.main_layout.addWidget(QLabel("Ly:"))
        self.layer_spin = QSpinBox()
        self.layer_spin.setRange(1, 20)
        self.layer_spin.setValue(1)
        self.layer_spin.setFixedWidth(50)
        self.main_layout.addWidget(self.layer_spin)
        
        # Media combo
        self.main_layout.addWidget(QLabel("Media:"))
        self.media_combo = QComboBox()
        self.media_combo.setEditable(True)
        self.media_combo.setMinimumWidth(120)
        self.media_combo.setPlaceholderText("Media file...")
        self.main_layout.addWidget(self.media_combo)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(separator2)
        
        # AMCP commands
        self.command_layout = QHBoxLayout()
        self.command_layout.setSpacing(3)
        
        commands = [("LOAD", "LOAD"), ("PLAY", "PLAY"), ("STOP", "STOP"), ("INFO", "INFO")]
        self.command_buttons = {}
        
        for cmd_text, cmd_value in commands:
            btn = QPushButton(cmd_text)
            btn.setFixedSize(50, 30)
            btn.clicked.connect(lambda checked, cmd=cmd_value: self.command_requested.emit(cmd))
            self.command_buttons[cmd_value] = btn
            self.command_layout.addWidget(btn)
        
        command_widget = QWidget()
        command_widget.setLayout(self.command_layout)
        self.main_layout.addWidget(command_widget)
        
        self.main_layout.addStretch()
        
        # Console button
        self.console_btn = QPushButton("💻 Console")
        self.console_btn.setFixedSize(80, 30)
        self.console_btn.clicked.connect(self.console_requested.emit)
        self.main_layout.addWidget(self.console_btn)
    
    def _update_layout_for_size(self):
        """Update layout for size"""
        if self.is_compact:
            # Compact mode - hide some elements
            self.disconnect_btn.setVisible(False)
            self.console_btn.setText("💻")
            self.console_btn.setFixedSize(40, 30)
            
            # Make command buttons smaller
            for btn in self.command_buttons.values():
                btn.setFixedSize(35, 30)
            
            # Reduce combo width
            self.media_combo.setMinimumWidth(80)
        else:
            # Full mode - show all elements
            self.disconnect_btn.setVisible(True)
            self.console_btn.setText("💻 Console")
            self.console_btn.setFixedSize(80, 30)
            
            # Normal button sizes
            for btn in self.command_buttons.values():
                btn.setFixedSize(50, 30)
            
            # Normal combo width
            self.media_combo.setMinimumWidth(120)
    
    def set_connection_status(self, connected: bool):
        """Set connection status"""
        self.amcp_connected = connected
        
        if connected:
            self.status_label.setText("🟢 Connected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 11px;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
        else:
            self.status_label.setText("🔴 Disconnected")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold; font-size: 11px;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
    
    def get_current_settings(self):
        """Get current AMCP settings"""
        return {
            'channel': self.channel_spin.value(),
            'layer': self.layer_spin.value(),
            'media': self.media_combo.currentText(),
            'connected': self.amcp_connected
        }


class LogSection(QWidget):
    """Responsive log section"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_compact = False
        
        # Set size constraints
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        
        self._init_ui()
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle resize for responsive behavior"""
        width = size.width()
        is_compact = width < 600
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_layout_for_size()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Log controls
        self.log_toolbar = QHBoxLayout()
        self.log_toolbar.setSpacing(4)
        
        # Filter buttons
        self.filter_buttons = {}
        filters = [("All", "all"), ("Err", "error"), ("AMCP", "amcp"), ("AUDIO", "audio")]
        
        for filter_text, filter_value in filters:
            btn = QPushButton(filter_text)
            btn.setCheckable(True)
            btn.setFixedSize(35, 18)
            btn.setStyleSheet("font-size: 9px; padding: 2px;")
            if filter_value == "all":
                btn.setChecked(True)
            self.filter_buttons[filter_value] = btn
            self.log_toolbar.addWidget(btn)
        
        self.log_toolbar.addStretch()
        
        # Clear and save buttons
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(40, 18)
        self.clear_btn.setStyleSheet("font-size: 9px; padding: 2px;")
        self.log_toolbar.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(35, 18)
        self.save_btn.setStyleSheet("font-size: 9px; padding: 2px;")
        self.log_toolbar.addWidget(self.save_btn)
        
        layout.addLayout(self.log_toolbar)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
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
    
    def _update_layout_for_size(self):
        """Update layout for size"""
        if self.is_compact:
            # Compact mode - hide some filter buttons
            for i, (filter_text, filter_value) in enumerate([("All", "all"), ("Err", "error"), ("AMCP", "amcp"), ("AUDIO", "audio")]):
                if i > 1:  # Hide last 2 buttons
                    self.filter_buttons[filter_value].setVisible(False)
                else:
                    self.filter_buttons[filter_value].setVisible(True)
            
            # Make buttons smaller
            for btn in self.filter_buttons.values():
                if btn.isVisible():
                    btn.setFixedSize(30, 18)
        else:
            # Full mode - show all buttons
            for btn in self.filter_buttons.values():
                btn.setVisible(True)
                btn.setFixedSize(35, 18)
    
    def add_log_entry(self, level: str, message: str, color: str = "#E0E0E0"):
        """Add log entry"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format with color
        formatted_entry = f'<span style="color: {color};">[{timestamp}] {level}:</span> {message}'
        self.log_text.append(formatted_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear log"""
        self.log_text.clear()
    
    def get_log_text(self):
        """Get log text"""
        return self.log_text.toPlainText()


class TransportControls(QWidget):
    """Responsive transport controls"""
    
    # Signals
    send_to_program = pyqtSignal()
    take_to_air = pyqtSignal()
    stream_program = pyqtSignal()
    fade_program = pyqtSignal()
    cut_program = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_compact = False
        
        # Set size constraints
        self.setFixedWidth(100)
        self.setMinimumHeight(200)
        
        self._init_ui()
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle resize for responsive behavior"""
        height = size.height()
        is_compact = height < 300
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_layout_for_size()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch(1)
        
        # Send to Program
        self.send_btn = QPushButton("➡️\nSEND TO\nPROGRAM")
        self.send_btn.setFixedSize(80, 45)
        self.send_btn.setStyleSheet(self._get_button_style("#2196F3"))
        self.send_btn.clicked.connect(self.send_to_program.emit)
        layout.addWidget(self.send_btn)
        
        # Stream Program Button
        self.stream_btn = QPushButton("📡\nSTREAM\nPROGRAM")
        self.stream_btn.setFixedSize(80, 45)
        self.stream_btn.setStyleSheet(self._get_button_style("#9C27B0"))
        self.stream_btn.clicked.connect(self.stream_program.emit)
        layout.addWidget(self.stream_btn)
        
        # TAKE TO AIR (main button)
        self.take_btn = QPushButton("📺\nTAKE TO AIR\n& STREAM")
        self.take_btn.setFixedSize(80, 65)
        self.take_btn.setStyleSheet(self._get_main_button_style())
        self.take_btn.clicked.connect(self.take_to_air.emit)
        layout.addWidget(self.take_btn)
        
        # Fade/Cut buttons
        fade_cut_layout = QHBoxLayout()
        fade_cut_layout.setSpacing(2)
        
        self.fade_btn = QPushButton("🌅\nFADE")
        self.fade_btn.setFixedSize(38, 35)
        self.fade_btn.setStyleSheet(self._get_button_style("#9C27B0"))
        self.fade_btn.clicked.connect(self.fade_program.emit)
        fade_cut_layout.addWidget(self.fade_btn)
        
        self.cut_btn = QPushButton("✂️\nCUT")
        self.cut_btn.setFixedSize(38, 35)
        self.cut_btn.setStyleSheet(self._get_button_style("#FF5722"))
        self.cut_btn.clicked.connect(self.cut_program.emit)
        fade_cut_layout.addWidget(self.cut_btn)
        
        layout.addLayout(fade_cut_layout)
        layout.addStretch(2)
    
    def _get_button_style(self, color):
        """Get button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 8px;
                font-weight: bold;
                border-radius: 6px;
                border: 2px solid {color};
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """
    
    def _get_main_button_style(self):
        """Get main button style"""
        return """
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
        """
    
    def _update_layout_for_size(self):
        """Update layout for size"""
        if self.is_compact:
            # Compact mode - make buttons smaller
            self.send_btn.setFixedSize(70, 35)
            self.stream_btn.setFixedSize(70, 35)
            self.take_btn.setFixedSize(70, 50)
            self.fade_btn.setFixedSize(33, 30)
            self.cut_btn.setFixedSize(33, 30)
        else:
            # Full mode - normal button sizes
            self.send_btn.setFixedSize(80, 45)
            self.stream_btn.setFixedSize(80, 45)
            self.take_btn.setFixedSize(80, 65)
            self.fade_btn.setFixedSize(38, 35)
            self.cut_btn.setFixedSize(38, 35)


__all__ = [
    'ResponsiveGroupBox',
    'ResponsiveLayout',
    'ResponsiveButton',
    'AMCPControlSection',
    'LogSection',
    'TransportControls'
]
