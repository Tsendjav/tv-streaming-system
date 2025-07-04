# tv_streaming_system/core/constants.py
#!/usr/bin/env python3
"""
Application Constants
Contains all constant values used throughout the application
"""

from pathlib import Path
from typing import Dict, List, Set

# models.stream_quality-г core-руу шилжүүлсэн тул импортыг өөрчилсөн.
try:
    from models.stream_quality import StreamQuality
except ImportError:
    # Fallback for development if models not yet structured
    class StreamQuality:
        def __init__(self, name, resolution, bitrate, framerate):
            self.name = name
            self.resolution = resolution
            self.bitrate = bitrate
            self.framerate = framerate
        def __str__(self):
            return self.name

# ===== Application Information =====
APP_NAME = "Professional Streaming Studio"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "Streaming Studio Corp"
APP_DESCRIPTION = "Professional streaming and playout software inspired by CasparCG, OpenBroadcaster, and AzuraCast"

# ===== File Extensions =====
SUPPORTED_VIDEO_EXTENSIONS: Set[str] = {
    '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm',
    '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.m2ts'
}

SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
    '.opus', '.aiff', '.au', '.ra'
}

SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tga',
    '.webp', '.svg', '.ico'
}

SUPPORTED_SUBTITLE_EXTENSIONS: Set[str] = {
    '.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx'
}

ALL_MEDIA_EXTENSIONS = (
    SUPPORTED_VIDEO_EXTENSIONS |
    SUPPORTED_AUDIO_EXTENSIONS |
    SUPPORTED_IMAGE_EXTENSIONS |
    SUPPORTED_SUBTITLE_EXTENSIONS
)

# ===== Default Directories =====
DEFAULT_DIRECTORIES: Dict[str, str] = {
    "data": "data",
    "media": "data/media",
    "logs": "data/logs",
    "backups": "data/backups",
    "plugins": "plugins",
    "cache": "data/cache",
    "temp": "data/temp"
}

# ===== UI Constants =====
UI_THEMES: List[str] = ["Dark", "Light", "System"] # Add more as needed
DEFAULT_UI_THEME: str = "Dark"
APP_ICON_PATH: Path = Path("assets/icons/app_icon.png") # Placeholder path
SPLASH_SCREEN_PATH: Path = Path("assets/images/splash_screen.png") # Placeholder path

# ===== Streaming Constants =====
DEFAULT_STREAM_QUALITY: StreamQuality = StreamQuality("720p", "1280x720", "2500k", "30")
AVAILABLE_STREAM_QUALITIES: List[StreamQuality] = [
    StreamQuality("240p", "426x240", "500k", "25"),
    StreamQuality("360p", "640x360", "800k", "25"),
    StreamQuality("480p", "854x480", "1200k", "25"),
    StreamQuality("720p", "1280x720", "2500k", "30"),
    StreamQuality("1080p", "1920x1080", "4500k", "30"),
    StreamQuality("1080p60", "1920x1080", "6000k", "60"),
    StreamQuality("4K", "3840x2160", "10000k", "30"),
]

FFMPEG_ENCODER_PRESETS: Dict[str, str] = {
    "software": "libx264",
    "nvidia": "h264_nvenc",
    "amd": "h264_amf",
    "intel": "h264_qsv"
}

DEFAULT_AUDIO_BITRATE: str = "128k" # Common audio bitrates
AVAILABLE_AUDIO_BITRATES: List[str] = ["64k", "96k", "128k", "192k", "256k", "320k"]

# ===== Audio Constants =====
SAMPLE_RATE: int = 48000  # Common sample rate for audio (Hz)
AUDIO_BUFFER_SIZE: int = 1024  # Number of frames per audio buffer


# ===== Logging Constants =====
LOG_LEVELS: List[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL: str = "INFO"
MAX_LOG_FILE_SIZE_MB: int = 10 # 10 MB per log file
MAX_LOG_FILES: int = 5 # Keep last 5 log files

# ===== AMCP Protocol Constants =====
AMCP_DEFAULT_HOST: str = "localhost"
AMCP_DEFAULT_PORT: int = 5250
AMCP_DEFAULT_TIMEOUT: int = 5

# ===== Messages and Notifications =====
MESSAGES: Dict[str, str] = {
    "app_started": "Application started successfully (Version {version})",
    "app_shutdown": "Application shutting down.",
    "error_loading_config": "Failed to load configuration: {error}",
    "error_saving_config": "Failed to save configuration: {error}",
    "error_initializing_module": "Failed to initialize {module}: {error}",
    "connection_error": "Connection to {server} failed: {error}",
    "connection_established": "Connected to {server}",
    "stream_started": "Stream started: {key}",
    "config_saved": "Configuration saved successfully",
    "plugin_loaded": "Plugin loaded: {plugin}",
    "media_imported": "Media imported: {count} files",
    "backup_created": "Backup created: {path}",
    "server_added": "Server added: {name}"
}

# ===== Performance Constants =====
PERFORMANCE_LIMITS: Dict[str, int] = {
    "max_concurrent_streams": 10,
    "max_playlist_items": 10000,
    "max_media_files": 50000,
    "max_log_entries": 100000,
    "media_scan_batch_size": 100,
    "thumbnail_generation_workers": 4,
    "max_undo_history": 50
}

# ===== Keyboard Shortcuts =====
KEYBOARD_SHORTCUTS: Dict[str, str] = {
    "play": "Space",
    "stop": "S",
    "pause": "P",
    "next": "Ctrl+Right",
    "previous": "Ctrl+Left",
    "volume_up": "Ctrl+Up",
    "volume_down": "Ctrl+Down",
    "mute": "M",
    "fullscreen": "F11",
    "refresh": "F5",
    "new_playlist": "Ctrl+N",
    "open_file": "Ctrl+O",
    "save": "Ctrl+S",
    "exit": "Ctrl+Q"
}