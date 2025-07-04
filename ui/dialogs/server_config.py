#!/usr/bin/env python3
"""
Fixed Server Configuration Dialog with Auto-Update and Standardized Sizes
Серверийн тохиргооны диалог автомат шинэчлэлт болон стандарт хэмжээтэй
"""

import sys
import json
import os
from pathlib import Path
import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Fallback imports
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


# =============================================================================
# SERVER CONFIGURATION MODEL
# =============================================================================

@dataclass
class ServerConfig:
    """Server configuration data class"""
    name: str
    host: str
    port: int
    rtmp_port: int
    ssl_enabled: bool = False
    api_endpoint: str = "/api/v1"
    stream_endpoint: str = "/live"
    username: Optional[str] = None
    password: Optional[str] = None
    max_streams: int = 10
    description: str = ""

    @property
    def rtmp_url(self) -> str:
        """Get RTMP URL"""
        protocol = "rtmps" if self.ssl_enabled else "rtmp"
        return f"{protocol}://{self.host}:{self.rtmp_port}{self.stream_endpoint}"

    @property
    def api_url(self) -> str:
        """Get API URL"""
        protocol = "https" if self.ssl_enabled else "http"
        return f"{protocol}://{self.host}:{self.port}{self.api_endpoint}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary"""
        defaults = {
            'ssl_enabled': False,
            'api_endpoint': '/api/v1',
            'stream_endpoint': '/live',
            'username': None,
            'password': None,
            'max_streams': 10,
            'description': ''
        }
        
        config_data = {**defaults, **data}
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in config_data.items() if k in valid_fields}
        
        return cls(**filtered_data)


# =============================================================================
# SERVER STORAGE MANAGER WITH SIGNALS
# =============================================================================

class ServerStorageManager(QObject):
    """Manages server configuration file storage with signals"""
    
    # Signals for auto-update
    servers_changed = pyqtSignal()
    server_added = pyqtSignal(str, object)  # server_id, ServerConfig
    server_updated = pyqtSignal(str, object)  # server_id, ServerConfig
    server_removed = pyqtSignal(str)  # server_id
    
    def __init__(self, config_file: str = "servers.json"):
        super().__init__()
        # ФАЙЛЫН ЗАМЫГ СТАНДАРТ БОЛГОХ
        self.config_file = Path(config_file)
        self.logger = get_logger(__name__)
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with empty config if file doesn't exist
        if not self.config_file.exists():
            self.save_servers({})
    
    def load_servers(self) -> Dict[str, ServerConfig]:
        """Load servers from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            servers = {}
            for server_id, server_data in data.get('servers', {}).items():
                try:
                    servers[server_id] = ServerConfig.from_dict(server_data)
                except Exception as e:
                    self.logger.warning(f"Failed to load server {server_id}: {e}")
            
            return servers
            
        except FileNotFoundError:
            self.logger.info("Server config file not found, creating new one")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in server config: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            return {}
    
    def save_servers(self, servers: Dict[str, ServerConfig]):
        """Save servers to file"""
        try:
            servers_data = {}
            for server_id, server_config in servers.items():
                servers_data[server_id] = server_config.to_dict()
            
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix(f'.backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                self.config_file.rename(backup_file)
                
                backup_files = sorted(self.config_file.parent.glob(f'{self.config_file.stem}.backup_*.json'))
                for old_backup in backup_files[:-5]:
                    old_backup.unlink()
            
            config_data = {
                "version": "1.0",
                "last_updated": datetime.datetime.now().isoformat(),
                "servers": servers_data
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(servers)} servers to {self.config_file}")
            # Emit signal for auto-update
            self.servers_changed.emit()
            
        except Exception as e:
            self.logger.error(f"Failed to save servers: {e}")
            raise
    
    def add_server(self, server_id: str, server_config: ServerConfig):
        """Add a new server"""
        servers = self.load_servers()
        servers[server_id] = server_config
        self.save_servers(servers)
        self.server_added.emit(server_id, server_config)
    
    def update_server(self, server_id: str, server_config: ServerConfig):
        """Update existing server"""
        servers = self.load_servers()
        if server_id in servers:
            servers[server_id] = server_config
            self.save_servers(servers)
            self.server_updated.emit(server_id, server_config)
        else:
            raise KeyError(f"Server {server_id} not found")
    
    def remove_server(self, server_id: str):
        """Remove server"""
        servers = self.load_servers()
        if server_id in servers:
            del servers[server_id]
            self.save_servers(servers)
            self.server_removed.emit(server_id)
        else:
            raise KeyError(f"Server {server_id} not found")
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get specific server"""
        servers = self.load_servers()
        return servers.get(server_id)


# =============================================================================
# SERVER EDIT DIALOG - STANDARDIZED SIZE
# =============================================================================

