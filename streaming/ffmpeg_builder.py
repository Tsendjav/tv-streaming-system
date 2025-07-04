"""
TV Stream - FFmpeg Command Builder
FFmpeg command generation and validation
"""

import shutil
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

# Safe imports
try:
    from .utils import MediaValidator, LoggerManager
except ImportError:
    try:
        from utils import MediaValidator, LoggerManager
    except ImportError:
        # Fallback implementations
        import logging
        
        class LoggerManager:
            @classmethod
            def get_logger(cls, name): return logging.getLogger(name)
        
        class MediaValidator:
            @classmethod
            def is_valid_media_file(cls, file_path): return True


class FFmpegCommandBuilder:
    """FFmpeg command builder"""
    
    def __init__(self, stream_config, logger=None):
        self.config = stream_config
        self.logger = logger or LoggerManager.get_logger(__name__)
        self.validator = MediaValidator()
    
    def build_command(self) -> List[str]:
        """Build complete FFmpeg command"""
        try:
            cmd = ["ffmpeg", "-y", "-hide_banner"]
            
            # Input parameters
            if hasattr(self.config, 'input_source'):
                if self.config.input_source.startswith("live:"):
                    cmd.extend(["-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30"])
                else:
                    cmd.extend(["-i", self.config.input_source])
            
            # Video encoding
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-b:v", "2500k",
                "-s", "1280x720",
                "-r", "30"
            ])
            
            # Audio encoding
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100"
            ])
            
            # Output
            if hasattr(self.config, 'server') and hasattr(self.config, 'stream_key'):
                rtmp_url = f"{self.config.server.rtmp_url}/{self.config.stream_key}"
                cmd.extend(["-f", "flv", rtmp_url])
            
            return cmd
            
        except Exception as e:
            self.logger.error(f"Failed to build FFmpeg command: {e}")
            return []
    
    def validate_command(self) -> bool:
        """Validate command"""
        cmd = self.build_command()
        return len(cmd) > 0 and "-i" in cmd
    
    def get_command_string(self) -> str:
        """Get command as string"""
        cmd = self.build_command()
        return ' '.join(cmd) if cmd else ""


class FFmpegValidator:
    """FFmpeg validation utilities"""
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if FFmpeg is available"""
        try:
            return shutil.which('ffmpeg') is not None
        except Exception:
            return False
    
    @staticmethod
    def get_ffmpeg_version() -> Optional[str]:
        """Get FFmpeg version"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                first_line = result.stdout.split('\n')[0]
                return first_line
            
        except Exception:
            pass
        
        return None
