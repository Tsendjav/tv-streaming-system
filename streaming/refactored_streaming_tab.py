"""
TV Stream - Updated Streaming Tab with Auto-Update Integration
Main streaming tab with server auto-update functionality
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

# Import the updated server configuration components
from models.server_config import ServerConfig, ServerManagerDialog, ServerStorageManager

# Safe imports with fallback
try:
    from .utils import MediaValidator, LoggerManager, StreamingUtils
    from .ui_helpers import UIUpdateManager, FormBuilder, DialogHelper
    from .program_stream_manager import ProgramStreamManager
    from .ffmpeg_builder import FFmpegValidator
except ImportError:
    try:
        from utils import MediaValidator, LoggerManager, StreamingUtils
        from ui_helpers import UIUpdateManager, FormBuilder, DialogHelper
        from program_stream_manager import ProgramStreamManager
        from ffmpeg_builder import FFmpegValidator
    except ImportError:
        # Fallback implementations for critical components
        import logging
        
        class LoggerManager:
            @classmethod
            def get_logger(cls, name): return logging.getLogger(name)
        
        class MediaValidator:
            @classmethod
            def is_valid_media_file(cls, file_path): return True
        
        class StreamingUtils:
            @staticmethod
            def generate_stream_key(prefix="stream"): 
                import time
                return f"{prefix}_{int(time.time())}"
        
        class UIUpdateManager:
            def __init__(self, parent): self.parent = parent
            def safe_update(self, func, msg=""): 
                try: return func()
                except: return False
            def update_combo_box(self, combo, items): pass
        
        class FormBuilder:
            def __init__(self, parent=None): self.parent = parent
            def create_group_box(self, title, layout_type='vertical'):
                group = QGroupBox(title)
                if layout_type == 'form': QFormLayout(group)
                elif layout_type == 'horizontal': QHBoxLayout(group)
                else: QVBoxLayout(group)
                return group
            def create_button_row(self, buttons):
                container = QWidget()
                layout = QHBoxLayout(container)
                for config in buttons:
                    btn = QPushButton(config.get('text', 'Button'))
                    if 'clicked' in config: btn.clicked.connect(config['clicked'])
                    if 'enabled' in config: btn.setEnabled(config['enabled'])
                    layout.addWidget(btn)
                    config['button_ref'] = btn
                return container
        
        class DialogHelper:
            @staticmethod
            def show_error(parent, title, msg): QMessageBox.critical(parent, title, msg)
            @staticmethod
            def show_info(parent, title, msg): QMessageBox.information(parent, title, msg)
        
        class ProgramStreamManager(QObject):
            def __init__(self, parent_tab, stream_manager): 
                super().__init__()
                self.parent_tab = parent_tab
            def connect_to_playout_tab(self, tab): return True
            def start_program_stream(self, file_path): return False
            def get_program_stream_status(self): return {"is_active": False}
        
        class FFmpegValidator:
            @staticmethod
            def is_ffmpeg_available(): return False


# Quality presets
QUALITY_PRESETS = {
    "480p": {"name": "480p (SD)", "width": 854, "height": 480, "fps": 30, 
             "video_bitrate": "1000k", "audio_bitrate": "128k"},
    "720p": {"name": "720p (HD)", "width": 1280, "height": 720, "fps": 30,
             "video_bitrate": "2500k", "audio_bitrate": "128k"},
    "1080p": {"name": "1080p (Full HD)", "width": 1920, "height": 1080, "fps": 30,
              "video_bitrate": "4500k", "audio_bitrate": "192k"}
}


# Fallback implementations for compatibility
class StreamConfig:
    def __init__(self, stream_key, input_source, server, quality, **kwargs):
        self.stream_key = stream_key
        self.input_source = input_source
        self.server = server
        self.quality = quality
        for k, v in kwargs.items():
            setattr(self, k, v)


class StreamManager(QObject):
    stream_started = pyqtSignal(str)
    stream_stopped = pyqtSignal(str)
    stream_error = pyqtSignal(str, str)
    streams_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.streams = {}
        self.logger = LoggerManager.get_logger(__name__)
    
    def start_stream(self, config) -> bool:
        # Mock implementation - replace with actual streaming logic
        self.streams[config.stream_key] = config
        self.stream_started.emit(config.stream_key)
        self.streams_updated.emit()
        return True
    
    def stop_stream(self, stream_key: str) -> bool:
        if stream_key in self.streams:
            del self.streams[stream_key]
            self.stream_stopped.emit(stream_key)
            self.streams_updated.emit()
            return True
        return False
    
    def stop_all_streams(self):
        for stream_key in list(self.streams.keys()):
            self.stop_stream(stream_key)


class UpdatedStreamingTab(QWidget):
    """Updated streaming tab with auto-update server integration"""
    
    status_message = pyqtSignal(str, int)
    stream_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        # Initialize modular components
        self.logger = LoggerManager.get_logger(__name__)
        self.validator = MediaValidator()
        self.streaming_utils = StreamingUtils()
        
        self.ui_manager = UIUpdateManager(self)
        self.form_builder = FormBuilder(self)
        self.dialog_helper = DialogHelper()
        
        self.stream_manager = StreamManager()
        self.program_stream_manager = ProgramStreamManager(self, self.stream_manager)
        self.ffmpeg_validator = FFmpegValidator()
        
        # Initialize server storage manager with AUTO-UPDATE
        config_dir = Path.home() / ".tv_stream"
        config_dir.mkdir(exist_ok=True)
        self.server_storage = ServerStorageManager(config_dir / "servers.json")
        
        # Connect signals for auto-update
        self.server_storage.servers_changed.connect(self._on_servers_changed)
        self.server_storage.server_added.connect(self._on_server_added)
        self.server_storage.server_updated.connect(self._on_server_updated)
        self.server_storage.server_removed.connect(self._on_server_removed)
        
        # Server management dialog
        self.server_manager_dialog = None
        
        # UI elements
        self.ui_elements = {}
        self.status_labels = {}
        
        # State
        self.current_input_source = None
        self.active_streams = {}
        self.servers = {}
        
        # Initialize UI
        self._init_ui()
        self._connect_signals()
        self._post_init_setup()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Header with standardized styling
        header = QWidget()
        header_layout = QHBoxLayout(header)
        title = QLabel("📡 Стриминг Сервер Удирдах")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50;
            font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
        """)
        header_layout.addWidget(title)
        
        # Add server management button
        manage_servers_btn = QPushButton("🛠️ Сервер Удирдах")
        manage_servers_btn.clicked.connect(self._open_server_manager)
        manage_servers_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(manage_servers_btn)
        header_layout.addStretch()
        layout.addWidget(header)
        
        # Server status indicator
        self.server_status_label = QLabel("📡 Серверүүд: Ачааллаж байна...")
        self.server_status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(self.server_status_label)
        
        # Input source
        input_group = self.form_builder.create_group_box("📹 Input Source", 'form')
        input_layout = input_group.layout()
        
        self.ui_elements['source_type_combo'] = QComboBox()
        self.ui_elements['source_type_combo'].addItems([
            "Media File", "Desktop Capture", "Test Pattern"
        ])
        input_layout.addRow("Source Type:", self.ui_elements['source_type_combo'])
        
        self.ui_elements['source_input'] = QLineEdit()
        self.ui_elements['source_input'].setPlaceholderText("Enter source or select file...")
        input_layout.addRow("Source:", self.ui_elements['source_input'])
        
        layout.addWidget(input_group)
        
        # Stream configuration
        config_group = self.form_builder.create_group_box("⚙️ Configuration", 'form')
        config_layout = config_group.layout()
        
        # Server combo with better styling
        self.ui_elements['server_combo'] = QComboBox()
        self.ui_elements['server_combo'].setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        config_layout.addRow("Server:", self.ui_elements['server_combo'])
        
        self.ui_elements['stream_key_input'] = QLineEdit()
        config_layout.addRow("Stream Key:", self.ui_elements['stream_key_input'])
        
        self.ui_elements['quality_combo'] = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.ui_elements['quality_combo'].addItem(quality_data["name"], quality_data)
        config_layout.addRow("Quality:", self.ui_elements['quality_combo'])
        
        layout.addWidget(config_group)
        
        # Controls
        controls_group = self.form_builder.create_group_box("🎛️ Controls", 'horizontal')
        controls_layout = controls_group.layout()
        
        button_configs = [
            {'text': '🚀 Start Stream', 'clicked': self._start_stream, 'ref': 'start_btn'},
            {'text': '⏹️ Stop Stream', 'clicked': self._stop_stream, 'enabled': False, 'ref': 'stop_btn'},
            {'text': '🧪 Test Config', 'clicked': self._test_config, 'ref': 'test_btn'}
        ]
        
        button_row = self.form_builder.create_button_row(button_configs)
        controls_layout.addWidget(button_row)
        
        # Store button references
        for config in button_configs:
            if 'ref' in config and 'button_ref' in config:
                self.ui_elements[config['ref']] = config['button_ref']
        
        layout.addWidget(controls_group)
        
        # Status
        status_group = self.form_builder.create_group_box("📊 Status", 'form')
        status_layout = status_group.layout()
        
        self.status_labels['stream_count'] = QLabel("0")
        self.status_labels['ffmpeg_status'] = QLabel("Checking...")
        self.status_labels['server_count'] = QLabel("0")
        
        status_layout.addRow("Active Streams:", self.status_labels['stream_count'])
        status_layout.addRow("Available Servers:", self.status_labels['server_count'])
        status_layout.addRow("FFmpeg:", self.status_labels['ffmpeg_status'])
        
        layout.addWidget(status_group)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect signals"""
        self.stream_manager.stream_started.connect(self._on_stream_started)
        self.stream_manager.stream_stopped.connect(self._on_stream_stopped)
        self.stream_manager.streams_updated.connect(self._update_ui_state)
        
        if 'source_type_combo' in self.ui_elements:
            self.ui_elements['source_type_combo'].currentTextChanged.connect(self._on_source_type_changed)
    
    def _post_init_setup(self):
        """Post-initialization setup"""
        QTimer.singleShot(100, self._check_ffmpeg)
        QTimer.singleShot(200, self._load_servers)
        QTimer.singleShot(300, self._update_ui_state)
    
    def _check_ffmpeg(self):
        """Check FFmpeg availability"""
        if self.ffmpeg_validator.is_ffmpeg_available():
            self.status_labels['ffmpeg_status'].setText("✅ Available")
        else:
            self.status_labels['ffmpeg_status'].setText("❌ Not Found")
    
    def _load_servers(self):
        """Load available servers with auto-update"""
        try:
            self.servers = self.server_storage.load_servers()
            self._update_server_combo()
            self._update_server_status()
            
            self.logger.info(f"Loaded {len(self.servers)} servers")
            
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self.server_status_label.setText("❌ Серверүүд: Ачаалахад алдаа гарлаа")
    
    def _update_server_combo(self):
        """Update server combo box"""
        try:
            current_text = self.ui_elements['server_combo'].currentText()
            self.ui_elements['server_combo'].clear()
            
            if not self.servers:
                self.ui_elements['server_combo'].addItem("Сервер байхгүй", None)
                return
            
            # Add servers to combo
            selected_index = -1
            for i, (server_id, server_config) in enumerate(self.servers.items()):
                # Add icon based on SSL and type
                if server_config.ssl_enabled:
                    icon = "🔒"
                elif server_config.host.lower() in ['localhost', '127.0.0.1']:
                    icon = "🏠"
                else:
                    icon = "🌐"
                
                display_name = f"{icon} {server_config.name}"
                self.ui_elements['server_combo'].addItem(display_name, server_config)
                
                # Try to maintain selection
                if display_name == current_text:
                    selected_index = i
            
            # Restore selection or select first
            if selected_index >= 0:
                self.ui_elements['server_combo'].setCurrentIndex(selected_index)
            else:
                self.ui_elements['server_combo'].setCurrentIndex(0)
                
            self.status_labels['server_count'].setText(str(len(self.servers)))
            
        except Exception as e:
            self.logger.error(f"Failed to update server combo: {e}")
    
    def _update_server_status(self):
        """Update server status label"""
        if not self.servers:
            self.server_status_label.setText("⚠️ Серверүүд: Сервер тохируулаагүй байна")
        else:
            ssl_count = sum(1 for s in self.servers.values() if s.ssl_enabled)
            local_count = sum(1 for s in self.servers.values() if s.host.lower() in ['localhost', '127.0.0.1'])
            self.server_status_label.setText(
                f"✅ Серверүүд: {len(self.servers)} нийт "
                f"({local_count} орон нутаг, {ssl_count} SSL)"
            )
    
    def _update_ui_state(self):
        """Update UI state"""
        has_streams = len(self.stream_manager.streams) > 0
        has_servers = len(self.servers) > 0
        
        if 'stop_btn' in self.ui_elements:
            self.ui_elements['stop_btn'].setEnabled(has_streams)
        
        if 'start_btn' in self.ui_elements:
            self.ui_elements['start_btn'].setEnabled(has_servers)
        
        if 'test_btn' in self.ui_elements:
            self.ui_elements['test_btn'].setEnabled(has_servers)
        
        self.status_labels['stream_count'].setText(str(len(self.stream_manager.streams)))
    
    def _on_source_type_changed(self, source_type: str):
        """Handle source type change"""
        mapping = {
            "Media File": "",
            "Desktop Capture": "live:desktop_capture",
            "Test Pattern": "live:test_pattern"
        }
        
        source_value = mapping.get(source_type, "")
        self.ui_elements['source_input'].setText(source_value)
        self.current_input_source = source_value
    
    def _start_stream(self):
        """Start streaming"""
        try:
            stream_key = self.ui_elements['stream_key_input'].text().strip()
            if not stream_key:
                stream_key = self.streaming_utils.generate_stream_key()
                self.ui_elements['stream_key_input'].setText(stream_key)
            
            server = self.ui_elements['server_combo'].currentData()
            quality = self.ui_elements['quality_combo'].currentData()
            
            if not server:
                self.dialog_helper.show_error(self, "Error", "No server selected")
                return
            
            input_source = self.ui_elements['source_input'].text().strip()
            if not input_source:
                input_source = "live:test_pattern"
            
            config = StreamConfig(
                stream_key=stream_key,
                input_source=input_source,
                server=server,
                quality=quality or QUALITY_PRESETS["720p"]
            )
            
            if self.stream_manager.start_stream(config):
                self.active_streams[stream_key] = config
                self.status_message.emit(f"Stream started: {stream_key}", 3000)
            else:
                self.dialog_helper.show_error(self, "Error", "Failed to start stream")
                
        except Exception as e:
            self.logger.error(f"Start stream error: {e}")
            self.dialog_helper.show_error(self, "Error", f"Failed to start stream: {e}")
    
    def _stop_stream(self):
        """Stop streaming"""
        if self.stream_manager.streams:
            stream_key = list(self.stream_manager.streams.keys())[0]
            if self.stream_manager.stop_stream(stream_key):
                if stream_key in self.active_streams:
                    del self.active_streams[stream_key]
                self.status_message.emit(f"Stream stopped: {stream_key}", 3000)
    
    def _test_config(self):
        """Test configuration"""
        server = self.ui_elements['server_combo'].currentData()
        if not server:
            self.dialog_helper.show_error(self, "Error", "No server selected")
            return
        
        try:
            import socket
            
            # Test RTMP port connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server.host, server.rtmp_port))
            sock.close()
            
            if result == 0:
                self.dialog_helper.show_info(self, "Test Result", 
                                           f"✅ Server '{server.name}' connection successful!")
            else:
                self.dialog_helper.show_error(self, "Test Result", 
                                            f"❌ Server '{server.name}' connection failed\n"
                                            f"Host: {server.host}:{server.rtmp_port}")
        except Exception as e:
            self.dialog_helper.show_error(self, "Test Result", 
                                        f"❌ Connection test failed: {str(e)}")
    
    def _open_server_manager(self):
        """Open server manager dialog"""
        try:
            if not self.server_manager_dialog:
                self.server_manager_dialog = ServerManagerDialog(self.config_manager, self)
                # Connect the signal for real-time updates
                self.server_manager_dialog.servers_changed.connect(self._on_servers_changed)
            
            if self.server_manager_dialog.exec() == QDialog.DialogCode.Accepted:
                # Force reload servers after dialog closes
                self._load_servers()
                self.status_message.emit("Server configuration updated", 2000)
                
        except Exception as e:
            self.logger.error(f"Failed to open server manager: {e}")
            self.dialog_helper.show_error(self, "Error", f"Failed to open server manager: {e}")
    
    # AUTO-UPDATE EVENT HANDLERS
    def _on_servers_changed(self):
        """Handle servers changed signal"""
        self.logger.info("Servers changed - reloading...")
        self._load_servers()
    
    def _on_server_added(self, server_id: str, server_config: ServerConfig):
        """Handle server added signal"""
        self.logger.info(f"Server added: {server_id}")
        self._load_servers()
        self.status_message.emit(f"Server '{server_config.name}' added", 2000)
    
    def _on_server_updated(self, server_id: str, server_config: ServerConfig):
        """Handle server updated signal"""
        self.logger.info(f"Server updated: {server_id}")
        self._load_servers()
        self.status_message.emit(f"Server '{server_config.name}' updated", 2000)
    
    def _on_server_removed(self, server_id: str):
        """Handle server removed signal"""
        self.logger.info(f"Server removed: {server_id}")
        self._load_servers()
        self.status_message.emit(f"Server removed", 2000)
    
    def _on_stream_started(self, stream_key: str):
        """Handle stream started"""
        self.status_message.emit(f"Stream started: {stream_key}", 3000)
        self._update_ui_state()
    
    def _on_stream_stopped(self, stream_key: str):
        """Handle stream stopped"""
        self.status_message.emit(f"Stream stopped: {stream_key}", 3000)
        self._update_ui_state()
    
    # External API for compatibility
    def connect_to_playout_tab(self, playout_tab) -> bool:
        """Connect to playout tab"""
        return self.program_stream_manager.connect_to_playout_tab(playout_tab)
    
    def load_and_start_stream(self, file_path: str) -> bool:
        """Load and start stream"""
        return self.program_stream_manager.start_program_stream(file_path)
    
    def get_program_stream_status(self) -> Dict[str, Any]:
        """Get program stream status"""
        return self.program_stream_manager.get_program_stream_status()
    
    def get_active_streams_count(self) -> int:
        """Get active streams count"""
        return len(self.stream_manager.streams)
    
    def is_streaming_active(self) -> bool:
        """Check if streaming is active"""
        return len(self.stream_manager.streams) > 0
    
    def refresh(self):
        """Refresh tab"""
        self._load_servers()
        self._update_ui_state()
    
    def cleanup(self):
        """Cleanup resources"""
        self.stream_manager.stop_all_streams()
        if self.server_manager_dialog:
            self.server_manager_dialog.close()


# Backward compatibility
StreamingTab = UpdatedStreamingTab
RefactoredStreamingTab = UpdatedStreamingTab

__all__ = ['UpdatedStreamingTab', 'StreamingTab', 'RefactoredStreamingTab', 'QUALITY_PRESETS']