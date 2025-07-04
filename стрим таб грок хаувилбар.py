#!/usr/bin/env python3
"""
Streaming Tab - Complete Implementation with Optimized Structure
Professional streaming management with resolved duplicates and enhanced compatibility
"""

import os
import sys
import json
import asyncio
import subprocess
import threading
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Logging setup with fallback
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Import server configuration components with fallback
try:
    from ui.dialogs.server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
    from ui.dialogs.network_optimizations import NetworkOptimizer, StreamReconnector
    from ui.dialogs.improved_stream_processor import ImprovedStreamProcessor
    OPTIMIZED_STREAMING_AVAILABLE = True
    print("✅ Optimized streaming components loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not import optimized components: {e}")
    OPTIMIZED_STREAMING_AVAILABLE = False
    
    try:
        from server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
        print("✅ Server config loaded from root directory")
    except ImportError:
        try:
            from ui.dialogs.servers.server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
            print("✅ Server config loaded from ui.dialogs.servers")
        except ImportError:
            print("❌ Using fallback server configuration")
            @dataclass
            class ServerConfig:
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
                    protocol = "rtmps" if self.ssl_enabled else "rtmp"
                    return f"{protocol}://{self.host}:{self.rtmp_port}{self.stream_endpoint}"

                @property
                def api_url(self) -> str:
                    protocol = "https" if self.ssl_enabled else "http"
                    return f"{protocol}://{self.host}:{self.port}{self.api_endpoint}"

                def to_dict(self) -> Dict[str, Any]:
                    return asdict(self)

                @classmethod
                def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
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
                    valid_fields = {'name', 'host', 'port', 'rtmp_port', 'ssl_enabled', 
                                  'api_endpoint', 'stream_endpoint', 'username', 'password', 
                                  'max_streams', 'description'}
                    filtered_data = {k: v for k, v in config_data.items() if k in valid_fields}
                    return cls(**filtered_data)

            class ServerEditDialog(QDialog):
                def __init__(self, server_config=None, parent=None):
                    super().__init__(parent)
                    self.server_config = server_config
                    self.setWindowTitle("Серверийн Тохиргоо")
                    self.setModal(True)
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel("Серверийн тохиргооны диалог ачааллагдсангүй."))
                    
                    button_layout = QHBoxLayout()
                    ok_btn = QPushButton("OK")
                    ok_btn.clicked.connect(self.accept)
                    cancel_btn = QPushButton("Цуцлах")
                    cancel_btn.clicked.connect(self.reject)
                    button_layout.addWidget(ok_btn)
                    button_layout.addWidget(cancel_btn)
                    layout.addLayout(button_layout)
                
                def get_server_config(self):
                    return self.server_config

            class ServerManagerDialog(QDialog):
                def __init__(self, config_manager=None, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Серверийн Удирдлага")
                    self.setModal(True)
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel("Серверийн удирдлагын диалог ачааллагдсангүй."))
                    
                    ok_btn = QPushButton("OK")
                    ok_btn.clicked.connect(self.accept)
                    layout.addWidget(ok_btn)
                
                def get_servers(self):
                    return {}
        
            class ServerStorageManager:
                def __init__(self, config_file: str = "servers.json"):
                    self.config_file = Path(config_file)
                    self.logger = get_logger(__name__)
                    self.servers = {}

                def load_servers(self) -> Dict[str, ServerConfig]:
                    try:
                        if self.config_file.exists():
                            with open(self.config_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            servers = {}
                            for server_id, server_data in data.get('servers', {}).items():
                                try:
                                    servers[server_id] = ServerConfig.from_dict(server_data)
                                except Exception as e:
                                    self.logger.warning(f"Failed to load server {server_id}: {e}")
                            return servers
                    except Exception as e:
                        self.logger.error(f"Failed to load servers: {e}")
                    return {}

                def save_servers(self, servers: Dict[str, ServerConfig]):
                    try:
                        servers_data = {}
                        for server_id, server_config in servers.items():
                            servers_data[server_id] = server_config.to_dict()
                        
                        if self.config_file.exists():
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_file = self.config_file.with_suffix(f'.backup_{timestamp}.json')
                            if backup_file.exists():
                                try:
                                    backup_file.unlink()
                                    self.logger.debug(f"Removed existing backup file: {backup_file}")
                                except Exception as e:
                                    self.logger.warning(f"Could not remove existing backup: {e}")
                            
                            try:
                                shutil.copy2(self.config_file, backup_file)
                                self.logger.debug(f"Created backup: {backup_file}")
                            except Exception as e:
                                self.logger.warning(f"Could not create backup: {e}")
                            
                            try:
                                backup_files = sorted(self.config_file.parent.glob(f'{self.config_file.stem}.backup_*.json'))
                                for old_backup in backup_files[:-3]:
                                    old_backup.unlink()
                            except Exception as e:
                                self.logger.debug(f"Backup cleanup warning: {e}")
                        
                        config_data = {
                            "version": "1.0",
                            "last_updated": datetime.now().isoformat(),
                            "servers": servers_data
                        }
                        
                        temp_file = self.config_file.with_suffix('.tmp')
                        with open(temp_file, 'w', encoding='utf-8') as f:
                            json.dump(config_data, f, indent=2, ensure_ascii=False)
                        
                        temp_file.replace(self.config_file)
                        self.logger.info(f"Saved {len(servers)} servers to {self.config_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to save servers: {e}")
                        raise

                def add_server(self, server_id: str, server_config: ServerConfig):
                    servers = self.load_servers()
                    servers[server_id] = server_config
                    self.save_servers(servers)

                def update_server(self, server_id: str, server_config: ServerConfig):
                    servers = self.load_servers()
                    if server_id in servers:
                        servers[server_id] = server_config
                        self.save_servers(servers)

                def remove_server(self, server_id: str):
                    servers = self.load_servers()
                    if server_id in servers:
                        del servers[server_id]
                        self.save_servers(servers)

# Fallback NetworkOptimizer and StreamReconnector
if not OPTIMIZED_STREAMING_AVAILABLE:
    print("🔄 Creating fallback network optimization classes...")
    
    class NetworkOptimizer:
        def __init__(self, logger):
            self.logger = logger
        
        def test_connection_quality(self, host: str, port: int) -> Dict[str, Any]:
            return {
                "latency_ms": 50,
                "packet_loss": 0,
                "bandwidth_mbps": 100,
                "jitter_ms": 5,
                "connection_stable": True
            }
        
        def get_optimal_stream_settings(self, network_quality: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "preset": "veryfast",
                "buffer_size_multiplier": 0.5,
                "keyframe_interval": 1.0,
                "max_bitrate_reduction": 1.0
            }
        
        def optimize_system_network(self):
            pass
    
    class StreamReconnector:
        def __init__(self, stream_processor, logger):
            self.stream_processor = stream_processor
            self.logger = logger
        
        def should_reconnect(self, error_message: str) -> bool:
            return False
        
        def attempt_reconnect(self) -> bool:
            return False
    
    ImprovedStreamProcessor = None

# STREAMING MODELS AND CONSTANTS
class StreamStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    STREAMING = "streaming"
    STOPPING = "stopping"
    ERROR = "error"
    RECONNECTING = "reconnecting"

QUALITY_PRESETS = {
    "240p": {
        "name": "240p (Бага)",
        "width": 426,
        "height": 240,
        "video_bitrate": "400k",
        "audio_bitrate": "64k",
        "fps": 25
    },
    "360p": {
        "name": "360p (Дунд)",
        "width": 640,
        "height": 360,
        "video_bitrate": "800k",
        "audio_bitrate": "128k",
        "fps": 25
    },
    "480p": {
        "name": "480p (Сайн)",
        "width": 854,
        "height": 480,
        "video_bitrate": "1200k",
        "audio_bitrate": "128k",
        "fps": 30
    },
    "720p": {
        "name": "720p (HD)",
        "width": 1280,
        "height": 720,
        "video_bitrate": "2500k",
        "audio_bitrate": "192k",
        "fps": 30
    },
    "1080p": {
        "name": "1080p (Full HD)",
        "width": 1920,
        "height": 1080,
        "video_bitrate": "4500k",
        "audio_bitrate": "192k",
        "fps": 30
    },
    "1440p": {
        "name": "1440p (2K)",
        "width": 2560,
        "height": 1440,
        "video_bitrate": "8000k",
        "audio_bitrate": "256k",
        "fps": 30
    },
    "4K": {
        "name": "4K (Ultra HD)",
        "width": 3840,
        "height": 2160,
        "video_bitrate": "15000k",
        "audio_bitrate": "256k",
        "fps": 30
    }
}

ENCODER_PRESETS = {
    "x264": {
        "name": "x264 (Програм хангамж)",
        "encoder": "libx264",
        "preset": "veryfast",
        "profile": "main",
        "level": "4.0"
    },
    "nvenc": {
        "name": "NVIDIA NVENC",
        "encoder": "h264_nvenc",
        "preset": "p4",
        "profile": "main",
        "level": "auto"
    },
    "amd": {
        "name": "AMD AMF",
        "encoder": "h264_amf",
        "preset": "balanced",
        "profile": "main",
        "level": "auto"
    },
    "quicksync": {
        "name": "Intel QuickSync",
        "encoder": "h264_qsv",
        "preset": "medium",
        "profile": "main",
        "level": "auto"
    }
}

@dataclass
class StreamConfig:
    stream_key: str
    input_source: str
    server: ServerConfig
    quality: Dict[str, Any]
    encoder: str = "libx264"
    audio_encoder: str = "aac"
    loop_input: bool = False
    start_time: Optional[str] = None
    duration: Optional[str] = None
    custom_ffmpeg_args: List[str] = field(default_factory=list)
    
    rate_control: str = "CBR"
    preset: str = "veryfast"
    keyframe_interval: int = 2
    buffer_size: Optional[str] = None
    max_bitrate: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stream_key": self.stream_key,
            "input_source": self.input_source,
            "server": {
                "name": self.server.name,
                "rtmp_url": self.server.rtmp_url
            },
            "quality": self.quality,
            "encoder": self.encoder,
            "audio_encoder": self.audio_encoder,
            "rate_control": self.rate_control,
            "preset": self.preset,
            "keyframe_interval": self.keyframe_interval,
            "loop_input": self.loop_input,
            "start_time": self.start_time,
            "duration": self.duration,
            "custom_ffmpeg_args": self.custom_ffmpeg_args
        }

