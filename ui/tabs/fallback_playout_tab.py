#!/usr/bin/env python3
"""
Fallback Playout Tab
Simple playout interface when full components are not available
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import *

class FallbackPlayoutTab(QWidget):
    """Simple fallback playout tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
    
    def _init_ui(self):
        """Initialize simple UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("🎬 Playout Control")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #00BCD4;
                margin: 20px;
            }
        """)
        layout.addWidget(header)
        
        # Status
        status = QLabel("⚠️ Full playout components not available")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet("font-size: 16px; color: #FF9800; margin: 10px;")
        layout.addWidget(status)
        
        # Simple controls
        controls_widget = QWidget()
        controls_widget.setMaximumWidth(400)
        controls_layout = QVBoxLayout(controls_widget)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #888; padding: 10px; border: 1px solid #555; border-radius: 4px;")
        file_layout.addWidget(self.file_label)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        controls_layout.addLayout(file_layout)
        
        # Transport controls
        transport_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._play)
        transport_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        transport_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(transport_layout)
        
        # Instructions
        instructions = QLabel("""
        <b>To enable full playout functionality:</b><br><br>
        1. Install VLC media player<br>
        2. Copy all playout component files to:<br>
           <code>ui/tabs/playout_components/</code><br>
        3. Restart the application<br><br>
        <i>Current functionality is limited to basic file selection.</i>
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                color: #666;
                padding: 15px;
                border-radius: 8px;
                font-size: 12px;
                margin: 20px;
            }
        """)
        controls_layout.addWidget(instructions)
        
        layout.addWidget(controls_widget)
        layout.addStretch()
        
        self.current_file = None
    
    def _browse_file(self):
        """Browse for media file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav);;All Files (*)"
        )
        
        if file_path:
            self.current_file = file_path
            file_name = file_path.split('/')[-1]
            self.file_label.setText(file_name)
            self.file_label.setStyleSheet("color: #00BCD4; padding: 10px; border: 1px solid #00BCD4; border-radius: 4px;")
            
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            self.status_message.emit(f"Selected: {file_name}", 3000)
    
    def _play(self):
        """Simulate play"""
        if self.current_file:
            self.status_message.emit("Play functionality requires full playout components", 5000)
        
    def _stop(self):
        """Simulate stop"""
        self.status_message.emit("Stop functionality requires full playout components", 5000)
    
    def cleanup(self):
        """Cleanup resources"""
        pass
    
    def refresh(self):
        """Refresh tab"""
        pass
    
    def get_tab_name(self):
        """Get tab name"""
        return "playout"
    
    def handle_system_event(self, event):
        """Handle system event"""
        pass
    
    def get_tab_status(self):
        """Get tab status"""
        return {
            "name": "playout",
            "status": "fallback",
            "available": True,
            "limited": True,
            "current_file": self.current_file
        }
    
    def execute_command(self, command, params=None):
        """Execute command"""
        return {"error": "Full playout functionality not available"}

# Export
__all__ = ['FallbackPlayoutTab']