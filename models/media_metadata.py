#!/usr/bin/env python3
"""
models/media_metadata.py - Fixed Version
Media Metadata Models with corrected exists() method and enhanced functionality
"""

import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class MediaType(Enum):
    """Media file types"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SUBTITLE = "subtitle"
    UNKNOWN = "unknown"


class PlaybackState(Enum):
    """Media playback states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class MediaMetadata:
    """Enhanced metadata for media files"""
    
    # Basic metadata
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    
    # Technical metadata
    duration: Optional[float] = None  # seconds
    bitrate: Optional[int] = None     # kbps
    sample_rate: Optional[int] = None # Hz
    channels: Optional[int] = None
    codec: Optional[str] = None
    
    # Video specific
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    aspect_ratio: Optional[str] = None
    video_codec: Optional[str] = None
    
    # Content metadata
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    language: Optional[str] = None
    copyright_info: Optional[str] = None
    
    # Media management
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0  # 0-5 stars
    play_count: int = 0
    last_played: Optional[datetime] = None
    date_added: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # File metadata
    file_size: int = 0  # bytes
    checksum: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure keywords and tags are lists
        if isinstance(self.keywords, str):
            self.keywords = [k.strip() for k in self.keywords.split(',')]
        if isinstance(self.tags, str):
            self.tags = [t.strip() for t in self.tags.split(',')]
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string (MM:SS or HH:MM:SS)"""
        if not self.duration:
            return "00:00"
        
        total_seconds = int(self.duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size"""
        if not self.file_size:
            return "0 B"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "year": self.year,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "description": self.description,
            "keywords": self.keywords.copy(),
            "category": self.category,
            "tags": self.tags.copy(),
            "rating": self.rating,
            "play_count": self.play_count,
            "last_played": self.last_played.isoformat() if self.last_played else None,
            "date_added": self.date_added.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "file_size": self.file_size,
            "checksum": self.checksum,
            "custom_fields": self.custom_fields.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaMetadata':
        """Create instance from dictionary"""
        # Handle datetime fields
        datetime_fields = ["last_played", "date_added", "last_modified"]
        for field in datetime_fields:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        # Ensure lists
        if "keywords" not in data:
            data["keywords"] = []
        if "tags" not in data:
            data["tags"] = []
        if "custom_fields" not in data:
            data["custom_fields"] = {}
        
        return cls(**data)


