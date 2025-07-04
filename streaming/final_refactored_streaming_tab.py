"""
TV Stream - Refactored Streaming Tab (Complete Implementation)
Давхардлыг арилгасан, сайжруулсан streaming tab
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try PyQt6 first, fallback to PyQt5
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

# Шинэ refactored модулууд
from utils import MediaValidator, LoggerManager, ConfigurationManager, StreamingUtils, ErrorHandler
from ui_helpers import UIUpdateManager, FormBuilder, StatusManager, DialogHelper, TableHelper, StyleManager
from server_management import ServerManager, ServerConfig
from program_stream_manager import ProgramStreamManager
from ffmpeg_builder import FFmpegCommandBuilder, FFmpegValidator

# Core streaming components (fallback imports)
try:
    from ui.tabs.streaming_tab import StreamManager, StreamTableModel, StreamConfig, QUALITY_PRESETS, ENCODER_PRESETS
    STREAMING_CORE_AVAILABLE = True
except ImportError:
    STREAMING_CORE_AVAILABLE = False
    # Create fallback implementations


# =============================================================================
# FALLBACK IMPLEMENTATIONS
# =============================================================================

if not STREAMING_CORE_AVAILABLE:
    # Quality presets fallback
    QUALITY_PRESETS = {
        "480p": {
            "name": "480p (SD)",
            "width": 854,
            "height": 480,
            "fps": 30,
            "video_bitrate": "1000k",
            "audio_bitrate": "128k"
        },
        "720p": {
            "name": "720p (HD)",  
            "width": 1280,
            "height": 720,
            "fps": 30,
            "video_bitrate": "2500k",
            "audio_bitrate": "128k"
        },
        "1080p": {
            "name": "1080p (Full HD)",
            "width": 1920,
            "height": 1080, 
            "fps": 30,
            "video_bitrate": "4500k",
            "audio_bitrate": "192k"
        }
    }
    
    # Encoder presets fallback
    ENCODER_PRESETS = {
        "x264": {
            "name": "x264 (CPU)",
            "encoder": "libx264",
            "description": "Software encoding"
        },
        "nvenc": {
            "name": "NVENC (NVIDIA)",
            "encoder": "h264_nvenc", 
            "description": "Hardware encoding"
        },
        "qsv": {
            "name": "QuickSync (Intel)",
            "encoder": "h264_qsv",
            "description": "Hardware encoding"
        }
    }
    
    # StreamConfig fallback
    class StreamConfig:
        def __init__(self, stream_key: str, input_source: str, server, quality: Dict,
                     encoder: str = "libx264", audio_encoder: str = "aac",
                     rate_control: str = "CBR", preset: str = "veryfast",
                     loop_input: bool = False, start_time: str = None,
                     duration: str = None, **kwargs):
            self.stream_key = stream_key
            self.input_source = input_source
            self.server = server
            self.quality = quality
            self.encoder = encoder
            self.audio_encoder = audio_encoder
            self.rate_control = rate_control
            self.preset = preset
            self.loop_input = loop_input
            self.start_time = start_time
            self.duration = duration
            self.custom_ffmpeg_args = []
            
            # Additional attributes
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                'stream_key': self.stream_key,
                'input_source': self.input_source,
                'server': self.server.to_dict() if hasattr(self.server, 'to_dict') else str(self.server),
                'quality': self.quality,
                'encoder': self.encoder,
                'audio_encoder': self.audio_encoder,
                'rate_control': self.rate_control,
                'preset': self.preset,
                'loop_input': self.loop_input,
                'start_time': self.start_time,
                'duration': self.duration
            }
    
    # StreamProcessor fallback
    class StreamProcessor:
        def __init__(self, stream_config: StreamConfig):
            self.stream_config = stream_config
            self.is_running = False
            self.start_time = time.time()
            self.stats = {
                'fps': 0.0,
                'bitrate': '0kbits/s',
                'frames_processed': 0,
                'dropped_frames': 0
            }
        
        def get_uptime(self) -> str:
            uptime_seconds = int(time.time() - self.start_time)
            return StreamingUtils.format_uptime(uptime_seconds)
        
        def stop(self):
            self.is_running = False
    
    # StreamManager fallback
    class StreamManager(QObject):
        stream_started = pyqtSignal(str)
        stream_stopped = pyqtSignal(str)
        stream_error = pyqtSignal(str, str)
        streams_updated = pyqtSignal()
        
        def __init__(self):
            super().__init__()
            self.streams = {}
            self.logger = LoggerManager.get_logger(__name__)
        
        def start_stream(self, stream_config: StreamConfig) -> bool:
            try:
                processor = StreamProcessor(stream_config)
                processor.is_running = True
                self.streams[stream_config.stream_key] = processor
                
                self.stream_started.emit(stream_config.stream_key)
                self.streams_updated.emit()
                
                self.logger.info(f"Started fallback stream: {stream_config.stream_key}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to start stream: {e}")
                return False
        
        def stop_stream(self, stream_key: str) -> bool:
            if stream_key in self.streams:
                processor = self.streams.pop(stream_key)
                processor.stop()
                
                self.stream_stopped.emit(stream_key)
                self.streams_updated.emit()
                
                self.logger.info(f"Stopped fallback stream: {stream_key}")
                return True
            return False
        
        def stop_all_streams(self):
            for stream_key in list(self.streams.keys()):
                self.stop_stream(stream_key)
    
    # StreamTableModel fallback
    class StreamTableModel(QAbstractTableModel):
        def __init__(self, stream_manager):
            super().__init__()
            self.stream_manager = stream_manager
            self.headers = ["Stream Key", "Status", "Server", "Quality", "FPS", "Bitrate", "Uptime", "Actions"]
        
        def rowCount(self, parent=QModelIndex()):
            return len(self.stream_manager.streams)
        
        def columnCount(self, parent=QModelIndex()):
            return len(self.headers)
        
        def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
            if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
                return self.headers[section]
            return None
        
        def data(self, index, role=Qt.ItemDataRole.DisplayRole):
            if not index.isValid():
                return None
            
            stream_keys = list(self.stream_manager.streams.keys())
            if index.row() >= len(stream_keys):
                return None
            
            stream_key = stream_keys[index.row()]
            processor = self.stream_manager.streams[stream_key]
            
            if role == Qt.ItemDataRole.DisplayRole:
                col = index.column()
                if col == 0:
                    return stream_key
                elif col == 1:
                    return "Running" if processor.is_running else "Stopped"
                elif col == 2:
                    return getattr(processor.stream_config.server, 'name', 'Unknown')
                elif col == 3:
                    return processor.stream_config.quality.get('name', 'Unknown')
                elif col == 4:
                    return f"{processor.stats.get('fps', 0):.1f}"
                elif col == 5:
                    return processor.stats.get('bitrate', '0kbits/s')
                elif col == 6:
                    return processor.get_uptime()
                elif col == 7:
                    return "•••"
            
            elif role == Qt.ItemDataRole.UserRole:
                return stream_key
            
            return None


class RefactoredStreamingTab(QWidget):
    """Давхардлыг арилгасан streaming tab"""
    
    # Signals
    status_message = pyqtSignal(str, int)
    stream_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        # Utility классууд
        self.logger = LoggerManager.get_logger(__name__)
        self.validator = MediaValidator()
        self.streaming_utils = StreamingUtils()
        self.error_handler = ErrorHandler()
        
        # UI управление
        self.ui_manager = UIUpdateManager(self)
        self.form_builder = FormBuilder(self)
        self.status_manager = StatusManager()
        self.dialog_helper = DialogHelper()
        self.table_helper = TableHelper()
        self.style_manager = StyleManager()
        
        # Core streaming
        self.stream_manager = StreamManager()
        
        # Server удирдлага
        self.server_manager = ServerManager()
        
        # Program streaming
        self.program_stream_manager = ProgramStreamManager(self, self.stream_manager)
        
        # FFmpeg
        self.ffmpeg_validator = FFmpegValidator()
        
        # UI элементүүд
        self.ui_elements = {}
        self.status_labels = {}
        
        # Төлөв
        self.current_input_source = None
        self.active_streams = {}
        
        # Store quality presets reference for other modules
        self.quality_presets = QUALITY_PRESETS
        
        # Initialization
        self._init_ui()
        self._connect_signals()
        self._post_init_setup()
    
    def _init_ui(self):
        """UI үүсгэх"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header section
        header_section = self._create_header_section()
        layout.addWidget(header_section)
        
        # Input source section
        input_section = self._create_input_source_section()
        layout.addWidget(input_section)
        
        # Stream configuration section
        config_section = self._create_stream_configuration_section()
        layout.addWidget(config_section)
        
        # Controls section
        controls_section = self._create_controls_section()
        layout.addWidget(controls_section)
        
        # Active streams section
        streams_section = self._create_streams_section()
        layout.addWidget(streams_section, stretch=1)
        
        # Status section
        status_section = self._create_status_section()
        layout.addWidget(status_section)
    
    def _create_header_section(self) -> QWidget:
        """Header section үүсгэх"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("📡 Professional Streaming")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50;
                padding: 8px;
            }
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # System status indicators
        status_items = [
            {'name': 'ffmpeg_status', 'display': 'FFmpeg', 'value': 'Checking...'},
            {'name': 'server_count', 'display': 'Servers', 'value': '0'},
            {'name': 'stream_count', 'display': 'Active', 'value': '0'}
        ]
        
        for item in status_items:
            status_label = QLabel(f"{item['display']}: {item['value']}")
            status_label.setStyleSheet("""
                QLabel {
                    padding: 4px 8px;
                    margin: 2px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    background-color: #f8f9fa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(status_label)
            self.status_labels[item['name']] = status_label
        
        return header
    
    def _create_input_source_section(self) -> QWidget:
        """Input source section үүсгэх"""
        group = self.form_builder.create_group_box("📹 Input Source", 'form')
        layout = group.layout()
        
        # Source type
        self.ui_elements['source_type_combo'] = QComboBox()
        self.ui_elements['source_type_combo'].addItems([
            "Media File", "Desktop Capture", "Webcam", "Audio Input", "Test Pattern"
        ])
        layout.addRow("Source Type:", self.ui_elements['source_type_combo'])
        
        # Source input with browse
        source_widgets = self.form_builder.create_input_with_browse(
            placeholder="Select media file or configure input...",
            file_filter="Media Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.mp3 *.wav *.flac *.aac);;All Files (*)"
        )
        self.ui_elements['source_input'] = source_widgets['input']
        self.ui_elements['browse_btn'] = source_widgets['button']
        layout.addRow("Source:", source_widgets['container'])
        
        # Options
        options_widget = self._create_input_options_widget()
        layout.addRow("Options:", options_widget)
        
        return group
    
    def _create_input_options_widget(self) -> QWidget:
        """Input options widget үүсгэх"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Loop input
        self.ui_elements['loop_input_cb'] = QCheckBox("Loop Input")
        layout.addWidget(self.ui_elements['loop_input_cb'])
        
        # Start time
        layout.addWidget(QLabel("Start:"))
        self.ui_elements['start_time_input'] = QLineEdit()
        self.ui_elements['start_time_input'].setPlaceholderText("HH:MM:SS")
        self.ui_elements['start_time_input'].setMaximumWidth(80)
        layout.addWidget(self.ui_elements['start_time_input'])
        
        # Duration
        layout.addWidget(QLabel("Duration:"))
        self.ui_elements['duration_input'] = QLineEdit()
        self.ui_elements['duration_input'].setPlaceholderText("HH:MM:SS")
        self.ui_elements['duration_input'].setMaximumWidth(80)
        layout.addWidget(self.ui_elements['duration_input'])
        
        layout.addStretch()
        return container
    
    def _create_stream_configuration_section(self) -> QWidget:
        """Stream configuration section үүсгэх"""
        group = self.form_builder.create_group_box("⚙️ Stream Configuration", 'form')
        layout = group.layout()
        
        # Server selection
        server_widget = self._create_server_selection_widget()
        layout.addRow("Server:", server_widget)
        
        # Stream key
        stream_key_widget = self._create_stream_key_widget()
        layout.addRow("Stream Key:", stream_key_widget)
        
        # Quality and encoder
        quality_encoder_widget = self._create_quality_encoder_widget()
        layout.addRow("Quality & Encoder:", quality_encoder_widget)
        
        # Advanced settings
        advanced_widget = self._create_advanced_settings_widget()
        layout.addRow("Advanced:", advanced_widget)
        
        return group
    
    def _create_server_selection_widget(self) -> QWidget:
        """Server selection widget үүсгэх"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Server combo
        self.ui_elements['server_combo'] = QComboBox()
        self.ui_elements['server_combo'].setMinimumWidth(200)
        layout.addWidget(self.ui_elements['server_combo'])
        
        # Server management buttons
        server_buttons = [
            {'text': '➕', 'clicked': self._add_server, 'tooltip': 'Add Server'},
            {'text': '✏️', 'clicked': self._edit_server, 'tooltip': 'Edit Server'},
            {'text': '🛠️', 'clicked': self._manage_servers, 'tooltip': 'Manage Servers'},
            {'text': '🔄', 'clicked': self._refresh_servers, 'tooltip': 'Refresh Servers'}
        ]
        
        for btn_config in server_buttons:
            btn = QPushButton(btn_config['text'])
            btn.setMaximumWidth(35)
            btn.setToolTip(btn_config['tooltip'])
            btn.clicked.connect(btn_config['clicked'])
            layout.addWidget(btn)
        
        return container
    
    def _create_stream_key_widget(self) -> QWidget:
        """Stream key widget үүсгэх"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Stream key input
        self.ui_elements['stream_key_input'] = QLineEdit()
        self.ui_elements['stream_key_input'].setPlaceholderText("Auto-generated or enter manually")
        layout.addWidget(self.ui_elements['stream_key_input'])
        
        # Generate key button
        self.ui_elements['generate_key_btn'] = QPushButton("🎲")
        self.ui_elements['generate_key_btn'].setMaximumWidth(35)
        self.ui_elements['generate_key_btn'].setToolTip("Generate Stream Key")
        self.ui_elements['generate_key_btn'].clicked.connect(self._generate_stream_key)
        layout.addWidget(self.ui_elements['generate_key_btn'])
        
        # Show/hide key button
        self.ui_elements['show_key_btn'] = QPushButton("👁")
        self.ui_elements['show_key_btn'].setCheckable(True)
        self.ui_elements['show_key_btn'].setMaximumWidth(35)
        self.ui_elements['show_key_btn'].setToolTip("Show/Hide Stream Key")
        self.ui_elements['show_key_btn'].toggled.connect(self._toggle_stream_key_visibility)
        layout.addWidget(self.ui_elements['show_key_btn'])
        
        return container
    
    def _create_quality_encoder_widget(self) -> QWidget:
        """Quality & encoder widget үүсгэх"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Quality preset
        layout.addWidget(QLabel("Quality:"))
        self.ui_elements['quality_combo'] = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.ui_elements['quality_combo'].addItem(quality_data["name"], quality_data)
        self.ui_elements['quality_combo'].setCurrentText("720p (HD)")
        layout.addWidget(self.ui_elements['quality_combo'])
        
        # Encoder
        layout.addWidget(QLabel("Encoder:"))
        self.ui_elements['encoder_combo'] = QComboBox()
        for encoder_key, encoder_data in ENCODER_PRESETS.items():
            self.ui_elements['encoder_combo'].addItem(encoder_data["name"], encoder_key)
        layout.addWidget(self.ui_elements['encoder_combo'])
        
        return container
    
    def _create_advanced_settings_widget(self) -> QWidget:
        """Advanced settings widget үүсгэх"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Rate control
        layout.addWidget(QLabel("Rate Control:"))
        self.ui_elements['rate_control_combo'] = QComboBox()
        self.ui_elements['rate_control_combo'].addItems(["CBR", "VBR", "CQP"])
        layout.addWidget(self.ui_elements['rate_control_combo'])
        
        # Preset
        layout.addWidget(QLabel("Preset:"))
        self.ui_elements['preset_combo'] = QComboBox()
        self.ui_elements['preset_combo'].addItems([
            "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"
        ])
        self.ui_elements['preset_combo'].setCurrentText("veryfast")
        layout.addWidget(self.ui_elements['preset_combo'])
        
        return container
    
    def _create_controls_section(self) -> QWidget:
        """Controls section үүсгэх"""
        group = self.form_builder.create_group_box("🎛️ Stream Controls", 'vertical')
        layout = group.layout()
        
        # Main controls
        main_controls = self._create_main_controls()
        layout.addWidget(main_controls)
        
        # Program streaming controls
        program_controls = self._create_program_controls()
        layout.addWidget(program_controls)
        
        return group
    
    def _create_main_controls(self) -> QWidget:
        """Main controls үүсгэх"""
        button_configs = [
            {
                'text': '🚀 Start Stream',
                'clicked': self._start_stream,
                'style': 'success',
                'ref': 'start_btn'
            },
            {
                'text': '⏹️ Stop Selected',
                'clicked': self._stop_selected_stream,
                'style': 'danger',
                'enabled': False,
                'ref': 'stop_btn'
            },
            {
                'text': '🧪 Test Stream',
                'clicked': self._test_stream,
                'ref': 'test_btn'
            },
            {
                'text': '🛑 Stop All',
                'clicked': self._stop_all_streams,
                'style': 'danger',
                'enabled': False,
                'ref': 'stop_all_btn'
            }
        ]
        
        controls_widget = self.form_builder.create_button_row(button_configs)
        
        # Store button references
        for config in button_configs:
            if 'ref' in config and 'button_ref' in config:
                self.ui_elements[config['ref']] = config['button_ref']
        
        return controls_widget
    
    def _create_program_controls(self) -> QWidget:
        """Program streaming controls үүсгэх"""
        group = self.form_builder.create_group_box("📺 Program Streaming", 'vertical')
        layout = group.layout()
        
        # Auto-stream control
        auto_stream_layout = QHBoxLayout()
        
        self.ui_elements['auto_stream_cb'] = QCheckBox("Auto-start streaming when ON AIR")
        self.ui_elements['auto_stream_cb'].setChecked(True)
        auto_stream_layout.addWidget(self.ui_elements['auto_stream_cb'])
        
        auto_stream_layout.addWidget(QLabel("Quality:"))
        self.ui_elements['program_quality_combo'] = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.ui_elements['program_quality_combo'].addItem(quality_data["name"], quality_key)
        self.ui_elements['program_quality_combo'].setCurrentText("720p (HD)")
        auto_stream_layout.addWidget(self.ui_elements['program_quality_combo'])
        
        auto_stream_layout.addStretch()
        layout.addLayout(auto_stream_layout)
        
        # Program status and controls
        program_status_layout = QHBoxLayout()
        
        self.ui_elements['program_status_label'] = QLabel("⚫ Not Streaming")
        self.ui_elements['program_status_label'].setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
        """)
        program_status_layout.addWidget(self.ui_elements['program_status_label'])
        
        program_status_layout.addStretch()
        
        # Program control buttons
        program_button_configs = [
            {
                'text': '🎬 Start Program',
                'clicked': self._start_program_stream,
                'enabled': False,
                'ref': 'start_program_btn'
            },
            {
                'text': '⏹️ Stop Program',
                'clicked': self._stop_program_streams,
                'enabled': False,
                'ref': 'stop_program_btn'
            }
        ]
        
        for config in program_button_configs:
            btn = QPushButton(config['text'])
            btn.clicked.connect(config['clicked'])
            btn.setEnabled(config.get('enabled', True))
            program_status_layout.addWidget(btn)
            
            if 'ref' in config:
                self.ui_elements[config['ref']] = btn
        
        layout.addLayout(program_status_layout)
        
        return group
    
    def _create_streams_section(self) -> QWidget:
        """Active streams section үүсгэх"""
        group = self.form_builder.create_group_box("📡 Active Streams", 'vertical')
        layout = group.layout()
        
        # Streams table
        self.ui_elements['streams_table'] = QTableView()
        self.stream_model = StreamTableModel(self.stream_manager)
        self.ui_elements['streams_table'].setModel(self.stream_model)
        
        # Table setup
        self.table_helper.setup_table_view(
            self.ui_elements['streams_table'],
            column_widths=[150, 120, 100, 100, 90, 60, 90, 90],
            selection_behavior='rows',
            alternating_colors=True
        )
        
        layout.addWidget(self.ui_elements['streams_table'])
        
        # Stream details and controls
        details_layout = self._create_stream_details_layout()
        layout.addLayout(details_layout)
        
        return group
    
    def _create_stream_details_layout(self) -> QHBoxLayout:
        """Stream details layout үүсгэх"""
        layout = QHBoxLayout()
        
        # Stream statistics
        stats_group = self.form_builder.create_group_box("📊 Statistics", 'form')
        stats_layout = stats_group.layout()
        
        self.status_labels.update({
            'selected_stream': QLabel("None"),
            'stream_server': QLabel("-"),
            'stream_quality': QLabel("-"),
            'stream_fps': QLabel("-"),
            'stream_bitrate': QLabel("-"),
            'stream_uptime': QLabel("-")
        })
        
        stats_layout.addRow("Selected:", self.status_labels['selected_stream'])
        stats_layout.addRow("Server:", self.status_labels['stream_server'])
        stats_layout.addRow("Quality:", self.status_labels['stream_quality'])
        stats_layout.addRow("FPS:", self.status_labels['stream_fps'])
        stats_layout.addRow("Bitrate:", self.status_labels['stream_bitrate'])
        stats_layout.addRow("Uptime:", self.status_labels['stream_uptime'])
        
        layout.addWidget(stats_group)
        
        # Stream controls
        controls_group = self.form_builder.create_group_box("🎮 Stream Controls", 'vertical')
        controls_layout = controls_group.layout()
        
        # Quality control
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Change Quality:"))
        
        self.ui_elements['live_quality_combo'] = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.ui_elements['live_quality_combo'].addItem(quality_data["name"], quality_data)
        quality_layout.addWidget(self.ui_elements['live_quality_combo'])
        
        self.ui_elements['apply_quality_btn'] = QPushButton("Apply")
        self.ui_elements['apply_quality_btn'].clicked.connect(self._apply_quality_change)
        self.ui_elements['apply_quality_btn'].setEnabled(False)
        quality_layout.addWidget(self.ui_elements['apply_quality_btn'])
        
        controls_layout.addLayout(quality_layout)
        
        # Action buttons
        action_button_configs = [
            {
                'text': '🔄 Restart',
                'clicked': self._restart_selected_stream,
                'enabled': False,
                'ref': 'restart_stream_btn'
            },
            {
                'text': '📋 Stream Info',
                'clicked': self._show_stream_info,
                'enabled': False,
                'ref': 'stream_info_btn'
            }
        ]
        
        action_buttons = self.form_builder.create_button_row(action_button_configs, stretch_before=False)
        controls_layout.addWidget(action_buttons)
        
        # Store button references
        for config in action_button_configs:
            if 'ref' in config and 'button_ref' in config:
                self.ui_elements[config['ref']] = config['button_ref']
        
        layout.addWidget(controls_group)
        
        return layout
    
    def _create_status_section(self) -> QWidget:
        """Status section үүсгэх"""
        group = self.form_builder.create_group_box("📈 System Status", 'horizontal')
        layout = group.layout()
        
        # Overall statistics
        overall_stats = self.form_builder.create_group_box("Overall", 'form')
        overall_layout = overall_stats.layout()
        
        self.status_labels.update({
            'total_streams': QLabel("0"),
            'total_bitrate': QLabel("0 kbps"),
            'estimated_bandwidth': QLabel("0.0 Mbps"),
            'network_latency': QLabel("N/A")
        })
        
        overall_layout.addRow("Active Streams:", self.status_labels['total_streams'])
        overall_layout.addRow("Total Bitrate:", self.status_labels['total_bitrate'])
        overall_layout.addRow("Est. Bandwidth:", self.status_labels['estimated_bandwidth'])
        overall_layout.addRow("Network Latency:", self.status_labels['network_latency'])
        
        layout.addWidget(overall_stats)
        
        # System health
        health_stats = self.form_builder.create_group_box("System Health", 'form')
        health_layout = health_stats.layout()
        
        self.status_labels.update({
            'ffmpeg_version': QLabel("Unknown"),
            'available_encoders': QLabel("Unknown"),
            'optimization_status': QLabel("Disabled"),
            'reconnect_count': QLabel("0")
        })
        
        health_layout.addRow("FFmpeg:", self.status_labels['ffmpeg_version'])
        health_layout.addRow("Encoders:", self.status_labels['available_encoders'])
        health_layout.addRow("Optimization:", self.status_labels['optimization_status'])
        health_layout.addRow("Reconnects:", self.status_labels['reconnect_count'])
        
        layout.addWidget(health_stats)
        
        return group
    
    def _connect_signals(self):
        """Signals холбох"""
        # Stream manager signals
        self.stream_manager.stream_started.connect(self._on_stream_started)
        self.stream_manager.stream_stopped.connect(self._on_stream_stopped)
        self.stream_manager.stream_error.connect(self._on_stream_error)
        self.stream_manager.streams_updated.connect(self._update_ui_state)
        
        # Program stream manager signals
        self.program_stream_manager.stream_started.connect(self._on_program_stream_started)
        self.program_stream_manager.stream_stopped.connect(self._on_program_stream_stopped)
        self.program_stream_manager.status_changed.connect(self._on_program_status_changed)
        
        # UI signals
        if 'source_type_combo' in self.ui_elements:
            self.ui_elements['source_type_combo'].currentTextChanged.connect(self._on_source_type_changed)
        
        if 'auto_stream_cb' in self.ui_elements:
            self.ui_elements['auto_stream_cb'].toggled.connect(self._on_auto_stream_toggled)
        
        if 'program_quality_combo' in self.ui_elements:
            self.ui_elements['program_quality_combo'].currentTextChanged.connect(self._on_program_quality_changed)
        
        # Table selection
        if 'streams_table' in self.ui_elements:
            selection_model = self.ui_elements['streams_table'].selectionModel()
            if selection_model:
                selection_model.currentRowChanged.connect(self._on_stream_selection_changed)
    
    def _post_init_setup(self):
        """Эхний тохиргоо дуусгах"""
        # FFmpeg шалгах
        QTimer.singleShot(100, self._check_system_requirements)
        
        # Серверүүд ачаалах
        QTimer.singleShot(200, self._load_servers)
        
        # UI төлөв шинэчлэх
        QTimer.singleShot(300, self._update_ui_state)
        
        # Status monitoring эхлүүлэх
        self._start_status_monitoring()
    
    def _check_system_requirements(self):
        """Системийн шаардлагыг шалгах"""
        # FFmpeg шалгах
        if self.ffmpeg_validator.is_ffmpeg_available():
            version = self.ffmpeg_validator.get_ffmpeg_version()
            self.status_labels['ffmpeg_version'].setText(version or "Available")
            self.status_labels['ffmpeg_status'].setText("✅ Available")
            
            # Encoders шалгах
            encoders = self.ffmpeg_validator.get_available_encoders()
            self.status_labels['available_encoders'].setText(f"{len(encoders)} available")
            
        else:
            self.status_labels['ffmpeg_version'].setText("Not Found")
            self.status_labels['ffmpeg_status'].setText("❌ Missing")
            
            # Warning диалог
            QTimer.singleShot(1000, self._show_ffmpeg_warning)
    
    def _show_ffmpeg_warning(self):
        """FFmpeg warning диалог"""
        self.dialog_helper.show_warning(
            self,
            "FFmpeg Not Found",
            "FFmpeg is required for streaming but was not found in system PATH.\n\n"
            "Please install FFmpeg:\n"
            "• Download from https://ffmpeg.org/download.html\n"
            "• Or use: winget install ffmpeg (Windows 10/11)\n\n"
            "Restart the application after installation."
        )
    
    def _load_servers(self):
        """Серверүүд ачаалах"""
        try:
            servers = self.server_manager.get_servers()
            
            # Server combo шинэчлэх
            server_items = []
            for server_id, server_config in servers.items():
                # Icon тодорхойлох
                if server_config.is_local:
                    icon = "🏠"
                elif server_config.is_local_network:
                    icon = "🏢"
                else:
                    icon = "🌐"
                
                server_items.append({
                    'name': f"{icon} {server_config.name} ({server_config.host}:{server_config.rtmp_port})",
                    'data': server_config
                })
            
            self.ui_manager.update_combo_box(
                self.ui_elements['server_combo'],
                server_items
            )
            
            # Status шинэчлэх
            self.status_labels['server_count'].setText(str(len(servers)))
            
            self.logger.info(f"Loaded {len(servers)} servers")
            
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
    
    def _start_status_monitoring(self):
        """Status monitoring эхлүүлэх"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # 2 секунд тутамд
    
    def _update_status(self):
        """Статус шинэчлэх"""
        try:
            # Stream statistics
            active_count = len(self.stream_manager.streams)
            self.status_labels['stream_count'].setText(str(active_count))
            self.status_labels['total_streams'].setText(str(active_count))
            
            # Calculate total bitrate
            total_bitrate = 0
            for processor in self.stream_manager.streams.values():
                bitrate_str = processor.stats.get('bitrate', '0kbits/s')
                try:
                    if 'kbits/s' in bitrate_str:
                        bitrate_value = float(bitrate_str.replace('kbits/s', ''))
                        total_bitrate += bitrate_value
                except (ValueError, AttributeError):
                    pass
            
            self.status_labels['total_bitrate'].setText(f"{total_bitrate:.0f} kbps")
            self.status_labels['estimated_bandwidth'].setText(f"{total_bitrate/1000:.1f} Mbps")
            
            # Table model шинэчлэх
            self.ui_manager.update_table_model(self.ui_elements['streams_table'])
            
        except Exception as e:
            self.logger.error(f"Status update failed: {e}")
    
    def _update_ui_state(self):
        """UI төлөв шинэчлэх"""
        try:
            has_streams = len(self.stream_manager.streams) > 0
            has_selection = (self.ui_elements['streams_table'].currentIndex().isValid() 
                           if 'streams_table' in self.ui_elements else False)
            
            # Button states - safely get button references
            buttons_to_update = {}
            
            if 'stop_all_btn' in self.ui_elements:
                buttons_to_update[self.ui_elements['stop_all_btn']] = has_streams
            
            if 'stop_btn' in self.ui_elements:
                buttons_to_update[self.ui_elements['stop_btn']] = has_selection
                
            if 'restart_stream_btn' in self.ui_elements:
                buttons_to_update[self.ui_elements['restart_stream_btn']] = has_selection
                
            if 'stream_info_btn' in self.ui_elements:
                buttons_to_update[self.ui_elements['stream_info_btn']] = has_selection
                
            if 'apply_quality_btn' in self.ui_elements:
                buttons_to_update[self.ui_elements['apply_quality_btn']] = has_selection
            
            self.ui_manager.enable_controls(buttons_to_update)
            
        except Exception as e:
            self.logger.error(f"UI state update failed: {e}")
    
    # Event handlers
    def _on_source_type_changed(self, source_type: str):
        """Source type өөрчлөгдөх"""
        input_mapping = {
            "Media File": "",
            "Desktop Capture": "live:desktop_capture",
            "Webcam": "live:webcam",
            "Audio Input": "live:audio_input",
            "Test Pattern": "live:test_pattern"
        }
        
        source_value = input_mapping.get(source_type, "")
        
        if source_value:
            self.ui_elements['source_input'].setText(source_value)
            self.ui_elements['browse_btn'].setEnabled(False)
        else:
            self.ui_elements['source_input'].clear()
            self.ui_elements['browse_btn'].setEnabled(True)
        
        self.current_input_source = source_value
    
    def _on_auto_stream_toggled(self, enabled: bool):
        """Auto stream тохиргоо өөрчлөгдөх"""
        self.program_stream_manager.set_auto_stream_enabled(enabled)
        
        # UI шинэчлэх
        if 'start_program_btn' in self.ui_elements:
            self.ui_elements['start_program_btn'].setEnabled(not enabled)
        if 'stop_program_btn' in self.ui_elements:
            self.ui_elements['stop_program_btn'].setEnabled(not enabled)
    
    def _on_program_quality_changed(self, quality_name: str):
        """Program quality өөрчлөгдөх"""
        # Quality key олох
        for quality_key, quality_data in QUALITY_PRESETS.items():
            if quality_data["name"] == quality_name:
                self.program_stream_manager.set_stream_quality(quality_key)
                break
    
    def _on_stream_selection_changed(self, current, previous):
        """Stream сонголт өөрчлөгдөх"""
        if current.isValid():
            stream_key = self.table_helper.get_selected_data(self.ui_elements['streams_table'])
            
            if stream_key and stream_key in self.stream_manager.streams:
                processor = self.stream_manager.streams[stream_key]
                config = processor.stream_config
                stats = processor.stats
                
                # Stream details шинэчлэх
                label_updates = {
                    self.status_labels['selected_stream']: stream_key,
                    self.status_labels['stream_server']: getattr(config.server, 'name', 'Unknown'),
                    self.status_labels['stream_quality']: config.quality.get('name', 'Unknown'),
                    self.status_labels['stream_fps']: f"{stats.get('fps', 0):.1f}",
                    self.status_labels['stream_bitrate']: stats.get('bitrate', 'N/A'),
                    self.status_labels['stream_uptime']: processor.get_uptime()
                }
                
                self.ui_manager.update_labels(label_updates)
        else:
            # Clear details
            label_updates = {
                self.status_labels['selected_stream']: "None",
                self.status_labels['stream_server']: "-",
                self.status_labels['stream_quality']: "-",
                self.status_labels['stream_fps']: "-",
                self.status_labels['stream_bitrate']: "-",
                self.status_labels['stream_uptime']: "-"
            }
            
            self.ui_manager.update_labels(label_updates)
        
        # UI state шинэчлэх
        self._update_ui_state()
    
    # Signal handlers
    def _on_stream_started(self, stream_key: str):
        """Stream эхэлсэн"""
        self.status_message.emit(f"Stream started: {stream_key}", 3000)
        self._update_ui_state()
    
    def _on_stream_stopped(self, stream_key: str):
        """Stream зогссон"""
        self.status_message.emit(f"Stream stopped: {stream_key}", 3000)
        
        if stream_key in self.active_streams:
            del self.active_streams[stream_key]
        
        self._update_ui_state()
    
    def _on_stream_error(self, stream_key: str, error_message: str):
        """Stream алдаа"""
        self.logger.error(f"Stream error for {stream_key}: {error_message}")
        self.status_message.emit(f"Stream error: {stream_key}", 5000)
        
        # Critical error бол диалог харуулах
        if any(critical in error_message.lower() for critical in 
               ['connection refused', 'timeout', 'failed to start']):
            self.dialog_helper.show_error(
                self,
                f"Stream Error - {stream_key}",
                f"Stream encountered an error:\n\n{error_message}\n\n"
                "Please check server connection and configuration."
            )
    
    def _on_program_stream_started(self, stream_key: str, file_path: str):
        """Program stream эхэлсэн"""
        self.ui_elements['program_status_label'].setText("🟢 Streaming Program")
        self.ui_elements['program_status_label'].setStyleSheet("""
            QLabel {
                color: #28a745; 
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
            }
        """)
        
        if 'stop_program_btn' in self.ui_elements:
            self.ui_elements['stop_program_btn'].setEnabled(True)
        
        self.stream_status_changed.emit(True, stream_key)
    
    def _on_program_stream_stopped(self, stream_key: str, reason: str):
        """Program stream зогссон"""
        self.ui_elements['program_status_label'].setText("⚫ Not Streaming")
        self.ui_elements['program_status_label'].setStyleSheet("""
            QLabel {
                color: #6c757d; 
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
        """)
        
        if 'stop_program_btn' in self.ui_elements:
            self.ui_elements['stop_program_btn'].setEnabled(False)
        
        self.stream_status_changed.emit(False, "")
    
    def _on_program_status_changed(self, is_active: bool, stream_key: str):
        """Program status өөрчлөгдөх"""
        if is_active:
            self._on_program_stream_started(stream_key, "")
        else:
            self._on_program_stream_stopped(stream_key, "")
    
    # Action methods
    def _generate_stream_key(self):
        """Stream key үүсгэх"""
        current_key = self.ui_elements['stream_key_input'].text().strip()
        if current_key and len(current_key) >= 3:
            return
        
        new_key = self.streaming_utils.generate_stream_key()
        self.ui_elements['stream_key_input'].setText(new_key)
        
        self.status_message.emit(f"Generated stream key: {new_key}", 2000)
    
    def _toggle_stream_key_visibility(self, visible: bool):
        """Stream key харуулах/нуух"""
        if visible:
            self.ui_elements['stream_key_input'].setEchoMode(QLineEdit.EchoMode.Normal)
            self.ui_elements['show_key_btn'].setText("🙈")
        else:
            self.ui_elements['stream_key_input'].setEchoMode(QLineEdit.EchoMode.Password)
            self.ui_elements['show_key_btn'].setText("👁")
    
    def _start_stream(self):
        """Stream эхлүүлэх"""
        try:
            # Validation
            if not self._validate_stream_inputs():
                return
            
            # Stream config үүсгэх
            stream_config = self._build_stream_config()
            if not stream_config:
                self.dialog_helper.show_error(
                    self, "Configuration Error",
                    "Failed to build stream configuration.\n\n"
                    "Please check all required fields."
                )
                return
            
            # Давхардсан stream key шалгах
            if stream_config.stream_key in self.stream_manager.streams:
                if self.dialog_helper.show_question(
                    self, "Duplicate Stream Key",
                    f"Stream '{stream_config.stream_key}' is already active.\n\n"
                    "Generate a new unique key?"
                ):
                    new_key = self.streaming_utils.generate_stream_key()
                    stream_config.stream_key = new_key
                    self.ui_elements['stream_key_input'].setText(new_key)
                else:
                    return
            
            # Stream эхлүүлэх
            self.status_message.emit(f"Starting stream: {stream_config.stream_key}", 3000)
            
            if self.stream_manager.start_stream(stream_config):
                self.active_streams[stream_config.stream_key] = stream_config
                self.status_message.emit(f"Stream started successfully: {stream_config.stream_key}", 5000)
            else:
                self.status_message.emit("Failed to start stream", 5000)
                self.dialog_helper.show_error(
                    self, "Stream Error",
                    "Failed to start stream.\n\n"
                    "Possible causes:\n"
                    "• RTMP server is not running\n"
                    "• Stream key already in use\n"
                    "• Network connection issues\n\n"
                    "Please check FFmpeg logs and server connection."
                )
                
        except Exception as e:
            self.logger.error(f"Error starting stream: {e}")
            self.status_message.emit(f"Stream start error: {e}", 5000)
            self.dialog_helper.show_error(
                self, "Stream Error",
                f"Failed to start stream:\n\n{str(e)}\n\n"
                "Check the logs for more details."
            )
    
    def _validate_stream_inputs(self) -> bool:
        """Stream inputs шалгах"""
        try:
            # Stream key шалгах
            stream_key = self.ui_elements['stream_key_input'].text().strip()
            if not stream_key:
                self._generate_stream_key()
                stream_key = self.ui_elements['stream_key_input'].text().strip()
            
            if len(stream_key) < 3:
                self.dialog_helper.show_warning(
                    self, "Invalid Stream Key",
                    "Stream key must be at least 3 characters long."
                )
                return False
            
            # Input source шалгах
            if not self.current_input_source:
                self.current_input_source = self.ui_elements['source_input'].text().strip()
                
            if not self.current_input_source:
                self.current_input_source = "live:test_pattern"
                self.ui_elements['source_input'].setText(self.current_input_source)
            
            # File source бол файл шалгах
            if not self.current_input_source.startswith('live:'):
                if not self.validator.is_valid_media_file(self.current_input_source):
                    self.dialog_helper.show_error(
                        self, "Invalid Media File",
                        f"Selected file is not a valid media file:\n{self.current_input_source}\n\n"
                        "Please select a new media file or use a live source."
                    )
                    return False
            
            # Server шалгах
            server = self.ui_elements['server_combo'].currentData()
            if not server:
                self.dialog_helper.show_error(
                    self, "No Server Selected",
                    "No server is selected.\n\n"
                    "Please:\n"
                    "1. Add a server using the Add button\n"
                    "2. Or manage servers using the Manage button"
                )
                return False
            
            # Time format шалгах
            start_time = self.ui_elements['start_time_input'].text().strip()
            if start_time and not self.streaming_utils.validate_time_format(start_time):
                self.dialog_helper.show_warning(
                    self, "Invalid Time Format",
                    f"Start time format is invalid: {start_time}\n\n"
                    "Please use HH:MM:SS format (e.g., 01:30:45)"
                )
                return False
            
            duration = self.ui_elements['duration_input'].text().strip()
            if duration and not self.streaming_utils.validate_time_format(duration):
                self.dialog_helper.show_warning(
                    self, "Invalid Time Format",
                    f"Duration format is invalid: {duration}\n\n"
                    "Please use HH:MM:SS format (e.g., 02:00:00)"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            self.dialog_helper.show_error(
                self, "Validation Error",
                f"Error validating inputs:\n{str(e)}"
            )
            return False
    
    def _build_stream_config(self) -> Optional[StreamConfig]:
        """Stream configuration үүсгэх"""
        try:
            # Basic configuration
            stream_key = self.ui_elements['stream_key_input'].text().strip()
            server = self.ui_elements['server_combo'].currentData()
            quality = self.ui_elements['quality_combo'].currentData()
            
            if not quality:
                quality = QUALITY_PRESETS["720p"]
            
            # Encoder
            encoder_key = self.ui_elements['encoder_combo'].currentData() or "x264"
            encoder = ENCODER_PRESETS.get(encoder_key, {}).get("encoder", "libx264")
            
            # Advanced settings
            rate_control = self.ui_elements['rate_control_combo'].currentText()
            preset = self.ui_elements['preset_combo'].currentText()
            loop_input = self.ui_elements['loop_input_cb'].isChecked()
            
            # Time settings
            start_time = self.ui_elements['start_time_input'].text().strip() or None
            duration = self.ui_elements['duration_input'].text().strip() or None
            
            # Create config
            config = StreamConfig(
                stream_key=stream_key,
                input_source=self.current_input_source,
                server=server,
                quality=quality,
                encoder=encoder,
                rate_control=rate_control,
                preset=preset,
                loop_input=loop_input,
                start_time=start_time,
                duration=duration
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to build stream config: {e}")
            return None
    
    def _test_stream(self):
        """Stream тест хийх"""
        if not self._validate_stream_inputs():
            return
        
        config = self._build_stream_config()
        if not config:
            return
        
        # FFmpeg command үүсгэх
        command_builder = FFmpegCommandBuilder(config, self.logger)
        
        if not command_builder.validate_command():
            self.dialog_helper.show_error(
                self, "Invalid Configuration",
                "Stream configuration is invalid.\n\n"
                "Please check all settings and try again."
            )
            return
        
        # Test results харуулах
        quality = config.quality
        video_bitrate = int(quality["video_bitrate"].replace("k", ""))
        audio_bitrate = int(quality["audio_bitrate"].replace("k", ""))
        total_bitrate = video_bitrate + audio_bitrate
        
        test_results = f"""Stream Configuration Test

✅ Input Source: {config.input_source}
✅ Server: {config.server.name}
✅ RTMP URL: {config.server.rtmp_url}
✅ Stream Key: {'*' * len(config.stream_key)}
✅ Quality: {quality['name']}
✅ Resolution: {quality['width']}x{quality['height']}
✅ Frame Rate: {quality['fps']} fps
✅ Video Encoder: {config.encoder}
✅ Rate Control: {config.rate_control}
✅ Preset: {config.preset}

📊 Bandwidth Estimation:
• Video: {video_bitrate} kbps
• Audio: {audio_bitrate} kbps
• Total: {total_bitrate} kbps ({total_bitrate/1000:.1f} Mbps)

⚠️ Note: This is only a configuration test.
Use "Start Stream" button to begin actual streaming."""
        
        self.dialog_helper.show_info(self, "Stream Configuration Test", test_results)
    
    def _stop_selected_stream(self):
        """Сонгогдсон stream зогсоох"""
        stream_key = self.table_helper.get_selected_data(self.ui_elements['streams_table'])
        if stream_key:
            self._stop_stream(stream_key)
    
    def _stop_stream(self, stream_key: str):
        """Тодорхой stream зогсоох"""
        if self.stream_manager.stop_stream(stream_key):
            if stream_key in self.active_streams:
                del self.active_streams[stream_key]
            self.status_message.emit(f"Stream stopped: {stream_key}", 3000)
        else:
            self.status_message.emit(f"Failed to stop stream: {stream_key}", 5000)
    
    def _stop_all_streams(self):
        """Бүх stream зогсоох"""
        if not self.stream_manager.streams:
            return
        
        if self.dialog_helper.show_question(
            self, "Stop All Streams",
            "Are you sure you want to stop all active streams?"
        ):
            self.stream_manager.stop_all_streams()
            self.active_streams.clear()
            self.status_message.emit("All streams stopped", 3000)
    
    def _restart_selected_stream(self):
        """Сонгогдсон stream дахин эхлүүлэх"""
        stream_key = self.table_helper.get_selected_data(self.ui_elements['streams_table'])
        if stream_key and stream_key in self.active_streams:
            config = self.active_streams[stream_key]
            self._stop_stream(stream_key)
            
            QTimer.singleShot(1000, lambda: self.stream_manager.start_stream(config))
            self.status_message.emit(f"Restarting stream: {stream_key}", 3000)
    
    def _show_stream_info(self):
        """Stream мэдээлэл харуулах"""
        stream_key = self.table_helper.get_selected_data(self.ui_elements['streams_table'])
        if not stream_key or stream_key not in self.stream_manager.streams:
            return
        
        processor = self.stream_manager.streams[stream_key]
        config = processor.stream_config
        stats = processor.stats
        
        info_text = f"""Stream Information: {stream_key}

Configuration:
• Server: {config.server.name}
• Host: {config.server.host}:{config.server.rtmp_port}
• RTMP URL: {config.server.rtmp_url}
• Source: {Path(config.input_source).name if not config.input_source.startswith('live:') else config.input_source}
• Quality: {config.quality['name']}
• Resolution: {config.quality['width']}x{config.quality['height']}
• Frame Rate: {config.quality['fps']} fps
• Video Encoder: {config.encoder}
• Audio Encoder: {config.audio_encoder}
• Rate Control: {config.rate_control}
• Preset: {config.preset}

Statistics:
• Status: {'Streaming' if processor.is_running else 'Stopped'}
• Uptime: {processor.get_uptime()}
• Current FPS: {stats.get('fps', 0):.1f}
• Current Bitrate: {stats.get('bitrate', 'N/A')}
• Frames Processed: {stats.get('frames_processed', 0)}
• Dropped Frames: {stats.get('dropped_frames', 0)}

Additional Settings:
• Loop Input: {'Yes' if config.loop_input else 'No'}
• Start Time: {config.start_time or 'Not Set'}
• Duration: {config.duration or 'Unlimited'}
• Custom FFmpeg Args: {', '.join(config.custom_ffmpeg_args) if config.custom_ffmpeg_args else 'None'}"""
        
        self.dialog_helper.show_info(self, f"Stream Information - {stream_key}", info_text)
    
    def _apply_quality_change(self):
        """Quality өөрчлөлт хэрэглэх"""
        stream_key = self.table_helper.get_selected_data(self.ui_elements['streams_table'])
        quality_data = self.ui_elements['live_quality_combo'].currentData()
        
        if not stream_key or not quality_data:
            return
        
        if self.dialog_helper.show_question(
            self, "Change Quality",
            f"Change quality of stream '{stream_key}' to '{quality_data['name']}'?\n\n"
            "This will temporarily stop and restart the stream."
        ):
            if stream_key in self.active_streams:
                config = self.active_streams[stream_key]
                config.quality = quality_data
                
                self._stop_stream(stream_key)
                QTimer.singleShot(2000, lambda: self.stream_manager.start_stream(config))
                
                self.status_message.emit(f"Changing stream quality: {stream_key}", 3000)
                self.ui_elements['apply_quality_btn'].setEnabled(False)
    
    # Server management
    def _add_server(self):
        """Сервер нэмэх"""
        try:
            # Simple input dialog
            name = self.dialog_helper.get_text_input(self, "Add Server", "Server Name:")
            if not name:
                return
            
            host = self.dialog_helper.get_text_input(self, "Add Server", "Host:")
            if not host:
                return
            
            port_str = self.dialog_helper.get_text_input(self, "Add Server", "Port:", "8080")
            if not port_str:
                return
            
            rtmp_port_str = self.dialog_helper.get_text_input(self, "Add Server", "RTMP Port:", "1935")
            if not rtmp_port_str:
                return
            
            try:
                port = int(port_str)
                rtmp_port = int(rtmp_port_str)
            except ValueError:
                self.dialog_helper.show_error(self, "Invalid Input", "Ports must be valid numbers.")
                return
            
            # Server config үүсгэх
            server_config = ServerConfig(
                name=name,
                host=host,
                port=port,
                rtmp_port=rtmp_port
            )
            
            # Validation
            errors = server_config.validate()
            if errors:
                self.dialog_helper.show_error(self, "Validation Error", "\n".join(errors))
                return
            
            # Server нэмэх
            server_id = self.server_manager.add_server(server_config)
            
            # UI шинэчлэх
            self._load_servers()
            
            # Шинэ серверийг сонгох
            for i in range(self.ui_elements['server_combo'].count()):
                if self.ui_elements['server_combo'].itemData(i) == server_config:
                    self.ui_elements['server_combo'].setCurrentIndex(i)
                    break
            
            self.status_message.emit(f"Server '{name}' added successfully", 3000)
            
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            self.dialog_helper.show_error(self, "Error", f"Failed to add server:\n\n{str(e)}")
    
    def _edit_server(self):
        """Сервер засах"""
        current_server = self.ui_elements['server_combo'].currentData()
        if not current_server:
            self.dialog_helper.show_warning(self, "No Selection", "Please select a server to edit.")
            return
        
        self.dialog_helper.show_info(self, "Edit Server", 
                                   f"Editing server: {current_server.name}\n\n"
                                   "Advanced server editing will be available in a future update.")
    
    def _manage_servers(self):
        """Серверүүдийг удирдах"""
        self.dialog_helper.show_info(self, "Server Management", 
                                   "Advanced server management dialog will be available in a future update.")
    
    def _refresh_servers(self):
        """Серверүүдийг refresh хийх"""
        self._load_servers()
        self.status_message.emit("Servers refreshed", 2000)
    
    # Program streaming
    def _start_program_stream(self):
        """Program stream гараар эхлүүлэх"""
        try:
            self.dialog_helper.show_info(self, "Program Stream", 
                                       "Manual program streaming will be available when connected to playout tab.")
            
        except Exception as e:
            self.logger.error(f"Failed to start program stream: {e}")
    
    def _stop_program_streams(self):
        """Program streams зогсоох"""
        stopped_count = self.program_stream_manager.stop_program_streams()
        
        if stopped_count > 0:
            self.status_message.emit(f"Stopped {stopped_count} program stream(s)", 3000)
        else:
            self.status_message.emit("No program streams to stop", 2000)
    
    # External API methods for integration
    def connect_to_playout_tab(self, playout_tab) -> bool:
        """Playout tab-тай холбогдох"""
        return self.program_stream_manager.connect_to_playout_tab(playout_tab)
    
    def load_and_start_stream(self, file_path: str) -> bool:
        """Файл ачаалж stream эхлүүлэх (playout integration)"""
        return self.program_stream_manager.start_program_stream(file_path)
    
    def get_program_stream_status(self) -> Dict[str, Any]:
        """Program stream status авах"""
        return self.program_stream_manager.get_program_stream_status()
    
    def stop_program_streams_external(self) -> int:
        """External program streams зогсоох"""
        return self.program_stream_manager.stop_program_streams()
    
    def get_active_streams(self) -> Dict[str, StreamConfig]:
        """Идэвхтэй streams авах"""
        return self.active_streams.copy()
    
    def is_streaming_active(self) -> bool:
        """Stream идэвхтэй эсэхийг шалгах"""
        return len(self.stream_manager.streams) > 0
    
    def get_stream_status(self, stream_key: str) -> Optional[Dict[str, Any]]:
        """Stream status авах"""
        if stream_key in self.stream_manager.streams:
            processor = self.stream_manager.streams[stream_key]
            return {
                'running': processor.is_running,
                'uptime': processor.get_uptime(),
                'stats': processor.stats.copy(),
                'config': processor.stream_config.to_dict()
            }
        return None
    
    def get_active_streams_count(self) -> int:
        """Идэвхтэй stream-уудын тоо авах"""
        return len(self.stream_manager.streams)
    
    def refresh(self):
        """Tab refresh"""
        self._load_servers()
        self._update_ui_state()
        self._update_status()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            self.stream_manager.stop_all_streams()
            self.logger.info("Streaming tab cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


# Backward compatibility alias
StreamingTab = RefactoredStreamingTab

# Export all necessary classes
__all__ = [
    'RefactoredStreamingTab',
    'StreamingTab',
    'StreamConfig',
    'QUALITY_PRESETS',
    'ENCODER_PRESETS'
]
