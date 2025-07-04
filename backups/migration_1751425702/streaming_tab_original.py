#!/usr/bin/env python3
"""
Fixed Streaming Tab - Complete Implementation with All Import Issues Resolved
Professional streaming management with fixed imports and full functionality
"""

import os
import sys
import json
import asyncio
import subprocess
import threading
import shutil
import time 
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# FIXED: Add proper logging import with fallback
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

# FIXED: Import server configuration components with better error handling
try:
    from ui.dialogs.server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
    from ui.dialogs.network_optimizations import NetworkOptimizer, StreamReconnector
    from ui.dialogs.improved_stream_processor import ImprovedStreamProcessor
    OPTIMIZED_STREAMING_AVAILABLE = True
    print("✅ Optimized streaming components loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not import optimized components: {e}")
    OPTIMIZED_STREAMING_AVAILABLE = False
    
    # Try alternative import paths
    try:
        from server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
        print("✅ Server config loaded from root directory")
    except ImportError:
        try:
            from ui.dialogs.servers.server_config import ServerConfig, ServerEditDialog, ServerManagerDialog, ServerStorageManager
            print("✅ Server config loaded from ui.dialogs.servers")
        except ImportError:
            print("❌ Using fallback server configuration")
            # Fallback server config implementation
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

            # Fallback dialog classes
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

def is_valid_media_file(file_path):
    """Медиа файл эсэхийг шалгах"""
    media_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.mp3', '.wav', '.flac', '.aac'}
    return Path(file_path).suffix.lower() in media_extensions and not file_path.endswith('__init__.py')

# Create fallback NetworkOptimizer and StreamReconnector if not available
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

# =============================================================================
# STREAMING MODELS AND CONSTANTS
# =============================================================================

class StreamStatus(Enum):
    """Stream status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    STREAMING = "streaming"
    STOPPING = "stopping"
    ERROR = "error"
    RECONNECTING = "reconnecting"

# Quality presets
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

# Encoder presets
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
    """Stream configuration"""
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
    
    # Advanced settings
    rate_control: str = "CBR"
    preset: str = "veryfast"
    keyframe_interval: int = 2
    buffer_size: Optional[str] = None
    max_bitrate: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
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

# =============================================================================
# STREAM PROCESSOR
# =============================================================================

class StreamProcessor(QObject):
    """FFmpeg-based stream processor"""
    
    # Signals
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
            'uptime': '00:00:00',
            'stream_time': '00:00:00',
            'encoding_speed': 0.0,
            'process_running': False
        }
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        
        self.logger = get_logger(__name__)
    
    def start_stream(self) -> bool:
        """Start streaming process"""
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
        """Stop streaming process"""
        if self.process and self.is_running:
            self.stats_timer.stop()
            self.process.terminate()
            if not self.process.waitForFinished(5000):
                self.process.kill()
            self.is_running = False
    
    def _build_ffmpeg_command(self) -> List[str]:
        """Build FFmpeg command with enhanced validation"""
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "info", "-stats"]

        # ✅ ENHANCED INPUT VALIDATION
        if self.stream_config.input_source.startswith("live:"):
            input_type = self.stream_config.input_source.split(":")[1]
            if input_type == "test_pattern":
                cmd.extend([
                    "-f", "lavfi",
                    "-i", "testsrc=size=1280x720:rate=30,aevalsrc=0"
                ])
            elif input_type == "desktop_capture":
                cmd.extend(["-f", "gdigrab", "-i", "desktop"])
            elif input_type == "webcam":
                cmd.extend(["-f", "dshow", "-i", "video=Integrated Camera"])
        else:
            # ✅ FILE INPUT WITH STRICT VALIDATION
            try:
                file_path = Path(self.stream_config.input_source)
                
                # Double check file exists
                if not file_path.exists():
                    self.logger.error(f"File not found: {file_path}")
                    return []

                # Double check it's a media file
                if not is_valid_media_file(str(file_path)):
                    self.logger.error(f"Invalid media file: {file_path}")
                    return []

                self.logger.info(f"Loading validated media file: {file_path}")

            except Exception as e:
                self.logger.error(f"File validation error: {e}")
                return []

            # Enhanced input parameters for better compatibility
            if self.stream_config.loop_input:
                cmd.extend(["-stream_loop", "-1"])
            
            if self.stream_config.start_time:
                cmd.extend(["-ss", self.stream_config.start_time])

            # Add input file with error resilience
            cmd.extend([
                "-fflags", "+genpts+igndts",
                "-err_detect", "ignore_err",
                "-i", str(self.stream_config.input_source)
            ])
            
            if self.stream_config.duration:
                cmd.extend(["-t", self.stream_config.duration])

        # Continue with existing video/audio encoding...
        quality = self.stream_config.quality
        cmd.extend([
            "-c:v", "libx264",
            "-b:v", quality["video_bitrate"],
            "-s", f"{quality['width']}x{quality['height']}",
            "-r", str(quality["fps"]),
            "-preset", "veryfast",
            "-tune", "zerolatency",
            "-g", str(quality["fps"] * 2),
            "-pix_fmt", "yuv420p",
            "-profile:v", "main",
            "-level", "4.0"
        ])

        # Rate control
        if self.stream_config.rate_control == "CBR":
            cmd.extend([
                "-minrate", quality["video_bitrate"],
                "-maxrate", quality["video_bitrate"],
                "-bufsize", f"{int(quality['video_bitrate'].replace('k', '')) * 2}k"
            ])

        # Audio encoding
        cmd.extend([
            "-c:a", "aac",
            "-b:a", quality["audio_bitrate"],
            "-ar", "44100",
            "-ac", "2"
        ])

        # Output
        rtmp_url = f"{self.stream_config.server.rtmp_url}/{self.stream_config.stream_key}"
        cmd.extend([
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            "-progress", "pipe:1",
            rtmp_url
        ])

        self.logger.info(f"Enhanced FFmpeg command: {' '.join(cmd)}")
        return cmd
    
    def _is_valid_media_file(self, file_path: str) -> bool:
        """Check if file is a valid media file"""
        try:
            from pathlib import Path
            
            if not file_path or not Path(file_path).exists():
                return False
            
            # Media file extensions
            media_extensions = {
                '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v',
                '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob', '.ts',
                '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'
            }
            
            file_ext = Path(file_path).suffix.lower()
            
            # Check extension
            if file_ext not in media_extensions:
                return False
            
            # Additional checks for Python files
            if file_ext == '.py' or 'init' in Path(file_path).name.lower():
                return False
            
            # Check file size (media files are usually larger than 1KB)
            if Path(file_path).stat().st_size < 1024:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"File validation error: {e}")
            return False

    def _get_media_file_info(self, file_path: str) -> dict:
        """Get media file information"""
        try:
            from pathlib import Path
            
            if not self._is_valid_media_file(file_path):
                return {'valid': False, 'error': 'Invalid media file'}
            
            file_info = Path(file_path).stat()
            
            return {
                'valid': True,
                'name': Path(file_path).name,
                'size': file_info.st_size,
                'size_mb': round(file_info.st_size / (1024 * 1024), 2),
                'extension': Path(file_path).suffix.lower(),
                'is_video': Path(file_path).suffix.lower() in {
                    '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'
                },
                'is_audio': Path(file_path).suffix.lower() in {
                    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Media file info error: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _update_stats(self):
        """Update streaming statistics with enhanced monitoring"""
        if self.start_time:
            uptime = datetime.now() - self.start_time
            self.stats['uptime'] = str(uptime).split('.')[0]
        
        # Get real-time process stats if available
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.stats['process_running'] = True
            
            # Force read any pending output for stats
            if self.process.bytesAvailable() > 0:
                output_data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
                if output_data:
                    self._parse_ffmpeg_output(output_data)
            
            # Force read any pending error output
            if self.process.canReadLine():
                error_data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
                if error_data:
                    self._parse_ffmpeg_output(error_data)
        else:
            self.stats['process_running'] = False
        
        # Ensure minimum stats are available
        if 'fps' not in self.stats:
            self.stats['fps'] = 0.0
        if 'bitrate' not in self.stats:
            self.stats['bitrate'] = '0kbits/s'
        if 'frames_processed' not in self.stats:
            self.stats['frames_processed'] = 0
        if 'dropped_frames' not in self.stats:
            self.stats['dropped_frames'] = 0
        
        self.statistics_updated.emit(self.stream_config.stream_key, self.stats.copy())
    
    def _on_process_finished(self, exit_code, exit_status):
        """Handle process finished"""
        self.is_running = False
        self.stats_timer.stop()
        message = f"Process finished, exit code: {exit_code}"
        self.stopped.emit(self.stream_config.stream_key, exit_code, message)
    
    def _on_process_error(self, error):
        """Handle process error with better cleanup"""
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
                
                # Check for specific RTMP errors
                if "Already publishing" in stderr_data:
                    error_message = f"Stream key '{self.stream_config.stream_key}' is already in use.\nPlease use a different stream key or wait for the previous stream to end."
                elif "Operation not permitted" in stderr_data:
                    error_message = f"Permission denied. Check RTMP server settings and stream key authorization."
        
        self.logger.error(f"Process error: {error_message}")
        self.error_occurred.emit(self.stream_config.stream_key, error_message)
    
    def _on_output_ready(self):
        """Handle standard output"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _on_error_ready(self):
        """Handle error output"""
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _parse_ffmpeg_output(self, output: str):
        """Parse FFmpeg output for statistics and errors - ENHANCED VERSION"""
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Error detection
            if any(error_word in line.lower() for error_word in 
                ['error', 'failed', 'connection refused', 'timeout', 'cannot', 'unable']):
                self.logger.error(f"FFmpeg error: {line}")
                self.error_occurred.emit(self.stream_config.stream_key, line)
                
            # Enhanced statistics parsing
            if 'frame=' in line and 'fps=' in line and 'bitrate=' in line:
                try:
                    # Parse frame number
                    if 'frame=' in line:
                        frame_match = re.search(r'frame=\s*(\d+)', line)
                        if frame_match:
                            self.stats['frames_processed'] = int(frame_match.group(1))
                    
                    # Parse FPS
                    fps_match = re.search(r'fps=\s*([\d.]+)', line)
                    if fps_match:
                        self.stats['fps'] = float(fps_match.group(1))
                    
                    # Parse bitrate
                    bitrate_match = re.search(r'bitrate=\s*([\d.]+\.?\d*\w*bits?/s)', line)
                    if bitrate_match:
                        self.stats['bitrate'] = bitrate_match.group(1)
                    
                    # Parse dropped frames
                    drop_match = re.search(r'drop=\s*(\d+)', line)
                    if drop_match:
                        self.stats['dropped_frames'] = int(drop_match.group(1))
                        
                    # Parse time
                    time_match = re.search(r'time=\s*([\d:\.]+)', line)
                    if time_match:
                        self.stats['stream_time'] = time_match.group(1)
                    
                    # Parse speed
                    speed_match = re.search(r'speed=\s*([\d.]+)x', line)
                    if speed_match:
                        self.stats['encoding_speed'] = float(speed_match.group(1))
                    
                    # Emit updated statistics
                    self.statistics_updated.emit(self.stream_config.stream_key, self.stats.copy())
                    
                except (ValueError, AttributeError) as e:
                    self.logger.debug(f"Stats parsing error: {e}")
            
            # Additional progress indicators
            elif 'Stream mapping:' in line:
                self.logger.info("FFmpeg stream mapping configured")
            elif 'encoder' in line.lower() and 'configuration' in line.lower():
                self.logger.info(f"Encoder info: {line}")
    
    def get_uptime(self) -> str:
        """Get stream uptime"""
        return self.stats['uptime']

# =============================================================================
# STREAM MANAGER
# =============================================================================