@dataclass
class MediaFile:
    """Media file with metadata and management information - FIXED VERSION"""
    
    file_path: Path
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    media_type: MediaType = MediaType.UNKNOWN
    mime_type: str = ""
    id: str = ""
    
    # File state
    last_modified: Optional[datetime] = None
    last_scanned: Optional[datetime] = None
    
    # Playback state
    playback_state: PlaybackState = PlaybackState.STOPPED
    current_position: float = 0.0  # seconds
    
    # Import information
    import_source: Optional[str] = None
    import_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization processing"""
        self.file_path = Path(self.file_path)
        
        # Generate ID if not provided
        if not self.id:
            self.id = self._generate_id()
        
        # Detect MIME type and media type
        if not self.mime_type:
            self.mime_type = self._detect_mime_type()
        
        if self.media_type == MediaType.UNKNOWN:
            self.media_type = self._detect_media_type()
        
        # Get file stats
        self.update_file_info()
    
    def _generate_id(self) -> str:
        """Generate unique ID for media file"""
        content = f"{self.file_path.absolute()}"
        if self.file_path.exists():
            content += str(self.file_path.stat().st_mtime)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _detect_mime_type(self) -> str:
        """Detect MIME type of the file"""
        mime_type, _ = mimetypes.guess_type(str(self.file_path))
        return mime_type or "application/octet-stream"
    
    def _detect_media_type(self) -> MediaType:
        """Detect media type from extension and MIME type"""
        ext = self.file_path.suffix.lower()
        
        # Video extensions
        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v']:
            return MediaType.VIDEO
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']:
            return MediaType.AUDIO
        # Image extensions
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']:
            return MediaType.IMAGE
        # Subtitle extensions
        elif ext in ['.srt', '.vtt', '.ass', '.ssa', '.sub']:
            return MediaType.SUBTITLE
        # MIME type fallback
        elif self.mime_type.startswith('video/'):
            return MediaType.VIDEO
        elif self.mime_type.startswith('audio/'):
            return MediaType.AUDIO
        elif self.mime_type.startswith('image/'):
            return MediaType.IMAGE
        else:
            return MediaType.UNKNOWN
    
    def update_file_info(self):
        """Update file information from filesystem"""
        if self.file_path.exists():
            stat = self.file_path.stat()
            self.last_modified = datetime.fromtimestamp(stat.st_mtime)
            if not self.metadata.file_size:
                self.metadata.file_size = stat.st_size
    
    def exists(self) -> bool:
        """Check if file exists on filesystem - FIXED METHOD"""
        try:
            return self.file_path.exists()
        except Exception:
            return False
    
    @property
    def filename(self) -> str:
        """Get filename without path"""
        return self.file_path.name
    
    @property
    def extension(self) -> str:
        """Get file extension"""
        return self.file_path.suffix.lower()
    
    @property
    def display_name(self) -> str:
        """Get display name (title or filename)"""
        return self.metadata.title or self.filename
    
    @property
    def is_video(self) -> bool:
        """Check if file is video"""
        return self.media_type == MediaType.VIDEO
    
    @property
    def is_audio(self) -> bool:
        """Check if file is audio"""
        return self.media_type == MediaType.AUDIO
    
    @property
    def is_image(self) -> bool:
        """Check if file is image"""
        return self.media_type == MediaType.IMAGE
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration from metadata"""
        return self.metadata.duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": str(self.file_path),
            "metadata": self.metadata.to_dict(),
            "media_type": self.media_type.value,
            "mime_type": self.mime_type,
            "id": self.id,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "last_scanned": self.last_scanned.isoformat() if self.last_scanned else None,
            "playback_state": self.playback_state.value,
            "current_position": self.current_position,
            "import_source": self.import_source,
            "import_date": self.import_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaFile':
        """Create instance from dictionary"""
        # Handle nested metadata
        if "metadata" in data:
            data["metadata"] = MediaMetadata.from_dict(data["metadata"])
        
        # Handle enums
        if "media_type" in data:
            data["media_type"] = MediaType(data["media_type"])
        if "playback_state" in data:
            data["playback_state"] = PlaybackState(data["playback_state"])
        
        # Handle datetime fields
        datetime_fields = ["last_modified", "last_scanned", "import_date"]
        for field in datetime_fields:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation"""
        return f"MediaFile('{self.display_name}', {self.media_type.value})"


def create_media_file_from_path(file_path: Union[str, Path], 
                               scan_metadata: bool = True) -> MediaFile:
    """Create MediaFile instance from file path"""
    
    path = Path(file_path)
    media_file = MediaFile(file_path=path)
    
    if scan_metadata and path.exists():
        # Basic file metadata
        stat = path.stat()
        media_file.metadata.file_size = stat.st_size
        media_file.metadata.date_added = datetime.now()
        media_file.metadata.last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Set basic title from filename if not extracted
        if not media_file.metadata.title:
            media_file.metadata.title = path.stem
        
        # Try to extract more metadata using FFprobe if available
        try:
            import subprocess
            import json
            
            if media_file.is_video or media_file.is_audio:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', str(path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    
                    # Get duration
                    if 'format' in data and 'duration' in data['format']:
                        media_file.metadata.duration = float(data['format']['duration'])
                    
                    # Get video dimensions
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            media_file.metadata.width = stream.get('width')
                            media_file.metadata.height = stream.get('height')
                            media_file.metadata.fps = eval(stream.get('r_frame_rate', '0/1'))
                            break
                            
        except Exception:
            pass  # Ignore metadata extraction errors
    
    return media_file