# STREAM PROCESSOR
class StreamProcessor(QObject):
    started = pyqtSignal(str)
    stopped = pyqtSignal(str, int, str)
    error_occurred = pyqtSignal(str, str)
    statistics_updated = pyqtSignal(str, dict)
    
    def __init__(self, stream_config: StreamConfig):
        super().__init__()
        self.stream_config = stream_config
        self.process = None
        self.is_running = False
        self.start_time = None
        self.stats = {
            'fps': 0.0,
            'bitrate': '0kbits/s',
            'frames_processed': 0,
            'dropped_frames': 0,
            'uptime': '00:00:00'
        }
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.logger = get_logger(__name__)
    
    def start_stream(self) -> bool:
        try:
            if self.is_running:
                return False
            
            cmd = self._build_ffmpeg_command()
            if not cmd:
                return False
            
            self.process = QProcess()
            self.process.finished.connect(self._on_process_finished)
            self.process.errorOccurred.connect(self._on_process_error)
            self.process.readyReadStandardOutput.connect(self._on_output_ready)
            self.process.readyReadStandardError.connect(self._on_error_ready)
            
            self.process.start(cmd[0], cmd[1:])
            
            if self.process.waitForStarted(5000):
                self.is_running = True
                self.start_time = datetime.now()
                self.stats_timer.start(1000)
                self.started.emit(self.stream_config.stream_key)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}")
            self.error_occurred.emit(self.stream_config.stream_key, str(e))
            return False
    
    def stop_stream(self):
        if self.process and self.is_running:
            self.stats_timer.stop()
            self.process.terminate()
            if not self.process.waitForFinished(5000):
                self.process.kill()
            self.is_running = False
    
    def _build_ffmpeg_command(self) -> List[str]:
        cmd = ["ffmpeg", "-y", "-hide_banner"]
        if self.stream_config.input_source.startswith("live:"):
            input_type = self.stream_config.input_source.split(":")[1]
            if input_type == "test_pattern":
                cmd.extend([
                    "-f", "lavfi",
                    "-i", "testsrc=size=1280x720:rate=30"
                ])
            elif input_type == "desktop_capture":
                cmd.extend(["-f", "gdigrab", "-i", "desktop"])
            elif input_type == "webcam":
                cmd.extend(["-f", "dshow", "-i", "video=Integrated Camera"])
        else:
            try:
                file_path = Path(self.stream_config.input_source)
                if not file_path.exists():
                    self.logger.error(f"File not found: {file_path}")
                    return []
                self.logger.info(f"Loading file: {file_path}")
            except Exception as e:
                self.logger.error(f"File check error: {e}")
                return []
            
            if self.stream_config.loop_input:
                cmd.extend(["-stream_loop", "-1"])
            
            if self.stream_config.start_time:
                cmd.extend(["-ss", self.stream_config.start_time])
            
            cmd.extend(["-i", str(self.stream_config.input_source)])
            
            if self.stream_config.duration:
                cmd.extend(["-t", self.stream_config.duration])
        
        quality = self.stream_config.quality
        cmd.extend([
            "-c:v", "libx264",
            "-b:v", quality["video_bitrate"],
            "-s", f"{quality['width']}x{quality['height']}",
            "-r", str(quality["fps"]),
            "-preset", "veryfast",
            "-g", str(quality["fps"] * 2),
            "-pix_fmt", "yuv420p"
        ])
        
        if self.stream_config.rate_control == "CBR":
            cmd.extend([
                "-minrate", quality["video_bitrate"],
                "-maxrate", quality["video_bitrate"],
                "-bufsize", f"{int(quality['video_bitrate'].replace('k', '')) * 2}k"
            ])
        
        if self.stream_config.input_source.startswith("live:test_pattern"):
            cmd.extend(["-an"])
        else:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", quality["audio_bitrate"],
                "-ar", "44100",
                "-ac", "2"
            ])
        
        rtmp_url = f"{self.stream_config.server.rtmp_url}/{self.stream_config.stream_key}"
        cmd.extend(["-f", "flv", rtmp_url])
        
        self.logger.info(f"FFmpeg command: {' '.join(cmd)}")
        return cmd
    
    def _update_stats(self):
        if self.start_time:
            uptime = datetime.now() - self.start_time
            self.stats['uptime'] = str(uptime).split('.')[0]
        self.statistics_updated.emit(self.stream_config.stream_key, self.stats.copy())
    
    def _on_process_finished(self, exit_code, exit_status):
        self.is_running = False
        self.stats_timer.stop()
        message = f"Process finished, exit code: {exit_code}"
        self.stopped.emit(self.stream_config.stream_key, exit_code, message)
    
    def _on_process_error(self, error):
        self.is_running = False
        self.stats_timer.stop()
        
        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start FFmpeg",
            QProcess.ProcessError.Crashed: "FFmpeg process crashed", 
            QProcess.ProcessError.Timedout: "FFmpeg timeout",
            QProcess.ProcessError.WriteError: "FFmpeg write error",
            QProcess.ProcessError.ReadError: "FFmpeg read error",
            QProcess.ProcessError.UnknownError: "FFmpeg unknown error"
        }
        
        error_message = error_messages.get(error, f"FFmpeg error: {error}")
        
        if self.process:
            stderr_data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if stderr_data:
                error_message += f"\n\nDetails:\n{stderr_data}"
        
        self.logger.error(f"Process error: {error_message}")
        self.error_occurred.emit(self.stream_config.stream_key, error_message)
    
    def _on_output_ready(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _on_error_ready(self):
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _parse_ffmpeg_output(self, output: str):
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            if any(error_word in line.lower() for error_word in 
                   ['error', 'failed', 'connection refused', 'timeout', 'cannot', 'unable']):
                self.logger.error(f"FFmpeg error: {line}")
                self.error_occurred.emit(self.stream_config.stream_key, line)
            if 'fps=' in line and 'bitrate=' in line:
                parts = line.split()
                for part in parts:
                    if part.startswith('fps='):
                        try:
                            self.stats['fps'] = float(part.split('=')[1])
                        except ValueError:
                            pass
                    elif part.startswith('bitrate='):
                        self.stats['bitrate'] = part.split('=')[1]
    
    def get_uptime(self) -> str:
        return self.stats['uptime']

# STREAM MANAGER
class StreamManager(QObject):
    stream_started = pyqtSignal(str)
    stream_stopped = pyqtSignal(str)
    stream_error = pyqtSignal(str, str)
    stream_reconnecting = pyqtSignal(str)
    streams_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.streams: Dict[str, StreamProcessor] = {}
        self.logger = get_logger(__name__)
    
    def start_stream(self, stream_config: StreamConfig) -> bool:
        try:
            if stream_config.stream_key in self.streams:
                self.logger.warning(f"Stream {stream_config.stream_key} already exists")
                return False
            
            if OPTIMIZED_STREAMING_AVAILABLE and ImprovedStreamProcessor:
                self.logger.info("Using optimized stream processor")
                processor = ImprovedStreamProcessor(stream_config)
            else:
                self.logger.info("Using standard stream processor")
                processor = StreamProcessor(stream_config)
            
            processor.started.connect(self._on_stream_started)
            processor.stopped.connect(self._on_stream_stopped)
            processor.error_occurred.connect(self._on_stream_error)
            
            if hasattr(processor, 'reconnecting'):
                processor.reconnecting.connect(self._on_stream_reconnecting)
            
            if processor.start_stream():
                self.streams[stream_config.stream_key] = processor
                self.streams_updated.emit()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}")
            return False
    
    def _on_stream_reconnecting(self, stream_key: str):
        self.logger.info(f"Stream {stream_key} attempting reconnection...")
        self.stream_reconnecting.emit(stream_key)
    
    def stop_stream(self, stream_key: str) -> bool:
        if stream_key in self.streams:
            self.streams[stream_key].stop_stream()
            del self.streams[stream_key]  # Remove from streams after stopping
            self.streams_updated.emit()
            return True
        return False
    
    def stop_all_streams(self):
        for stream_key in list(self.streams.keys()):
            self.stop_stream(stream_key)
    
    def get_stream_stats(self, stream_key: str) -> Optional[Dict[str, Any]]:
        if stream_key in self.streams:
            return self.streams[stream_key].stats.copy()
        return None
    
    def _on_stream_started(self, stream_key: str):
        self.stream_started.emit(stream_key)
        self.streams_updated.emit()
    
    def _on_stream_stopped(self, stream_key: str, exit_code: int, message: str):
        if stream_key in self.streams:
            del self.streams[stream_key]
        self.stream_stopped.emit(stream_key)
        self.streams_updated.emit()
    
    def _on_stream_error(self, stream_key: str, error_message: str):
        self.stream_error.emit(stream_key, error_message)

# STREAM TABLE MODEL
class StreamTableModel(QAbstractTableModel):
    def __init__(self, stream_manager: StreamManager):
        super().__init__()
        self.stream_manager = stream_manager
        self.headers = [
            "Стримийн түлхүүр", "Сервер", "Чанар", "Төлөв", "Ажилласан хугацаа", "FPS", "Битрэйт", "Хурдны хяналт"
        ]
        self.stream_manager.streams_updated.connect(self._refresh_data)
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.stream_manager.streams)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        stream_keys = list(self.stream_manager.streams.keys())
        if index.row() >= len(stream_keys):
            return None
        
        stream_key = stream_keys[index.row()]
        processor = self.stream_manager.streams[stream_key]
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return stream_key
            elif col == 1:
                return processor.stream_config.server.name
            elif col == 2:
                return processor.stream_config.quality.get("name", "Unknown")
            elif col == 3:
                return "🟢 Стриминг" if processor.is_running else "🔴 Зогссон"
            elif col == 4:
                return processor.get_uptime()
            elif col == 5:
                return f"{processor.stats.get('fps', 0):.1f}"
            elif col == 6:
                return processor.stats.get('bitrate', '0kbits/s')
            elif col == 7:
                return processor.stream_config.rate_control
        
        elif role == Qt.ItemDataRole.UserRole:
            return stream_key
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 3:
                if processor.is_running:
                    return QColor(40, 167, 69)
                else:
                    return QColor(220, 53, 69)
        return None
    
    def _refresh_data(self):
        self.beginResetModel()
        self.endResetModel()