class ServerEditDialog(QDialog):
    """Dialog for editing server configuration with standardized size"""

    def __init__(self, server_config: Optional[ServerConfig] = None, parent=None):
        super().__init__(parent)
        self.server_config = server_config
        self.logger = get_logger(__name__)

        self.setWindowTitle("Серверийн Тохиргоо" if not server_config else "Сервер Засах")
        self.setModal(True)
        
        # СТАНДАРТ ХЭМЖЭЭ - жижиг цонх
        self.setMinimumSize(650, 750)
        self.resize(720, 850)
        self.setSizeGripEnabled(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self._init_ui()

        if server_config:
            self._populate_fields()

    def _init_ui(self):
        """Initialize dialog UI with improved layout and sizing"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Main dialog font setting
        main_font = QFont()
        main_font.setFamily("Segoe UI")
        main_font.setPointSize(10)
        self.setFont(main_font)

        # Header - СТАНДАРТ ХЭМЖЭЭ
        header_label = QLabel("🖥️ Стриминг Сервер Удирдах")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                padding: 8px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: white;
                border-radius: 4px;
                text-align: center;
            }
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFixedHeight(35)
        header_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(header_label)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 4, 0, 0)

        # Styling
        group_style = """
            QGroupBox {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: #34495e;
                font-weight: bold;
            }
        """

        input_style = """
            QLineEdit, QSpinBox, QTextEdit {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                font-size: 11px;
                padding: 8px 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: #ffffff;
                min-height: 18px;
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            QLineEdit:hover, QSpinBox:hover, QTextEdit:hover {
                border-color: #95a5a6;
                color: #2c3e50;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: border;
                width: 18px;
                border-left: 1px solid #ddd;
                background-color: #ecf0f1;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #bdc3c7;
            }
        """

        label_style = """
            QLabel {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                font-size: 11px;
                font-weight: 600;
                color: #34495e;
                margin-bottom: 4px;
            }
        """

        # Basic server settings group
        form_group = QGroupBox("Серверийн Үндсэн Мэдээлэл")
        form_group.setStyleSheet(group_style)
        form_layout = QFormLayout(form_group)
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Server name
        name_label = QLabel("Серверийн Нэр:")
        name_label.setStyleSheet(label_style)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Жишээ: Орон нутгийн RTMP сервер")
        self.name_edit.setStyleSheet(input_style)
        form_layout.addRow(name_label, self.name_edit)

        # Host
        host_label = QLabel("Хост Хаяг:")
        host_label.setStyleSheet(label_style)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("Жишээ: localhost эсвэл rtmp.example.com")
        self.host_edit.setStyleSheet(input_style)
        form_layout.addRow(host_label, self.host_edit)

        # Ports section
        ports_widget = QWidget()
        ports_layout = QHBoxLayout(ports_widget)
        ports_layout.setSpacing(12)
        ports_layout.setContentsMargins(0, 0, 0, 0)

        # HTTP Port
        http_container = QWidget()
        http_layout = QVBoxLayout(http_container)
        http_layout.setContentsMargins(0, 0, 0, 0)
        http_layout.setSpacing(4)

        http_label = QLabel("HTTP Порт:")
        http_label.setStyleSheet(label_style)
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(8080)
        self.port_edit.setStyleSheet(input_style)
        self.port_edit.setMinimumWidth(100)

        http_layout.addWidget(http_label)
        http_layout.addWidget(self.port_edit)

        # RTMP Port
        rtmp_container = QWidget()
        rtmp_layout = QVBoxLayout(rtmp_container)
        rtmp_layout.setContentsMargins(0, 0, 0, 0)
        rtmp_layout.setSpacing(4)

        rtmp_label = QLabel("RTMP Порт:")
        rtmp_label.setStyleSheet(label_style)
        self.rtmp_port_edit = QSpinBox()
        self.rtmp_port_edit.setRange(1, 65535)
        self.rtmp_port_edit.setValue(1935)
        self.rtmp_port_edit.setStyleSheet(input_style)
        self.rtmp_port_edit.setMinimumWidth(100)

        rtmp_layout.addWidget(rtmp_label)
        rtmp_layout.addWidget(self.rtmp_port_edit)

        ports_layout.addWidget(http_container)
        ports_layout.addWidget(rtmp_container)
        ports_layout.addStretch()

        ports_main_label = QLabel("Портууд:")
        ports_main_label.setStyleSheet(label_style)
        form_layout.addRow(ports_main_label, ports_widget)

        # SSL checkbox
        security_label = QLabel("Аюулгүй Байдал:")
        security_label.setStyleSheet(label_style)
        self.ssl_cb = QCheckBox("SSL/TLS шифрлэлт идэвхжүүлэх")
        self.ssl_cb.setStyleSheet("""
            QCheckBox {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                font-size: 11px;
                padding: 6px;
                color: #34495e;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #3498db;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                color: white;
            }
        """)
        form_layout.addRow(security_label, self.ssl_cb)

        content_layout.addWidget(form_group)

        # Authentication group
        auth_group = QGroupBox("Нэвтрэх Эрх (Заавал биш)")
        auth_group.setStyleSheet(group_style)
        auth_layout = QFormLayout(auth_group)
        auth_layout.setVerticalSpacing(10)
        auth_layout.setHorizontalSpacing(12)
        auth_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Username
        username_label = QLabel("Хэрэглэгчийн Нэр:")
        username_label.setStyleSheet(label_style)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Хэрэглэгчийн нэр (шаардлагатай бол)")
        self.username_edit.setStyleSheet(input_style)
        auth_layout.addRow(username_label, self.username_edit)

        # Password with show/hide functionality
        password_label = QLabel("Нууц Үг:")
        password_label.setStyleSheet(label_style)
        
        password_widget = QWidget()
        password_layout = QHBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(6)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Нууц үг (шаардлагатай бол)")
        self.password_edit.setStyleSheet(input_style)
        password_layout.addWidget(self.password_edit)
        
        # Show/hide password button
        show_password_btn = QPushButton("👁")
        show_password_btn.setCheckable(True)
        show_password_btn.setFixedSize(35, 35)
        show_password_btn.toggled.connect(self._toggle_password_visibility)
        show_password_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #3498db;
                border-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                border-color: #95a5a6;
            }
        """)
        password_layout.addWidget(show_password_btn)
        
        auth_layout.addRow(password_label, password_widget)

        content_layout.addWidget(auth_group)

        # Endpoints group
        endpoints_group = QGroupBox("Холболтын Цэгүүд")
        endpoints_group.setStyleSheet(group_style)
        endpoints_layout = QFormLayout(endpoints_group)
        endpoints_layout.setVerticalSpacing(10)
        endpoints_layout.setHorizontalSpacing(12)
        endpoints_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # API Endpoint
        api_label = QLabel("API Цэг:")
        api_label.setStyleSheet(label_style)
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setText("/api/v1")
        self.api_endpoint_edit.setStyleSheet(input_style)
        endpoints_layout.addRow(api_label, self.api_endpoint_edit)

        # Stream Endpoint
        stream_label = QLabel("Стримийн Цэг:")
        stream_label.setStyleSheet(label_style)
        self.stream_endpoint_edit = QLineEdit()
        self.stream_endpoint_edit.setText("/live")
        self.stream_endpoint_edit.setStyleSheet(input_style)
        endpoints_layout.addRow(stream_label, self.stream_endpoint_edit)

        # Max streams
        streams_label = QLabel("Ихдээ Стрим:")
        streams_label.setStyleSheet(label_style)
        self.max_streams_edit = QSpinBox()
        self.max_streams_edit.setRange(1, 100)
        self.max_streams_edit.setValue(10)
        self.max_streams_edit.setStyleSheet(input_style)
        self.max_streams_edit.setMinimumWidth(100)
        endpoints_layout.addRow(streams_label, self.max_streams_edit)

        # Description - expandable text area
        description_label = QLabel("Тайлбар:")
        description_label.setStyleSheet(label_style)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(70)
        self.description_edit.setMinimumHeight(50)
        self.description_edit.setPlaceholderText("Серверийн тухай нэмэлт мэдээлэл...")
        self.description_edit.setStyleSheet(input_style + """
            QTextEdit {
                line-height: 1.3;
            }
        """)
        endpoints_layout.addRow(description_label, self.description_edit)

        content_layout.addWidget(endpoints_group)

        # URL Preview group
        preview_group = QGroupBox("URL Урьдчилан Үзэх")
        preview_group.setStyleSheet(group_style)
        preview_layout = QFormLayout(preview_group)
        preview_layout.setVerticalSpacing(8)
        preview_layout.setHorizontalSpacing(12)
        preview_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Info label
        info_label = QLabel("💡 URL дээр дарж хуулна уу")
        info_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                color: #7f8c8d;
                font-style: italic;
                font-size: 10px;
                margin-bottom: 6px;
            }
        """)
        preview_layout.addRow("", info_label)

        # URL styling
        url_style = """
            QLabel {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                color: #2c3e50;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                padding: 8px 10px;
                border-radius: 5px;
                border: 2px solid #e9ecef;
                min-height: 14px;
                word-wrap: break-word;
            }
            QLabel:hover {
                border-color: #3498db;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """

        # RTMP URL
        rtmp_label = QLabel("RTMP Хаяг:")
        rtmp_label.setStyleSheet(label_style)
        self.rtmp_url_label = QLabel("rtmp://localhost:1935/live")
        self.rtmp_url_label.setStyleSheet(url_style)
        self.rtmp_url_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rtmp_url_label.setWordWrap(True)
        preview_layout.addRow(rtmp_label, self.rtmp_url_label)

        # API URL
        api_url_label = QLabel("API Хаяг:")
        api_url_label.setStyleSheet(label_style)
        self.api_url_label = QLabel("http://localhost:8080/api/v1")
        self.api_url_label.setStyleSheet(url_style)
        self.api_url_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.api_url_label.setWordWrap(True)
        preview_layout.addRow(api_url_label, self.api_url_label)

        content_layout.addWidget(preview_group)

        # Setup URL click handlers
        self._setup_url_click_handlers()

        # Add stretch to push content to top
        content_layout.addStretch()

        # Set scroll area content
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Connect signals for live preview
        self.host_edit.textChanged.connect(self._update_preview)
        self.port_edit.valueChanged.connect(self._update_preview)
        self.rtmp_port_edit.valueChanged.connect(self._update_preview)
        self.ssl_cb.toggled.connect(self._update_preview)
        self.api_endpoint_edit.textChanged.connect(self._update_preview)
        self.stream_endpoint_edit.textChanged.connect(self._update_preview)

        # Button styling
        button_style_base = """
            QPushButton {
                font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
                border: none;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 4, 0, 0)

        # Test connection button
        test_btn = QPushButton("🧪 Холболт Шалгах")
        test_btn.clicked.connect(self._test_connection)
        test_btn.setStyleSheet(button_style_base + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
        """)
        button_layout.addWidget(test_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Цуцлах")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(button_style_base + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
        """)
        button_layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Хадгалах")
        save_btn.clicked.connect(self._save_server)
        save_btn.setDefault(True)
        save_btn.setStyleSheet(button_style_base + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e7e34);
                }
            QPushButton:default {
                border: 2px solid #ffffff;
            }
        """)
        button_layout.addWidget(save_btn)

        main_layout.addLayout(button_layout)

        # Set initial focus
        self.name_edit.setFocus()

        # Initial preview update
        self._update_preview()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.update()

    def _toggle_password_visibility(self, checked):
        """Toggle password field visibility"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _copy_to_clipboard(self, text, label="URL"):
        """Copy text to clipboard with visual feedback"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        QToolTip.showText(
            QCursor.pos(), 
            f"{label} хуулагдлаа!", 
            None,
            QRect(),
            2000
        )

    def _setup_url_click_handlers(self):
        """Setup click handlers for URL labels"""
        def rtmp_click_handler(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._copy_to_clipboard(self.rtmp_url_label.text(), "RTMP URL")
        
        def api_click_handler(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._copy_to_clipboard(self.api_url_label.text(), "API URL")
        
        self.rtmp_url_label.mousePressEvent = rtmp_click_handler
        self.api_url_label.mousePressEvent = api_click_handler

    def _populate_fields(self):
        """Populate fields with existing server config"""
        if not self.server_config:
            return

        self.name_edit.setText(self.server_config.name)
        self.host_edit.setText(self.server_config.host)
        self.port_edit.setValue(self.server_config.port)
        self.rtmp_port_edit.setValue(self.server_config.rtmp_port)
        self.ssl_cb.setChecked(self.server_config.ssl_enabled)
        self.username_edit.setText(self.server_config.username or "")
        self.password_edit.setText(self.server_config.password or "")
        self.api_endpoint_edit.setText(self.server_config.api_endpoint)
        self.stream_endpoint_edit.setText(self.server_config.stream_endpoint)
        self.max_streams_edit.setValue(self.server_config.max_streams)
        self.description_edit.setPlainText(self.server_config.description)

    def _update_preview(self):
        """Update URL preview"""
        try:
            host = self.host_edit.text().strip() or "localhost"
            port = self.port_edit.value()
            rtmp_port = self.rtmp_port_edit.value()
            ssl = self.ssl_cb.isChecked()
            api_endpoint = self.api_endpoint_edit.text().strip() or "/api/v1"
            stream_endpoint = self.stream_endpoint_edit.text().strip() or "/live"
            
            clean_host = self._clean_host_url(host)
            
            rtmp_protocol = "rtmps" if ssl else "rtmp"
            rtmp_url = f"{rtmp_protocol}://{clean_host}:{rtmp_port}{stream_endpoint}"
            self.rtmp_url_label.setText(rtmp_url)
            
            api_protocol = "https" if ssl else "http"
            api_url = f"{api_protocol}://{clean_host}:{port}{api_endpoint}"
            self.api_url_label.setText(api_url)
            
        except Exception:
            self.rtmp_url_label.setText("rtmp://localhost:1935/live")
            self.api_url_label.setText("http://localhost:8080/api/v1")

    def _clean_host_url(self, host: str) -> str:
        """Clean and validate host URL"""
        if not host or host.isspace():
            return "localhost"
        
        host = host.strip()
        
        if "://" in host:
            host = host.split("://", 1)[1]
        
        if "/" in host:
            host = host.split("/")[0]
        
        if host.lower() in ["localhost", "127.0.0.1", "::1"]:
            return "localhost"
        
        try:
            import re
            cleaned = re.sub(r'[^a-zA-Z0-9.\-_:]', '', host)
            
            if not cleaned:
                return "localhost"
            
            if self._is_valid_host_format(cleaned):
                return cleaned
            else:
                return "localhost"
                
        except Exception:
            return "localhost"

    def _is_valid_host_format(self, host: str) -> bool:
        """Check if host format is valid"""
        if not host:
            return False
        
        if host.lower() == "localhost":
            return True
        
        import re
        
        patterns = [
            r'^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            r'^[0-9a-fA-F:]+$',
            r'^[a-zA-Z0-9._-]+$'
        ]
        
        for pattern in patterns:
            if re.match(pattern, host):
                return True
        
        return False

    def _test_connection(self):
        """Test server connection"""
        try:
            config = self._create_server_config()
            if not config:
                return
            
            test_dialog = QDialog(self)
            test_dialog.setWindowTitle("Холболтын Шалгалт")
            test_dialog.setModal(True)
            test_dialog.resize(550, 500)
            test_dialog.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                }
            """)
            
            layout = QVBoxLayout(test_dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            header = QLabel("🔍 Серверийн Тохиргооны Шалгалт")
            header.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 12px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ecf0f1, stop:1 #bdc3c7);
                    border-radius: 6px;
                    text-align: center;
                }
            """)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)
            
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(15, 15, 15, 15)
            content_layout.setSpacing(12)
            
            results_text = f"""
            <div style="font-family: 'Segoe UI', sans-serif; line-height: 1.5; font-size: 12px;">
            <h3 style="color: #27ae60; margin-bottom: 12px;">✅ Тохиргоо Зөв</h3>
            
            <h4 style="color: #34495e; margin-bottom: 8px;">Серверийн Мэдээлэл:</h4>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px; border: 1px solid #ddd;">
            <tr><td style="padding: 8px; font-weight: bold; background: #ecf0f1; border: 1px solid #ddd; width: 40%;">Нэр:</td><td style="padding: 8px; background: #f8f9fa; border: 1px solid #ddd;">{config.name}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; background: #ecf0f1; border: 1px solid #ddd;">Хост:</td><td style="padding: 8px; background: #f8f9fa; border: 1px solid #ddd;">{config.host}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; background: #ecf0f1; border: 1px solid #ddd;">HTTP Порт:</td><td style="padding: 8px; background: #f8f9fa; border: 1px solid #ddd;">{config.port}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; background: #ecf0f1; border: 1px solid #ddd;">RTMP Порт:</td><td style="padding: 8px; background: #f8f9fa; border: 1px solid #ddd;">{config.rtmp_port}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; background: #ecf0f1; border: 1px solid #ddd;">SSL:</td><td style="padding: 8px; background: #f8f9fa; border: 1px solid #ddd;">{'🔒 Идэвхтэй' if config.ssl_enabled else '🔓 Идэвхгүй'}</td></tr>
            </table>
            
            <h4 style="color: #34495e; margin-bottom: 8px;">Үүссэн URL Хаягууд:</h4>
            <div style="background: #e8f5e8; padding: 10px; border-radius: 6px; margin: 6px 0; border-left: 3px solid #27ae60;">
            <strong>RTMP URL:</strong><br/>
            <code style="background: #ffffff; padding: 4px; border-radius: 3px; font-family: 'Consolas', monospace; word-break: break-all; display: block; margin-top: 4px;">{config.rtmp_url}</code>
            </div>
            
            <div style="background: #e3f2fd; padding: 10px; border-radius: 6px; margin: 6px 0; border-left: 3px solid #2196f3;">
            <strong>API URL:</strong><br/>
            <code style="background: #ffffff; padding: 4px; border-radius: 3px; font-family: 'Consolas', monospace; word-break: break-all; display: block; margin-top: 4px;">{config.api_url}</code>
            </div>
            </div>"""
            
            results_label = QLabel(results_text)
            results_label.setWordWrap(True)
            results_label.setTextFormat(Qt.TextFormat.RichText)
            results_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            content_layout.addWidget(results_label)
            content_layout.addStretch()
            
            scroll_area.setWidget(content_widget)
            layout.addWidget(scroll_area)
            
            button_layout = QHBoxLayout()
            button_layout.setSpacing(8)
            
            copy_rtmp_btn = QPushButton("📋 RTMP Хуулах")
            copy_rtmp_btn.clicked.connect(lambda: self._copy_to_clipboard(config.rtmp_url, "RTMP URL"))
            copy_rtmp_btn.setStyleSheet("""
                QPushButton {
                    font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 5px;
                    border: none;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2980b9, stop:1 #21618c);
                }
            """)
            button_layout.addWidget(copy_rtmp_btn)
            
            copy_api_btn = QPushButton("📋 API Хуулах")
            copy_api_btn.clicked.connect(lambda: self._copy_to_clipboard(config.api_url, "API URL"))
            copy_api_btn.setStyleSheet("""
                QPushButton {
                    font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #9b59b6, stop:1 #8e44ad);
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 5px;
                    border: none;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #8e44ad, stop:1 #7d3c98);
                }
            """)
            button_layout.addWidget(copy_api_btn)
            
            button_layout.addStretch()
            
            close_btn = QPushButton("Хаах")
            close_btn.clicked.connect(test_dialog.accept)
            close_btn.setDefault(True)
            close_btn.setStyleSheet("""
                QPushButton {
                    font-family: 'Segoe UI', 'Arial Unicode MS', sans-serif;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #229954);
                    color: white;
                    font-weight: bold;
                    padding: 8px 20px;
                    border-radius: 5px;
                    border: none;
                    min-width: 70px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #229954, stop:1 #1e7e34);
                }
                QPushButton:default {
                    border: 2px solid #ffffff;
                }
            """)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            test_dialog.exec()
            
        except ValueError as e:
            QMessageBox.warning(self, "Тохиргооны Алдаа", str(e))
        except Exception as e:
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Warning)
            error_dialog.setWindowTitle("Тохиргооны Алдаа")
            error_dialog.setText("Серверийн тохиргоо баталгаажуулахад алдаа гарлаа")
            error_dialog.setDetailedText(f"Алдааны дэлгэрэнгүй:\n{str(e)}")
            error_dialog.exec()

    def _create_server_config(self):
        """Create server configuration from form"""
        name = self.name_edit.text().strip()
        host_input = self.host_edit.text().strip()
        
        if not name:
            raise ValueError("Серверийн нэр шаардлагатай")
        
        if not host_input:
            raise ValueError("Хост хаяг шаардлагатай")
        
        clean_host = self._clean_host_url(host_input)
        
        if clean_host == "localhost" and host_input.lower() != "localhost":
            reply = QMessageBox.question(
                self,
                "Хост Хаяг Анхааруулга",
                f"Оруулсан хост хаяг '{host_input}' нь 'localhost' болж өөрчлөгдөнө.\n\nҮргэлжлүүлэх үү?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.host_edit.setFocus()
                self.host_edit.selectAll()
                raise ValueError("Хост хаягийг шалгаж засна уу")
        
        username = self.username_edit.text().strip() or None
        password = self.password_edit.text().strip() or None
        
        return ServerConfig(
            name=name,
            host=clean_host,
            port=self.port_edit.value(),
            rtmp_port=self.rtmp_port_edit.value(),
            ssl_enabled=self.ssl_cb.isChecked(),
            api_endpoint=self.api_endpoint_edit.text().strip(),
            stream_endpoint=self.stream_endpoint_edit.text().strip(),
            username=username,
            password=password,
            max_streams=self.max_streams_edit.value(),
            description=self.description_edit.toPlainText().strip()
        )

    def _save_server(self):
        """Save server configuration"""
        try:
            config = self._create_server_config()
            if config:
                self.server_config = config
                self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Хадгалах Алдаа", f"Тохиргоог хадгалахад алдаа гарлаа:\n{e}")

    def get_server_config(self) -> Optional[ServerConfig]:
        """Get the created/edited server configuration"""
        return self.server_config


# =============================================================================
# MAIN SERVER MANAGER DIALOG - STANDARDIZED SIZE
# =============================================================================

class ServerManagerDialog(QDialog):
    """Main dialog for managing streaming servers with standardized size"""

    # Signal for auto-update
    servers_changed = pyqtSignal()

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)

        # Initialize file storage manager with signals
        config_dir = Path.home() / ".tv_stream"
        config_dir.mkdir(exist_ok=True)
        self.storage_manager = ServerStorageManager(config_dir / "servers.json")

        # Connect storage manager signals for auto-update
        self.storage_manager.servers_changed.connect(self.servers_changed.emit)

        # Load servers from file
        self.servers: Dict[str, ServerConfig] = {}
        self._load_servers()

        self.setWindowTitle("🖥️ Сервер Удирдах")
        self.setModal(True)
        
        # СТАНДАРТ ХЭМЖЭЭ - том цонх
        self.setMinimumSize(850, 650)
        self.resize(950, 750)
        self.setSizeGripEnabled(True)

        self._init_ui()
        self._populate_servers()

    def _init_ui(self):
        """Initialize dialog UI with standardized styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header - СТАНДАРТ ХЭМЖЭЭ
        header_label = QLabel("📡 Стриминг Сервер Удирдах")
        header_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            background-color: #2c3e50;
            color: white;
            border-radius: 6px;
            margin-bottom: 15px;
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # File info
        file_info_label = QLabel(f"📁 Тохиргооны файл: {self.storage_manager.config_file}")
        file_info_label.setStyleSheet("color: #7f8c8d; font-size: 9px; font-style: italic;")
        layout.addWidget(file_info_label)

        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(2)
        content_splitter.setStyleSheet("QSplitter::handle { background-color: #bdc3c7; }")

        # Left panel - Server list
        left_panel = self._create_server_list_panel()
        content_splitter.addWidget(left_panel)

        # Right panel - Server details
        right_panel = self._create_server_details_panel()
        content_splitter.addWidget(right_panel)

        content_splitter.setSizes([320, 480])
        layout.addWidget(content_splitter)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        defaults_btn = QPushButton("🔄 Үндсэн Тохиргоог Ачаалах")
        defaults_btn.clicked.connect(self._load_default_servers)
        defaults_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        button_layout.addWidget(defaults_btn)

        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self._export_servers)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2471a3;
            }
        """)
        button_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 Импорт")
        import_btn.clicked.connect(self._import_servers)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        button_layout.addWidget(import_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Хаах")
        close_btn.clicked.connect(self._save_and_close)
        close_btn.setDefault(True)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #616e70;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _create_server_list_panel(self) -> QWidget:
        """Create server list panel"""
        panel = QGroupBox("Серверүүд")
        panel.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; } QGroupBox::title { color: #34495e; padding: 3px 0; }")
        layout = QVBoxLayout(panel)

        # Server list
        self.server_list = QListWidget()
        self.server_list.currentItemChanged.connect(self._on_server_selection_changed)
        self.server_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: #ecf0f1;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #dfe6e9;
            }
        """)
        layout.addWidget(self.server_list)

        # List buttons
        list_buttons = QHBoxLayout()
        list_buttons.setSpacing(8)

        add_btn = QPushButton("➕ Нэмэх")
        add_btn.clicked.connect(self._add_server)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #229a54;
            }
        """)
        list_buttons.addWidget(add_btn)

        self.edit_btn = QPushButton("✏️ Засах")
        self.edit_btn.clicked.connect(self._edit_server)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        list_buttons.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Устгах")
        self.delete_btn.clicked.connect(self._delete_server)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        list_buttons.addWidget(self.delete_btn)

        layout.addLayout(list_buttons)

        return panel

    def _create_server_details_panel(self) -> QWidget:
        """Create server details panel"""
        panel = QGroupBox("Серверийн Дэлгэрэнгүй")
        panel.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; } QGroupBox::title { color: #34495e; padding: 3px 0; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        # Details form
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(6)

        self.detail_name_label = QLabel("-")
        self.detail_name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        form_layout.addRow("Нэр:", self.detail_name_label)

        self.detail_host_label = QLabel("-")
        self.detail_host_label.setStyleSheet("color: #34495e; font-size: 11px;")
        form_layout.addRow("Хост:", self.detail_host_label)

        self.detail_ports_label = QLabel("-")
        self.detail_ports_label.setStyleSheet("color: #34495e; font-size: 11px;")
        form_layout.addRow("Порт:", self.detail_ports_label)

        self.detail_ssl_label = QLabel("-")
        self.detail_ssl_label.setStyleSheet("color: #34495e; font-size: 11px;")
        form_layout.addRow("SSL:", self.detail_ssl_label)

        self.detail_auth_label = QLabel("-")
        self.detail_auth_label.setStyleSheet("color: #34495e; font-size: 11px;")
        form_layout.addRow("Нэвтрэлт:", self.detail_auth_label)

        self.detail_rtmp_label = QLabel("-")
        self.detail_rtmp_label.setStyleSheet("""
            color: #2c3e50;
            font-family: monospace;
            font-size: 10px;
            background-color: #ecf0f1;
            padding: 4px;
            border-radius: 3px;
            border: 1px solid #ccc;
        """)
        self.detail_rtmp_label.setWordWrap(True)
        form_layout.addRow("RTMP URL:", self.detail_rtmp_label)

        self.detail_api_label = QLabel("-")
        self.detail_api_label.setStyleSheet("""
            color: #2c3e50;
            font-family: monospace;
            font-size: 10px;
            background-color: #ecf0f1;
            padding: 4px;
            border-radius: 3px;
            border: 1px solid #ccc;
        """)
        self.detail_api_label.setWordWrap(True)
        form_layout.addRow("API URL:", self.detail_api_label)

        layout.addLayout(form_layout)

        # Description
        desc_group = QGroupBox("Тайлбар")
        desc_group.setStyleSheet("QGroupBox { margin-top: 12px; font-weight: bold; font-size: 11px; } QGroupBox::title { color: #34495e; padding: 3px 0; }")
        desc_layout = QVBoxLayout(desc_group)

        self.detail_description_label = QLabel("Тайлбар байхгүй")
        self.detail_description_label.setWordWrap(True)
        self.detail_description_label.setStyleSheet("color: #555; font-style: italic; padding: 8px; background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 3px; font-size: 10px;")
        desc_layout.addWidget(self.detail_description_label)

        layout.addWidget(desc_group)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.test_btn = QPushButton("🧪 Шалгах")
        self.test_btn.clicked.connect(self._test_selected_server)
        self.test_btn.setEnabled(False)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        action_layout.addWidget(self.test_btn)

        self.copy_rtmp_btn = QPushButton("📋 RTMP URL Хуулах")
        self.copy_rtmp_btn.clicked.connect(self._copy_rtmp_url)
        self.copy_rtmp_btn.setEnabled(False)
        self.copy_rtmp_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        action_layout.addWidget(self.copy_rtmp_btn)

        layout.addLayout(action_layout)
        layout.addStretch()

        return panel

    def _load_servers(self):
        """Load servers from file storage"""
        try:
            self.servers = self.storage_manager.load_servers()
            
            if not self.servers:
                self._create_default_servers()
                self.storage_manager.save_servers(self.servers)

        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self._create_default_servers()

    def _create_default_servers(self):
        """Create default server configurations"""
        default_servers = {
            "local": ServerConfig(
                name="Орон нутгийн NGINX+RTMP",
                host="localhost",
                port=8080,
                rtmp_port=1935,
                ssl_enabled=False,
                description="Үндсэн орон нутгийн RTMP сервер"
            ),
            "youtube": ServerConfig(
                name="YouTube Live",
                host="a.rtmp.youtube.com",
                port=443,
                rtmp_port=1935,
                ssl_enabled=True,
                stream_endpoint="/live2",
                description="YouTube Live дамжуулалт"
            ),
            "twitch": ServerConfig(
                name="Twitch",
                host="live.twitch.tv",
                port=443,
                rtmp_port=1935,
                ssl_enabled=True,
                stream_endpoint="/live",
                description="Twitch дамжуулалт"
            )
        }
        self.servers.update(default_servers)

    def _populate_servers(self):
        """Populate server list"""
        self.server_list.clear()

        for server_key, server_config in self.servers.items():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, server_key)

            if server_config.ssl_enabled:
                item.setText(f"🔒 {server_config.name}")
            else:
                item.setText(f"🌐 {server_config.name}")

            if server_config.description:
                item.setToolTip(server_config.description)

            self.server_list.addItem(item)

    def _on_server_selection_changed(self, current, previous):
        """Handle server selection change"""
        if current:
            server_key = current.data(Qt.ItemDataRole.UserRole)
            if server_key in self.servers:
                server = self.servers[server_key]
                self._update_server_details(server)

                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                self.test_btn.setEnabled(True)
                self.copy_rtmp_btn.setEnabled(True)
        else:
            self._clear_server_details()

            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.copy_rtmp_btn.setEnabled(False)

    def _update_server_details(self, server: ServerConfig):
        """Update server details display"""
        self.detail_name_label.setText(server.name)
        self.detail_host_label.setText(server.host)
        self.detail_ports_label.setText(f"HTTP: {server.port}, RTMP: {server.rtmp_port}")
        self.detail_ssl_label.setText("Идэвхтэй" if server.ssl_enabled else "Идэвхгүй")
        self.detail_auth_label.setText("Шаардлагатай" if server.username else "Шаардлагагүй")
        self.detail_rtmp_label.setText(server.rtmp_url)
        self.detail_api_label.setText(server.api_url)

        if server.description:
            self.detail_description_label.setText(server.description)
            self.detail_description_label.setStyleSheet("color: #333; padding: 8px; background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 3px; font-size: 10px;")
        else:
            self.detail_description_label.setText("Тайлбар байхгүй")
            self.detail_description_label.setStyleSheet("color: #666; font-style: italic; padding: 8px; background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 3px; font-size: 10px;")

    def _clear_server_details(self):
        """Clear server details display"""
        for label in [self.detail_name_label, self.detail_host_label, self.detail_ports_label,
                      self.detail_ssl_label, self.detail_auth_label, self.detail_rtmp_label, self.detail_api_label]:
            label.setText("-")

        self.detail_description_label.setText("Сервер сонгогдоогүй байна")
        self.detail_description_label.setStyleSheet("color: #666; font-style: italic; padding: 8px; background-color: #f9f9f9; border: 1px dashed #ddd; border-radius: 3px; font-size: 10px;")

    def _add_server(self):
        """Add new server"""
        dialog = ServerEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_config = dialog.get_server_config()
            if server_config:
                key = server_config.name.lower().replace(" ", "_").replace("-", "_")
                counter = 1
                original_key = key
                while key in self.servers:
                    key = f"{original_key}_{counter}"
                    counter += 1

                try:
                    self.storage_manager.add_server(key, server_config)
                    self.servers[key] = server_config
                    self._populate_servers()
                    
                    QMessageBox.information(self, "Амжилттай", f"Сервер '{server_config.name}' нэмэгдлээ")
                except Exception as e:
                    QMessageBox.warning(self, "Алдаа", f"Сервер нэмэхэд алдаа гарлаа:\n{e}")

    def _edit_server(self):
        """Edit selected server"""
        current = self.server_list.currentItem()
        if not current:
            return

        server_key = current.data(Qt.ItemDataRole.UserRole)
        if server_key not in self.servers:
            return

        dialog = ServerEditDialog(self.servers[server_key], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_config = dialog.get_server_config()
            if server_config:
                try:
                    self.storage_manager.update_server(server_key, server_config)
                    self.servers[server_key] = server_config
                    self._populate_servers()
                    self._update_server_details(server_config)
                    
                    QMessageBox.information(self, "Амжилттай", f"Сервер '{server_config.name}' шинэчлэгдлээ")
                except Exception as e:
                    QMessageBox.warning(self, "Алдаа", f"Сервер шинэчлэхэд алдаа гарлаа:\n{e}")

    def _delete_server(self):
        """Delete selected server"""
        current = self.server_list.currentItem()
        if not current:
            return

        server_key = current.data(Qt.ItemDataRole.UserRole)
        if server_key not in self.servers:
            return

        server_name = self.servers[server_key].name

        reply = QMessageBox.question(
            self,
            "Сервер Устгах",
            f"Та '{server_name}' серверийг устгахдаа итгэлтэй байна уу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.storage_manager.remove_server(server_key)
                del self.servers[server_key]
                self._populate_servers()
                
                QMessageBox.information(self, "Амжилттай", f"Сервер '{server_name}' устгагдлаа")
            except Exception as e:
                QMessageBox.warning(self, "Алдаа", f"Сервер устгахад алдаа гарлаа:\n{e}")

    def _test_selected_server(self):
        """Test connection to selected server"""
        current = self.server_list.currentItem()
        if not current:
            QMessageBox.information(self, "Сонголт хийх", "Тест хийх серверийг сонгоно уу")
            return

        server_key = current.data(Qt.ItemDataRole.UserRole)
        if server_key in self.servers:
            server = self.servers[server_key]
            
            try:
                import socket
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server.host, server.rtmp_port))
                sock.close()
                
                if result == 0:
                    QMessageBox.information(self, "Холболтын Тест", 
                                          f"✅ '{server.name}' серверт амжилттай холбогдлоо!")
                else:
                    QMessageBox.warning(self, "Холболтын Тест", 
                                      f"❌ '{server.name}' серверт холбогдож чадсангүй\n"
                                      f"Хост: {server.host}:{server.rtmp_port}")
                    
            except Exception as e:
                QMessageBox.warning(self, "Холболтын Тест", 
                                  f"❌ Холболтын тест хийхэд алдаа гарлаа:\n{str(e)}")

    def _copy_rtmp_url(self):
        """Copy the RTMP URL of the selected server to clipboard"""
        current = self.server_list.currentItem()
        if not current:
            QMessageBox.information(self, "Хуулах", "Хуулах серверийг сонгоно уу.")
            return

        server_key = current.data(Qt.ItemDataRole.UserRole)
        if server_key in self.servers:
            server = self.servers[server_key]
            clipboard = QApplication.clipboard()
            clipboard.setText(server.rtmp_url)
            QToolTip.showText(
                QCursor.pos(), 
                f"RTMP URL амжилттай хуулагдлаа! 📋", 
                self.copy_rtmp_btn,
                QRect(),
                3000
            )
        else:
            QMessageBox.warning(self, "Хуулах Алдаа", "Сонгосон серверийн RTMP URL-ийг олж чадсангүй.")

    def _import_servers(self):
        """Import servers from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Сервер Импорт",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                imported_count = 0
                servers_data = data.get('servers', {})
                
                for server_id, server_info in servers_data.items():
                    try:
                        server_config = ServerConfig.from_dict(server_info)
                        
                        key = server_id
                        counter = 1
                        while key in self.servers:
                            key = f"{server_id}_{counter}"
                            counter += 1
                        
                        self.storage_manager.add_server(key, server_config)
                        self.servers[key] = server_config
                        imported_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to import server {server_id}: {e}")
                
                self._populate_servers()
                QMessageBox.information(self, "Импорт", f"{imported_count} сервер амжилттай импорт хийгдлээ")
                
            except Exception as e:
                QMessageBox.warning(self, "Импорт Алдаа", f"Файл импорт хийхэд алдаа гарлаа:\n{e}")

    def _export_servers(self):
        """Export servers to file"""
        if not self.servers:
            QMessageBox.information(self, "Экспорт", "Экспорт хийх сервер байхгүй байна")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сервер Экспорт",
            f"servers_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                servers_data = {key: server.to_dict() for key, server in self.servers.items()}
                
                export_data = {
                    "version": "1.0",
                    "exported_at": datetime.datetime.now().isoformat(),
                    "total_servers": len(self.servers),
                    "servers": servers_data
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Экспорт", f"Серверүүд амжилттай экспорт хийгдлээ:\n{file_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "Экспорт Алдаа", f"Файл экспорт хийхэд алдаа гарлаа:\n{e}")

    def _save_and_close(self):
        """Save servers and close dialog"""
        try:
            self.accept()
        except Exception as e:
            self.logger.error(f"Failed to close dialog: {e}")
            self.accept()

    def get_servers(self) -> Dict[str, ServerConfig]:
        """Get all servers"""
        return self.servers.copy()
    
    def _load_default_servers(self):
        """Load default server configurations"""
        reply = QMessageBox.question(
            self,
            "Үндсэн Тохиргоог Ачаалах",
            "Та одоогийн бүх серверийн тохиргоог үндсэн тохиргоогоор солихдоо итгэлтэй байна уу?\n\nЭнэ үйлдлийг буцаах боломжгүй.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.servers.clear()
            self._create_default_servers()
            self.storage_manager.save_servers(self.servers)
            self._populate_servers()
            self._clear_server_details()
            QMessageBox.information(self, "Амжилттай", "Үндсэн серверийн тохиргоог амжилттай ачааллаа.")
            self.logger.info("Default server configurations loaded and saved.")


# =============================================================================
# EXPORT FOR INTEGRATION
# =============================================================================

__all__ = [
    'ServerConfig',
    'ServerEditDialog', 
    'ServerManagerDialog',
    'ServerStorageManager'
]


# =============================================================================
# TESTING AND STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    """Test the server configuration dialog standalone"""
    import sys

    app = QApplication(sys.argv)
    
    print("🧪 Testing Server Storage Manager...")
    storage = ServerStorageManager("test_servers.json")
    
    test_server = ServerConfig(
        name="Test Server",
        host="test.example.com",
        port=8080,
        rtmp_port=1935,
        description="Test server configuration"
    )
    storage.add_server("test", test_server)
    
    dialog = ServerManagerDialog()
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        servers = dialog.get_servers()
        print(f"✅ Dialog completed with {len(servers)} servers:")
        for key, server in servers.items():
            print(f"  - {key}: {server.name} ({server.host})")
    else:
        print("❌ Dialog cancelled")

    try:
        os.remove("test_servers.json")
        print("🧹 Test file cleaned up")
    except:
        pass

    sys.exit(0)