"""
TV Stream - Utility Functions
Core utilities for streaming functionality
"""

import os
import json
import time
import socket
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any


class MediaValidator:
    """Media file validation utility"""
    
    MEDIA_EXTENSIONS = {
        '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm',
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'
    }
    
    _validation_cache = {}
    
    @classmethod
    def is_valid_media_file(cls, file_path: str) -> bool:
        """Check if file is a valid media file"""
        if file_path in cls._validation_cache:
            return cls._validation_cache[file_path]
        
        try:
            if not file_path or not Path(file_path).exists():
                result = False
            else:
                file_ext = Path(file_path).suffix.lower()
                result = file_ext in cls.MEDIA_EXTENSIONS and Path(file_path).stat().st_size > 1024
            
            cls._validation_cache[file_path] = result
            return result
        except Exception:
            cls._validation_cache[file_path] = False
            return False
    
    @classmethod
    def get_media_file_info(cls, file_path: str) -> dict:
        """Get media file information"""
        try:
            if not cls.is_valid_media_file(file_path):
                return {'valid': False, 'error': 'Invalid media file'}
            
            file_info = Path(file_path).stat()
            return {
                'valid': True,
                'name': Path(file_path).name,
                'size': file_info.st_size,
                'size_mb': round(file_info.st_size / (1024 * 1024), 2),
                'path': str(file_path)
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class LoggerManager:
    """Logger management utility"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str):
        """Get or create logger"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
            cls._loggers[name] = logger
        return cls._loggers[name]


class StreamingUtils:
    """Streaming utilities"""
    
    @staticmethod
    def generate_stream_key(prefix: str = "stream") -> str:
        """Generate unique stream key"""
        import random
        timestamp = int(time.time())
        random_part = random.randint(1000, 9999)
        return f"{prefix}_{timestamp}_{random_part}"
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate HH:MM:SS time format"""
        try:
            import re
            pattern = r'^\d{1,2}:\d{2}:\d{2}$'
            return bool(re.match(pattern, time_str))
        except Exception:
            return False
    
    @staticmethod
    def format_uptime(seconds: int) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class NetworkUtils:
    """Network utilities"""
    
    @staticmethod
    def test_connection(host: str, port: int, timeout: int = 3) -> bool:
        """Test network connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def validate_rtmp_url(url: str) -> bool:
        """Validate RTMP URL format"""
        return url.startswith(('rtmp://', 'rtmps://'))


class ErrorHandler:
    """Error handling utility"""
    
    @staticmethod
    def safe_execute(func, error_msg="Operation failed", logger=None):
        """Safely execute function with error handling"""
        try:
            return func()
        except Exception as e:
            if logger:
                logger.error(f"{error_msg}: {e}")
            return None


# Backward compatibility functions
def get_logger(name: str):
    return LoggerManager.get_logger(name)

def is_valid_media_file(file_path: str) -> bool:
    return MediaValidator.is_valid_media_file(file_path)
