#!/usr/bin/env python3
"""
examples/integration_example.py
Complete integration example showing how to use the tab integration system
"""

import sys
import json
from pathlib import Path

# Add the parent directory to path so we can import from core
sys.path.append(str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import pyqtSignal

# Import the integration system
from core.integration import (
    setup_integration_system,
    IntegrationConfig,
    MongolianSystemMessages,
    EventType
)

# =============================================================================
# EXAMPLE TAB CLASSES
# =============================================================================

class ExampleMediaLibraryTab(QWidget):
    """Example media library tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Media Library Tab"))
        
        self.load_btn = QPushButton("Load Media File")
        self.load_btn.clicked.connect(self.load_media)
        layout.addWidget(self.load_btn)
        
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_media(self):
        # Simulate loading media
        self.status_message.emit("Media loaded: example.mp4", 3000)
        self.status_label.setText("Media loaded: example.mp4")
    
    def refresh(self):
        self.status_label.setText("Refreshed")

class ExamplePlayoutTab(QWidget):
    """Example playout tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Playout Tab"))
        
        self.cue_btn = QPushButton("Cue Preview")
        self.cue_btn.clicked.connect(self.cue_preview)
        layout.addWidget(self.cue_btn)
        
        self.take_btn = QPushButton("Take to Air")
        self.take_btn.clicked.connect(self.take_to_air)
        layout.addWidget(self.take_btn)
        
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def cue_preview(self):
        self.status_message.emit("Preview cued", 2000)
        self.status_label.setText("Preview cued")
    
    def take_to_air(self):
        self.status_message.emit("LIVE - On Air", 5000)
        self.status_label.setText("LIVE - On Air")
    
    def refresh(self):
        self.status_label.setText("Refreshed")

class ExampleStreamingTab(QWidget):
    """Example streaming tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Streaming Tab"))
        
        self.start_btn = QPushButton("Start Stream")
        self.start_btn.clicked.connect(self.start_stream)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Stream")
        self.stop_btn.clicked.connect(self.stop_stream)
        layout.addWidget(self.stop_btn)
        
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def start_stream(self):
        self.status_message.emit("Stream started", 3000)
        self.status_label.setText("Streaming...")
    
    def stop_stream(self):
        self.status_message.emit("Stream stopped", 2000)
        self.status_label.setText("Stream stopped")
    
    def refresh(self):
        self.status_label.setText("Refreshed")

class ExampleSchedulerTab(QWidget):
    """Example scheduler tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Scheduler Tab"))
        
        self.auto_btn = QPushButton("Enable Automation")
        self.auto_btn.clicked.connect(self.toggle_automation)
        layout.addWidget(self.auto_btn)
        
        self.status_label = QLabel("Manual mode")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def toggle_automation(self):
        if "Enable" in self.auto_btn.text():
            self.auto_btn.setText("Disable Automation")
            self.status_label.setText("Automation enabled")
            self.status_message.emit("Automation enabled", 2000)
        else:
            self.auto_btn.setText("Enable Automation")
            self.status_label.setText("Manual mode")
            self.status_message.emit("Automation disabled", 2000)
    
    def refresh(self):
        self.status_label.setText("Refreshed")

# =============================================================================
# EXAMPLE CONFIG MANAGER
# =============================================================================

class ExampleConfigManager:
    """Simple config manager for example"""
    
    def __init__(self):
        self.config = {}
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value

# =============================================================================
# ENHANCED MAIN WINDOW WITH INTEGRATION
# =============================================================================

class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with integration system"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ExampleConfigManager()
        self.init_ui()
        self.setup_integration()
    
    def init_ui(self):
        self.setWindowTitle("TV Streaming Studio - Integration Example")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setPlainText("System starting...\n")
        layout.addWidget(QLabel("System Status:"))
        layout.addWidget(self.status_text)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.tabs = {
            "media_library": ExampleMediaLibraryTab(),
            "playout": ExamplePlayoutTab(),
            "streaming": ExampleStreamingTab(),
            "scheduler": ExampleSchedulerTab()
        }
        
        # Add tabs to widget
        self.tab_widget.addTab(self.tabs["media_library"], "Media Library")
        self.tab_widget.addTab(self.tabs["playout"], "Playout")
        self.tab_widget.addTab(self.tabs["streaming"], "Streaming")
        self.tab_widget.addTab(self.tabs["scheduler"], "Scheduler")
        
        # Control buttons
        control_layout = QVBoxLayout()
        
        # Workflow buttons
        self.workflow_btn = QPushButton("Execute Media-to-Air Workflow")
        self.workflow_btn.clicked.connect(self.execute_media_workflow)
        control_layout.addWidget(self.workflow_btn)
        
        self.stream_workflow_btn = QPushButton("Execute Live Streaming Workflow")
        self.stream_workflow_btn.clicked.connect(self.execute_stream_workflow)
        control_layout.addWidget(self.stream_workflow_btn)
        
        self.emergency_btn = QPushButton("🛑 Emergency Stop")
        self.emergency_btn.clicked.connect(self.emergency_stop)
        self.emergency_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        control_layout.addWidget(self.emergency_btn)
        
        # System status button
        self.status_btn = QPushButton("📊 Show System Status")
        self.status_btn.clicked.connect(self.show_system_status)
        control_layout.addWidget(self.status_btn)
        
        layout.addLayout(control_layout)
        
        # Connect tab status messages
        for tab in self.tabs.values():
            if hasattr(tab, 'status_message'):
                tab.status_message.connect(self._show_status_message)
    
    def setup_integration(self):
        """Setup the integration system"""
        try:
            # Create integration config
            integration_config = IntegrationConfig()
            integration_config.apply_defaults_for_broadcasting()
            integration_config.monitoring_interval = 3000  # 3 seconds for demo
            
            # Setup integration system
            self.integration_system, self.system_monitor = setup_integration_system(
                self, self.config_manager, integration_config
            )
            
            # Connect integration events
            if self.integration_system:
                self.integration_system.event_bus.global_event.connect(self._on_integration_event)
            
            if self.system_monitor:
                self.system_monitor.alert_triggered.connect(self._on_alert)
                self.system_monitor.system_health_changed.connect(self._on_health_change)
            
            self._append_status("✅ Integration system initialized successfully")
            
        except Exception as e:
            self._append_status(f"❌ Integration setup failed: {e}")
    
    def _show_status_message(self, message: str, timeout: int):
        """Show status message"""
        self._append_status(f"📝 {message}")
    
    def _append_status(self, message: str):
        """Append message to status display"""
        self.status_text.append(message)
        # Scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
    
    def _on_integration_event(self, event):
        """Handle integration events"""
        event_msg = MongolianSystemMessages.get_message(
            "event_broadcast",
            event_type=event.event_type.value
        )
        self._append_status(f"🔄 {event_msg}")
    
    def _on_alert(self, alert_type: str, message: str, severity: int):
        """Handle system alerts"""
        severity_icons = {1: "ℹ️", 2: "⚠️", 3: "🚨"}
        icon = severity_icons.get(severity, "❓")
        self._append_status(f"{icon} ALERT: {message}")
    
    def _on_health_change(self, health_status: str):
        """Handle health status changes"""
        health_msg = MongolianSystemMessages.get_health_message(health_status)
        self._append_status(f"💊 {health_msg}")
    
    def execute_media_workflow(self):
        """Execute media-to-air workflow"""
        if hasattr(self, 'integration_system'):
            try:
                execution_id = self.integration_system.execute_workflow(
                    "complete_media_to_air",
                    {"file_path": "/example/video.mp4"}
                )
                self._append_status(f"🎬 Started media-to-air workflow: {execution_id}")
            except Exception as e:
                self._append_status(f"❌ Workflow failed: {e}")
        else:
            self._append_status("❌ Integration system not available")
    
    def execute_stream_workflow(self):
        """Execute live streaming workflow"""
        if hasattr(self, 'integration_system'):
            try:
                execution_id = self.integration_system.execute_workflow("live_streaming_setup")
                self._append_status(f"📡 Started live streaming workflow: {execution_id}")
            except Exception as e:
                self._append_status(f"❌ Workflow failed: {e}")
        else:
            self._append_status("❌ Integration system not available")
    
    def emergency_stop(self):
        """Trigger emergency stop"""
        if hasattr(self, 'integration_system'):
            self.integration_system.trigger_emergency_stop("Manual emergency stop from UI")
            self._append_status("🛑 Emergency stop triggered!")
        else:
            self._append_status("❌ Integration system not available")
    
    def show_system_status(self):
        """Show comprehensive system status"""
        if hasattr(self, 'integration_system'):
            status = self.integration_system.get_system_status()
            status_text = json.dumps(status, indent=2, ensure_ascii=False)
            self._append_status("📊 System Status:")
            self._append_status(status_text)
        else:
            self._append_status("❌ Integration system not available")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to run the example"""
    app = QApplication(sys.argv)
    
    # Create and show the enhanced main window
    window = EnhancedMainWindow()
    window.show()
    
    # Add some demo content
    window._append_status("🎯 Welcome to TV Streaming Studio Integration Example")
    window._append_status("💡 Try the workflow buttons to see cross-tab automation")
    window._append_status("📊 Use 'Show System Status' to see integration details")
    window._append_status("🛑 Emergency stop will stop all operations")
    window._append_status("")
    window._append_status("Available workflows:")
    window._append_status("  • Media-to-Air: Load → Cue → Take")
    window._append_status("  • Live Streaming: Prepare → Start → Monitor")
    window._append_status("  • Emergency procedures available")
    window._append_status("")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()