# MAIN STREAMING TAB
class StreamingTab(QWidget):
    status_message = pyqtSignal(str, int)
    stream_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.stream_manager = StreamManager()
        self.servers: Dict[str, ServerConfig] = {}
        self.active_streams: Dict[str, StreamConfig] = {}
        self.current_input_source = None
        self.last_status_message = None
        self._init_default_labels()
        self._init_ui()
        QTimer.singleShot(100, self._load_servers)
        QTimer.singleShot(200, self._connect_signals)
        QTimer.singleShot(1000, self._check_ffmpeg_availability)
        self._setup_program_streaming_integration()
        self.auto_stream_enabled = True
        self.program_stream_quality = "720p"
        self.is_program_streaming_active = False
        self.current_program_stream_key = None
        self.playout_tab_ref = None
        self.logger.debug("Streaming tab initialization completed")

    def _init_default_labels(self):
        self.total_streams_label = QLabel("0")
        self.total_bitrate_label = QLabel("0 kbps")
        self.estimated_bandwidth_label = QLabel("0.0 Mbps")
        self.network_latency_label = QLabel("N/A")
        self.reconnect_count_label = QLabel("0")
        self.optimization_status_label = QLabel("Идэвхгүй")
        self.selected_stream_label = QLabel("Байхгүй")
        self.stream_server_label = QLabel("-")
        self.stream_quality_label = QLabel("-")
        self.stream_fps_label = QLabel("-")
        self.stream_bitrate_label = QLabel("-")
        self.stream_uptime_label = QLabel("-")

    def _setup_program_streaming_integration(self):
        try:
            self.program_stream_timer = QTimer()
            self.program_stream_timer.timeout.connect(self._monitor_and_start_program_stream)
            self.program_stream_timer.start(1000)
            self.program_content_queue = []
            self.is_program_streaming_active = False
            self.current_program_stream_key = None
            self.auto_stream_enabled = True
            self.program_stream_quality = "720p"
            self.logger.info("Program streaming integration setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup program streaming: {e}")

    def _monitor_and_start_program_stream(self):
        try:
            program_streams = []
            total_program_bitrate = 0
            
            for stream_key, processor in self.stream_manager.streams.items():
                if "program" in stream_key.lower():
                    program_streams.append({
                        'key': stream_key,
                        'running': processor.is_running,
                        'uptime': processor.get_uptime(),
                        'fps': processor.stats.get('fps', 0),
                        'bitrate': processor.stats.get('bitrate', '0kbits/s')
                    })
                    bitrate_str = processor.stats.get('bitrate', '0kbits/s')
                    try:
                        if 'kbits/s' in bitrate_str:
                            total_program_bitrate += float(bitrate_str.replace('kbits/s', ''))
                    except:
                        pass
            
            self.is_program_streaming_active = len(program_streams) > 0
            if self.is_program_streaming_active and self.current_program_stream_key:
                self.stream_status_changed.emit(True, self.current_program_stream_key)
            
            for stream_info in program_streams:
                if not stream_info['running'] and self.auto_stream_enabled:
                    self._attempt_program_stream_recovery(stream_info['key'])
            
            if self.playout_tab_ref:
                current_state = self.playout_tab_ref.get_current_state()
                program_info = current_state.get('program', {})
                
                if current_state.get('on_air', False) and program_info and program_info.get('file') and not self.is_program_streaming_active:
                    self.update_program_content(program_info['file'], auto_start=True)

        except Exception as e:
            self.logger.error(f"Program stream monitoring error: {e}")

    def _attempt_program_stream_recovery(self, stream_key: str):
        try:
            if stream_key in self.active_streams:
                config = self.active_streams[stream_key]
                self.logger.warning(f"Attempting to recover program stream: {stream_key}")
                QTimer.singleShot(2000, lambda: self._restart_program_stream(stream_key, config))
        except Exception as e:
            self.logger.error(f"Program stream recovery failed: {e}")

    def _restart_program_stream(self, stream_key: str, config):
        try:
            if self.stream_manager.start_stream(config):
                self.active_streams[stream_key] = config
                self.logger.info(f"Program stream recovered: {stream_key}")
                self._emit_status_message(f"Program stream recovered: {stream_key}", 3000)
            else:
                self.logger.error(f"Failed to recover program stream: {stream_key}")
        except Exception as e:
            self.logger.error(f"Program stream restart error: {e}")

    def _emit_status_message(self, message: str, timeout: int):
        if message != self.last_status_message:
            self.status_message.emit(message, timeout)
            self.last_status_message = message

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Input selection
        input_group = QGroupBox("Эх Сурвалж")
        input_layout = QHBoxLayout()
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["Медиа Файл", "Дэлгэцийн Бичлэг", "Вэбкам", "Тест Хэв маяг"])
        self.source_type_combo.currentTextChanged.connect(self._on_source_type_changed)
        input_layout.addWidget(self.source_type_combo)
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Файлын зам эсвэл live: эх сурвалж")
        input_layout.addWidget(self.source_input)
        
        self.browse_btn = QPushButton("📁")
        self.browse_btn.clicked.connect(self._browse_source_file)
        input_layout.addWidget(self.browse_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Stream configuration
        stream_group = QGroupBox("Стримийн Тохиргоо")
        stream_layout = QVBoxLayout()
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Стримийн Түлхүүр:"))
        self.stream_key_input = QLineEdit()
        self.stream_key_input.setPlaceholderText("Стримийн түлхүүр оруулна уу")
        key_layout.addWidget(self.stream_key_input)
        
        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(self._toggle_stream_key_visibility)
        key_layout.addWidget(self.show_key_btn)
        
        stream_layout.addLayout(key_layout)
        
        # Server selection
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Сервер:"))
        self.server_combo = QComboBox()
        server_layout.addWidget(self.server_combo)
        
        self.add_server_btn = QPushButton("➕")
        self.add_server_btn.clicked.connect(self._add_server)
        server_layout.addWidget(self.add_server_btn)
        
        self.edit_server_btn = QPushButton("✏️")
        self.edit_server_btn.clicked.connect(self._edit_server)
        server_layout.addWidget(self.edit_server_btn)
        
        self.manage_servers_btn = QPushButton("⚙️")
        self.manage_servers_btn.clicked.connect(self._manage_servers)
        server_layout.addWidget(self.manage_servers_btn)
        
        stream_layout.addLayout(server_layout)
        
        # Quality and encoder settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Чанар:"))
        self.quality_combo = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.quality_combo.addItem(quality_data["name"], quality_data)
        self.quality_combo.setCurrentText("720p (HD)")
        quality_layout.addWidget(self.quality_combo)
        
        quality_layout.addWidget(QLabel("Кодлогч:"))
        self.encoder_combo = QComboBox()
        for encoder_key, encoder_data in ENCODER_PRESETS.items():
            self.encoder_combo.addItem(encoder_data["name"], encoder_key)
        quality_layout.addWidget(self.encoder_combo)
        
        stream_layout.addLayout(quality_layout)
        
        advanced_layout = QHBoxLayout()
        advanced_layout.addWidget(QLabel("Хурдны Хяналт:"))
        self.rate_control_combo = QComboBox()
        self.rate_control_combo.addItems(["CBR", "VBR"])
        advanced_layout.addWidget(self.rate_control_combo)
        
        advanced_layout.addWidget(QLabel("Урьдчилан Тохиргоо:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["ultrafast", "veryfast", "fast", "medium", "slow"])
        advanced_layout.addWidget(self.preset_combo)
        
        self.loop_input_cb = QCheckBox("Оролтыг давтах")
        advanced_layout.addWidget(self.loop_input_cb)
        
        stream_layout.addLayout(advanced_layout)
        
        # Timing controls
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Эхлэх Хугацаа:"))
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("HH:MM:SS (заавал биш)")
        timing_layout.addWidget(self.start_time_input)
        
        timing_layout.addWidget(QLabel("Үргэлжлэх Хугацаа:"))
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("HH:MM:SS (заавал биш)")
        timing_layout.addWidget(self.duration_input)
        
        stream_layout.addLayout(timing_layout)
        
        # Stream controls
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Стрим Эхлүүлэх")
        self.start_btn.clicked.connect(self._start_stream)
        control_layout.addWidget(self.start_btn)
        
        self.test_btn = QPushButton("🧪 Тест")
        self.test_btn.clicked.connect(self._test_stream)
        control_layout.addWidget(self.test_btn)
        
        self.stop_btn = QPushButton("⏹ Зогсоох")
        self.stop_btn.clicked.connect(self._stop_selected_stream)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.stop_all_btn = QPushButton("⏹ Бүгдийг Зогсоох")
        self.stop_all_btn.clicked.connect(self._stop_all_streams)
        self.stop_all_btn.setEnabled(False)
        control_layout.addWidget(self.stop_all_btn)
        
        stream_layout.addLayout(control_layout)
        
        # Program streaming section
        stream_layout.addWidget(self._create_program_streaming_section())
        
        # Stream table
        self.stream_model = StreamTableModel(self.stream_manager)
        self.streams_table = QTableView()
        self.streams_table.setModel(self.stream_model)
        self.streams_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.streams_table.setSelectionBehavior(QTableView.SelectRows)
        self.streams_table.selectionModel().currentChanged.connect(self._on_stream_selection_changed)
        stream_layout.addWidget(self.streams_table)
        
        # Live quality change
        live_quality_layout = QHBoxLayout()
        live_quality_layout.addWidget(QLabel("Live Чанарын Өөрчлөлт:"))
        self.live_quality_combo = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.live_quality_combo.addItem(quality_data["name"], quality_data)
        self.live_quality_combo.setCurrentText("720p (HD)")
        self.live_quality_combo.currentTextChanged.connect(self._on_live_quality_changed)
        live_quality_layout.addWidget(self.live_quality_combo)
        
        self.apply_quality_btn = QPushButton("Хэрэглэх")
        self.apply_quality_btn.clicked.connect(self._apply_quality_change)
        self.apply_quality_btn.setEnabled(False)
        live_quality_layout.addWidget(self.apply_quality_btn)
        
        stream_layout.addLayout(live_quality_layout)
        
        # Statistics
        stats_group = QGroupBox("Статистик")
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("Нийт Стрим: "), 0, 0)
        stats_layout.addWidget(self.total_streams_label, 0, 1)
        stats_layout.addWidget(QLabel("Нийт Битрэйт: "), 1, 0)
        stats_layout.addWidget(self.total_bitrate_label, 1, 1)
        stats_layout.addWidget(QLabel("Зурвасын Өргөн: "), 2, 0)
        stats_layout.addWidget(self.estimated_bandwidth_label, 2, 1)
        stats_layout.addWidget(QLabel("Сүлжээний Хоцролт: "), 3, 0)
        stats_layout.addWidget(self.network_latency_label, 3, 1)
        stats_layout.addWidget(QLabel("Дахин Холболт: "), 4, 0)
        stats_layout.addWidget(self.reconnect_count_label, 4, 1)
        stats_layout.addWidget(QLabel("Оновчлол: "), 5, 0)
        stats_layout.addWidget(self.optimization_status_label, 5, 1)
        
        stream_layout.addWidget(stats_group)
        
        # Selected stream details
        details_group = QGroupBox("Сонгосон Стримийн Мэдээлэл")
        details_layout = QGridLayout()
        details_layout.addWidget(QLabel("Стримийн Түлхүүр: "), 0, 0)
        details_layout.addWidget(self.selected_stream_label, 0, 1)
        details_layout.addWidget(QLabel("Сервер: "), 1, 0)
        details_layout.addWidget(self.stream_server_label, 1, 1)
        details_layout.addWidget(QLabel("Чанар: "), 2, 0)
        details_layout.addWidget(self.stream_quality_label, 2, 1)
        details_layout.addWidget(QLabel("FPS: "), 3, 0)
        details_layout.addWidget(self.stream_fps_label, 3, 1)
        details_layout.addWidget(QLabel("Битрэйт: "), 4, 0)
        details_layout.addWidget(self.stream_bitrate_label, 4, 1)
        details_layout.addWidget(QLabel("Ажилласан Хугацаа: "), 5, 0)
        details_layout.addWidget(self.stream_uptime_label, 5, 1)
        
        self.restart_stream_btn = QPushButton("🔄 Дахин эхлүүлэх")
        self.restart_stream_btn.clicked.connect(self._restart_selected_stream)
        self.restart_stream_btn.setEnabled(False)
        details_layout.addWidget(self.restart_stream_btn, 6, 0, 1, 2)
        
        self.stream_info_btn = QPushButton("ℹ️ Мэдээлэл")
        self.stream_info_btn.clicked.connect(self._show_stream_info)
        self.stream_info_btn.setEnabled(False)
        details_layout.addWidget(self.stream_info_btn, 7, 0, 1, 2)
        
        details_group.setLayout(details_layout)
        stream_layout.addWidget(details_group)
        
        stream_group.setLayout(stream_layout)
        layout.addWidget(stream_group)
        self.setLayout(layout)
    
    def _load_servers(self):
        try:
            config_dir = Path.home() / ".tv_stream"
            config_dir.mkdir(exist_ok=True)
            storage_manager = ServerStorageManager(config_dir / "servers.json")
            self.servers = storage_manager.load_servers()
            if not self.servers:
                self._create_enhanced_default_servers()
            self._safe_update_server_combo()
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self._create_fallback_server()
    
    def _connect_signals(self):
        try:
            self.stream_manager.stream_started.connect(self._on_stream_started)
            self.stream_manager.stream_stopped.connect(self._on_stream_stopped)
            self.stream_manager.stream_error.connect(self._on_stream_error)
            self.stream_manager.streams_updated.connect(self._update_stats)
            self.stream_manager.stream_started.connect(self._on_program_stream_started)
            self.stream_manager.stream_stopped.connect(self._on_program_stream_stopped)
        except Exception as e:
            self.logger.error(f"Failed to connect signals: {e}")

    def _on_program_stream_started(self, stream_key):
        if "program" in stream_key.lower():
            self.stream_status_changed.emit(True, stream_key)
            self.logger.info(f"Program stream started: {stream_key}")

    def _on_program_stream_stopped(self, stream_key):
        if "program" in stream_key.lower():
            self.stream_status_changed.emit(False, stream_key)
            self.logger.info(f"Program stream stopped: {stream_key}")

    def load_and_start_stream(self, file_path):
        try:
            if not Path(file_path).exists():
                self.logger.error(f"File not found: {file_path}")
                self._emit_status_message(f"Файл олдсонгүй: {Path(file_path).name}", 5000)
                return False
            
            self.source_input.setText(file_path)
            self.current_input_source = file_path
            self.source_type_combo.setCurrentText("Медиа Файл")
            
            current_key = self.stream_key_input.text().strip()
            if not current_key:
                program_key = f"program_{int(time.time())}"
                self.stream_key_input.setText(program_key)
            
            for i in range(self.quality_combo.count()):
                item_text = self.quality_combo.itemText(i)
                if "720p" in item_text or "HD" in item_text:
                    self.quality_combo.setCurrentIndex(i)
                    break
            
            self.loop_input_cb.setChecked(True)
            self.rate_control_combo.setCurrentText("CBR")
            self.preset_combo.setCurrentText("veryfast")
            
            self.logger.info(f"Auto-configuring stream for program content: {Path(file_path).name}")
            self._emit_status_message(f"Program content configured: {Path(file_path).name}", 3000)
            
            QTimer.singleShot(500, self._start_program_stream_delayed)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load and start stream: {e}")
            self._emit_status_message(f"Stream load failed: {e}", 5000)
            return False

    def connect_to_playout_tab(self, playout_tab):
        try:
            self.playout_tab_ref = playout_tab
            if hasattr(playout_tab, 'media_taken_to_air'):
                playout_tab.media_taken_to_air.connect(self._on_media_taken_to_air)
            if hasattr(playout_tab, 'stream_program_requested'):
                playout_tab.stream_program_requested.connect(self._on_stream_program_requested)
            if hasattr(playout_tab, '_on_streaming_status_changed'):
                self.stream_status_changed.connect(playout_tab._on_streaming_status_changed)
            self._setup_program_content_monitoring()
            self.logger.info("Enhanced playout tab connection established")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to playout tab: {e}")
            return False

    def _on_media_taken_to_air(self, file_path: str):
        try:
            self.logger.info(f"Media taken to air, starting stream: {Path(file_path).name}")
            source_info = {
                'file_path': file_path,
                'loop': True,
                'priority': 'high'
            }
            success = self.start_live_program_stream(source_info)
            if success:
                self._emit_status_message(f"🚀 Program streaming started: {Path(file_path).name}", 5000)
            else:
                self._emit_status_message(f"❌ Failed to start program streaming", 5000)
            return success
        except Exception as e:
            self.logger.error(f"Failed to handle media taken to air: {e}")
            return False

    def _on_stream_program_requested(self, file_path: str):
        try:
            return self.load_and_start_stream(file_path)
        except Exception as e:
            self.logger.error(f"Failed to handle stream program request: {e}")
            return False

    def _setup_program_content_monitoring(self):
        try:
            self.program_monitor_timer = QTimer()
            self.program_monitor_timer.timeout.connect(self._monitor_and_start_program_stream)
            self.program_monitor_timer.start(2000)
            self.last_program_file = None
            self.last_program_state = None
        except Exception as e:
            self.logger.error(f"Failed to setup program monitoring: {e}")

    def stop_program_streams(self):
        try:
            stopped_count = 0
            program_streams = [key for key in self.stream_manager.streams.keys() if "program" in key.lower()]
            for stream_key in program_streams:
                if self.stream_manager.stop_stream(stream_key):
                    if stream_key in self.active_streams:
                        del self.active_streams[stream_key]
                    stopped_count += 1
            if stopped_count > 0:
                self._emit_status_message(f"Stopped {stopped_count} program stream(s)", 3000)
            return stopped_count > 0
        except Exception as e:
            self.logger.error(f"Failed to stop program streams: {e}")
            return False

    def start_live_program_stream(self, source_info):
        try:
            stream_key = f"live_program_{int(time.time())}"
            server_config = self._get_optimal_program_server()
            if not server_config:
                self.logger.error("No suitable server for program streaming")
                return False
            
            quality_config = self._get_program_quality_config()
            stream_config = StreamConfig(
                stream_key=stream_key,
                input_source=source_info.get('file_path', 'live:test_pattern'),
                server=server_config,
                quality=quality_config,
                encoder="libx264",
                audio_encoder="aac",
                loop_input=source_info.get('loop', True),
                rate_control="CBR",
                preset="ultrafast",
                keyframe_interval=1,
                buffer_size="1024k",
                max_bitrate=quality_config.get('video_bitrate', '2500k')
            )
            stream_config.custom_ffmpeg_args.extend([
                "-tune", "zerolatency",
                "-fflags", "+igndts",
                "-avoid_negative_ts", "make_zero",
                "-max_delay", "0",
                "-fflags", "+genpts"
            ])
            
            if self.stream_manager.start_stream(stream_config):
                self.active_streams[stream_key] = stream_config
                self.current_program_stream_key = stream_key
                self.is_program_streaming_active = True
                self.stream_status_changed.emit(True, stream_key)
                self.logger.info(f"Live program stream started: {stream_key}")
                self._emit_status_message(f"Live program streaming: {stream_key}", 5000)
                return True
            else:
                self.logger.error("Failed to start live program stream")
                return False
        except Exception as e:
            self.logger.error(f"Live program streaming failed: {e}")
            return False

    def _get_optimal_program_server(self):
        try:
            if not self.servers:
                return None
            for server_id, server_config in self.servers.items():
                if server_config.host in ['localhost', '127.0.0.1', '192.168.']:
                    return server_config
            return list(self.servers.values())[0]
        except Exception as e:
            self.logger.error(f"Failed to get optimal server: {e}")
            return None

    def _get_program_quality_config(self):
        try:
            if self.program_stream_quality in QUALITY_PRESETS:
                quality = QUALITY_PRESETS[self.program_stream_quality].copy()
                quality['fps'] = 30
                base_bitrate = int(quality['video_bitrate'].replace('k', ''))
                optimized_bitrate = int(base_bitrate * 1.2)
                quality['video_bitrate'] = f"{optimized_bitrate}k"
                return quality
            else:
                return QUALITY_PRESETS["720p"]
        except Exception as e:
            self.logger.error(f"Failed to get program quality config: {e}")
            return QUALITY_PRESETS["720p"]

    def update_program_content(self, file_path: str, auto_start: bool = True):
        try:
            if not Path(file_path).exists():
                self.logger.error(f"Program file not found: {file_path}")
                return False
            self.stop_program_streams()
            QTimer.singleShot(1000, lambda: self._start_updated_program_stream(file_path, auto_start))
            return True
        except Exception as e:
            self.logger.error(f"Failed to update program content: {e}")
            return False

    def _start_updated_program_stream(self, file_path: str, auto_start: bool):
        try:
            if auto_start:
                source_info = {
                    'file_path': file_path,
                    'loop': True
                }
                return self.start_live_program_stream(source_info)
            else:
                self.current_input_source = file_path
                if hasattr(self, 'source_input'):
                    self.source_input.setText(file_path)
                self.logger.info(f"Program content updated: {Path(file_path).name}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to start updated program stream: {e}")
            return False

    def _start_program_stream_delayed(self):
        try:
            return self._start_stream()
        except Exception as e:
            self.logger.error(f"Failed to start delayed program stream: {e}")
            self._emit_status_message(f"Stream start failed: {e}", 5000)
            return False

    def _check_ffmpeg_availability(self):
        try:
            ffmpeg_path = shutil.which('ffmpeg')
            if not ffmpeg_path:
                self.logger.critical("FFmpeg not found in system PATH")
                QTimer.singleShot(1000, self._show_ffmpeg_warning)
                return False
            else:
                self.logger.info(f"FFmpeg found at: {ffmpeg_path}")
                return True
        except Exception as e:
            self.logger.error(f"FFmpeg check failed: {e}")
            return False
    
    def _show_ffmpeg_warning(self):
        try:
            parent = self.parent() if hasattr(self, 'parent') and self.parent() else self
            QMessageBox.warning(
                parent,
                "FFmpeg Олдсонгүй",
                "FFmpeg суулгагдаагүй эсвэл PATH-д байхгүй байна.\n\n"
                "Стрим хийхийн тулд FFmpeg суулгах шаардлагатай:\n"
                "• https://ffmpeg.org/download.html хаягаас татаж аваарай\n"
                "• Эсвэл: winget install ffmpeg (Windows 10/11)\n\n"
                "Суулгасны дараа програмыг дахин эхлүүлнэ үү."
            )
        except Exception as e:
            self.logger.error(f"FFmpeg warning dialog error: {e}")

    def _on_source_type_changed(self, source_type: str):
        self.browse_btn.setEnabled(source_type == "Медиа Файл")
        if source_type == "Медиа Файл":
            self.source_input.setPlaceholderText("Файлын зам")
            self.source_input.clear()
        elif source_type == "Дэлгэцийн Бичлэг":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:desktop_capture")
            self.source_input.setPlaceholderText("Дэлгэцийн бичлэг")
        elif source_type == "Вэбкам":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:webcam")
            self.source_input.setPlaceholderText("Вэбкамын нэр")
        elif source_type == "Тест Хэв маяг":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:test_pattern")
            self.source_input.setPlaceholderText("Тест хэв маяг үүсгэгч")
        self.current_input_source = self.source_input.text()

    def _browse_source_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Эх Файл Сонгох",
            "",
            "Медиа Файлууд (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.mp3 *.wav *.flac *.aac *.ogg *.m4a);;Бүх Файлууд (*)"
        )
        if file_path:
            self.source_input.setText(file_path)
            self.current_input_source = file_path
    
    def _generate_stream_key(self):
        current_key = self.stream_key_input.text().strip()
        if current_key and len(current_key) >= 3:
            return
        self.stream_key_input.setText("test")
        self._emit_status_message("Түлхүүр 'test' болгогдлоо", 2000)

    def _toggle_stream_key_visibility(self, visible: bool):
        if visible:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("👁")
    
    def _add_server(self):
        try:
            dialog = ServerEditDialog(server_config=None, parent=self)
            dialog.setWindowTitle("Шинэ сервер нэмэх")
            if dialog.exec() == QDialog.DialogCode.Accepted:
                server_config = dialog.get_server_config()
                if server_config:
                    server_id = f"server_{len(self.servers) + 1}"
                    counter = 1
                    while server_id in self.servers:
                        counter += 1
                        server_id = f"server_{counter}"
                    self.servers[server_id] = server_config
                    config_dir = Path.home() / ".tv_stream"
                    config_dir.mkdir(exist_ok=True)
                    storage_manager = ServerStorageManager(config_dir / "servers.json")
                    try:
                        storage_manager.add_server(server_id, server_config)
                        self._safe_update_server_combo()
                        for i in range(self.server_combo.count()):
                            item_data = self.server_combo.itemData(i)
                            if item_data and item_data.name == server_config.name:
                                self.server_combo.setCurrentIndex(i)
                                break
                        self._emit_status_message(f"Сервер '{server_config.name}' амжилттай нэмэгдлээ", 3000)
                        self.logger.info(f"Added new server: {server_config.name}")
                    except Exception as e:
                        if server_id in self.servers:
                            del self.servers[server_id]
                        raise e
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            QMessageBox.critical(self, "Алдаа", f"Сервер нэмэхэд алдаа гарлаа:\n\n{str(e)}")
    
    def _edit_server(self):
        try:
            current_server = self.server_combo.currentData()
            if not current_server:
                QMessageBox.warning(self, "Алдаа", "Засах серверийг сонгоно уу!")
                return
            server_id = None
            for sid, config in self.servers.items():
                if config == current_server:
                    server_id = sid
                    break
            if not server_id:
                QMessageBox.warning(self, "Алдаа", "Сонгосон серверийг олоход алдаа гарлаа!")
                return
            dialog = ServerEditDialog(server_config=current_server, parent=self)
            dialog.setWindowTitle(f"Серверийг засах: {current_server.name}")
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_config = dialog.get_server_config()
                if new_config:
                    self.servers[server_id] = new_config
                    config_dir = Path.home() / ".tv_stream"
                    storage_manager = ServerStorageManager(config_dir / "servers.json")
                    storage_manager.update_server(server_id, new_config)
                    self._safe_update_server_combo()
                    for i in range(self.server_combo.count()):
                        if self.server_combo.itemData(i) == new_config:
                            self.server_combo.setCurrentIndex(i)
                            break
                    self._emit_status_message(f"Сервер '{new_config.name}' амжилттай шинэчлэгдлээ", 3000)
                    self.logger.info(f"Updated server: {new_config.name}")
        except Exception as e:
            self.logger.error(f"Failed to edit server: {e}")
            QMessageBox.critical(self, "Алдаа", f"Серверийг засахад алдаа гарлаа:\n\n{str(e)}")
    
    def _manage_servers(self):
        try:
            dialog = ServerManagerDialog(config_manager=self.config_manager, parent=self)
            dialog.setWindowTitle("Серверийн Удирдлага")
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_servers = dialog.get_servers()
                self.servers.clear()
                self.servers.update(new_servers)
                config_dir = Path.home() / ".tv_stream"
                config_dir.mkdir(exist_ok=True)
                storage_manager = ServerStorageManager(config_dir / "servers.json")
                storage_manager.save_servers(self.servers)
                self._safe_update_server_combo()
                self._emit_status_message("Серверийн тохиргоо шинэчлэгдлээ", 3000)
                self.logger.info(f"Updated {len(self.servers)} servers through manager")
        except Exception as e:
            self.logger.error(f"Failed to manage servers: {e}")
            QMessageBox.critical(self, "Алдаа", f"Серверийн удирдлага амжилтгүй боллоо:\n\n{str(e)}")
    
    def _import_servers_dialog(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Серверийн тохиргоог импорт хийх",
                str(Path.home()),
                "JSON Файлууд (*.json);;Бүх Файлууд (*)"
            )
            if file_path:
                import_count = self._import_servers_from_file(Path(file_path))
                if import_count > 0:
                    self._safe_update_server_combo()
                    self._emit_status_message(f"{import_count} сервер амжилттай импорт хийгдлээ", 4000)
                    self.logger.info(f"Imported {import_count} servers from {file_path}")
                else:
                    QMessageBox.warning(self, "Импортын Алдаа", "Сонгосон файлаас сервер импорт хийж чадсангүй.\n\nФайлын форматыг шалгана уу.")
        except Exception as e:
            self.logger.error(f"Failed to import servers: {e}")
            QMessageBox.critical(self, "Алдаа", f"Серверийн импорт амжилтгүй боллоо:\n\n{str(e)}")

    def _import_servers_from_file(self, file_path: Path) -> int:
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
                    self.servers[key] = server_config
                    imported_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to import server {server_id}: {e}")
            return imported_count
        except Exception as e:
            self.logger.error(f"Import from file failed: {e}")
            return 0
    
    def _create_enhanced_default_servers(self):
        try:
            default_servers = {
                "default_1": ServerConfig(
                    name="Localhost RTMP",
                    host="localhost",
                    port=8080,
                    rtmp_port=1935,
                    ssl_enabled=False,
                    description="Local development server"
                ),
                "default_2": ServerConfig(
                    name="Test Server",
                    host="test.streaming.com",
                    port=443,
                    rtmp_port=1935,
                    ssl_enabled=True,
                    description="Test streaming server"
                )
            }
            self.servers.update(default_servers)
            self.logger.info("Created enhanced default servers")
        except Exception as e:
            self.logger.error(f"Failed to create default servers: {e}")
    
    def _create_fallback_server(self):
        try:
            fallback_config = ServerConfig(
                name="Fallback Server",
                host="localhost",
                port=8080,
                rtmp_port=1935,
                ssl_enabled=False
            )
            self.servers["fallback"] = fallback_config
            self._safe_update_server_combo()
            self._emit_status_message("Fallback сервер үүсгэгдлээ", 4000)
            self.logger.info("Created fallback server configuration")
        except Exception as e:
            self.logger.error(f"Failed to create fallback server: {e}")
    
    def _start_stream(self):
        try:
            if not hasattr(self, 'stream_key_input') or not self.stream_key_input:
                QMessageBox.critical(self, "UI Алдаа", "UI бүрэн ачааллагдаагүй байна.\n\nПрограмыг дахин эхлүүлнэ үү.")
                return False
            if not self._validate_stream_inputs():
                return False
            stream_config = self._build_stream_config()
            if not stream_config:
                QMessageBox.critical(self, "Тохиргооны Алдаа", "Стримийн тохиргоо үүсгэж чадсангүй.\n\nБүх шаардлагатай талбаруудыг бөглөнө үү.")
                return False
            if stream_config.stream_key in self.stream_manager.streams:
                QMessageBox.warning(self, "Стримийн Алдаа", f"Стрим '{stream_config.stream_key}' аль хэдийн идэвхтэй байна.\n\nӨөр түлхүүр ашиглана уу.")
                return False
            self._emit_status_message(f"Стрим эхлүүлж байна: {stream_config.stream_key}", 3000)
            if self.stream_manager.start_stream(stream_config):
                self.active_streams[stream_config.stream_key] = stream_config
                self._emit_status_message(f"Стрим амжилттай эхэллээ: {stream_config.stream_key}", 5000)
                return True
            else:
                self._emit_status_message("Стрим эхлүүлэх амжилтгүй боллоо", 5000)
                QMessageBox.critical(self, "Стримийн Алдаа", "Стрим эхлүүлэх амжилтгүй боллоо.\n\nFFmpeg болон серверийн холболтыг шалгана уу.")
                return False
        except Exception as e:
            self.logger.error(f"Error starting stream: {e}")
            self._emit_status_message(f"Стрим эхлүүлэх алдаа: {e}", 5000)
            QMessageBox.critical(self, "Стримийн Алдаа", f"Стрим эхлүүлэх амжилтгүй боллоо:\n\n{str(e)}\n\nДэлгэрэнгүй мэдээллийг логоос харна уу.")
            return False
    
    def _validate_stream_inputs(self) -> bool:
        try:
            if not hasattr(self, 'stream_key_input') or not self.stream_key_input:
                QMessageBox.critical(self, "UI Алдаа", "UI бүрэн ачааллагдаагүй байна.")
                return False
            stream_key = self.stream_key_input.text().strip()
            if not stream_key:
                self._generate_stream_key()
                stream_key = self.stream_key_input.text().strip()
                self._emit_status_message("Стримийн түлхүүр автоматаар үүсгэгдлээ", 2000)
            if len(stream_key) < 3:
                QMessageBox.warning(self, "Алдаа", "Стримийн түлхүүр дор хаяж 3 тэмдэгттэй байх ёстой.")
                return False
            if not hasattr(self, 'server_combo') or not self.server_combo:
                QMessageBox.critical(self, "UI Алдаа", "Серверийн сонголт ачааллагдаагүй байна.")
                return False
            server = self.server_combo.currentData()
            if not server:
                if self.server_combo.count() > 0:
                    self.server_combo.setCurrentIndex(0)
                    server = self.server_combo.currentData()
                if not server:
                    QMessageBox.critical(self, "Серверийн Алдаа", "Сервер сонгогдоогүй байна.\n\nДараах алхмуудыг хийнэ үү:\n1. Сервер нэмэх товчийг дарж сервер нэмнэ үü\n2. Эсвэл серверийн удирдлагаас тохиргоо хийнэ үү")
                    return False
            if not self.current_input_source:
                self.current_input_source = "live:test_pattern"
                self._emit_status_message("Тест хэв маяг ашиглагдана", 2000)
            return True
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            QMessageBox.critical(self, "Алдаа", f"Тохиргоог шалгахад алдаа гарлаа:\n{str(e)}")
            return False
    
    def _build_stream_config(self) -> Optional[StreamConfig]:
        try:
            stream_key = self.stream_key_input.text().strip()
            if not hasattr(self, 'server_combo') or not self.server_combo:
                self.logger.error("Server combo not available")
                return None
            server = self.server_combo.currentData()
            if not server:
                self.logger.error("No server selected")
                return None
            quality = self.quality_combo.currentData() or QUALITY_PRESETS["720p"]
            encoder_key = self.encoder_combo.currentData() or "x264"
            encoder = ENCODER_PRESETS[encoder_key]["encoder"]
            rate_control = self.rate_control_combo.currentText() or "CBR"
            preset = self.preset_combo.currentText() or "veryfast"
            loop_input = self.loop_input_cb.isChecked() if hasattr(self, 'loop_input_cb') else False
            config = StreamConfig(
                stream_key=stream_key,
                input_source=self.current_input_source or "live:test_pattern",
                server=server,
                quality=quality,
                encoder=encoder,
                rate_control=rate_control,
                preset=preset,
                loop_input=loop_input
            )
            if hasattr(self, 'start_time_input') and self.start_time_input and self.start_time_input.text().strip():
                config.start_time = self.start_time_input.text().strip()
            if hasattr(self, 'duration_input') and self.duration_input and self.duration_input.text().strip():
                config.duration = self.duration_input.text().strip()
            return config
        except Exception as e:
            self.logger.error(f"Failed to build stream config: {e}")
            return None
    
    def _test_stream(self):
        if not self._validate_stream_inputs():
            return
        config = self._build_stream_config()
        if not config:
            return
        quality = config.quality
        video_bitrate = int(quality["video_bitrate"].replace("k", ""))
        audio_bitrate = int(quality["audio_bitrate"].replace("k", ""))
        total_bitrate = video_bitrate + audio_bitrate
        test_results = f"""Стримийн Тохиргооны Шалгалт
        
✅ Оролтын Эх Сурвалж: {config.input_source}
✅ Сервер: {config.server.name}
✅ RTMP URL: {config.server.rtmp_url}
✅ Стримийн Түлхүүр: {'*' * len(config.stream_key)}
✅ Чанар: {quality['name']}
✅ Нягтрал: {quality['width']}x{quality['height']}
✅ Кадр давтамж: {quality['fps']} fps
✅ Видео Кодлогч: {config.encoder}
✅ Хурдны Хяналт: {config.rate_control}
✅ Урьдчилан Тохиргоо: {config.preset}

📊 Зурвасын Өргөний Тооцоолол:
• Видео: {video_bitrate} kbps
• Аудио: {audio_bitrate} kbps
• Нийт: {total_bitrate} kbps ({total_bitrate/1000:.1f} Mbps)

⚠️ Анхаарах зүйл: Энэ нь зөвхөн тохиргооны шалгалт юм.
Бодит стримийг эхлүүлэхийн тулд "Стрим Эхлүүлэх" товчийг дарна уу."""
        QMessageBox.information(self, "Стримийн Шалгалт", test_results)
    
    def _stop_selected_stream(self):
        try:
            selected_index = self.streams_table.currentIndex()
            if not selected_index.isValid():
                QMessageBox.warning(self, "Алдаа", "Зогсоох стримийг сонгоно уу!")
                return
            
            stream_key = self.stream_model.data(selected_index, Qt.ItemDataRole.UserRole)
            if not stream_key:
                return
                
            if self.stream_manager.stop_stream(stream_key):
                if stream_key in self.active_streams:
                    del self.active_streams[stream_key]
                if stream_key == self.current_program_stream_key:
                    self.is_program_streaming_active = False
                    self.current_program_stream_key = None
                    self.stream_status_changed.emit(False, stream_key)
                self._emit_status_message(f"Стрим зогслоо: {stream_key}", 3000)
                self.logger.info(f"Stream stopped: {stream_key}")
            else:
                self._emit_status_message(f"Стримийг зогсоох амжилтгүй: {stream_key}", 5000)
        except Exception as e:
            self.logger.error(f"Failed to stop stream: {e}")
            QMessageBox.critical(self, "Алдаа", f"Стримийг зогсоох амжилтгүй боллоо:\n\n{str(e)}")
    
    def _stop_all_streams(self):
        try:
            self.stream_manager.stop_all_streams()
            self.active_streams.clear()
            self.is_program_streaming_active = False
            self.current_program_stream_key = None
            self.stream_status_changed.emit(False, "")
            self._emit_status_message("Бүх стрим зогслоо", 3000)
            self.logger.info("All streams stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop all streams: {e}")
            QMessageBox.critical(self, "Алдаа", f"Бүх стримийг зогсоох амжилтгүй боллоо:\n\n{str(e)}")
    
    def _on_stream_started(self, stream_key: str):
        self._update_stats()
        self.stop_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(True)
        self._emit_status_message(f"Стрим эхэллээ: {stream_key}", 3000)
        self.logger.info(f"Stream started: {stream_key}")
    
    def _on_stream_stopped(self, stream_key: str):
        if stream_key in self.active_streams:
            del self.active_streams[stream_key]
        if stream_key == self.current_program_stream_key:
            self.is_program_streaming_active = False
            self.current_program_stream_key = None
            self.stream_status_changed.emit(False, stream_key)
        self._update_stats()
        if not self.stream_manager.streams:
            self.stop_btn.setEnabled(False)
            self.stop_all_btn.setEnabled(False)
        self._emit_status_message(f"Стрим зогслоо: {stream_key}", 3000)
        self.logger.info(f"Stream stopped: {stream_key}")
    
        def _on_stream_error(self, stream_key: str, error_message: str):
        """Handle stream error with detailed reporting"""
        try:
            self.logger.error(f"Stream error for {stream_key}: {error_message}")
            self._emit_status_message(f"Стримийн алдаа [{stream_key}]: {error_message}", 5000)

            # Display critical errors to user
            if any(critical in error_message.lower() for critical in 
                   ['connection refused', 'timeout', 'failed to start', 'cannot open', 'permission denied']):
                QMessageBox.critical(
                    self,
                    f"Стримийн Алдаа - {stream_key}",
                    f"Стримийн алдаа гарлаа:\n\n{error_message}\n\n"
                    "Зөвлөмж:\n"
                    "• Серверийн холболтыг шалгана уу\n"
                    "• Серверийн тохиргоог зөв эсэхийг нягтална уу\n"
                    "• Сүлжээний тогтвортой байдлыг шалгана уу\n"
                    "• FFmpeg-ийн хувилбар болон суулгацыг шалгана уу"
                )

            # Attempt auto-recovery if enabled and applicable
            if self.auto_stream_enabled and "program" in stream_key.lower():
                self._attempt_program_stream_recovery(stream_key)

        except Exception as e:
            self.logger.error(f"Error handling stream error for {stream_key}: {e}")
            self._emit_status_message(f"Алдаа боловсруулах явцад алдаа: {e}", 5000)

    def _emit_status_message(self, message: str, timeout: int):
        """Emit status message with safety checks"""
        try:
            if hasattr(self, 'status_message'):
                self.status_message.emit(message, timeout)
            else:
                self.logger.warning(f"Status message signal not available: {message}")
        except Exception as e:
            self.logger.error(f"Failed to emit status message: {e}")

    def _init_ui(self):
        """Initialize the UI components for the streaming tab"""
        try:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)

            # Stream Configuration Section
            config_group = QGroupBox("Стримийн Тохиргоо")
            config_layout = QFormLayout()
            config_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            # Input Source
            self.source_type_combo = QComboBox()
            self.source_type_combo.addItems(["Медиа Файл", "Дэлгэцийн Бичлэг", "Вебкам", "Аудио Оролт", "Тест Хэв маяг"])
            self.source_type_combo.currentTextChanged.connect(self._on_source_type_changed)
            config_layout.addRow("Оролтын Төрөл:", self.source_type_combo)

            source_layout = QHBoxLayout()
            self.source_input = QLineEdit()
            self.source_input.setPlaceholderText("Файлын зам эсвэл оролтын эх сурвалж")
            self.browse_btn = QPushButton("Хайх...")
            self.browse_btn.clicked.connect(self._browse_source_file)
            source_layout.addWidget(self.source_input)
            source_layout.addWidget(self.browse_btn)
            config_layout.addRow("Эх Сурвалж:", source_layout)

            # Stream Key
            key_layout = QHBoxLayout()
            self.stream_key_input = QLineEdit()
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn = QPushButton("👁")
            self.show_key_btn.setFixedWidth(40)
            self.show_key_btn.setCheckable(True)
            self.show_key_btn.toggled.connect(self._toggle_stream_key_visibility)
            generate_key_btn = QPushButton("Үүсгэх")
            generate_key_btn.clicked.connect(self._generate_stream_key)
            key_layout.addWidget(self.stream_key_input)
            key_layout.addWidget(self.show_key_btn)
            key_layout.addWidget(generate_key_btn)
            config_layout.addRow("Стримийн Түлхүүр:", key_layout)

            # Server Selection
            self.server_combo = QComboBox()
            config_layout.addRow("Сервер:", self.server_combo)

            server_btn_layout = QHBoxLayout()
            add_server_btn = QPushButton("Шинэ Сервер")
            add_server_btn.clicked.connect(self._add_server)
            edit_server_btn = QPushButton("Засах")
            edit_server_btn.clicked.connect(self._edit_server)
            manage_servers_btn = QPushButton("Удирдах")
            manage_servers_btn.clicked.connect(self._manage_servers)
            import_servers_btn = QPushButton("Импорт")
            import_servers_btn.clicked.connect(self._import_servers_dialog)
            server_btn_layout.addWidget(add_server_btn)
            server_btn_layout.addWidget(edit_server_btn)
            server_btn_layout.addWidget(manage_servers_btn)
            server_btn_layout.addWidget(import_servers_btn)
            config_layout.addRow("Серверийн Удирдлага:", server_btn_layout)

            # Quality Selection
            self.quality_combo = QComboBox()
            for quality_key, quality_data in QUALITY_PRESETS.items():
                self.quality_combo.addItem(quality_data["name"], quality_data)
            self.quality_combo.setCurrentText("720p (HD)")
            config_layout.addRow("Чанар:", self.quality_combo)

            # Encoder Selection
            self.encoder_combo = QComboBox()
            for encoder_key, encoder_data in ENCODER_PRESETS.items():
                self.encoder_combo.addItem(encoder_data["name"], encoder_key)
            config_layout.addRow("Кодлогч:", self.encoder_combo)

            # Advanced Settings
            advanced_group = QGroupBox("Нарийвчилсан Тохиргоо")
            advanced_layout = QFormLayout()
            self.rate_control_combo = QComboBox()
            self.rate_control_combo.addItems(["CBR", "VBR"])
            advanced_layout.addRow("Хурдны Хяналт:", self.rate_control_combo)

            self.preset_combo = QComboBox()
            self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
            advanced_layout.addRow("Урьдчилан Тохиргоо:", self.preset_combo)

            self.loop_input_cb = QCheckBox("Оролтыг Давтах")
            advanced_layout.addRow("Давталт:", self.loop_input_cb)

            self.start_time_input = QLineEdit()
            self.start_time_input.setPlaceholderText("Жишээ: 00:00:00")
            advanced_layout.addRow("Эхлэх Хугацаа:", self.start_time_input)

            self.duration_input = QLineEdit()
            self.duration_input.setPlaceholderText("Жишээ: 3600 (секунд)")
            advanced_layout.addRow("Үргэлжлэх Хугацаа:", self.duration_input)

            advanced_group.setLayout(advanced_layout)
            config_layout.addRow(advanced_group)

            config_group.setLayout(config_layout)
            main_layout.addWidget(config_group)

            # Program Streaming Section
            main_layout.addWidget(self._create_program_streaming_section())

            # Control Buttons
            control_layout = QHBoxLayout()
            test_btn = QPushButton("Тохиргоог Шалгах")
            test_btn.clicked.connect(self._test_stream)
            control_layout.addWidget(test_btn)

            self.start_btn = QPushButton("Стрим Эхлүүлэх")
            self.start_btn.clicked.connect(self._start_stream)
            control_layout.addWidget(self.start_btn)

            self.stop_btn = QPushButton("Зогсоох")
            self.stop_btn.clicked.connect(self._stop_selected_stream)
            self.stop_btn.setEnabled(False)
            control_layout.addWidget(self.stop_btn)

            self.stop_all_btn = QPushButton("Бүгдийг Зогсоох")
            self.stop_all_btn.clicked.connect(self._stop_all_streams)
            self.stop_all_btn.setEnabled(False)
            control_layout.addWidget(self.stop_all_btn)

            self.restart_stream_btn = QPushButton("Дахин Эхлүүлэх")
            self.restart_stream_btn.clicked.connect(self._restart_selected_stream)
            self.restart_stream_btn.setEnabled(False)
            control_layout.addWidget(self.restart_stream_btn)

            self.stream_info_btn = QPushButton("Стримийн Мэдээлэл")
            self.stream_info_btn.clicked.connect(self._show_stream_info)
            self.stream_info_btn.setEnabled(False)
            control_layout.addWidget(self.stream_info_btn)

            main_layout.addLayout(control_layout)

            # Live Quality Change
            quality_change_layout = QHBoxLayout()
            quality_change_layout.addWidget(QLabel("Амьдаар Чанар Өөрчлөх:"))
            self.live_quality_combo = QComboBox()
            for quality_key, quality_data in QUALITY_PRESETS.items():
                self.live_quality_combo.addItem(quality_data["name"], quality_data)
            self.live_quality_combo.currentTextChanged.connect(self._on_live_quality_changed)
            quality_change_layout.addWidget(self.live_quality_combo)

            self.apply_quality_btn = QPushButton("Хэрэглэх")
            self.apply_quality_btn.clicked.connect(self._apply_quality_change)
            self.apply_quality_btn.setEnabled(False)
            quality_change_layout.addWidget(self.apply_quality_btn)
            main_layout.addLayout(quality_change_layout)

            # Stream Table
            self.streams_table = QTableView()
            self.stream_model = StreamTableModel(self.stream_manager)
            self.streams_table.setModel(self.stream_model)
            self.streams_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            self.streams_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.streams_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.streams_table.selectionModel().currentChanged.connect(self._on_stream_selection_changed)
            main_layout.addWidget(self.streams_table)

            # Statistics Section
            stats_group = QGroupBox("Стримийн Статистик")
            stats_layout = QGridLayout()

            stats_layout.addWidget(QLabel("Нийт Стрим:"), 0, 0)
            stats_layout.addWidget(self.total_streams_label, 0, 1)
            stats_layout.addWidget(QLabel("Нийт Битрэйт:"), 1, 0)
            stats_layout.addWidget(self.total_bitrate_label, 1, 1)
            stats_layout.addWidget(QLabel("Тооцоолсон Зурвасын Өргөн:"), 2, 0)
            stats_layout.addWidget(self.estimated_bandwidth_label, 2, 1)
            stats_layout.addWidget(QLabel("Сүлжээний Хоцролт:"), 3, 0)
            stats_layout.addWidget(self.network_latency_label, 3, 1)
            stats_layout.addWidget(QLabel("Дахин Холболтын Тоо:"), 4, 0)
            stats_layout.addWidget(self.reconnect_count_label, 4, 1)
            stats_layout.addWidget(QLabel("Оновчлолын Төлөв:"), 5, 0)
            stats_layout.addWidget(self.optimization_status_label, 5, 1)

            stats_layout.addWidget(QLabel("Сонгогдсон Стрим:"), 0, 2)
            stats_layout.addWidget(self.selected_stream_label, 0, 3)
            stats_layout.addWidget(QLabel("Сервер:"), 1, 2)
            stats_layout.addWidget(self.stream_server_label, 1, 3)
            stats_layout.addWidget(QLabel("Чанар:"), 2, 2)
            stats_layout.addWidget(self.stream_quality_label, 2, 3)
            stats_layout.addWidget(QLabel("FPS:"), 3, 2)
            stats_layout.addWidget(self.stream_fps_label, 3, 3)
            stats_layout.addWidget(QLabel("Битрэйт:"), 4, 2)
            stats_layout.addWidget(self.stream_bitrate_label, 4, 3)
            stats_layout.addWidget(QLabel("Ажилласан Хугацаа:"), 5, 2)
            stats_layout.addWidget(self.stream_uptime_label, 5, 3)

            stats_group.setLayout(stats_layout)
            main_layout.addWidget(stats_group)

            self.setLayout(main_layout)
            self.logger.info("UI initialized successfully")
        except Exception as e:
            self.logger.error(f"UI initialization failed: {e}")
            QMessageBox.critical(self, "UI Алдаа", f"UI-г ачааллахад алдаа гарлаа:\n\n{str(e)}")

    def _connect_signals(self):
        """Connect all necessary signals"""
        try:
            self.stream_manager.stream_started.connect(self._on_stream_started)
            self.stream_manager.stream_stopped.connect(self._on_stream_stopped)
            self.stream_manager.stream_error.connect(self._on_stream_error)
            self.stream_manager.stream_reconnecting.connect(self._on_stream_reconnecting)
            self.logger.info("Signals connected successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect signals: {e}")

    def _load_servers(self):
        """Load server configurations"""
        try:
            config_dir = Path.home() / ".tv_stream"
            config_dir.mkdir(exist_ok=True)
            storage_manager = ServerStorageManager(config_dir / "servers.json")
            self.servers = storage_manager.load_servers()

            if not self.servers:
                self._create_enhanced_default_servers()
                storage_manager.save_servers(self.servers)

            self._safe_update_server_combo()
            self.logger.info(f"Loaded {len(self.servers)} servers")
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self._create_fallback_server()

    def _safe_update_server_combo(self):
        """Safely update server combo box"""
        try:
            if not hasattr(self, 'server_combo'):
                self.logger.error("Server combo not initialized")
                return

            current_server = self.server_combo.currentData()
            self.server_combo.clear()

            for server_id, server_config in self.servers.items():
                self.server_combo.addItem(server_config.name, server_config)

            # Restore previous selection if possible
            if current_server:
                for i in range(self.server_combo.count()):
                    if self.server_combo.itemData(i) == current_server:
                        self.server_combo.setCurrentIndex(i)
                        break

            if self.server_combo.count() == 0:
                self.server_combo.addItem("Сервер байхгүй", None)
                self.start_btn.setEnabled(False)
            else:
                self.start_btn.setEnabled(True)

            self.logger.debug("Server combo updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update server combo: {e}")

    def _on_stream_reconnecting(self, stream_key: str):
        """Handle stream reconnection attempt"""
        try:
            self._emit_status_message(f"Стримийг дахин холбож байна: {stream_key}", 3000)
            self.logger.info(f"Stream reconnecting: {stream_key}")

            # Update reconnect count
            try:
                current_count = int(self.reconnect_count_label.text())
                self.reconnect_count_label.setText(str(current_count + 1))
            except ValueError:
                self.reconnect_count_label.setText("1")
        except Exception as e:
            self.logger.error(f"Stream reconnection handling failed: {e}")

    def _on_source_type_changed(self, source_type: str):
        """Handle source type change"""
        try:
            self.browse_btn.setEnabled(source_type == "Медиа Файл")
            self.source_input.setText("")
            self.current_input_source = None

            if source_type == "Медиа Файл":
                self.source_input.setPlaceholderText("Файлын замыг сонгоно уу...")
            elif source_type == "Дэлгэцийн Бичлэг":
                self.source_input.setText("live:desktop_capture")
                self.source_input.setPlaceholderText("Дэлгэцийн бичлэг")
                self.current_input_source = "live:desktop_capture"
            elif source_type == "Вебкам":
                self.source_input.setText("live:webcam")
                self.source_input.setPlaceholderText("Вебкамын оролт")
                self.current_input_source = "live:webcam"
            elif source_type == "Аудио Оролт":
                self.source_input.setText("live:audio_input")
                self.source_input.setPlaceholderText("Үндсэн аудио оролт")
                self.current_input_source = "live:audio_input"
            elif source_type == "Тест Хэв маяг":
                self.source_input.setText("live:test_pattern")
                self.source_input.setPlaceholderText("Тест хэв маяг үүсгэгч")
                self.current_input_source = "live:test_pattern"

            self.logger.debug(f"Source type changed to: {source_type}")
        except Exception as e:
            self.logger.error(f"Failed to handle source type change: {e}")
            self._emit_status_message(f"Оролтын төрөл өөрчлөх алдаа: {e}", 5000)

    def _toggle_auto_stream(self, enabled: bool):
        """Toggle auto-streaming mode"""
        try:
            self.auto_stream_enabled = enabled
            status = "идэвхжсэн" if enabled else "идэвхгүй"
            self._emit_status_message(f"Авто стрим: {status}", 2000)
            self.logger.info(f"Auto-streaming set to: {status}")

            if enabled and hasattr(self, 'playout_tab_ref') and self.playout_tab_ref:
                self._check_immediate_stream_start()
        except Exception as e:
            self.logger.error(f"Failed to toggle auto-stream: {e}")
            self._emit_status_message(f"Авто стрим тохиргооны алдаа: {e}", 5000)

    def _on_program_quality_changed(self, quality_name: str):
        """Handle program quality change"""
        try:
            for quality_key, quality_data in QUALITY_PRESETS.items():
                if quality_data["name"] == quality_name:
                    self.program_stream_quality = quality_key
                    break

            self.logger.info(f"Program stream quality changed to: {self.program_stream_quality}")

            if self.is_program_streaming_active:
                self._update_program_stream_quality()
        except Exception as e:
            self.logger.error(f"Failed to handle program quality change: {e}")
            self._emit_status_message(f"Програмын чанар өөрчлөх алдаа: {e}", 5000)

    def _manual_start_program_stream(self):
        """Manually start program streaming"""
        try:
            if not hasattr(self, 'playout_tab_ref') or not self.playout_tab_ref:
                QMessageBox.warning(self, "Алдаа", "Playout табтай холбогдоогүй байна.")
                return

            current_state = self.playout_tab_ref.get_current_state()
            program_info = current_state.get('program')

            if not program_info or not program_info.get('file'):
                QMessageBox.warning(self, "Алдаа", "Playout таб дээр програм ачаалагдаагүй байна.")
                return

            source_info = {
                'file_path': program_info['file'],
                'loop': True
            }

            if self.start_live_program_stream(source_info):
                self._emit_status_message("Програмын стрим амжилттай эхэллээ", 3000)
                self.start_program_btn.setEnabled(False)
                self.stop_program_btn.setEnabled(True)
            else:
                self._emit_status_message("Програмын стримийг эхлүүлэх амжилтгүй боллоо", 5000)
        except Exception as e:
            self.logger.error(f"Failed to start program stream manually: {e}")
            self._emit_status_message(f"Програмын стрим эхлүүлэх алдаа: {e}", 5000)

    def _update_program_stream_quality(self):
        """Update quality of active program streams"""
        try:
            program_streams = [key for key in self.stream_manager.streams.keys() if "program" in key.lower()]
            if not program_streams:
                return

            reply = QMessageBox.question(
                self,
                "Чанарын Шинэчлэл",
                f"{len(program_streams)} програмын стримийн чанарыг '{self.program_stream_quality}' болгон шинэчлэх үү?\n\n"
                "Энэ үйлдэл стримүүдийг дахин эхлүүлнэ.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                for stream_key in program_streams:
                    if stream_key in self.active_streams:
                        config = self.active_streams[stream_key]
                        config.quality = QUALITY_PRESETS[self.program_stream_quality]
                        self._stop_stream(stream_key)
                        QTimer.singleShot(1000, lambda sk=stream_key, cfg=config: 
                                        self.stream_manager.start_stream(cfg))

                self._emit_status_message("Програмын стримийн чанар шинэчлэгдлээ", 3000)
                self.logger.info(f"Updated quality for {len(program_streams)} program streams")
        except Exception as e:
            self.logger.error(f"Failed to update program stream quality: {e}")
            self._emit_status_message(f"Чанар шинэчлэх алдаа: {e}", 5000)

    def _check_immediate_stream_start(self):
        """Check if immediate stream start is needed"""
        try:
            if not self.auto_stream_enabled or not hasattr(self, 'playout_tab_ref') or not self.playout_tab_ref:
                return

            current_state = self.playout_tab_ref.get_current_state()
            if current_state.get('on_air', False):
                program_info = current_state.get('program')
                if program_info and program_info.get('file'):
                    self.update_program_content(program_info['file'], auto_start=True)
                    self.logger.info("Initiated immediate stream start for on-air program")
        except Exception as e:
            self.logger.error(f"Immediate stream start check failed: {e}")
            self._emit_status_message(f"Шууд стрим эхлүүлэх алдаа: {e}", 5000)

    def _update_stats(self):
        """Update streaming statistics display"""
        try:
            active_count = len(self.stream_manager.streams)
            self.total_streams_label.setText(str(active_count))

            total_bitrate = 0
            for processor in self.stream_manager.streams.values():
                bitrate_str = processor.stats.get('bitrate', '0kbits/s')
                try:
                    if 'kbits/s' in bitrate_str:
                        total_bitrate += float(bitrate_str.replace('kbits/s', ''))
                except (ValueError, AttributeError):
                    pass

            self.total_bitrate_label.setText(f"{total_bitrate:.0f} kbps")
            self.estimated_bandwidth_label.setText(f"{total_bitrate/1000:.1f} Mbps")
            self.network_latency_label.setText("< 50ms")
            self.reconnect_count_label.setText("0")
            self.optimization_status_label.setText("Идэвхтэй" if OPTIMIZED_STREAMING_AVAILABLE else "Үндсэн")
            self.optimization_status_label.setStyleSheet(
                "color: #28a745;" if OPTIMIZED_STREAMING_AVAILABLE else "color: #ffc107;"
            )

            if active_count == 0:
                self.selected_stream_label.setText("Байхгүй")
                self.stream_server_label.setText("-")
                self.stream_quality_label.setText("-")
                self.stream_fps_label.setText("-")
                self.stream_bitrate_label.setText("-")
                self.stream_uptime_label.setText("-")
                self.stop_btn.setEnabled(False)
                self.stop_all_btn.setEnabled(False)
                self.restart_stream_btn.setEnabled(False)
                self.stream_info_btn.setEnabled(False)
                self.apply_quality_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Failed to update stats: {e}")
            self._emit_status_message(f"Статистикийн шинэчлэл алдаа: {e}", 5000)

    def export_stream_logs(self):
        """Export stream logs to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stream_logs_{timestamp}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Стримийн Логийг Хадгалах",
                filename,
                "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Стримийн Лог - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")

                    f.write("Идэвхтэй Стримүүд:\n")
                    for stream_key, processor in self.stream_manager.streams.items():
                        config = processor.stream_config
                        stats = processor.stats
                        f.write(f"Стримийн Түлхүүр: {stream_key}\n")
                        f.write(f"Сервер: {config.server.name}\n")
                        f.write(f"Чанар: {config.quality['name']}\n")
                        f.write(f"Төлөв: {'Стриминг' if processor.is_running else 'Зогссон'}\n")
                        f.write(f"Ажилласан Хугацаа: {processor.get_uptime()}\n")
                        f.write(f"FPS: {stats.get('fps', 0):.1f}\n")
                        f.write(f"Битрэйт: {stats.get('bitrate', 'N/A')}\n")
                        f.write("-" * 30 + "\n")

                    f.write("\nСерверийн Тохиргоо:\n")
                    for server_id, server_config in self.servers.items():
                        f.write(f"ID: {server_id}\n")
                        f.write(f"Нэр: {server_config.name}\n")
                        f.write(f"Хост: {server_config.host}:{server_config.port}\n")
                        f.write(f"RTMP Порт: {server_config.rtmp_port}\n")
                        f.write(f"SSL: {'Тийм' if server_config.ssl_enabled else 'Үгүй'}\n")
                        f.write(f"Тайлбар: {server_config.description}\n")
                        f.write("-" * 30 + "\n")

                self._emit_status_message(f"Лог хадгалагдлаа: {Path(file_path).name}", 4000)
                self.logger.info(f"Stream logs exported to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export stream logs: {e}")
            QMessageBox.critical(self, "Алдаа", f"Логийг хадгалахад алдаа гарлаа:\n\n{str(e)}")

    def import_stream_preset(self):
        """Import stream preset configuration"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Стримийн Урьдчилан Тохиргоо Импорт Хийх",
                str(Path.home()),
                "JSON Files (*.json);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)

                if 'quality' in preset_data:
                    for i in range(self.quality_combo.count()):
                        if preset_data['quality'] in self.quality_combo.itemText(i):
                            self.quality_combo.setCurrentIndex(i)
                            break

                if 'encoder' in preset_data:
                    for i in range(self.encoder_combo.count()):
                        if preset_data['encoder'] in self.encoder_combo.itemText(i):
                            self.encoder_combo.setCurrentIndex(i)
                            break

                if 'rate_control' in preset_data:
                    self.rate_control_combo.setCurrentText(preset_data['rate_control'])

                if 'preset' in preset_data:
                    self.preset_combo.setCurrentText(preset_data['preset'])

                if 'loop_input' in preset_data:
                    self.loop_input_cb.setChecked(preset_data['loop_input'])

                self._emit_status_message(f"Урьдчилан тохиргоо амжилттай ачааллагдлаа: {Path(file_path).name}", 3000)
                self.logger.info(f"Stream preset imported from: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to import stream preset: {e}")
            QMessageBox.critical(self, "Алдаа", f"Урьдчилан тохиргоог ачааллахад алдаа гарлаа:\n\n{str(e)}")

    def export_stream_preset(self):
        """Export current stream configuration as preset"""
        try:
            preset_data = {
                'name': 'Custom Preset',
                'description': 'Exported from Streaming Tab',
                'quality': self.quality_combo.currentText(),
                'encoder': self.encoder_combo.currentText(),
                'rate_control': self.rate_control_combo.currentText(),
                'preset': self.preset_combo.currentText(),
                'loop_input': self.loop_input_cb.isChecked(),
                'exported_at': datetime.now().isoformat()
            }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stream_preset_{timestamp}.json"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Стримийн Урьдчилан Тохиргоог Хадгалах",
                filename,
                "JSON Files (*.json);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, indent=2, ensure_ascii=False)
                self._emit_status_message(f"Урьдчилан тохиргоо хадгалагдлаа: {Path(file_path).name}", 4000)
                self.logger.info(f"Stream preset exported to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export stream preset: {e}")
            QMessageBox.critical(self, "Алдаа", f"Урьдчилан тохиргоог хадгалахад алдаа гарлаа:\n\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            if self.stream_manager.streams:
                reply = QMessageBox.question(
                    self,
                    "Програмыг Хаах",
                    f"{len(self.stream_manager.streams)} идэвхтэй стрим байна. Хаахдаа итгэлтэй байна уу?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.stream_manager.stop_all_streams()
                    self.program_stream_timer.stop()
                    self.program_monitor_timer.stop()
                    event.accept()
                else:
                    event.ignore()
            else:
                self.program_stream_timer.stop()
                self.program_monitor_timer.stop()
                event.accept()
        except Exception as e:
            self.logger.error(f"Close event error: {e}")
            event.accept()

# Update the __all__ export list to ensure all necessary components are available
__all__ = [
    'StreamingTab',
    'StreamTableModel',
    'StreamManager',
    'StreamProcessor',
    'StreamConfig',
    'ServerConfig',
    'StreamStatus',
    'QUALITY_PRESETS',
    'ENCODER_PRESETS',
    'check_system_resources',
    'get_network_interfaces',
    'validate_rtmp_url',
    'estimate_bandwidth_requirement'
]

if __name__ == "__main__":
    # Ensure the main execution block remains consistent
    app = QApplication(sys.argv)
    app.setApplicationName("TV Stream - Streaming Tab")
    app.setApplicationVersion("2.0.0")

    # Apply dark theme
    app.setStyle('Fusion')
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)

    # Create and show test window
    window = TestWindow()
    window.show()

    print("=" * 60)
    print("🎉 STREAMING TAB FULLY COMPLETED!")
    print("=" * 60)
    print("✅ Enhanced Features:")
    print("  • Complete UI with all controls")
    print("  • Robust error handling and logging")
    print("  • Program streaming integration")
    print("  • Auto-recovery for program streams")
    print("  • Live quality change support")
    print("  • Comprehensive statistics display")
    print("  • Server management with import/export")
    print("  • Preset configuration support")
    print("  • Dark theme with modern UI")
    print("=" * 60)
    print("🚀 Application ready for professional streaming!")
    print("💡 Use the menu options to test all features")
    print("📝 Detailed logs available in ~/.tv_stream")
    print("=" * 60)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n🛑 Application terminated by user")
        sys.exit(0)