class StreamManager(QObject):
    """Stream manager with features"""
    
    # Signals
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
        """Start a new stream with enhanced validation"""
        try:
            # Check for existing stream with same key
            if stream_config.stream_key in self.streams:
                self.logger.warning(f"Stream {stream_config.stream_key} already exists")
                return False
            
            # Check for "Already publishing" scenario prevention
            existing_keys = list(self.streams.keys())
            if stream_config.stream_key in existing_keys:
                # Generate new unique key
                import time
                new_key = f"{stream_config.stream_key}_{int(time.time())}"
                self.logger.info(f"Stream key conflict, using: {new_key}")
                stream_config.stream_key = new_key
            
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
        """Handle stream reconnecting"""
        self.logger.info(f"Stream {stream_key} attempting reconnection...")
        self.stream_reconnecting.emit(stream_key)
    
    def stop_stream(self, stream_key: str) -> bool:
        """Stop a specific stream"""
        if stream_key in self.streams:
            self.streams[stream_key].stop_stream()
            return True
        return False
    
    def stop_all_streams(self):
        """Stop all active streams"""
        for stream_key in list(self.streams.keys()):
            self.stop_stream(stream_key)
    
    def get_stream_stats(self, stream_key: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific stream"""
        if stream_key in self.streams:
            return self.streams[stream_key].stats.copy()
        return None
    
    def _on_stream_started(self, stream_key: str):
        """Handle stream started"""
        self.stream_started.emit(stream_key)
        self.streams_updated.emit()
    
    def _on_stream_stopped(self, stream_key: str, exit_code: int, message: str):
        """Handle stream stopped"""
        if stream_key in self.streams:
            del self.streams[stream_key]
        self.stream_stopped.emit(stream_key)
        self.streams_updated.emit()
    
    def _on_stream_error(self, stream_key: str, error_message: str):
        """Handle stream error"""
        self.stream_error.emit(stream_key, error_message)

# =============================================================================
# STREAM TABLE MODEL
# =============================================================================

class StreamTableModel(QAbstractTableModel):
    """Table model for active streams"""
    
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
        """Refresh table data with forced update"""
        self.beginResetModel()
        self.endResetModel()
        
        # Force update statistics for all active streams
        for stream_key, processor in self.stream_manager.streams.items():
            processor._update_stats()

# =============================================================================
# MAIN STREAMING TAB
# =============================================================================

class StreamingTab(QWidget):
    """Streaming tab with complete professional features"""
    
    # Signals
    status_message = pyqtSignal(str, int)
    stream_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # FIXED: Initialize all program streaming attributes FIRST
        self.auto_stream_enabled = True
        self.program_stream_quality = "720p"
        self.is_program_streaming_active = False
        self.current_program_stream_key = None
        self.playout_tab_ref = None
        self.program_content_queue = []
        self.last_program_file = None
        self.last_program_state = None
        
        # Initialize stream manager
        self.stream_manager = StreamManager()
        
        # Server configurations
        self.servers: Dict[str, ServerConfig] = {}
        
        # Active streams tracking
        self.active_streams: Dict[str, StreamConfig] = {}
        
        # Current input source
        self.current_input_source = None
        
        # Initialize labels first to prevent AttributeError
        self._init_default_labels()
        
        # Initialize UI first
        self._init_ui()
        
        # Load servers after UI
        QTimer.singleShot(100, self._load_servers)
        
        # Connect signals after everything is ready
        QTimer.singleShot(200, self._connect_signals)
        
        # Check FFmpeg availability
        QTimer.singleShot(1000, self._check_ffmpeg_availability)
        
        # Connect playout integration signals
        self._connect_playout_signals()
        
        # Initialize program streaming integration after UI and attributes are set
        self._setup_program_streaming_integration()
        
        self.logger.debug("Streaming tab initialization completed")
        
        # Cleanup timer for dead streams
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_dead_streams)
        self.cleanup_timer.start(30000)  # 30 секунд тутамд cleanup хийх

    def _init_default_labels(self):
        """Initialize default labels to prevent AttributeError"""
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

    def _connect_playout_signals(self):
        """Connect signals for playout integration"""
        try:
            self.stream_manager.stream_started.connect(self._on_program_stream_started)
            self.stream_manager.stream_stopped.connect(self._on_program_stream_stopped)
        except Exception as e:
            self.logger.error(f"Failed to connect playout signals: {e}")

    def _setup_program_streaming_integration(self):
        """Setup advanced program streaming integration"""
        try:
            # Program streaming timer for status updates
            self.program_stream_timer = QTimer()
            self.program_stream_timer.timeout.connect(self._monitor_program_streams)
            self.program_stream_timer.start(1000)  # Update every second
            
            self.logger.info("Program streaming integration setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup program streaming: {e}")

    def _monitor_program_streams(self):
        """Monitor program streams for health and performance"""
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
                    
                    # Calculate bitrate
                    bitrate_str = processor.stats.get('bitrate', '0kbits/s')
                    try:
                        if 'kbits/s' in bitrate_str:
                            total_program_bitrate += float(bitrate_str.replace('kbits/s', ''))
                    except:
                        pass
            
            # Update program streaming status
            self.is_program_streaming_active = len(program_streams) > 0
            
            # Emit status for playout tab
            if self.is_program_streaming_active and self.current_program_stream_key:
                self.stream_status_changed.emit(True, self.current_program_stream_key)
            
            # Health check - restart if stream fails
            for stream_info in program_streams:
                if not stream_info['running'] and self.auto_stream_enabled:
                    self._attempt_program_stream_recovery(stream_info['key'])
                    
        except Exception as e:
            self.logger.error(f"Program stream monitoring error: {e}")

    def _attempt_program_stream_recovery(self, stream_key: str):
        """Attempt to recover failed program stream"""
        try:
            if stream_key in self.active_streams:
                config = self.active_streams[stream_key]
                
                # Try to restart the stream
                self.logger.warning(f"Attempting to recover program stream: {stream_key}")
                
                QTimer.singleShot(2000, lambda: self._restart_program_stream(stream_key, config))
                
        except Exception as e:
            self.logger.error(f"Program stream recovery failed: {e}")

    def _restart_program_stream(self, stream_key: str, config):
        """Restart program stream with configuration"""
        try:
            if self.stream_manager.start_stream(config):
                self.active_streams[stream_key] = config
                self.logger.info(f"Program stream recovered: {stream_key}")
                self.status_message.emit(f"Program stream recovered: {stream_key}", 3000)
            else:
                self.logger.error(f"Failed to recover program stream: {stream_key}")
                
        except Exception as e:
            self.logger.error(f"Program stream restart error: {e}")

    def _on_program_stream_started(self, stream_key):
        """Handle program stream started"""
        if "program" in stream_key.lower():
            self.stream_status_changed.emit(True, stream_key)
            self.logger.info(f"Program stream started: {stream_key}")

    def _on_program_stream_stopped(self, stream_key):
        """Handle program stream stopped"""
        if "program" in stream_key.lower():
            self.stream_status_changed.emit(False, stream_key)
            self.logger.info(f"Program stream stopped: {stream_key}")

    def load_and_start_stream(self, file_path):
        """Load file and start streaming for playout integration - FIXED VERSION"""
        try:
            if not Path(file_path).exists():
                self.logger.error(f"File not found: {file_path}")
                self.status_message.emit(f"Файл олдсонгүй: {Path(file_path).name}", 5000)
                return False
            
            # ✅ VALIDATE MEDIA FILE
            if not self._is_valid_media_file(file_path):
                self.logger.error(f"Invalid media file: {file_path}")
                self.status_message.emit(f"Буруу медиа файл: {Path(file_path).name}", 5000)
                return False
            
            file_info = self._get_media_file_info(file_path)
            self.logger.info(f"Loading valid media file: {file_info['name']} ({file_info['size_mb']} MB)")
            
            if hasattr(self, 'source_input') and self.source_input:
                self.source_input.setText(file_path)
                self.current_input_source = file_path
            
            if hasattr(self, 'source_type_combo') and self.source_type_combo:
                self.source_type_combo.setCurrentText("Медиа Файл")
            
            # Continue with existing logic...
            current_key = ""
            if hasattr(self, 'stream_key_input') and self.stream_key_input:
                current_key = self.stream_key_input.text().strip()
                
            if not current_key:
                program_key = f"program_{int(time.time())}"
                if hasattr(self, 'stream_key_input') and self.stream_key_input:
                    self.stream_key_input.setText(program_key)
            
            # Set optimal quality for the media type
            if file_info['is_video']:
                self._set_optimal_video_quality()
            else:  # Audio only
                self._set_optimal_audio_quality()
            
            if hasattr(self, 'loop_input_cb') and self.loop_input_cb:
                self.loop_input_cb.setChecked(True)
            
            if hasattr(self, 'rate_control_combo') and self.rate_control_combo:
                self.rate_control_combo.setCurrentText("CBR")
            
            if hasattr(self, 'preset_combo') and self.preset_combo:
                self.preset_combo.setCurrentText("veryfast")
            
            self.logger.info(f"Auto-configuring stream for program content: {Path(file_path).name}")
            self.status_message.emit(f"Program content configured: {Path(file_path).name}", 3000)
            
            QTimer.singleShot(500, self._start_program_stream_delayed)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load and start stream: {e}")
            self.status_message.emit(f"Stream load failed: {e}", 5000)
            return False

    def connect_to_playout_tab(self, playout_tab):
        """Enhanced connection to playout tab with bidirectional communication"""
        try:
            self.playout_tab_ref = playout_tab
            
            # Connect playout signals to streaming actions
            if hasattr(playout_tab, 'media_taken_to_air'):
                playout_tab.media_taken_to_air.connect(self._on_media_taken_to_air)
            
            if hasattr(playout_tab, 'stream_program_requested'):
                playout_tab.stream_program_requested.connect(self._on_stream_program_requested)
            
            # Connect our signals to playout tab
            if hasattr(playout_tab, '_on_streaming_status_changed'):
                self.stream_status_changed.connect(playout_tab._on_streaming_status_changed)
            
            # Set up program content monitoring
            self._setup_program_content_monitoring()
            
            self.logger.info("Enhanced playout tab connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to playout tab: {e}")
            return False

    def _on_media_taken_to_air(self, file_path: str):
        """Handle media taken to air - start streaming immediately"""
        try:
            self.logger.info(f"Media taken to air, starting stream: {Path(file_path).name}")
            
            # Configure for live program streaming
            source_info = {
                'file_path': file_path,
                'loop': True,
                'priority': 'high'
            }
            
            # Start streaming with minimal delay
            success = self.start_live_program_stream(source_info)
            
            if success:
                self.status_message.emit(f"🚀 Program streaming started: {Path(file_path).name}", 5000)
            else:
                self.status_message.emit(f"❌ Failed to start program streaming", 5000)
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to handle media taken to air: {e}")
            return False

    def _on_stream_program_requested(self, file_path: str):
        """Handle direct stream program request"""
        try:
            return self.load_and_start_stream(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to handle stream program request: {e}")
            return False

    def _setup_program_content_monitoring(self):
        """Setup monitoring of program content changes"""
        try:
            # Monitor program player state
            self.program_monitor_timer = QTimer()
            self.program_monitor_timer.timeout.connect(self._check_program_content)
            self.program_monitor_timer.start(2000)  # Check every 2 seconds
            
        except Exception as e:
            self.logger.error(f"Failed to setup program monitoring: {e}")

    def _check_program_content(self):
        """Check for program content changes"""
        try:
            if not hasattr(self, 'playout_tab_ref') or not self.playout_tab_ref:
                return
            
            # Get current program state
            current_state = self.playout_tab_ref.get_current_state()
            program_info = current_state.get('program')
            
            if program_info:
                current_file = program_info.get('file')
                is_playing = program_info.get('playing', False)
                
                # Check for content change
                if current_file != self.last_program_file:
                    self.last_program_file = current_file
                    
                    # Update streaming if auto-enabled and on air
                    if (self.auto_stream_enabled and 
                        current_state.get('on_air', False) and 
                        current_file):
                        self.update_program_content(current_file, auto_start=True)
                
                # Check for playback state change
                if is_playing != self.last_program_state:
                    self.last_program_state = is_playing
                    
                    if is_playing and current_state.get('on_air', False):
                        # Resume or start streaming
                        if not self.is_program_streaming_active and current_file:
                            self.update_program_content(current_file, auto_start=True)
                        
        except Exception as e:
            self.logger.debug(f"Program content check error: {e}")

    def stop_program_streams(self):
        """Stop all program-related streams"""
        try:
            stopped_count = 0
            
            # Find and stop program streams
            program_streams = []
            for stream_key in list(self.stream_manager.streams.keys()):
                if "program" in stream_key.lower():
                    program_streams.append(stream_key)
            
            for stream_key in program_streams:
                if self.stream_manager.stop_stream(stream_key):
                    if stream_key in self.active_streams:
                        del self.active_streams[stream_key]
                    stopped_count += 1
            
            if stopped_count > 0:
                self.status_message.emit(f"Stopped {stopped_count} program stream(s)", 3000)
                
            return stopped_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to stop program streams: {e}")
            return False

    def start_live_program_stream(self, source_info):
        """Start live program streaming with enhanced real-time support"""
        try:
            # Enhanced program stream configuration
            stream_key = f"live_program_{int(time.time())}"
            
            # Get optimal server for program content
            server_config = self._get_optimal_program_server()
            if not server_config:
                self.logger.error("No suitable server for program streaming")
                return False
            
            # Enhanced quality settings for program content
            quality_config = self._get_program_quality_config()
            
            # Create optimized stream configuration for live content
            stream_config = StreamConfig(
                stream_key=stream_key,
                input_source=source_info.get('file_path', 'live:test_pattern'),
                server=server_config,
                quality=quality_config,
                encoder="libx264",
                audio_encoder="aac",
                loop_input=source_info.get('loop', True),
                rate_control="CBR",  # Consistent bitrate for live
                preset="ultrafast",  # Low latency for live
                keyframe_interval=1,  # Frequent keyframes for live
                buffer_size="1024k",  # Optimized buffer
                max_bitrate=quality_config.get('video_bitrate', '2500k')
            )
            
            # Add real-time optimizations
            stream_config.custom_ffmpeg_args.extend([
                "-tune", "zerolatency",  # Zero latency tuning
                "-fflags", "+igndts",    # Ignore DTS
                "-avoid_negative_ts", "make_zero",  # Avoid negative timestamps
                "-max_delay", "0",       # No delay
                "-fflags", "+genpts"     # Generate PTS
            ])
            
            # Start streaming
            if self.stream_manager.start_stream(stream_config):
                self.active_streams[stream_key] = stream_config
                self.current_program_stream_key = stream_key
                self.is_program_streaming_active = True
                
                # Notify playout tab
                self.stream_status_changed.emit(True, stream_key)
                
                self.logger.info(f"Live program stream started: {stream_key}")
                self.status_message.emit(f"Live program streaming: {stream_key}", 5000)
                return True
            else:
                self.logger.error("Failed to start live program stream")
                return False
                
        except Exception as e:
            self.logger.error(f"Live program streaming failed: {e}")
            return False

    def _get_optimal_program_server(self):
        """FIXED: Get optimal server for program streaming"""
        try:
            if not self.servers:
                return None
            
            # PRIORITY 1: 192.168.1.50 (танай NGINX сервер)
            for server_id, server_config in self.servers.items():
                if server_config.host == "192.168.1.50":
                    self.logger.info(f"✅ Using 192.168.1.50 server: {server_config.name}")
                    return server_config
            
            # PRIORITY 2: Local network servers
            for server_id, server_config in self.servers.items():
                if server_config.host.startswith("192.168."):
                    self.logger.info(f"✅ Using local network server: {server_config.name}")
                    return server_config
            
            # FALLBACK: First available
            return list(self.servers.values())[0]
            
        except Exception as e:
            self.logger.error(f"Failed to get optimal server: {e}")
            return None

    def _get_program_quality_config(self):
        """Get optimized quality configuration for program content"""
        try:
            if self.program_stream_quality in QUALITY_PRESETS:
                quality = QUALITY_PRESETS[self.program_stream_quality].copy()
                
                # Optimize for program content
                quality['fps'] = 30  # Smooth playback
                
                # Adjust bitrate based on content type
                base_bitrate = int(quality['video_bitrate'].replace('k', ''))
                optimized_bitrate = int(base_bitrate * 1.2)  # 20% increase for quality
                quality['video_bitrate'] = f"{optimized_bitrate}k"
                
                return quality
            else:
                return QUALITY_PRESETS["720p"]
                
        except Exception as e:
            self.logger.error(f"Failed to get program quality config: {e}")
            return QUALITY_PRESETS["720p"]

    def update_program_content(self, file_path: str, auto_start: bool = True):
        """Update program content and optionally restart streaming"""
        try:
            if not Path(file_path).exists():
                self.logger.error(f"Program file not found: {file_path}")
                return False
            
            # Stop existing program streams
            self.stop_program_streams()
            
            # Wait for clean shutdown
            QTimer.singleShot(1000, lambda: self._start_updated_program_stream(file_path, auto_start))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update program content: {e}")
            return False

    def _start_updated_program_stream(self, file_path: str, auto_start: bool):
        """Start streaming with updated program content"""
        try:
            if auto_start:
                source_info = {
                    'file_path': file_path,
                    'loop': True
                }
                return self.start_live_program_stream(source_info)
            else:
                # Just prepare for manual start
                self.current_input_source = file_path
                if hasattr(self, 'source_input'):
                    self.source_input.setText(file_path)
                
                self.logger.info(f"Program content updated: {Path(file_path).name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start updated program stream: {e}")
            return False

    def _start_program_stream_delayed(self):
        """Start the configured program stream with delay"""
        try:
            return self._start_stream()
        except Exception as e:
            self.logger.error(f"Failed to start delayed program stream: {e}")
            self.status_message.emit(f"Stream start failed: {e}", 5000)
            return False

    def _check_ffmpeg_availability(self):
        """Check if FFmpeg is available"""
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
        """Show FFmpeg warning dialog"""
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
            self.logger.error(f"Failed to show FFmpeg warning: {e}")
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Input source selection
        input_section = self._create_input_source_section()
        layout.addWidget(input_section)
        
        # Stream configuration
        config_section = self._create_stream_configuration_section()
        layout.addWidget(config_section)
        
        # Stream controls
        controls_section = self._create_controls_section()
        layout.addWidget(controls_section)
        
        # Active streams table
        streams_section = self._create_streams_section()
        layout.addWidget(streams_section, stretch=1)
  
    def _create_input_source_section(self) -> QWidget:
        """Create input source selection section"""
        group = QGroupBox("📹 Оролтын Эх Сурвалж")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Эх Сурвалжийн Төрөл:"), 0, 0)
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems([
            "Медиа Файл", "Дэлгэц Хураах", "Вэбкамер", "Аудио Оролт", "Тест Хэв маяг"
        ])
        self.source_type_combo.currentTextChanged.connect(self._on_source_type_changed)
        layout.addWidget(self.source_type_combo, 0, 1)
        
        layout.addWidget(QLabel("Эх Сурвалж:"), 1, 0)
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Медиа файл сонгох эсвэл оролтыг тохируулах...")
        layout.addWidget(self.source_input, 1, 1, 1, 2)
        
        self.browse_btn = QPushButton("📁 Хайх")
        self.browse_btn.clicked.connect(self._browse_source_file)
        layout.addWidget(self.browse_btn, 1, 3)
        
        layout.addWidget(QLabel("Сонголтууд:"), 2, 0)
        
        options_layout = QHBoxLayout()
        self.loop_input_cb = QCheckBox("Оролтыг давтах")
        options_layout.addWidget(self.loop_input_cb)
        
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("Эхлэх хугацаа (ЦЦ:ММ:СС)")
        self.start_time_input.setMaximumWidth(120)
        options_layout.addWidget(QLabel("Эхлэх:"))
        options_layout.addWidget(self.start_time_input)
        
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Үргэлжлэх хугацаа (ЦЦ:ММ:СС)")
        self.duration_input.setMaximumWidth(120)
        options_layout.addWidget(QLabel("Үргэлжлэх:"))
        options_layout.addWidget(self.duration_input)
        
        options_layout.addStretch()
        layout.addLayout(options_layout, 2, 1, 1, 3)
        
        return group
    
    def _create_stream_configuration_section(self) -> QWidget:
        """Create stream configuration section"""
        group = QGroupBox("⚙️ Стримийн Тохиргоо")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Сервер:"), 0, 0)
        self.server_combo = QComboBox()
        self.server_combo.setMinimumWidth(200)
        self.server_combo.addItem("Серверүүд ачаалж байна...", None)
        self.server_combo.setEnabled(False)
        layout.addWidget(self.server_combo, 0, 1)
        
        self.server_status_label = QLabel("⏳ Серверүүд ачаалж байна...")
        self.server_status_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 10px;")
        layout.addWidget(self.server_status_label, 1, 1, 1, 2)
        
        # Server management
        server_mgmt_layout = QHBoxLayout()
        
        self.add_server_btn = QPushButton("➕ Нэмэх")
        self.add_server_btn.clicked.connect(self._add_server)
        server_mgmt_layout.addWidget(self.add_server_btn)
        
        self.edit_server_btn = QPushButton("✏️ Засах")
        self.edit_server_btn.clicked.connect(self._edit_server)
        server_mgmt_layout.addWidget(self.edit_server_btn)
        
        self.import_servers_btn = QPushButton("📥 Импорт")
        self.import_servers_btn.clicked.connect(self._import_servers_dialog)
        server_mgmt_layout.addWidget(self.import_servers_btn)
        
        self.manage_servers_btn = QPushButton("🛠️ Удирдах")
        self.manage_servers_btn.clicked.connect(self._manage_servers)
        server_mgmt_layout.addWidget(self.manage_servers_btn)
        
        server_mgmt_layout.addStretch()
        layout.addLayout(server_mgmt_layout, 0, 2, 1, 2)
        
        # Stream key
        layout.addWidget(QLabel("Стримийн Түлхүүр:"), 1, 0)
        
        stream_key_widget = QWidget()
        stream_key_layout = QHBoxLayout(stream_key_widget)
        stream_key_layout.setContentsMargins(0, 0, 0, 0)
        stream_key_layout.setSpacing(8)
        
        self.stream_key_input = QLineEdit()
        self.stream_key_input.setPlaceholderText("автоматаар үүсгэгдэнэ эсвэл гараар оруулна уу")
        stream_key_layout.addWidget(self.stream_key_input)
        
        self.generate_key_btn = QPushButton("🎲")
        self.generate_key_btn.setToolTip("Автоматаар түлхүүр үүсгэх")
        self.generate_key_btn.setMaximumWidth(40)
        self.generate_key_btn.clicked.connect(self._generate_stream_key)
        stream_key_layout.addWidget(self.generate_key_btn)
        
        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.setMaximumWidth(40)
        self.show_key_btn.toggled.connect(self._toggle_stream_key_visibility)
        stream_key_layout.addWidget(self.show_key_btn)
        
        layout.addWidget(stream_key_widget, 1, 1, 1, 2)
        
        # Quality preset
        layout.addWidget(QLabel("Чанар:"), 3, 0)
        self.quality_combo = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.quality_combo.addItem(quality_data["name"], quality_data)
        self.quality_combo.setCurrentText("720p (HD)")
        layout.addWidget(self.quality_combo, 3, 1)
        
        # Encoder selection
        layout.addWidget(QLabel("Кодлогч:"), 3, 2)
        self.encoder_combo = QComboBox()
        for encoder_key, encoder_data in ENCODER_PRESETS.items():
            self.encoder_combo.addItem(encoder_data["name"], encoder_key)
        layout.addWidget(self.encoder_combo, 3, 3)
        
        # Advanced settings
        layout.addWidget(QLabel("Хурдны Хяналт:"), 4, 0)
        self.rate_control_combo = QComboBox()
        self.rate_control_combo.addItems(["CBR", "VBR", "CQP"])
        layout.addWidget(self.rate_control_combo, 4, 1)
        
        layout.addWidget(QLabel("Урьдчилан Тохиргоо:"), 4, 2)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"])
        self.preset_combo.setCurrentText("veryfast")
        layout.addWidget(self.preset_combo, 4, 3)
        
        return group

    def _create_controls_section(self) -> QWidget:
        """Create stream controls section with program integration"""
        group = QGroupBox("🎛️ Стримийн Хяналт")
        main_layout = QVBoxLayout(group)
        
        # Main controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Стрим Эхлүүлэх")
        self.start_btn.clicked.connect(self._start_stream)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Сонгосныг Зогсоох")
        self.stop_btn.clicked.connect(self._stop_selected_stream)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        self.test_btn = QPushButton("🧪 Стрим Шалгах")
        self.test_btn.clicked.connect(self._test_stream)
        controls_layout.addWidget(self.test_btn)
        
        self.stop_all_btn = QPushButton("🛑 Бүгдийг Зогсоох")
        self.stop_all_btn.clicked.connect(self._stop_all_streams)
        self.stop_all_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_all_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Program streaming integration section
        program_section = self._create_program_streaming_section()
        main_layout.addWidget(program_section)
        
        return group
    
    def _create_program_streaming_section(self):
        """Create program streaming control section"""
        group = QGroupBox("📺 Program Streaming Integration")
        layout = QVBoxLayout(group)
        
        # Auto-stream control
        auto_stream_layout = QHBoxLayout()
        
        self.auto_stream_cb = QCheckBox("Auto-start streaming when ON AIR")
        self.auto_stream_cb.setChecked(self.auto_stream_enabled)
        self.auto_stream_cb.toggled.connect(self._toggle_auto_stream)
        auto_stream_layout.addWidget(self.auto_stream_cb)
        
        # Program quality selector
        auto_stream_layout.addWidget(QLabel("Quality:"))
        self.program_quality_combo = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.program_quality_combo.addItem(quality_data["name"], quality_key)
        self.program_quality_combo.setCurrentText("720p (HD)")
        self.program_quality_combo.currentTextChanged.connect(self._on_program_quality_changed)
        auto_stream_layout.addWidget(self.program_quality_combo)
        
        layout.addLayout(auto_stream_layout)
        
        # Program streaming status
        status_layout = QHBoxLayout()
        
        self.program_stream_status = QLabel("⚫ Not Streaming")
        self.program_stream_status.setStyleSheet("font-weight: bold; color: #6c757d;")
        status_layout.addWidget(self.program_stream_status)
        
        status_layout.addStretch()
        
        # Manual control buttons
        self.start_program_btn = QPushButton("🎬 Start Program Stream")
        self.start_program_btn.clicked.connect(self._manual_start_program_stream)
        self.start_program_btn.setEnabled(False)
        status_layout.addWidget(self.start_program_btn)
        
        self.stop_program_btn = QPushButton("⏹️ Stop Program Stream")
        self.stop_program_btn.clicked.connect(self.stop_program_streams)
        self.stop_program_btn.setEnabled(False)
        status_layout.addWidget(self.stop_program_btn)
        
        layout.addLayout(status_layout)
        
        return group

    def _create_streams_section(self) -> QWidget:
        """Create active streams section"""
        group = QGroupBox("📡 Идэвхтэй Стримүүд")
        layout = QVBoxLayout(group)
        
        # Streams table
        self.streams_table = QTableView()
        self.stream_model = StreamTableModel(self.stream_manager)
        self.streams_table.setModel(self.stream_model)
        
        self.streams_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.streams_table.setAlternatingRowColors(True)
        self.streams_table.verticalHeader().setVisible(False)
        self.streams_table.horizontalHeader().setStretchLastSection(True)
        
        # Set column widths
        header = self.streams_table.horizontalHeader()
        header.resizeSection(0, 150)
        header.resizeSection(1, 120)
        header.resizeSection(2, 100)
        header.resizeSection(3, 100)
        header.resizeSection(4, 90)
        header.resizeSection(5, 60)
        header.resizeSection(6, 90)
        header.resizeSection(7, 90)
        
        selection_model = self.streams_table.selectionModel()
        if selection_model:
            selection_model.currentRowChanged.connect(self._on_stream_selection_changed)
        
        layout.addWidget(self.streams_table)
        
        # Statistics panel
        info_layout = QHBoxLayout()
        
        stats_group = QGroupBox("📊 Ерөнхий Статистик")
        stats_layout = QFormLayout(stats_group)
        stats_layout.addRow("Идэвхтэй Стрим:", self.total_streams_label)
        stats_layout.addRow("Нийт Битрэйт:", self.total_bitrate_label)
        stats_layout.addRow("Дундаж Latency:", self.network_latency_label)
        stats_layout.addRow("Дахин Холбох:", self.reconnect_count_label)
        stats_layout.addRow("Оптимизаци:", self.optimization_status_label)
        info_layout.addWidget(stats_group)
        
        details_group = QGroupBox("ℹ️ Стримийн Дэлгэрэнгүй")
        details_layout = QFormLayout(details_group)
        details_layout.addRow("Сонгогдсон:", self.selected_stream_label)
        details_layout.addRow("Сервер:", self.stream_server_label)
        details_layout.addRow("Чанар:", self.stream_quality_label)
        details_layout.addRow("FPS:", self.stream_fps_label)
        details_layout.addRow("Битрэйт:", self.stream_bitrate_label)
        details_layout.addRow("Ажилласан хугацаа:", self.stream_uptime_label)
        info_layout.addWidget(details_group)
        
        controls_group = QGroupBox("🎮 Стримийн Хяналт")
        controls_layout = QVBoxLayout(controls_group)
        
        quality_control_layout = QHBoxLayout()
        quality_control_layout.addWidget(QLabel("Чанар Өөрчлөх:"))
        self.live_quality_combo = QComboBox()
        for quality_key, quality_data in QUALITY_PRESETS.items():
            self.live_quality_combo.addItem(quality_data["name"], quality_data)
        quality_control_layout.addWidget(self.live_quality_combo)
        
        self.apply_quality_btn = QPushButton("Хэрэгжүүлэх")
        self.apply_quality_btn.clicked.connect(self._apply_quality_change)
        self.apply_quality_btn.setEnabled(False)
        quality_control_layout.addWidget(self.apply_quality_btn)
        
        controls_layout.addLayout(quality_control_layout)
        
        actions_layout = QHBoxLayout()
        
        self.restart_stream_btn = QPushButton("🔄 Дахин эхлүүлэх")
        self.restart_stream_btn.clicked.connect(self._restart_selected_stream)
        self.restart_stream_btn.setEnabled(False)
        actions_layout.addWidget(self.restart_stream_btn)
        
        self.stream_info_btn = QPushButton("📋 Мэдээлэл")
        self.stream_info_btn.clicked.connect(self._show_stream_info)
        self.stream_info_btn.setEnabled(False)
        actions_layout.addWidget(self.stream_info_btn)
        
        controls_layout.addLayout(actions_layout)
        info_layout.addWidget(controls_group)
        
        layout.addLayout(info_layout)
        
        return group
    
    def _load_servers(self):
        """Load server configurations with proper priority"""
        try:
            self.servers.clear()
            
            if not hasattr(self, 'server_combo') or self.server_combo is None:
                self.logger.error("Server combo not available during load")
                QTimer.singleShot(500, self._load_servers)
                return
                        
            config_dir = Path.home() / ".tv_stream"
            config_dir.mkdir(exist_ok=True)
            
            storage_manager = ServerStorageManager(config_dir / "servers.json")
            
            try:
                loaded_servers = storage_manager.load_servers()
                if loaded_servers:
                    self.servers.update(loaded_servers)
                    self.logger.info(f"Loaded {len(loaded_servers)} servers from storage")
                    # ✅ IMPORTED SERVERS БАЙВАЛ DEFAULT НЭМ
                    self._safe_update_server_combo()
                    return  # ❌ DEFAULT SERVERS ҮҮСГЭХГҮЙ
            except Exception as e:
                self.logger.error(f"Failed to load from storage: {e}")
            
            # Only create defaults if NO servers loaded
            if not self.servers:
                self._create_enhanced_default_servers()
                try:
                    storage_manager.save_servers(self.servers)
                except Exception as e:
                    self.logger.warning(f"Could not save default servers: {e}")
            
            self._safe_update_server_combo()
            
        except Exception as e:
            self.logger.error(f"Load servers failed: {e}")
            self._create_fallback_server()

    def _safe_update_server_combo(self):
        """Safe update server combo with better server selection"""
        try:
            if not hasattr(self, 'server_combo') or self.server_combo is None:
                self.logger.error("Server combo not available")
                return
            
            current_selection = self.server_combo.currentData()
            self.server_combo.clear()
            
            if not self.servers:
                self.server_combo.addItem("❌ Сервер байхгүй", None)
                self.server_combo.setEnabled(False)
                self.server_status_label.setText("⚠️ Сервер нэмэх шаардлагатай")
            else:
                self.server_combo.setEnabled(True)
                
                # Sort servers by priority: local network first, then others
                sorted_servers = []
                local_servers = []
                remote_servers = []
                
                for server_id, server_config in self.servers.items():
                    host = server_config.host.lower()
                    if (host in ['localhost', '127.0.0.1', '::1'] or
                        host.startswith('192.168.') or
                        host.startswith('10.') or
                        any(host.startswith(f'172.{i}.') for i in range(16, 32))):
                        local_servers.append((server_id, server_config))
                    else:
                        remote_servers.append((server_id, server_config))
                
                # Add local servers first, then remote
                sorted_servers = local_servers + remote_servers
                
                for server_id, server_config in sorted_servers:
                    # Add visual indicator for server type
                    if server_config.host.lower() in ['localhost', '127.0.0.1', '::1']:
                        icon = "🏠"  # Home icon for localhost
                    elif server_config.host.startswith('192.168.'):
                        icon = "🏠"  # Local network icon
                    else:
                        icon = "🌐"  # Remote server icon
                    
                    display_text = f"{icon} {server_config.name} ({server_config.host}:{server_config.rtmp_port})"
                    self.server_combo.addItem(display_text, server_config)
                
                # Smart selection: prefer local network servers
                if not current_selection and sorted_servers:
                    # Auto-select first local server if available
                    first_server = sorted_servers[0][1]
                    self.server_combo.setCurrentIndex(0)
                    self.logger.info(f"Auto-selected server: {first_server.name} ({first_server.host})")
                elif current_selection:
                    # Try to restore previous selection
                    for i in range(self.server_combo.count()):
                        if self.server_combo.itemData(i) == current_selection:
                            self.server_combo.setCurrentIndex(i)
                            break
                
                self.server_status_label.setText(f"✅ {len(self.servers)} сервер ачааллагдлаа")
            
            has_selection = self.server_combo.currentData() is not None
            if hasattr(self, 'edit_server_btn'):
                self.edit_server_btn.setEnabled(has_selection)
            
        except Exception as e:
            self.logger.warning(f"Failed to update server combo: {e}")
    
    def test_server_connection(self, server_config: ServerConfig) -> bool:
        """Test if server is reachable"""
        try:
            import socket
            
            # Test RTMP port connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 second timeout
            result = sock.connect_ex((server_config.host, server_config.rtmp_port))
            sock.close()
            
            is_reachable = result == 0
            self.logger.info(f"Server {server_config.name} ({server_config.host}:{server_config.rtmp_port}) - {'✅ Reachable' if is_reachable else '❌ Unreachable'}")
            return is_reachable
            
        except Exception as e:
            self.logger.warning(f"Could not test server {server_config.name}: {e}")
            return False
    
    def debug_current_server_selection(self):
        """Debug current server selection"""
        current_server = self.server_combo.currentData()
        if current_server:
            print(f"🔍 Current selected server:")
            print(f"  Name: {current_server.name}")
            print(f"  Host: {current_server.host}")
            print(f"  RTMP Port: {current_server.rtmp_port}")
            print(f"  RTMP URL: {current_server.rtmp_url}")
        else:
            print("❌ No server selected!")
        
        print(f"📊 Available servers: {len(self.servers)}")
        for sid, config in self.servers.items():
            print(f"  {sid}: {config.name} ({config.host}:{config.rtmp_port})")
    
    def _get_optimal_program_server_with_test(self):
        """Get optimal server with connectivity testing"""
        try:
            if not self.servers:
                return None
            
            # Get server priority list
            priority_servers = []
            
            # 1. Test localhost servers
            for server_id, server_config in self.servers.items():
                if server_config.host.lower() in ['localhost', '127.0.0.1', '::1']:
                    priority_servers.append((1, server_config))  # Priority 1 (highest)
            
            # 2. Test local network servers  
            for server_id, server_config in self.servers.items():
                host = server_config.host.lower()
                if (host.startswith('192.168.') or 
                    host.startswith('10.') or 
                    any(host.startswith(f'172.{i}.') for i in range(16, 32))):
                    priority_servers.append((2, server_config))  # Priority 2
            
            # 3. Other servers
            for server_id, server_config in self.servers.items():
                host = server_config.host.lower()
                if not (host in ['localhost', '127.0.0.1', '::1'] or
                        host.startswith('192.168.') or
                        host.startswith('10.') or
                        any(host.startswith(f'172.{i}.') for i in range(16, 32))):
                    priority_servers.append((3, server_config))  # Priority 3 (lowest)
            
            # Sort by priority and test connectivity
            priority_servers.sort(key=lambda x: x[0])
            
            for priority, server_config in priority_servers:
                self.logger.info(f"Testing server: {server_config.name} ({server_config.host})")
                
                # Quick connectivity test
                if self.test_server_connection(server_config):
                    self.logger.info(f"✅ Selected working server: {server_config.name}")
                    return server_config
                else:
                    self.logger.warning(f"❌ Server unreachable: {server_config.name}")
            
            # If no server is reachable, return first one anyway
            if priority_servers:
                fallback_server = priority_servers[0][1]
                self.logger.warning(f"⚠️ Using fallback server (untested): {fallback_server.name}")
                return fallback_server
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get optimal server with test: {e}")
            return self._get_optimal_program_server() 
    
    def diagnose_server_issues(self):
        """Diagnose server connectivity issues"""
        try:
            if not self.servers:
                self.logger.error("❌ No servers configured")
                return
            
            self.logger.info("🔍 Diagnosing server connectivity...")
            
            working_servers = []
            failed_servers = []
            
            for server_id, server_config in self.servers.items():
                self.logger.info(f"Testing {server_config.name} ({server_config.host}:{server_config.rtmp_port})")
                
                if self.test_server_connection(server_config):
                    working_servers.append(server_config)
                    self.logger.info(f"  ✅ {server_config.name} - OK")
                else:
                    failed_servers.append(server_config)
                    self.logger.error(f"  ❌ {server_config.name} - FAILED")
            
            # Report results
            self.logger.info(f"📊 Connectivity Report:")
            self.logger.info(f"  Working servers: {len(working_servers)}")
            self.logger.info(f"  Failed servers: {len(failed_servers)}")
            
            if working_servers:
                optimal = working_servers[0]
                self.logger.info(f"  🎯 Recommended server: {optimal.name} ({optimal.host})")
            else:
                self.logger.error(f"  ⚠️ No servers are reachable!")
                
            return {
                'working': working_servers,
                'failed': failed_servers,
                'total': len(self.servers)
            }
            
        except Exception as e:
            self.logger.error(f"Server diagnosis failed: {e}")
            return None
    
    def _connect_signals(self):
        """Connect signals"""
        self.stream_manager.stream_started.connect(self._on_stream_started)
        self.stream_manager.stream_stopped.connect(self._on_stream_stopped)
        self.stream_manager.stream_error.connect(self._on_stream_error)
        self.stream_manager.streams_updated.connect(self._update_controls_state)
        
        if hasattr(self, 'live_quality_combo'):
            self.live_quality_combo.currentTextChanged.connect(self._on_live_quality_changed)

        if hasattr(self.stream_manager, 'stream_reconnecting'):
            self.stream_manager.stream_reconnecting.connect(self._on_stream_reconnecting)

    def _on_stream_reconnecting(self, stream_key: str):
        """Handle stream reconnecting"""
        self.status_message.emit(f"🔄 Стрим '{stream_key}' дахин холбож байна...", 3000)
        self.logger.info(f"Stream reconnecting: {stream_key}")
    
    def _on_source_type_changed(self, source_type: str):
        """Handle source type change"""
        if source_type == "Медиа Файл":
            self.browse_btn.setEnabled(True)
            self.source_input.setPlaceholderText("Медиа файл сонгох...")
            self.source_input.clear()
        elif source_type == "Дэлгэц Хураах":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:desktop_capture")
            self.source_input.setPlaceholderText("Дэлгэц хураалт идэвхтэй")
        elif source_type == "Вэбкамер":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:webcam")
            self.source_input.setPlaceholderText("Үндсэн вэбкамер")
        elif source_type == "Аудио Оролт":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:audio_input")
            self.source_input.setPlaceholderText("Үндсэн аудио оролт")
        elif source_type == "Тест Хэв маяг":
            self.browse_btn.setEnabled(False)
            self.source_input.setText("live:test_pattern")
            self.source_input.setPlaceholderText("Тест хэв маяг үүсгэгч")
        
        self.current_input_source = self.source_input.text()
    
    def _browse_source_file(self):
        """Browse for source file with validation"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Эх Файл Сонгох",
            "",
            "Медиа Файлууд (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.mp3 *.wav *.flac *.aac *.ogg *.m4a);;Бүх Файлууд (*)"
        )
        
        if file_path:
            # Validate media file
            if not self._is_valid_media_file(file_path):
                QMessageBox.warning(
                    self,
                    "Файлын Алдаа",
                    f"Сонгосон файл медиа файл биш байна:\n{Path(file_path).name}\n\n"
                    "Зөвхөн дараахь форматыг дэмжинэ:\n"
                    "Видео: mp4, avi, mkv, mov, flv, wmv, webm\n"
                    "Аудио: mp3, wav, flac, aac, ogg, m4a"
                )
                return
            
            self.source_input.setText(file_path)
            self.current_input_source = file_path
            
            # Show file info
            file_info = self._get_media_file_info(file_path)
            if file_info['valid']:
                self.status_message.emit(
                    f"Медиа файл сонгогдлоо: {file_info['name']} ({file_info['size_mb']} MB)", 
                    3000
                )
    
    def _generate_stream_key(self):
        """Generate unique stream key"""
        current_key = self.stream_key_input.text().strip()
        if current_key and len(current_key) >= 3:
            return
        
        # Unique timestamp-based key үүсгэх
        import time
        timestamp = int(time.time())
        unique_key = f"stream_{timestamp}"
        
        self.stream_key_input.setText(unique_key)
        
        if hasattr(self, 'status_message'):
            self.status_message.emit(f"Түлхүүр '{unique_key}' болгогдлоо", 2000)

    def _toggle_stream_key_visibility(self, visible: bool):
        """Toggle stream key visibility"""
        if visible:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("👁")
    
    def _add_server(self):
        """Add new server"""
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
                        
                        self.status_message.emit(f"Сервер '{server_config.name}' амжилттай нэмэгдлээ", 3000)
                        self.logger.info(f"Added new server: {server_config.name}")
                        
                    except Exception as e:
                        if server_id in self.servers:
                            del self.servers[server_id]
                        raise e
                        
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            QMessageBox.critical(
                self, 
                "Алдаа", 
                f"Сервер нэмэхэд алдаа гарлаа:\n\n{str(e)}"
            )
    
    def _edit_server(self):
        """Edit selected server"""
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
                            
                    self.status_message.emit(f"Сервер '{new_config.name}' амжилттай шинэчлэгдлээ", 3000)
                    self.logger.info(f"Updated server: {new_config.name}")
                    
        except Exception as e:
            self.logger.error(f"Failed to edit server: {e}")
            QMessageBox.critical(
                self, 
                "Алдаа", 
                f"Серверийг засахад алдаа гарлаа:\n\n{str(e)}"
            )
    
    def _manage_servers(self):
        """Manage servers through dialog"""
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
                self.status_message.emit("Серверийн тохиргоо шинэчлэгдлээ", 3000)
                self.logger.info(f"Updated {len(self.servers)} servers through manager")
                
        except Exception as e:
            self.logger.error(f"Failed to manage servers: {e}")
            QMessageBox.critical(
                self,
                "Алдаа",
                f"Серверийн удирдлага амжилтгүй боллоо:\n\n{str(e)}"
            )
    
    def _import_servers_dialog(self):
        """Import servers from file"""
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
                    self.status_message.emit(f"{import_count} сервер амжилттай импорт хийгдлээ", 4000)
                    self.logger.info(f"Imported {import_count} servers from {file_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Импортын Алдаа",
                        "Сонгосон файлаас сервер импорт хийж чадсангүй.\n\nФайлын форматыг шалгана уу."
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to import servers: {e}")
            QMessageBox.critical(
                self,
                "Алдаа",
                f"Серверийн импорт амжилтгүй боллоо:\n\n{str(e)}"
            )

    def _import_servers_from_file(self, file_path: Path) -> int:
        """Import servers from file"""
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
        """Create enhanced default server configurations"""
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
        """Create a fallback server configuration"""
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
            self.status_message.emit("Fallback сервер үүсгэгдлээ", 4000)
            self.logger.info("Created fallback server configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback server: {e}")
    
    def _start_stream(self):
        """Start stream with better error handling"""
        current_server = self.server_combo.currentData()
        if current_server:
            self.logger.critical(f"🎯 SELECTED SERVER: {current_server.name} ({current_server.host}:{current_server.rtmp_port})")
            self.logger.critical(f"🔗 RTMP URL WILL BE: {current_server.rtmp_url}")
        else:
            self.logger.critical("❌ NO SERVER SELECTED!")
            
        try:
            if not hasattr(self, 'stream_key_input') or not self.stream_key_input:
                QMessageBox.critical(self, "UI Алдаа", 
                                "UI бүрэн ачааллагдаагүй байна.\n\n"
                                "Програмыг дахин эхлүүлнэ үү.")
                return False
            
            if not self._validate_stream_inputs():
                return False
            
            stream_config = self._build_stream_config()
            if not stream_config:
                QMessageBox.critical(self, "Тохиргооны Алдаа", 
                                "Стримийн тохиргоо үүсгэж чадсангүй.\n\n"
                                "Бүх шаардлагатай талбаруудыг бөглөнө үү.")
                return False
            
            # Check for existing streams with same key
            if stream_config.stream_key in self.stream_manager.streams:
                reply = QMessageBox.question(
                    self, 
                    "Стримийн Түлхүүр Давхцаж Байна", 
                    f"Стрим '{stream_config.stream_key}' аль хэдийн идэвхтэй байна.\n\n"
                    f"Автоматаар шинэ түлхүүр үүсгэх үү?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Generate new unique key
                    import time
                    new_key = f"{stream_config.stream_key}_{int(time.time())}"
                    stream_config.stream_key = new_key
                    self.stream_key_input.setText(new_key)
                    self.status_message.emit(f"Шинэ түлхүүр: {new_key}", 3000)
                else:
                    return False
            
            self.status_message.emit(f"Стрим эхлүүлж байна: {stream_config.stream_key}", 3000)
            
            if self.stream_manager.start_stream(stream_config):
                self.active_streams[stream_config.stream_key] = stream_config
                self.status_message.emit(f"Стрим амжилттай эхэллээ: {stream_config.stream_key}", 5000)
                return True
            else:
                self.status_message.emit("Стрим эхлүүлэх амжилтгүй боллоо", 5000)
                
                # Show more specific error message
                QMessageBox.critical(self, "Стримийн Алдаа", 
                                "Стрим эхлүүлэх амжилтгүй боллоо.\n\n"
                                "Магадгүй шалтгаан:\n"
                                "• RTMP сервер ажиллахгүй байна\n"
                                "• Стримийн түлхүүр аль хэдийн ашиглагдаж байна\n"
                                "• Network холболтын асуудал\n\n"
                                "FFmpeg болон серверийн холболтыг шалгана уу.")
                return False
                        
        except Exception as e:
            self.logger.error(f"Error starting stream: {e}")
            self.status_message.emit(f"Стрим эхлүүлэх алдаа: {e}", 5000)
            QMessageBox.critical(self, "Стримийн Алдаа", 
                            f"Стрим эхлүүлэх амжилтгүй боллоо:\n\n{str(e)}\n\n"
                            f"Дэлгэрэнгүй мэдээллийг логоос харна уу.")
            return False
    
    # Cleanup function нэмэх
    def cleanup_dead_streams(self):
        """Cleanup terminated/crashed streams"""
        try:
            dead_streams = []
            
            for stream_key, processor in self.stream_manager.streams.items():
                if (processor.process and 
                    processor.process.state() == QProcess.ProcessState.NotRunning and
                    not processor.is_running):
                    dead_streams.append(stream_key)
            
            for stream_key in dead_streams:
                self.logger.info(f"Cleaning up dead stream: {stream_key}")
                if stream_key in self.stream_manager.streams:
                    del self.stream_manager.streams[stream_key]
                if stream_key in self.active_streams:
                    del self.active_streams[stream_key]
            
            if dead_streams:
                self.stream_manager.streams_updated.emit()
                self.status_message.emit(f"Цэвэрлэгдсэн streams: {len(dead_streams)}", 2000)
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def _validate_stream_inputs(self) -> bool:
        """Validate stream inputs - ENHANCED VERSION"""
        try:
            if not hasattr(self, 'stream_key_input') or not self.stream_key_input:
                QMessageBox.critical(self, "UI Алдаа", "UI бүрэн ачааллагдаагүй байна.")
                return False
            
            stream_key = self.stream_key_input.text().strip()
            if not stream_key:
                self._generate_stream_key()
                stream_key = self.stream_key_input.text().strip()
                self.status_message.emit("Стримийн түлхүүр автоматаар үүсгэгдлээ", 2000)
            
            if len(stream_key) < 3:
                QMessageBox.warning(self, "Алдаа", "Стримийн түлхүүр дор хаяж 3 тэмдэгттэй байх ёстой.")
                return False
            
            # ✅ VALIDATE INPUT SOURCE
            if not self.current_input_source:
                self.current_input_source = "live:test_pattern"
                self.status_message.emit("Тест хэв маяг ашиглагдана", 2000)
            else:
                # Check if it's a file source
                if not self.current_input_source.startswith('live:'):
                    if not self._is_valid_media_file(self.current_input_source):
                        QMessageBox.critical(
                            self, 
                            "Медиа Файлын Алдаа", 
                            f"Сонгосон файл медиа файл биш байна:\n{self.current_input_source}\n\n"
                            "Шинэ медиа файл сонгох эсвэл Live source ашиглана уу."
                        )
                        return False
            
            # Validate server
            if not hasattr(self, 'server_combo') or not self.server_combo:
                QMessageBox.critical(self, "UI Алдаа", "Серверийн сонголт ачааллагдаагүй байна.")
                return False
                    
            server = self.server_combo.currentData()
            if not server:
                if self.server_combo.count() > 0:
                    self.server_combo.setCurrentIndex(0)
                    server = self.server_combo.currentData()
                    
                if not server:
                    QMessageBox.critical(self, "Серверийн Алдаа", 
                                    "Сервер сонгогдоогүй байна.\n\n"
                                    "Дараах алхмуудыг хийнэ үү:\n"
                                    "1. Сервер нэмэх товчийг дарж сервер нэмнэ үү\n"
                                    "2. Эсвэл серверийн удирдлагаас тохиргоо хийнэ үү")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            QMessageBox.critical(self, "Алдаа", f"Тохиргоог шалгахад алдаа гарлаа:\n{str(e)}")
            return False
    
    def _is_valid_media_file(self, file_path: str) -> bool:
        """Check if file is a valid media file"""
        try:
            from pathlib import Path
            
            if not file_path or not Path(file_path).exists():
                return False
            
            # Media file extensions
            media_extensions = {
                '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v',
                '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob', '.ts',
                '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'
            }
            
            file_ext = Path(file_path).suffix.lower()
            
            # Check extension
            if file_ext not in media_extensions:
                return False
            
            # Additional checks for Python files
            if file_ext == '.py' or 'init' in Path(file_path).name.lower():
                return False
            
            # Check file size (media files are usually larger than 1KB)
            if Path(file_path).stat().st_size < 1024:
                return False
                
            return True
            
        except Exception:
            return False

    def _get_media_file_info(self, file_path: str) -> dict:
        """Get media file information"""
        try:
            from pathlib import Path
            
            if not self._is_valid_media_file(file_path):
                return {'valid': False, 'error': 'Invalid media file'}
            
            file_info = Path(file_path).stat()
            
            return {
                'valid': True,
                'name': Path(file_path).name,
                'size': file_info.st_size,
                'size_mb': round(file_info.st_size / (1024 * 1024), 2),
                'extension': Path(file_path).suffix.lower(),
                'is_video': Path(file_path).suffix.lower() in {
                    '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'
                },
                'is_audio': Path(file_path).suffix.lower() in {
                    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'
                }
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def _set_optimal_video_quality(self):
        """Set optimal quality for video files"""
        if hasattr(self, 'quality_combo') and self.quality_combo:
            for i in range(self.quality_combo.count()):
                item_text = self.quality_combo.itemText(i)
                if "720p" in item_text or "HD" in item_text:
                    self.quality_combo.setCurrentIndex(i)
                    break

    def _set_optimal_audio_quality(self):
        """Set optimal quality for audio files"""
        if hasattr(self, 'quality_combo') and self.quality_combo:
            for i in range(self.quality_combo.count()):
                item_text = self.quality_combo.itemText(i)
                if "360p" in item_text:  # Lower quality for audio-only streams
                    self.quality_combo.setCurrentIndex(i)
                    break
    
    def _build_stream_config(self) -> Optional[StreamConfig]:
        """Build stream configuration from UI"""
        try:
            stream_key = self.stream_key_input.text().strip()
            
            if not hasattr(self, 'server_combo') or not self.server_combo:
                self.logger.error("Server combo not available")
                return None
                
            server = self.server_combo.currentData()
            if not server:
                self.logger.error("No server selected")
                return None
            
            quality = None
            if hasattr(self, 'quality_combo') and self.quality_combo:
                quality = self.quality_combo.currentData()
            
            if not quality:
                quality = QUALITY_PRESETS["720p"]
                self.logger.warning("Quality combo not available, using default 720p")
            
            encoder_key = "x264"
            if hasattr(self, 'encoder_combo') and self.encoder_combo:
                encoder_key = self.encoder_combo.currentData() or "x264"
            
            encoder = "libx264"
            if encoder_key in ENCODER_PRESETS:
                encoder = ENCODER_PRESETS[encoder_key]["encoder"]
            
            rate_control = "CBR"
            if hasattr(self, 'rate_control_combo') and self.rate_control_combo:
                rate_control = self.rate_control_combo.currentText() or "CBR"
            
            preset = "veryfast"
            if hasattr(self, 'preset_combo') and self.preset_combo:
                preset = self.preset_combo.currentText() or "veryfast"
            
            loop_input = False
            if hasattr(self, 'loop_input_cb') and self.loop_input_cb:
                loop_input = self.loop_input_cb.isChecked()
            
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
        """Test stream configuration"""
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
Бодит стримийг эхлүүлэхийн тулд "Стрим Эхлүүлэх" товчийг ашиглана уу."""
        
        QMessageBox.information(self, "Стримийн Тохиргооны Шалгалт", test_results)
    
    def _stop_selected_stream(self):
        """Stop the currently selected stream"""
        current = self.streams_table.currentIndex()
        if current.isValid():
            stream_key = self.stream_model.data(current, Qt.ItemDataRole.UserRole)
            if stream_key:
                self._stop_stream(stream_key)
    
    def _stop_stream(self, stream_key: str):
        """Stop a specific stream"""
        if self.stream_manager.stop_stream(stream_key):
            if stream_key in self.active_streams:
                del self.active_streams[stream_key]
            self.status_message.emit(f"Стрим зогсоосон: {stream_key}", 3000)
        else:
            self.status_message.emit(f"Стрим зогсоох амжилтгүй боллоо: {stream_key}", 5000)
    
    def _stop_all_streams(self):
        """Stop all active streams"""
        if not self.stream_manager.streams:
            return
        
        reply = QMessageBox.question(
            self,
            "Бүх Стримийг Зогсоох",
            "Та идэвхтэй байгаа бүх стримийг зогсоохдоо итгэлтэй байна уу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stream_manager.stop_all_streams()
            self.active_streams.clear()
            self.status_message.emit("Бүх стрим зогссон", 3000)
    
    def _restart_selected_stream(self):
        """Restart the currently selected stream"""
        current = self.streams_table.currentIndex()
        if current.isValid():
            stream_key = self.stream_model.data(current, Qt.ItemDataRole.UserRole)
            if stream_key and stream_key in self.active_streams:
                config = self.active_streams[stream_key]
                self._stop_stream(stream_key)
                
                QTimer.singleShot(1000, lambda: self.stream_manager.start_stream(config))
                self.status_message.emit(f"Стрим дахин эхлүүлж байна: {stream_key}", 3000)
    
    def _show_stream_info(self):
        """Show detailed stream information"""
        current = self.streams_table.currentIndex()
        if not current.isValid():
            return
        
        stream_key = self.stream_model.data(current, Qt.ItemDataRole.UserRole)
        if not stream_key or stream_key not in self.stream_manager.streams:
            return
        
        processor = self.stream_manager.streams[stream_key]
        config = processor.stream_config
        stats = processor.stats
        
        info_text = f"""Стримийн Мэдээлэл: {stream_key}

Тохиргоо:
• Сервер: {config.server.name}
• Хост: {config.server.host}:{config.server.rtmp_port}
• RTMP URL: {config.server.rtmp_url}
• Эх Сурвалж: {Path(config.input_source).name if not config.input_source.startswith('live:') else config.input_source}
• Чанар: {config.quality['name']}
• Нягтрал: {config.quality['width']}x{config.quality['height']}
• Кадр давтамж: {config.quality['fps']} fps
• Видео Кодлогч: {config.encoder}
• Аудио Кодлогч: {config.audio_encoder}
• Хурдны Хяналт: {config.rate_control}
• Урьдчилан Тохиргоо: {config.preset}

Статистик:
• Төлөв: {'Стриминг' if processor.is_running else 'Зогссон'}
• Ажилласан хугацаа: {processor.get_uptime()}
• Одоогийн FPS: {stats.get('fps', 0):.1f}
• Одоогийн Битрэйт: {stats.get('bitrate', 'N/A')}
• Боловсруулсан Кадр: {stats.get('frames_processed', 0)}
• Алгассан Кадр: {stats.get('dropped_frames', 0)}

Нэмэлт Тохиргоо:
• Оролтыг давтах: {'Тийм' if config.loop_input else 'Үгүй'}
• Эхлэх хугацаа: {config.start_time or 'Тохируулаагүй'}
• Үргэлжлэх хугацаа: {config.duration or 'Хязгааргүй'}
• Гарын Аргаар Нэмэлт Аргумент: {', '.join(config.custom_ffmpeg_args) if config.custom_ffmpeg_args else 'Байхгүй'}"""
        
        QMessageBox.information(self, f"Стримийн Мэдээлэл - {stream_key}", info_text)
    
    def _on_stream_selection_changed(self, current, previous):
        """Handle stream selection change"""
        if current.isValid():
            stream_key = self.stream_model.data(current, Qt.ItemDataRole.UserRole)
            if stream_key and stream_key in self.stream_manager.streams:
                processor = self.stream_manager.streams[stream_key]
                config = processor.stream_config
                stats = processor.stats
                
                self.selected_stream_label.setText(stream_key)
                self.stream_server_label.setText(config.server.name)
                self.stream_quality_label.setText(config.quality['name'])
                self.stream_fps_label.setText(f"{stats.get('fps', 0):.1f}")
                self.stream_bitrate_label.setText(stats.get('bitrate', 'N/A'))
                self.stream_uptime_label.setText(processor.get_uptime())
                
                self.stop_btn.setEnabled(True)
                if hasattr(self, 'restart_stream_btn'):
                    self.restart_stream_btn.setEnabled(True)
                if hasattr(self, 'stream_info_btn'):
                    self.stream_info_btn.setEnabled(True)
                if hasattr(self, 'apply_quality_btn'):
                    self.apply_quality_btn.setEnabled(False)
        else:
            # Clear details
            self.selected_stream_label.setText("Байхгүй")
            self.stream_server_label.setText("-")
            self.stream_quality_label.setText("-")
            self.stream_fps_label.setText("-")
            self.stream_bitrate_label.setText("-")
            self.stream_uptime_label.setText("-")
            
            # Disable controls
            self.stop_btn.setEnabled(False)
            if hasattr(self, 'restart_stream_btn'):
                self.restart_stream_btn.setEnabled(False)
            if hasattr(self, 'stream_info_btn'):
                self.stream_info_btn.setEnabled(False)
            if hasattr(self, 'apply_quality_btn'):
                self.apply_quality_btn.setEnabled(False)
    
    def _on_live_quality_changed(self, quality_name: str):
        """Handle live quality change selection"""
        current = self.streams_table.currentIndex()
        if current.isValid() and hasattr(self, 'apply_quality_btn'):
            self.apply_quality_btn.setEnabled(True)
    
    def _apply_quality_change(self):
        """Apply quality change to selected stream"""
        current = self.streams_table.currentIndex()
        if not current.isValid():
            return
        
        stream_key = self.stream_model.data(current, Qt.ItemDataRole.UserRole)
        quality_data = self.live_quality_combo.currentData()
        
        if not stream_key or not quality_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Чанар Өөрчлөх",
            f"Стрим '{stream_key}'-ийн чанарыг '{quality_data['name']}' болгон өөрчлөх үү?\n\n"
            "Энэ үйлдэл стримийг түр зогсоож дахин эхлүүлнэ.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if stream_key in self.active_streams:
                config = self.active_streams[stream_key]
                config.quality = quality_data
                
                self._stop_stream(stream_key)
                QTimer.singleShot(2000, lambda: self.stream_manager.start_stream(config))
                
                self.status_message.emit(f"Стримийн чанар өөрчлөгдөж байна: {stream_key}", 3000)
                if hasattr(self, 'apply_quality_btn'):
                    self.apply_quality_btn.setEnabled(False)
    
    def _on_stream_started(self, stream_key: str):
        """Handle stream started"""
        self.status_message.emit(f"Стрим эхэллээ: {stream_key}", 3000)
        self._update_controls_state()
        self._update_stats()
    
    def _on_stream_stopped(self, stream_key: str):
        """Handle stream stopped"""
        self.status_message.emit(f"Стрим зогссон: {stream_key}", 3000)
        
        if stream_key in self.active_streams:
            del self.active_streams[stream_key]
        
        self._update_controls_state()
        self._update_stats()
    
    def _on_stream_error(self, stream_key: str, error_message: str):
        """Handle stream error"""
        self.logger.error(f"Stream error for {stream_key}: {error_message}")
        self.status_message.emit(f"Стримийн алдаа: {stream_key}", 5000)
        
        # Show detailed error if it's a critical issue
        if any(critical in error_message.lower() for critical in 
               ['connection refused', 'timeout', 'failed to start', 'cannot open']):
            QMessageBox.critical(
                self,
                f"Стримийн Алдаа - {stream_key}",
                f"Стримд алдаа гарлаа:\n\n{error_message}\n\n"
                "Серверийн холболт болон тохиргоог шалгана уу."
            )
    
    def _update_controls_state(self):
        """Update controls state based on active streams"""
        has_streams = len(self.stream_manager.streams) > 0
        has_selection = self.streams_table.currentIndex().isValid()
        
        self.stop_all_btn.setEnabled(has_streams)
        self.stop_btn.setEnabled(has_selection)
        
        if hasattr(self, 'restart_stream_btn'):
            self.restart_stream_btn.setEnabled(has_selection)
        if hasattr(self, 'stream_info_btn'):
            self.stream_info_btn.setEnabled(has_selection)

    def handle_playout_command(self, command, params=None):
        """Handle commands from playout tab"""
        try:
            if command == "load_and_stream":
                if params and "file_path" in params:
                    return self.load_and_start_stream(params["file_path"])
            elif command == "stop_program_streams":
                return self.stop_program_streams()
            elif command == "get_stream_status":
                return self.get_program_stream_status()
            elif command == "take_to_air":
                if params and "file_path" in params:
                    return self._on_media_taken_to_air(params["file_path"])
            else:
                return {"error": f"Unknown playout command: {command}"}
                
        except Exception as e:
            return {"error": f"Playout command failed: {str(e)}"}

    def get_program_stream_status(self):
        """Get status of program streaming"""
        try:
            program_streams = []
            
            for stream_key, processor in self.stream_manager.streams.items():
                if "program" in stream_key.lower():
                    stream_info = {
                        'key': stream_key,
                        'file': processor.stream_config.input_source,
                        'server': processor.stream_config.server.name,
                        'quality': processor.stream_config.quality['name'],
                        'is_running': processor.is_running,
                        'uptime': processor.get_uptime(),
                        'fps': processor.stats.get('fps', 0),
                        'bitrate': processor.stats.get('bitrate', '0kbits/s')
                    }
                    program_streams.append(stream_info)
            
            return {
                'is_streaming': len(program_streams) > 0,
                'stream_count': len(program_streams),
                'streams': program_streams
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get program stream status: {e}")
            return {'is_streaming': False, 'stream_count': 0, 'streams': []}

    def _toggle_auto_stream(self, enabled: bool):
        """Toggle auto-streaming mode"""
        try:
            self.auto_stream_enabled = enabled
            status = "enabled" if enabled else "disabled"
            self.status_message.emit(f"Auto-streaming {status}", 2000)
            
            if enabled:
                # Check if we should start streaming now
                self._check_immediate_stream_start()
            
        except Exception as e:
            self.logger.error(f"Failed to toggle auto-stream: {e}")

    def _on_program_quality_changed(self, quality_name: str):
        """Handle program quality change"""
        try:
            # Find quality key
            for quality_key, quality_data in QUALITY_PRESETS.items():
                if quality_data["name"] == quality_name:
                    self.program_stream_quality = quality_key
                    break
            
            # Update active program streams if any
            if self.is_program_streaming_active:
                self._update_program_stream_quality()
                
        except Exception as e:
            self.logger.error(f"Failed to change program quality: {e}")

    def _manual_start_program_stream(self):
        """Manually start program streaming"""
        try:
            if hasattr(self, 'playout_tab_ref') and self.playout_tab_ref:
                current_state = self.playout_tab_ref.get_current_state()
                program_info = current_state.get('program')
                
                if program_info and program_info.get('file'):
                    file_path = program_info['file']
                    source_info = {
                        'file_path': file_path,
                        'loop': True
                    }
                    
                    success = self.start_live_program_stream(source_info)
                    if success:
                        self.status_message.emit("Program streaming started manually", 3000)
                    else:
                        self.status_message.emit("Failed to start program streaming", 3000)
                else:
                    QMessageBox.warning(self, "No Program Content", 
                                    "No program content loaded in playout tab.")
            else:
                QMessageBox.warning(self, "Playout Connection", 
                                "Not connected to playout tab.")
                
        except Exception as e:
            self.logger.error(f"Manual program stream start failed: {e}")

    def _check_immediate_stream_start(self):
        """Check if we should start streaming immediately"""
        try:
            if not hasattr(self, 'playout_tab_ref') or not self.playout_tab_ref:
                return
            
            current_state = self.playout_tab_ref.get_current_state()
            
            # Start streaming if program is on air
            if (current_state.get('on_air', False) and 
                not self.is_program_streaming_active):
                
                program_info = current_state.get('program')
                if program_info and program_info.get('file'):
                    self.update_program_content(program_info['file'], auto_start=True)
                    
        except Exception as e:
            self.logger.error(f"Immediate stream start check failed: {e}")

    def _update_program_stream_quality(self):
        """Update quality of active program streams"""
        try:
            program_streams = []
            for stream_key in list(self.stream_manager.streams.keys()):
                if "program" in stream_key.lower():
                    program_streams.append(stream_key)
            
            if program_streams:
                reply = QMessageBox.question(
                    self, "Update Stream Quality",
                    f"Update quality of {len(program_streams)} program stream(s) to {self.program_stream_quality}?\n\n"
                    "This will restart the streams.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    for stream_key in program_streams:
                        if stream_key in self.active_streams:
                            config = self.active_streams[stream_key]
                            config.quality = self._get_program_quality_config()
                            
                            # Restart with new quality
                            self._stop_stream(stream_key)
                            QTimer.singleShot(1000, lambda sk=stream_key, cfg=config: 
                                            self.stream_manager.start_stream(cfg))
                    
                    self.status_message.emit("Program stream quality updated", 3000)
                    
        except Exception as e:
            self.logger.error(f"Failed to update program stream quality: {e}")
    
    def _update_stats(self):
        """Update general statistics"""
        try:
            active_count = len(self.stream_manager.streams)
            self.total_streams_label.setText(str(active_count))
            
            total_bitrate = 0
            total_latency = 0
            latency_count = 0
            
            for processor in self.stream_manager.streams.values():
                # Calculate total bitrate
                bitrate_str = processor.stats.get('bitrate', '0kbits/s')
                try:
                    if 'kbits/s' in bitrate_str:
                        bitrate_value = float(bitrate_str.replace('kbits/s', ''))
                        total_bitrate += bitrate_value
                except (ValueError, AttributeError):
                    pass
            
            self.total_bitrate_label.setText(f"{total_bitrate:.0f} kbps")
            self.estimated_bandwidth_label.setText(f"{total_bitrate/1000:.1f} Mbps")
            
            # Network optimization status
            if OPTIMIZED_STREAMING_AVAILABLE:
                self.optimization_status_label.setText("✅ Идэвхтэй")
                self.optimization_status_label.setStyleSheet("color: #28a745;")
            else:
                self.optimization_status_label.setText("⚠️ Үндсэн")
                self.optimization_status_label.setStyleSheet("color: #ffc107;")
            
            # Update reconnect count (placeholder)
            self.reconnect_count_label.setText("0")
            
            # Update network latency (placeholder)
            self.network_latency_label.setText("< 50ms")
            
        except Exception as e:
            self.logger.error(f"Failed to update stats: {e}")
    
    def get_active_streams(self) -> Dict[str, StreamConfig]:
        """Get active streams for external access"""
        return self.active_streams.copy()
    
    def is_streaming_active(self) -> bool:
        """Check if any stream is active"""
        return len(self.stream_manager.streams) > 0
    
    def stop_all_streams_external(self):
        """External method to stop all streams"""
        self._stop_all_streams()
    
    def get_stream_status(self, stream_key: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific stream"""
        if stream_key in self.stream_manager.streams:
            processor = self.stream_manager.streams[stream_key]
            return {
                'running': processor.is_running,
                'uptime': processor.get_uptime(),
                'stats': processor.stats.copy(),
                'config': processor.stream_config.to_dict()
            }
        return None
    
    def export_stream_logs(self):
        """Export stream logs to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stream_logs_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Стримийн логийг хадгалах",
                filename,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Стримийн Лог Экспорт - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    # Active streams
                    f.write("Идэвхтэй Стримүүд:\n")
                    f.write("-" * 30 + "\n")
                    
                    for stream_key, processor in self.stream_manager.streams.items():
                        config = processor.stream_config
                        stats = processor.stats
                        
                        f.write(f"Стримийн Түлхүүр: {stream_key}\n")
                        f.write(f"Сервер: {config.server.name}\n")
                        f.write(f"Чанар: {config.quality['name']}\n")
                        f.write(f"Төлөв: {'Стриминг' if processor.is_running else 'Зогссон'}\n")
                        f.write(f"Ажилласан хугацаа: {processor.get_uptime()}\n")
                        f.write(f"FPS: {stats.get('fps', 0):.1f}\n")
                        f.write(f"Битрэйт: {stats.get('bitrate', 'N/A')}\n")
                        f.write("\n")
                    
                    # Server configurations
                    f.write("Серверийн Тохиргоо:\n")
                    f.write("-" * 30 + "\n")
                    
                    for server_id, server_config in self.servers.items():
                        f.write(f"ID: {server_id}\n")
                        f.write(f"Нэр: {server_config.name}\n")
                        f.write(f"Хост: {server_config.host}:{server_config.port}\n")
                        f.write(f"RTMP: {server_config.rtmp_port}\n")
                        f.write(f"SSL: {server_config.ssl_enabled}\n")
                        f.write(f"Тайлбар: {server_config.description}\n")
                        f.write("\n")
                
                self.status_message.emit(f"Лог хадгалагдлаа: {Path(file_path).name}", 4000)
                self.logger.info(f"Exported stream logs to: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
            QMessageBox.critical(
                self,
                "Экспортын Алдаа",
                f"Логийг экспорт хийхэд алдаа гарлаа:\n\n{str(e)}"
            )
    
    def import_stream_preset(self):
        """Import stream preset configuration"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Стримийн урьдчилан тохиргоо импорт хийх",
                str(Path.home()),
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)
                
                # Apply preset to current configuration
                if 'quality' in preset_data:
                    quality_name = preset_data['quality']
                    for i in range(self.quality_combo.count()):
                        if quality_name in self.quality_combo.itemText(i):
                            self.quality_combo.setCurrentIndex(i)
                            break
                
                if 'encoder' in preset_data:
                    encoder_name = preset_data['encoder']
                    for i in range(self.encoder_combo.count()):
                        if encoder_name in self.encoder_combo.itemText(i):
                            self.encoder_combo.setCurrentIndex(i)
                            break
                
                if 'rate_control' in preset_data:
                    self.rate_control_combo.setCurrentText(preset_data['rate_control'])
                
                if 'preset' in preset_data:
                    self.preset_combo.setCurrentText(preset_data['preset'])
                
                if 'loop_input' in preset_data:
                    self.loop_input_cb.setChecked(preset_data['loop_input'])
                
                self.status_message.emit("Урьдчилан тохиргоо ачааллагдлаа", 3000)
                self.logger.info(f"Imported stream preset from: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to import preset: {e}")
            QMessageBox.critical(
                self,
                "Импортын Алдаа",
                f"Урьдчилан тохиргоог импорт хийхэд алдаа гарлаа:\n\n{str(e)}"
            )
    
    def export_stream_preset(self):
        """Export current stream configuration as preset"""
        try:
            preset_data = {
                'name': 'Custom Preset',
                'description': 'Exported from TV Stream',
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
                "Стримийн урьдчилан тохиргоог хадгалах",
                filename,
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, indent=2, ensure_ascii=False)
                
                self.status_message.emit(f"Урьдчилан тохиргоо хадгалагдлаа: {Path(file_path).name}", 4000)
                self.logger.info(f"Exported stream preset to: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to export preset: {e}")
            QMessageBox.critical(
                self,
                "Экспортын Алдаа",
                f"Урьдчилан тохиргоог экспорт хийхэд алдаа гарлаа:\n\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """Handle close event"""
        try:
            if self.stream_manager.streams:
                reply = QMessageBox.question(
                    self,
                    "Програм хаах",
                    f"Идэвхтэй {len(self.stream_manager.streams)} стрим байна.\n\n"
                    "Стримүүдийг зогсоож програмыг хаах уу?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.stream_manager.stop_all_streams()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
                
        except Exception as e:
            self.logger.error(f"Close event error: {e}")
            event.accept()

# =============================================================================
# ADDITIONAL UTILITY FUNCTIONS
# =============================================================================

def check_system_resources() -> Dict[str, Any]:
    """Check system resources for streaming"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_usage': cpu_percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_free': disk.free,
            'disk_percent': (disk.used / disk.total) * 100
        }
    except ImportError:
        return {
            'cpu_usage': 0,
            'memory_total': 0,
            'memory_available': 0,
            'memory_percent': 0,
            'disk_total': 0,
            'disk_free': 0,
            'disk_percent': 0
        }

def get_network_interfaces() -> List[Dict[str, str]]:
    """Get available network interfaces"""
    try:
        import psutil
        
        interfaces = []
        for interface_name, interface_addresses in psutil.net_if_addrs().items():
            for address in interface_addresses:
                if address.family == 2:  # AF_INET (IPv4)
                    interfaces.append({
                        'name': interface_name,
                        'ip': address.address,
                        'netmask': address.netmask
                    })
        return interfaces
    except ImportError:
        return [{'name': 'Unknown', 'ip': '127.0.0.1', 'netmask': '255.0.0.0'}]

def validate_rtmp_url(url: str) -> bool:
    """Validate RTMP URL format"""
    try:
        import re
        pattern = r'^rtmps?://[a-zA-Z0-9.-]+:[0-9]+(/.*)?$'
        return bool(re.match(pattern, url))
    except ImportError:
        return url.startswith(('rtmp://', 'rtmps://'))

def estimate_bandwidth_requirement(quality: Dict[str, Any]) -> float:
    """Estimate bandwidth requirement in Mbps"""
    try:
        video_bitrate = int(quality.get('video_bitrate', '1000k').replace('k', ''))
        audio_bitrate = int(quality.get('audio_bitrate', '128k').replace('k', ''))
        
        total_kbps = video_bitrate + audio_bitrate
        # Add 20% overhead for stability
        total_kbps *= 1.2
        
        return total_kbps / 1000  # Convert to Mbps
    except (ValueError, KeyError):
        return 1.0  # Default 1 Mbps

# =============================================================================
# EXPORT FOR INTEGRATION
# =============================================================================

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

# =============================================================================
# MAIN EXECUTION (FOR TESTING)
# =============================================================================

if __name__ == "__main__":
    """Test the streaming tab standalone"""
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("TV Stream - Streaming Tab")
    app.setApplicationVersion("2.0.0")
    
    # Create a simple test window
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("TV Stream - Streaming Tab Test v2.0")
            self.setGeometry(100, 100, 1200, 800)
            
            # Create test config manager
            class TestConfigManager:
                def __init__(self):
                    self.servers = {}
                
                def get_servers(self):
                    return self.servers
                
                def set_servers(self, servers):
                    self.servers = servers
            
            # Create streaming tab
            self.config_manager = TestConfigManager()
            self.streaming_tab = StreamingTab(self.config_manager)
            self.setCentralWidget(self.streaming_tab)
            
            # Create status bar
            self.status_bar = self.statusBar()
            self.streaming_tab.status_message.connect(
                lambda msg, timeout: self.status_bar.showMessage(msg, timeout)
            )
            
            # Create menu bar
            self.create_menu_bar()
        
        def create_menu_bar(self):
            """Create menu bar for testing"""
            menubar = self.menuBar()
            
            # Stream menu
            stream_menu = menubar.addMenu('Стрим')
            
            # Add test stream action
            test_action = QAction('Тест Стрим Эхлүүлэх', self)
            test_action.triggered.connect(self.start_test_stream)
            stream_menu.addAction(test_action)
            
            # Stop all action
            stop_action = QAction('Бүх Стримийг Зогсоох', self)
            stop_action.triggered.connect(self.streaming_tab.stop_all_streams_external)
            stream_menu.addAction(stop_action)
            
            stream_menu.addSeparator()
            
            # Export logs
            export_action = QAction('Лог Экспорт', self)
            export_action.triggered.connect(self.streaming_tab.export_stream_logs)
            stream_menu.addAction(export_action)
            
            # Import/Export presets
            preset_menu = menubar.addMenu('Урьдчилан Тохиргоо')
            
            import_preset_action = QAction('Импорт', self)
            import_preset_action.triggered.connect(self.streaming_tab.import_stream_preset)
            preset_menu.addAction(import_preset_action)
            
            export_preset_action = QAction('Экспорт', self)
            export_preset_action.triggered.connect(self.streaming_tab.export_stream_preset)
            preset_menu.addAction(export_preset_action)
            
            # Help menu
            help_menu = menubar.addMenu('Тусламж')
            
            about_action = QAction('Програмын тухай', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        
        def start_test_stream(self):
            """Start a test stream"""
            try:
                # Configure test stream
                if hasattr(self.streaming_tab, 'source_type_combo'):
                    self.streaming_tab.source_type_combo.setCurrentText("Тест Хэв маяг")
                
                if hasattr(self.streaming_tab, 'stream_key_input'):
                    self.streaming_tab.stream_key_input.setText("test_stream")
                
                # Trigger start stream
                if hasattr(self.streaming_tab, '_start_stream'):
                    self.streaming_tab._start_stream()
            except Exception as e:
                QMessageBox.warning(self, "Тест Алдаа", f"Тест стрим эхлүүлэхэд алдаа гарлаа:\n{str(e)}")
        
        def show_about(self):
            """Show about dialog"""
            QMessageBox.about(
                self,
                "Програмын тухай",
                "TV Stream - Professional Broadcasting Software\n\n"
                "Streaming Tab v2.0\n"
                "Developed with PyQt6 and FFmpeg\n\n"
                "Features:\n"
                "• Multi-server streaming support\n"
                "• Real-time stream monitoring\n"
                "• Quality presets and encoder options\n"
                "• Network optimization\n"
                "• Stream reconnection\n"
                "• Import/Export configurations\n\n"
                "© 2024 TV Stream Team"
            )
    
    # Apply dark theme for better appearance
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
    
    # Create and show main window
    window = TestWindow()
    window.show()
    
    # Print completion message
    print("=" * 60)
    print("🎉 STREAMING TAB БҮРЭН ДУУСГАГДЛАА!")
    print("=" * 60)
    print("✅ Бүх функциональууд:")
    print("  • Professional streaming interface")
    print("  • Multi-server support with storage")
    print("  • Real-time stream monitoring")
    print("  • Quality presets and encoder options")
    print("  • Network optimization (if available)")
    print("  • Stream reconnection support")
    print("  • Import/Export functionality")
    print("  • Playout integration ready")
    print("  • Comprehensive error handling")
    print("  • Fallback mechanisms")
    print("  • Dark theme support")
    print("=" * 60)
    print("🚀 Application started successfully!")
    print("💡 Test the streaming functionality with the menu options")
    print("📝 Check logs for detailed information")
    print("=" * 60)
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)