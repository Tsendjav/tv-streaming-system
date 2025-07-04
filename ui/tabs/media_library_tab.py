#!/usr/bin/env python3
"""
media_library_tab.py - САЙЖРУУЛСАН ХУВИЛБАР
Дотоод тоглуулагч болон хугацааны мэдээлэл бүхий медиа номын сангийн удирдлага
"""

import os
import json
import sqlite3
import threading
import platform
import subprocess
import tempfile
import hashlib
import mimetypes
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set, Iterator, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# =============================================================================
# ТОГТМОЛ УТГУУД БА ЛОГ - ЗАСВАРЛАСАН
# =============================================================================

try:
    from core.constants import (
        SUPPORTED_VIDEO_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS, 
        SUPPORTED_IMAGE_EXTENSIONS, DEFAULT_MEDIA_CATEGORIES
    )
except ImportError:
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'}
    SUPPORTED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
    SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    DEFAULT_MEDIA_CATEGORIES = ["Default", "Music", "Videos", "Images", "Promos", "News"]

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

# =============================================================================
# МЕДИА ЗАГВАРУУД - ЗАСВАРЛАСАН
# =============================================================================

class MediaType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SUBTITLE = "subtitle"
    UNKNOWN = "unknown"

class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

@dataclass
class MediaMetadata:
    """Медиа файлын сайжруулсан метадата"""
    
    # Үндсэн метадата
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    
    # Техникийн метадата
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    
    # Удирдлага
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0
    play_count: int = 0
    last_played: Optional[datetime] = None
    date_added: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # Файлын мэдээлэл
    file_size: int = 0
    checksum: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.keywords, str):
            self.keywords = [k.strip() for k in self.keywords.split(',') if k.strip()]
        if isinstance(self.tags, str):
            self.tags = [t.strip() for t in self.tags.split(',') if t.strip()]
    
    @property
    def duration_formatted(self) -> str:
        if not self.duration:
            return "00:00"
        
        total_seconds = int(self.duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self) -> str:
        if not self.file_size:
            return "0 B"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def to_dict(self) -> Dict[str, Any]:
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
            "category": self.category,
            "tags": self.tags.copy(),
            "rating": self.rating,
            "play_count": self.play_count,
            "last_played": self.last_played.isoformat() if self.last_played else None,
            "date_added": self.date_added.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "file_size": self.file_size,
            "checksum": self.checksum,
            "description": self.description,
            "keywords": self.keywords.copy(),
            "custom_fields": self.custom_fields.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaMetadata':
        datetime_fields = ["last_played", "date_added", "last_modified"]
        for field in datetime_fields:
            if field in data and data[field]:
                try:
                    if isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field])
                except (ValueError, TypeError):
                    data[field] = datetime.now() if field != "last_played" else None
        
        clean_data = data.copy()
        custom_fields = clean_data.pop("custom_fields", {})
        expected_fields = {f.name for f in MediaMetadata.__dataclass_fields__.values()}
        
        for key in list(clean_data.keys()):
            if key not in expected_fields:
                custom_fields[key] = clean_data.pop(key)
        
        clean_data["custom_fields"] = custom_fields

        defaults = {
            "tags": [],
            "keywords": [],
            "date_added": datetime.now(),
            "last_modified": datetime.now()
        }
        
        for key, default_value in defaults.items():
            if key not in clean_data:
                clean_data[key] = default_value
        
        return cls(**clean_data)

@dataclass
class MediaFile:
    """Метадататай медиа файл"""
    
    file_path: Path
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    media_type: MediaType = MediaType.UNKNOWN
    mime_type: str = ""
    id: str = ""
    
    # Төлөв
    last_modified: Optional[datetime] = None
    last_scanned: Optional[datetime] = None
    playback_state: PlaybackState = PlaybackState.STOPPED
    current_position: float = 0.0
    
    # Импортын мэдээлэл
    import_source: Optional[str] = None
    import_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.file_path = Path(self.file_path)
        
        if not self.id:
            self.id = self._generate_id()
        
        if not self.mime_type:
            self.mime_type = self._detect_mime_type()
        
        if self.media_type == MediaType.UNKNOWN:
            self.media_type = self._detect_media_type()
        
        self.update_file_info()
    
    def _generate_id(self) -> str:
        content = f"{self.file_path.absolute()}"
        if self.file_path.exists():
            try:
                content += str(self.file_path.stat().st_mtime)
            except (OSError, IOError):
                pass
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _detect_mime_type(self) -> str:
        try:
            mime_type, _ = mimetypes.guess_type(str(self.file_path))
            return mime_type or "application/octet-stream"
        except Exception:
            return "application/octet-stream"
    
    def _detect_media_type(self) -> MediaType:
        ext = self.file_path.suffix.lower()
        
        if ext in SUPPORTED_VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        elif ext in SUPPORTED_AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        elif ext in ['.srt', '.vtt', '.ass', '.ssa', '.sub']:
            return MediaType.SUBTITLE
        elif self.mime_type.startswith('video/'):
            return MediaType.VIDEO
        elif self.mime_type.startswith('audio/'):
            return MediaType.AUDIO
        elif self.mime_type.startswith('image/'):
            return MediaType.IMAGE
        
        return MediaType.UNKNOWN
    
    def update_file_info(self):
        if self.exists():
            try:
                stat = self.file_path.stat()
                self.last_modified = datetime.fromtimestamp(stat.st_mtime)
                if not self.metadata.file_size:
                    self.metadata.file_size = stat.st_size
            except (OSError, IOError) as e:
                pass
    
    def exists(self) -> bool:
        try:
            return self.file_path.exists() and self.file_path.is_file()
        except (OSError, IOError):
            return False
    
    @property
    def filename(self) -> str:
        return self.file_path.name
    
    @property
    def extension(self) -> str:
        return self.file_path.suffix.lower()
    
    @property
    def display_name(self) -> str:
        return self.metadata.title or self.filename
    
    @property
    def is_video(self) -> bool:
        return self.media_type == MediaType.VIDEO
    
    @property
    def is_audio(self) -> bool:
        return self.media_type == MediaType.AUDIO
    
    @property
    def is_image(self) -> bool:
        return self.media_type == MediaType.IMAGE
    
    @property
    def duration(self) -> Optional[float]:
        return self.metadata.duration

# =============================================================================
# МЕДИА НОМЫН САНГИЙН BACKEND
# =============================================================================

class MediaLibrary:
    """Мэдээллийн сангийн backend-тэй төв медиа номын сан"""
    
    def __init__(self, library_path: str = "data/media", db_path: str = "data/media_library.db"):
        self.library_path = Path(library_path)
        self.db_path = Path(db_path)
        self.logger = get_logger(__name__)
        
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
        self._media_cache: Dict[str, MediaFile] = {}
        self._cache_dirty = True
        
        self.categories: List[str] = DEFAULT_MEDIA_CATEGORIES.copy()
        self.all_tags: Set[str] = set()
        
        self._scanning = False
        self._scan_progress = 0
        self._scan_total = 0
        
        try:
            self._init_database()
            self._load_cache()
            self.logger.info(f"Медиа номын сан инициализац хийгдлээ: {self.library_path}")
        except Exception as e:
            self.logger.error(f"Медиа номын санг инициализац хийхэд алдаа гарлаа: {e}")
            raise
    
    def _init_database(self):
        """SQLite мэдээллийн санг инициализац хийнэ"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS media_files (
                        id TEXT PRIMARY KEY,
                        file_path TEXT UNIQUE NOT NULL,
                        metadata_json TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        mime_type TEXT,
                        file_size INTEGER DEFAULT 0,
                        checksum TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_scanned TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        color TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media_files(media_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON media_files(file_path)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON media_files(updated_at)")
                
                for category in self.categories:
                    conn.execute(
                        "INSERT OR IGNORE INTO categories (name, created_at) VALUES (?, ?)",
                        (category, datetime.now().isoformat())
                    )
                
                conn.commit()
                self.logger.debug("Мэдээллийн сан амжилттай инициализац хийгдлээ")
                
        except sqlite3.Error as e:
            self.logger.error(f"Мэдээллийн сангийн инициализац амжилтгүй боллоо: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Мэдээллийн сангийн инициализацын үед гэнэтийн алдаа гарлаа: {e}")
            raise
    
    def _load_cache(self):
        """Медиа файлуудыг санах ойн кэш рүү ачаална"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, file_path, metadata_json, media_type, mime_type
                    FROM media_files
                    ORDER BY updated_at DESC
                """)
                
                self._media_cache.clear()
                loaded_count = 0
                error_count = 0
                
                for row in cursor:
                    try:
                        metadata_dict = json.loads(row['metadata_json'])
                        metadata = MediaMetadata.from_dict(metadata_dict)
                        
                        media_file = MediaFile(
                            file_path=Path(row['file_path']),
                            metadata=metadata,
                            media_type=MediaType(row['media_type']),
                            mime_type=row['mime_type'] or "",
                            id=row['id']
                        )
                        
                        self._media_cache[media_file.id] = media_file
                        self.all_tags.update(metadata.tags)
                        loaded_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.logger.warning(f"Медиа файл {row['id']} ачаалахад алдаа гарлаа: {e}")
                
                self._cache_dirty = False
                self.logger.info(f"Кэш рүү {loaded_count} медиа файл ачааллаа ({error_count} алдаа)")
                
        except sqlite3.Error as e:
            self.logger.error(f"Мэдээллийн сангийн кэш ачаалахад алдаа гарлаа: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Кэш ачаалахад гэнэтийн алдаа гарлаа: {e}")
            raise
    
    def add_media_file(self, media_file: MediaFile) -> bool:
        """Медиа файлыг номын санд нэмнэ"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    metadata_json = json.dumps(media_file.metadata.to_dict())
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO media_files 
                        (id, file_path, metadata_json, media_type, mime_type, file_size, checksum, updated_at, last_scanned)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        media_file.id,
                        str(media_file.file_path),
                        metadata_json,
                        media_file.media_type.value,
                        media_file.mime_type,
                        media_file.metadata.file_size,
                        media_file.metadata.checksum,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                
                self._media_cache[media_file.id] = media_file
                self.all_tags.update(media_file.metadata.tags)
                
                self.logger.debug(f"Медиа файл нэмэгдлээ: {media_file.display_name}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Мэдээллийн санд медиа файл нэмэхэд алдаа гарлаа: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Медиа файл нэмэхэд алдаа гарлаа: {e}")
            return False
    
    def remove_media_file(self, media_id: str) -> bool:
        """Медиа файлыг номын сангаас устгана"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    cursor = conn.execute("DELETE FROM media_files WHERE id = ?", (media_id,))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        
                        if media_id in self._media_cache:
                            del self._media_cache[media_id]
                        
                        self.logger.debug(f"Медиа файл устгагдлаа: {media_id}")
                        return True
                    else:
                        return False
                
        except sqlite3.Error as e:
            self.logger.error(f"Мэдээллийн сангаас медиа файл устгахад алдаа гарлаа: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Медиа файл устгахад алдаа гарлаа: {e}")
            return False
       
    def search_media(self, query: str = "", filters: Optional[Dict[str, Any]] = None, 
                    limit: Optional[int] = None) -> List[MediaFile]:
        """Медиа файлуудыг хайна"""
        
        if not query and not filters:
            with self._lock:
                results = list(self._media_cache.values())
            return results[:limit] if limit else results
        
        results = []
        query_lower = query.lower() if query else ""
        
        with self._lock:
            for media_file in self._media_cache.values():
                try:
                    if self._media_matches_search_criteria(media_file, query_lower, filters):
                        results.append(media_file)
                except Exception as e:
                    self.logger.warning(f"Медиа файл {media_file.id}-ийг тааруулахад алдаа гарлаа: {e}")
                    continue
        
        if query:
            try:
                results.sort(key=lambda m: self._calculate_search_score(m, query_lower), reverse=True)
            except Exception as e:
                self.logger.warning(f"Хайлтын үр дүнг эрэмбэлэхэд алдаа гарлаа: {e}")
        
        return results[:limit] if limit else results
    
    def _media_matches_search_criteria(self, media_file: MediaFile, query: str, 
                                     filters: Optional[Dict[str, Any]]) -> bool:
        """Медиа файл хайлтын шалгуурт нийцэж байгаа эсэхийг шалгана"""
        
        if query:
            try:
                searchable_parts = [
                    media_file.metadata.title,
                    media_file.metadata.artist,
                    media_file.metadata.album,
                    media_file.metadata.genre,
                    media_file.metadata.description,
                    media_file.filename
                ]
                
                searchable_parts.extend(media_file.metadata.tags)
                searchable_parts.extend(media_file.metadata.keywords)
                
                searchable_text = " ".join(filter(None, searchable_parts)).lower()
                
                if query not in searchable_text:
                    return False
            except Exception as e:
                self.logger.warning(f"Хайлт тааруулахад алдаа гарлаа: {e}")
                return False
        
        if filters:
            try:
                for filter_key, filter_value in filters.items():
                    if not self._apply_filter(media_file, filter_key, filter_value):
                        return False
            except Exception as e:
                self.logger.warning(f"Шүүлтүүр тааруулахад алдаа гарлаа: {e}")
                return False
        
        return True
    
    def _apply_filter(self, media_file: MediaFile, filter_key: str, filter_value: Any) -> bool:
        """Нэг шүүлтүүрийг медиа файл дээр хэрэглэнэ"""
        try:
            if filter_key == "media_type":
                return media_file.media_type == filter_value
            elif filter_key == "category":
                return media_file.metadata.category == filter_value
            elif filter_key == "genre":
                return media_file.metadata.genre == filter_value
            elif filter_key == "artist":
                return media_file.metadata.artist == filter_value
            elif filter_key == "tags":
                if isinstance(filter_value, list):
                    return any(tag in media_file.metadata.tags for tag in filter_value)
                else:
                    return filter_value in media_file.metadata.tags
            elif filter_key == "rating_min":
                return media_file.metadata.rating >= filter_value
            elif filter_key == "rating_max":
                return media_file.metadata.rating <= filter_value
            elif filter_key == "duration_min":
                return (media_file.metadata.duration or 0) >= filter_value
            elif filter_key == "duration_max":
                return (media_file.metadata.duration or 0) <= filter_value
            elif filter_key == "year":
                return media_file.metadata.year == filter_value
            elif filter_key == "file_extension":
                return media_file.extension == filter_value
        except Exception as e:
            self.logger.warning(f"Шүүлтүүр {filter_key} хэрэглэхэд алдаа гарлаа: {e}")
            return False
        
        return True
    
    def _calculate_search_score(self, media_file: MediaFile, query: str) -> float:
        """Хайлтын хамаарлын оноог тооцоолно"""
        score = 0.0
        
        try:
            if media_file.metadata.title and query in media_file.metadata.title.lower():
                score += 10.0
            
            if media_file.metadata.artist and query in media_file.metadata.artist.lower():
                score += 8.0
            
            if media_file.metadata.album and query in media_file.metadata.album.lower():
                score += 6.0
            
            if query in media_file.filename.lower():
                score += 5.0
            
            if media_file.metadata.genre and query in media_file.metadata.genre.lower():
                score += 4.0
            
            for tag in media_file.metadata.tags:
                if query in tag.lower():
                    score += 3.0
            
            if media_file.metadata.description and query in media_file.metadata.description.lower():
                score += 2.0
                
        except Exception as e:
            self.logger.warning(f"Хайлтын оноог тооцоолоход алдаа гарлаа: {e}")
        
        return score
    
    def get_total_duration(self) -> float:
        """Бүх медиа файлуудын нийлбэр хугацааг тооцоолно"""
        total_duration = 0.0
        
        for media_file in self._media_cache.values():
            if media_file.metadata.duration:
                total_duration += media_file.metadata.duration
        
        return total_duration
    
    def get_filtered_duration(self, media_files: List[MediaFile]) -> float:
        """Шүүгдсэн медиа файлуудын нийлбэр хугацааг тооцоолно"""
        total_duration = 0.0
        
        for media_file in media_files:
            if media_file.metadata.duration:
                total_duration += media_file.metadata.duration
        
        return total_duration
    
    def __iter__(self):
        with self._lock:
            return iter(list(self._media_cache.values()))
    
    def __len__(self):
        return len(self._media_cache)
    
    def __contains__(self, media_id: str):
        return media_id in self._media_cache

# =============================================================================
# САЙЖРУУЛСАН МЕДИА УРЬДЧИЛАН ХАРАХ УДИРДАГЧ
# =============================================================================

class MediaPreviewHandler(QObject):
    """Сайжруулсан медиа файлын урьдчилан харах болон тоглуулахыг зохицуулна"""
    
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str, int)
    position_changed = pyqtSignal(float)  # Тоглуулахын явцыг илэрхийлнэ
    duration_changed = pyqtSignal(float)  # Хугацааны өөрчлөлтийг илэрхийлнэ
    state_changed = pyqtSignal(str)  # Тоглуулагчийн төлөвийн өөрчлөлт
    
    def __init__(self, preview_label, parent=None):
        super().__init__(parent)
        self.preview_label = preview_label
        self.logger = get_logger(__name__)
        
        # VLC компонентууд
        self.vlc_instance = None
        self.media_player = None
        self.vlc_available = False
        
        # Тоглуулахын төлөв
        self.current_media_file = None
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(100)  # 100ms
        
        self._init_vlc()
    
    def _init_vlc(self):
        """VLC компонентуудыг инициализац хийнэ"""
        try:
            import vlc
            
            vlc_args = ['--no-xlib', '--quiet', '--intf=dummy']
            
            self.vlc_instance = vlc.Instance(vlc_args)
            if self.vlc_instance:
                self.media_player = self.vlc_instance.media_player_new()
                if self.media_player:
                    self.vlc_available = True
                    
                    # VLC event manager холбогдол
                    event_manager = self.media_player.event_manager()
                    event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
                    event_manager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
                    event_manager.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)
                    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
                    
                    self.logger.debug("VLC амжилттай инициализац хийгдлээ")
                else:
                    self.logger.warning("VLC медиа тоглуулагч үүсгэхэд алдаа гарлаа")
            else:
                self.logger.warning("VLC инстанс үүсгэхэд алдаа гарлаа")
                
        except ImportError:
            self.vlc_available = False
            self.logger.info("VLC байхгүй - урьдчилан харах функц идэвхгүй боллоо")
        except Exception as e:
            self.vlc_available = False
            self.logger.warning(f"VLC инициализац хийхэд алдаа гарлаа: {e}")
    
    def _on_playing(self, event):
        """Тоглуулж байгаа үеийн event"""
        self.state_changed.emit("playing")
        self.position_timer.start()
    
    def _on_paused(self, event):
        """Түр зогссон үеийн event"""
        self.state_changed.emit("paused")
        self.position_timer.stop()
    
    def _on_stopped(self, event):
        """Зогссон үеийн event"""
        self.state_changed.emit("stopped")
        self.position_timer.stop()
        self.position_changed.emit(0.0)
    
    def _on_end_reached(self, event):
        """Тоглуулалт дууссан үеийн event"""
        self.state_changed.emit("finished")
        self.position_timer.stop()
        self.position_changed.emit(0.0)
    
    def _update_position(self):
        """Тоглуулахын байршлыг шинэчилнэ"""
        if self.vlc_available and self.media_player and self.media_player.is_playing():
            try:
                position = self.media_player.get_position()  # 0.0 - 1.0
                duration = self.media_player.get_length() / 1000.0  # секундээр
                
                if duration > 0:
                    current_time = position * duration
                    self.position_changed.emit(current_time)
                    
                    # Хугацааг анх удаа авч байгаа бол сигнал илгээнэ
                    if hasattr(self, '_duration_emitted') == False:
                        self.duration_changed.emit(duration)
                        self._duration_emitted = True
                        
            except Exception as e:
                self.logger.warning(f"Байршлыг шинэчлэхэд алдаа гарлаа: {e}")
    
    def set_position(self, position: float):
        """Тоглуулахын байршлыг тохируулна (0.0 - 1.0)"""
        if self.vlc_available and self.media_player:
            try:
                self.media_player.set_position(position)
            except Exception as e:
                self.logger.warning(f"Байршлыг тохируулахад алдаа гарлаа: {e}")
    
    def update_preview(self, media_file: MediaFile):
        """Урьдчилан харах талбарыг медиа файлаар шинэчилнэ"""
        try:
            self.current_media_file = media_file
            self._duration_emitted = False
            
            if not media_file or not media_file.exists():
                self.preview_label.setText("Файл олдсонгүй")
                self.preview_label.setPixmap(QPixmap())
                return
            
            if media_file.is_image:
                self._load_image_preview(media_file)
            elif media_file.is_video or media_file.is_audio:
                self._load_vlc_preview(media_file)
            else:
                file_type = media_file.media_type.value.title()
                self.preview_label.setText(f"{file_type} файл\n\n{media_file.filename}")
                self.preview_label.setPixmap(QPixmap())
                
        except Exception as e:
            self.logger.error(f"Урьдчилан харахыг шинэчлэхэд алдаа гарлаа: {e}")
            self.preview_label.setText("Урьдчилан харах алдаа")
            self.preview_label.setPixmap(QPixmap())
    
    def _load_image_preview(self, media_file: MediaFile):
        """Зургийн урьдчилан харахыг ачаална"""
        try:
            pixmap = QPixmap(str(media_file.file_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")
            else:
                self.preview_label.setText("Зураг ачаалах боломжгүй")
                self.preview_label.setPixmap(QPixmap())
                
        except Exception as e:
            self.logger.error(f"Зургийн урьдчилан харахыг ачаалахад алдаа гарлаа: {e}")
            self.preview_label.setText("Зургийн урьдчилан харах алдаа")
            self.preview_label.setPixmap(QPixmap())
    
    def _load_vlc_preview(self, media_file: MediaFile):
        """VLC урьдчилан харахыг ачаална"""
        if not self.vlc_available or not self.media_player:
            self.preview_label.setText("VLC байхгүй эсвэл инициализац хийгдээгүй")
            self.preview_label.setPixmap(QPixmap())
            return

        try:
            self.stop_preview()
            media = self.vlc_instance.media_new(str(media_file.file_path))
            self.media_player.set_media(media)
            
            # Видео гаралтыг QLabel-д холбоно
            if platform.system() == "Windows":
                self.media_player.set_hwnd(self.preview_label.winId())
            elif platform.system().startswith('linux'):
                self.media_player.set_xwindow(self.preview_label.winId())
            elif platform.system() == "Darwin":
                self.media_player.set_nsobject(int(self.preview_label.winId()))
            
            self.preview_label.setText(f"Медиа файл\n\n{media_file.filename}\n\nБэлэн боллоо")
            self.preview_label.setPixmap(QPixmap())
            
        except Exception as e:
            self.logger.error(f"VLC урьдчилан харахыг ачаалахад алдаа гарлаа: {e}")
            self.preview_label.setText("VLC урьдчилан харах алдаа")
            self.preview_label.setPixmap(QPixmap())
    
    def play_preview(self, media_file: MediaFile = None) -> bool:
        """Медиа файлын урьдчилан харахыг тоглуулна"""
        if media_file:
            self.update_preview(media_file)
        
        if not self.vlc_available or not self.media_player:
            self.error_occurred.emit("VLC байхгүй эсвэл инициализац хийгдээгүй тул урьдчилан харах боломжгүй")
            return False
        
        if not self.current_media_file or not self.current_media_file.exists():
            self.error_occurred.emit("Тоглуулах файл олдсонгүй.")
            return False

        try:
            self.media_player.play()
            self.status_message.emit(f"Урьдчилан харахыг тоглуулж байна: {self.current_media_file.filename}", 2000)
            return True
        except Exception as e:
            self.logger.error(f"Урьдчилан харахыг тоглуулахад алдаа гарлаа: {e}")
            self.error_occurred.emit(f"Урьдчилан харахыг тоглуулахад алдаа гарлаа: {e}")
            return False
    
    def pause_preview(self):
        """Урьдчилан харахыг түр зогсооно"""
        if self.vlc_available and self.media_player:
            try:
                if self.media_player.is_playing():
                    self.media_player.pause()
                    self.status_message.emit("Урьдчилан харахыг түр зогсоолоо", 2000)
                else:
                    self.media_player.play()
                    self.status_message.emit("Урьдчилан харахыг үргэлжлүүллээ", 2000)
            except Exception as e:
                self.logger.error(f"Урьдчилан харахыг түр зогсооход алдаа гарлаа: {e}")
    
    def stop_preview(self):
        """Урьдчилан харахыг зогсооно"""
        if self.vlc_available and self.media_player:
            try:
                if self.media_player.is_playing():
                    self.media_player.stop()
                    self.status_message.emit("Урьдчилан харахыг зогсоолоо", 2000)
            except Exception as e:
                self.logger.error(f"Урьдчилан харахыг зогсооход алдаа гарлаа: {e}")
    
    def is_playing(self) -> bool:
        """Урьдчилан харах одоогоор тоглуулж байгаа эсэхийг шалгана"""
        if self.vlc_available and self.media_player:
            try:
                return self.media_player.is_playing()
            except Exception:
                return False
        return False
    
    def clear_preview(self):
        """Урьдчилан харах талбарыг цэвэрлэнэ"""
        try:
            self.stop_preview()
            self.current_media_file = None
            self.preview_label.setText("Урьдчилан харах боломжгүй")
            self.preview_label.setPixmap(QPixmap())
        except Exception as e:
            self.logger.error(f"Урьдчилан харахыг цэвэрлэхэд алдаа гарлаа: {e}")
    
    def cleanup(self):
        """Нөөцийг цэвэрлэнэ"""
        try:
            self.position_timer.stop()
            
            if self.vlc_available and self.media_player:
                if self.media_player.is_playing():
                    self.media_player.stop()
                self.media_player.release()
            
            if self.vlc_instance:
                self.vlc_instance.release()
                
        except Exception as e:
            self.logger.error(f"Урьдчилан харах удирдагчийг цэвэрлэх үед алдаа гарлаа: {e}")

# =============================================================================
# САЙЖРУУЛСАН МЕДИА НОМЫН САНГИЙН ТАБ
# =============================================================================

class MediaLibraryTab(QWidget):
    """Сайжруулсан медиа номын сангийн удирдлагын таб"""
    
    # Сигналууд
    status_message = pyqtSignal(str, int)
    progress_update = pyqtSignal(int)
    media_selected = pyqtSignal(object)
    scheduler_add_media = pyqtSignal(object)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Медиа номын санг инициализац хийнэ
        try:
            library_path = getattr(config_manager, 'media_library_path', 'data/media')
            if hasattr(library_path, '__fspath__'):
                library_path = str(library_path)
            
            self.media_library = MediaLibrary(library_path)
        except Exception as e:
            self.logger.error(f"Медиа номын санг инициализац хийхэд алдаа гарлаа: {e}")
            self.media_library = None
        
        # UI компонентууд
        self.search_input = None
        self.category_list = None
        self.media_table = None
        self.media_model = None
        self.preview_label = None
        
        # Метадата засварлах компонентууд
        self.title_edit = None
        self.artist_edit = None
        self.album_edit = None
        self.genre_edit = None
        self.category_combo = None
        self.rating_slider = None
        self.rating_label = None
        self.description_edit = None
        self.tags_edit = None
        
        # Файлын мэдээллийн шошго
        self.file_path_label = None
        self.file_size_label = None
        self.duration_label = None
        self.resolution_label = None
        self.date_added_label = None
        
        # Үйлдлийн товчнууд
        self.save_metadata_btn = None
        self.open_file_btn = None
        self.show_in_explorer_btn = None
        
        # Тоглуулагчийн удирдлага - ШИНЭ
        self.play_btn = None
        self.pause_btn = None
        self.stop_btn = None
        self.position_slider = None
        self.current_time_label = None
        self.total_time_label = None
        self.volume_slider = None
        
        # Статистикийн лэйбэлүүд - ШИНЭ
        self.current_files_count_label = None
        self.current_duration_label = None
        self.total_files_count_label = None
        self.total_duration_label = None
        
        # Харах горимын хяналт
        self.view_combo = None
        self.sort_combo = None
        self.sort_order_btn = None
        self.type_combo = None
        self.status_label = None
        
        # Урьдчилан харах удирдагч
        self.preview_handler = None
        
        # Одоогийн төлөв
        self.current_media_file = None
        self.current_filter = {}
        self.metadata_changed = False
        
        # UI-г инициализац хийнэ
        try:
            self._init_ui()
            if self.media_library:
                self._load_media_data()
                self._update_statistics()
            
            self.logger.debug("Медиа номын сангийн таб амжилттай инициализац хийгдлээ")
        except Exception as e:
            self.logger.error(f"Медиа номын сангийн таб UI-г инициализац хийхэд алдаа гарлаа: {e}")
    
    def _init_ui(self):
        """Хэрэглэгчийн интерфэйсийг инициализац хийнэ"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(8)
        
        if not self.media_library:
            # Номын сан инициализац хийгдэхгүй бол алдааны мессеж харуулна
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            
            error_label = QLabel("⚠️ Медиа номын сан инициализац хийгдсэнгүй")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
            error_layout.addWidget(error_label)
            
            error_details = QLabel("Дэлгэрэнгүй мэдээллийг лог-оос шалгаж, програмыг дахин эхлүүлнэ үү.")
            error_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_details)
            
            main_layout.addWidget(error_widget)
            return
        
        try:
            # Зүүн талын самбар - Ангилал болон шүүлтүүрүүд
            left_panel = self._create_left_panel()
            left_panel.setMaximumWidth(280)
            main_layout.addWidget(left_panel)
            
            # Төв самбар - Медиа хүснэгт
            center_panel = self._create_center_panel()
            main_layout.addWidget(center_panel, stretch=3)
            
            # Баруун талын самбар - Урьдчилан харах болон метадата
            right_panel = self._create_right_panel()
            right_panel.setMaximumWidth(350)
            main_layout.addWidget(right_panel)
            
            # UI үүсгэсний дараа урьдчилан харах удирдагчийг инициализац хийнэ
            if self.preview_label:
                try:
                    self.preview_handler = MediaPreviewHandler(self.preview_label, self)
                    self.preview_handler.error_occurred.connect(
                        lambda msg: self.status_message.emit(msg, 5000)
                    )
                    self.preview_handler.status_message.connect(self.status_message.emit)
                    self.preview_handler.position_changed.connect(self._update_position_display)
                    self.preview_handler.duration_changed.connect(self._update_duration_display)
                    self.preview_handler.state_changed.connect(self._update_playback_controls)
                except Exception as e:
                    self.logger.warning(f"Урьдчилан харах удирдагчийг инициализац хийхэд алдаа гарлаа: {e}")
            
            # Ангиллын комбо боксыг шинэчилнэ
            self._update_category_combo()
            
        except Exception as e:
            self.logger.error(f"UI үүсгэхэд алдаа гарлаа: {e}")
            raise
    
    def _create_left_panel(self) -> QWidget:
        """Ангилал болон шүүлтүүртэй зүүн талын самбарыг үүсгэнэ"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        try:
            # Статистикийн хэсэг - ШИНЭ
            stats_group = QGroupBox("📊 Статистик")
            stats_layout = QVBoxLayout(stats_group)
            
            # Одоогийн харагдац
            current_stats = QLabel("Одоогийн харагдац:")
            current_stats.setStyleSheet("font-weight: bold; color: #4CAF50;")
            stats_layout.addWidget(current_stats)
            
            self.current_files_count_label = QLabel("Файлын тоо: 0")
            stats_layout.addWidget(self.current_files_count_label)
            
            self.current_duration_label = QLabel("Нийт хугацаа: 00:00:00")
            stats_layout.addWidget(self.current_duration_label)
            
            stats_layout.addWidget(QLabel(""))  # Зай
            
            # Нийт номын сан
            total_stats = QLabel("Нийт номын сан:")
            total_stats.setStyleSheet("font-weight: bold; color: #2196F3;")
            stats_layout.addWidget(total_stats)
            
            self.total_files_count_label = QLabel("Нийт файл: 0")
            stats_layout.addWidget(self.total_files_count_label)
            
            self.total_duration_label = QLabel("Нийт хугацаа: 00:00:00")
            stats_layout.addWidget(self.total_duration_label)
            
            layout.addWidget(stats_group)
            
            # Хайлтын хэсэг
            search_group = QGroupBox("🔍 Хайлт")
            search_layout = QVBoxLayout(search_group)
            
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Медиа файлуудыг хайна уу...")
            self.search_input.textChanged.connect(self._on_search_changed)
            search_layout.addWidget(self.search_input)
            
            clear_search_btn = QPushButton("Цэвэрлэх")
            clear_search_btn.clicked.connect(self._clear_search)
            search_layout.addWidget(clear_search_btn)
            
            layout.addWidget(search_group)
                        
            # Ангиллын хэсэг
            categories_group = QGroupBox("📁 Ангилал")
            categories_layout = QVBoxLayout(categories_group)
            
            self.category_list = QListWidget()
            self.category_list.addItem("Бүх медиа")
            if self.media_library:
                self.category_list.addItems(self.media_library.categories)
            self.category_list.setCurrentRow(0)
            self.category_list.currentTextChanged.connect(self._on_category_changed)
            categories_layout.addWidget(self.category_list)
            
            cat_buttons = QHBoxLayout()
            add_cat_btn = QPushButton("Нэмэх")
            add_cat_btn.clicked.connect(self._add_category)
            cat_buttons.addWidget(add_cat_btn)
            
            remove_cat_btn = QPushButton("Устгах")
            remove_cat_btn.clicked.connect(self._remove_category)
            cat_buttons.addWidget(remove_cat_btn)
            
            categories_layout.addLayout(cat_buttons)
            layout.addWidget(categories_group)
            
            # Медиа төрлийн шүүлтүүр
            type_group = QGroupBox("🎬 Медиа төрөл")
            type_layout = QVBoxLayout(type_group)
            
            self.type_combo = QComboBox()
            self.type_combo.addItems(["Бүх төрөл", "Видео", "Аудио", "Зураг"])
            self.type_combo.currentTextChanged.connect(self._on_type_filter_changed)
            type_layout.addWidget(self.type_combo)
            
            layout.addWidget(type_group)
            
            # Үйлдлүүдийн хэсэг - ЗӨВӨӨР БАЙРЛУУЛСАН
            actions_group = QGroupBox("⚡ Үйлдлүүд")
            actions_layout = QVBoxLayout(actions_group)
            
            scan_btn = QPushButton("🔄 Номын санг скан хийх")
            scan_btn.clicked.connect(self.scan_media_library)
            actions_layout.addWidget(scan_btn)
            
            import_btn = QPushButton("📥 Файл импортлох")
            import_btn.clicked.connect(self.import_media_files)
            actions_layout.addWidget(import_btn)
            
            cleanup_btn = QPushButton("🧹 Алга болсон файлуудыг цэвэрлэх")
            cleanup_btn.clicked.connect(self._cleanup_missing_files)
            actions_layout.addWidget(cleanup_btn)
            
            add_to_scheduler_btn = QPushButton("➕ Scheduler-т нэмэх")
            add_to_scheduler_btn.clicked.connect(self._add_selected_to_scheduler)
            actions_layout.addWidget(add_to_scheduler_btn)
            
            # ШИНЭ ТОВЧНУУД - actions_layout тодорхойлогдсоны дараа
            clear_selection_btn = QPushButton("🧹 Сонголт цэвэрлэх")
            clear_selection_btn.clicked.connect(self.clear_media_selection)
            actions_layout.addWidget(clear_selection_btn)

            refresh_all_btn = QPushButton("♻️ Бүгдийг шинэчлэх")
            refresh_all_btn.clicked.connect(self._refresh_all_metadata)
            actions_layout.addWidget(refresh_all_btn)
            
            layout.addWidget(actions_group)
            layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Зүүн талын самбар үүсгэхэд алдаа гарлаа: {e}")
            raise
        
        return panel
      
    def _create_center_panel(self) -> QWidget:
        """Медиа хүснэгттэй төв самбарыг үүсгэнэ"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        try:
            # Хэрэгслийн самбар
            toolbar = QHBoxLayout()
            
            self.view_combo = QComboBox()
            self.view_combo.addItems(["Хүснэгтийн харагдац", "Сүлжээний харагдац", "Жагсаалтын харагдац"])
            self.view_combo.currentTextChanged.connect(self._change_view_mode)
            toolbar.addWidget(QLabel("Харагдац:"))
            toolbar.addWidget(self.view_combo)
            
            toolbar.addStretch()
            
            self.sort_combo = QComboBox()
            self.sort_combo.addItems([
                "Гарчиг", "Уран бүтээлч", "Цомог", "Хугацаа", "Төрөл", 
                "Ангилал", "Үнэлгээ", "Нэмэгдсэн огноо", "Файлын хэмжээ"
            ])
            self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
            toolbar.addWidget(QLabel("Эрэмбэлэх:"))
            toolbar.addWidget(self.sort_combo)
            
            self.sort_order_btn = QPushButton("↑ Өсөх")
            self.sort_order_btn.setCheckable(True)
            self.sort_order_btn.clicked.connect(self._toggle_sort_order)
            toolbar.addWidget(self.sort_order_btn)
            
            layout.addLayout(toolbar)
            
            # Медиа хүснэгт
            self.media_table = QTableView()
            self.media_model = MediaTableModel()
            self.media_table.setModel(self.media_model)
            
            self.media_table.setSortingEnabled(True)
            self.media_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.media_table.setAlternatingRowColors(True)
            self.media_table.verticalHeader().setVisible(False)
            
            if self.media_table.selectionModel():
                self.media_table.selectionModel().currentRowChanged.connect(self._on_media_selected)
            self.media_table.doubleClicked.connect(self._on_media_double_clicked)
            
            self.media_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.media_table.customContextMenuRequested.connect(self._show_context_menu)
            
            layout.addWidget(self.media_table)
            
            # Төлөв
            self.status_label = QLabel("0 файл")
            self.status_label.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(self.status_label)
            
        except Exception as e:
            self.logger.error(f"Төв самбар үүсгэхэд алдаа гарлаа: {e}")
            raise
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Урьдчилан харах болон метадата засварлагч баруун талын самбарыг үүсгэнэ"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        try:
            # Урьдчилан харах хэсэг - САЙЖРУУЛСАН
            preview_group = QGroupBox("🎥 Дотоод тоглуулагч")
            preview_layout = QVBoxLayout(preview_group)
            
            self.preview_label = QLabel()
            self.preview_label.setMinimumSize(320, 180)
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: #1a1a1a;
                    border: 2px solid #555;
                    border-radius: 4px;
                    color: #888;
                }
            """)
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setText("Медиа файл сонгоно уу")
            preview_layout.addWidget(self.preview_label)
            
            # Тоглуулагчийн удирдлага - ШИНЭ
            controls_layout = QHBoxLayout()
            
            self.play_btn = QPushButton("▶️")
            self.play_btn.setFixedSize(40, 30)
            self.play_btn.clicked.connect(self._play_preview)
            self.play_btn.setEnabled(False)
            controls_layout.addWidget(self.play_btn)
            
            self.pause_btn = QPushButton("⏸️")
            self.pause_btn.setFixedSize(40, 30)
            self.pause_btn.clicked.connect(self._pause_preview)
            self.pause_btn.setEnabled(False)
            controls_layout.addWidget(self.pause_btn)
            
            self.stop_btn = QPushButton("⏹️")
            self.stop_btn.setFixedSize(40, 30)
            self.stop_btn.clicked.connect(self._stop_preview)
            self.stop_btn.setEnabled(False)
            controls_layout.addWidget(self.stop_btn)
            
            controls_layout.addStretch()
            
            # Дууны түвшний хяналт
            volume_label = QLabel("🔊")
            controls_layout.addWidget(volume_label)
            
            self.volume_slider = QSlider(Qt.Orientation.Horizontal)
            self.volume_slider.setMaximumWidth(80)
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(70)
            self.volume_slider.valueChanged.connect(self._set_volume)
            controls_layout.addWidget(self.volume_slider)
            
            preview_layout.addLayout(controls_layout)
            
            # Байршлын хяналт - ШИНЭ
            position_layout = QVBoxLayout()
            
            self.position_slider = QSlider(Qt.Orientation.Horizontal)
            self.position_slider.setRange(0, 1000)
            self.position_slider.sliderPressed.connect(self._position_slider_pressed)
            self.position_slider.sliderReleased.connect(self._position_slider_released)
            position_layout.addWidget(self.position_slider)
            
            time_layout = QHBoxLayout()
            self.current_time_label = QLabel("00:00")
            self.current_time_label.setStyleSheet("font-size: 10px; color: #888;")
            time_layout.addWidget(self.current_time_label)
            
            time_layout.addStretch()
            
            self.total_time_label = QLabel("00:00")
            self.total_time_label.setStyleSheet("font-size: 10px; color: #888;")
            time_layout.addWidget(self.total_time_label)
            
            position_layout.addLayout(time_layout)
            preview_layout.addLayout(position_layout)
            
            layout.addWidget(preview_group)
            
            # Метадата засварлагч
            metadata_group = QGroupBox("📝 Метадата")
            metadata_layout = QFormLayout(metadata_group)
            
            self.title_edit = QLineEdit()
            self.title_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Гарчиг:", self.title_edit)
            
            self.artist_edit = QLineEdit()
            self.artist_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Уран бүтээлч:", self.artist_edit)
            
            self.album_edit = QLineEdit()
            self.album_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Цомог:", self.album_edit)
            
            self.genre_edit = QLineEdit()
            self.genre_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Төрөл:", self.genre_edit)
            
            self.category_combo = QComboBox()
            self.category_combo.currentTextChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Ангилал:", self.category_combo)
            
            self.rating_slider = QSlider(Qt.Orientation.Horizontal)
            self.rating_slider.setRange(0, 5)
            self.rating_slider.valueChanged.connect(self._on_rating_changed)
            rating_layout = QHBoxLayout()
            rating_layout.addWidget(self.rating_slider)
            self.rating_label = QLabel("0")
            rating_layout.addWidget(self.rating_label)
            metadata_layout.addRow("Үнэлгээ:", rating_layout)
            
            self.description_edit = QTextEdit()
            self.description_edit.setMaximumHeight(60)
            self.description_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Тайлбар:", self.description_edit)
            
            self.tags_edit = QLineEdit()
            self.tags_edit.setPlaceholderText("Тагуудыг таслалаар тусгаарлана уу")
            self.tags_edit.textChanged.connect(self._on_metadata_changed)
            metadata_layout.addRow("Тагууд:", self.tags_edit)
            
            layout.addWidget(metadata_group)
            
            # Файлын мэдээллийн хэсэг
            info_group = QGroupBox("ℹ️ Файлын мэдээлэл")
            info_layout = QFormLayout(info_group)
            
            self.file_path_label = QLabel("-")
            self.file_path_label.setWordWrap(True)
            info_layout.addRow("Зам:", self.file_path_label)
            
            self.file_size_label = QLabel("-")
            info_layout.addRow("Хэмжээ:", self.file_size_label)
            
            self.duration_label = QLabel("-")
            info_layout.addRow("Хугацаа:", self.duration_label)
            
            self.resolution_label = QLabel("-")
            info_layout.addRow("Нягтрал:", self.resolution_label)
            
            self.date_added_label = QLabel("-")
            info_layout.addRow("Нэмэгдсэн огноо:", self.date_added_label)
            
            layout.addWidget(info_group)
            
            # Үйлдлийн товчнууд
            actions_layout = QVBoxLayout()
            
            self.save_metadata_btn = QPushButton("💾 Метадата хадгалах")
            self.save_metadata_btn.clicked.connect(self._save_metadata)
            self.save_metadata_btn.setEnabled(False)
            actions_layout.addWidget(self.save_metadata_btn)
            
            self.open_file_btn = QPushButton("📁 Файл нээх")
            self.open_file_btn.clicked.connect(self._open_file)
            self.open_file_btn.setEnabled(False)
            actions_layout.addWidget(self.open_file_btn)
            
            self.show_in_explorer_btn = QPushButton("🗂️ Explorer-т харуулах")
            self.show_in_explorer_btn.clicked.connect(self._show_in_explorer)
            self.show_in_explorer_btn.setEnabled(False)
            actions_layout.addWidget(self.show_in_explorer_btn)
            
            layout.addLayout(actions_layout)
            layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Баруун талын самбар үүсгэхэд алдаа гарлаа: {e}")
            raise
        
        return panel
    
    # =============================================================================
    # ШИНЭ ФУНКЦУУД - ТОГЛУУЛАГЧИЙН УДИРДЛАГА
    # =============================================================================
    
    def _update_position_display(self, current_time: float):
        """Одоогийн байршлыг харуулна"""
        try:
            if self.current_time_label:
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                self.current_time_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Хэрэв хэрэглэгч slider-ыг дарж байгаа биш бол шинэчилнэ
            if self.position_slider and not self.position_slider.isSliderDown():
                # Нийт хугацааг мэддэг бол пропорционалаар тооцно
                if self.preview_handler and self.preview_handler.media_player:
                    try:
                        duration = self.preview_handler.media_player.get_length() / 1000.0
                        if duration > 0:
                            position = int((current_time / duration) * 1000)
                            self.position_slider.setValue(position)
                    except Exception:
                        pass
                        
        except Exception as e:
            self.logger.error(f"Байршлын дэлгэцийг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _update_duration_display(self, duration: float):
        """Нийт хугацааг харуулна"""
        try:
            if self.total_time_label:
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.total_time_label.setText(f"{minutes:02d}:{seconds:02d}")
                
        except Exception as e:
            self.logger.error(f"Хугацааны дэлгэцийг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _update_playback_controls(self, state: str):
        """Тоглуулагчийн товчнуудын төлөвийг шинэчилнэ"""
        try:
            if state == "playing":
                if self.play_btn:
                    self.play_btn.setEnabled(False)
                if self.pause_btn:
                    self.pause_btn.setEnabled(True)
                if self.stop_btn:
                    self.stop_btn.setEnabled(True)
            elif state == "paused":
                if self.play_btn:
                    self.play_btn.setEnabled(True)
                if self.pause_btn:
                    self.pause_btn.setEnabled(True)
                if self.stop_btn:
                    self.stop_btn.setEnabled(True)
            elif state in ["stopped", "finished"]:
                if self.play_btn:
                    self.play_btn.setEnabled(True)
                if self.pause_btn:
                    self.pause_btn.setEnabled(False)
                if self.stop_btn:
                    self.stop_btn.setEnabled(False)
                    
        except Exception as e:
            self.logger.error(f"Тоглуулагчийн товчнуудыг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _position_slider_pressed(self):
        """Байршлын slider дарагдах үед"""
        pass  # Slider дарагдсан үед position update-ийг түр зогсооно
    
    def _position_slider_released(self):
        """Байршлын slider суллагдах үед"""
        try:
            if self.preview_handler and self.position_slider:
                position = self.position_slider.value() / 1000.0  # 0.0 - 1.0
                self.preview_handler.set_position(position)
        except Exception as e:
            self.logger.error(f"Байршлыг тохируулахад алдаа гарлаа: {e}")
    
    def _set_volume(self, volume: int):
        """Дууны түвшинг тохируулна"""
        try:
            if self.preview_handler and self.preview_handler.media_player:
                self.preview_handler.media_player.audio_set_volume(volume)
        except Exception as e:
            self.logger.error(f"Дууны түвшинг тохируулахад алдаа гарлаа: {e}")
    
    def _play_preview(self):
        """Урьдчилан харахыг тоглуулна"""
        if not self.preview_handler or not self.current_media_file:
            self.status_message.emit("Тоглуулах медиа файл сонгогдоогүй байна.", 3000)
            return

        try:
            self.preview_handler.play_preview(self.current_media_file)
        except Exception as e:
            self.logger.error(f"Урьдчилан харахыг тоглуулахад алдаа гарлаа: {e}")
            self.status_message.emit(f"Урьдчилан харахыг тоглуулахад алдаа гарлаа: {e}", 5000)
    
    def _pause_preview(self):
        """Урьдчилан харахыг түр зогсооно"""
        if self.preview_handler:
            try:
                self.preview_handler.pause_preview()
            except Exception as e:
                self.logger.error(f"Урьдчилан харахыг түр зогсооход алдаа гарлаа: {e}")
    
    def _stop_preview(self):
        """Урьдчилан харахыг зогсооно"""
        if self.preview_handler:
            try:
                self.preview_handler.stop_preview()
            except Exception as e:
                self.logger.error(f"Урьдчилан харахыг зогсооход алдаа гарлаа: {e}")
    
    # =============================================================================
    # СТАТИСТИКИЙН ФУНКЦУУД - ШИНЭ
    # =============================================================================
    
    def _update_statistics(self):
        """Статистикийн мэдээллийг шинэчилнэ"""
        try:
            if not self.media_library:
                return
            
            # Нийт номын сангийн статистик
            total_files = len(self.media_library)
            total_duration = self.media_library.get_total_duration()
            
            if self.total_files_count_label:
                self.total_files_count_label.setText(f"Нийт файл: {total_files}")
            
            if self.total_duration_label:
                self.total_duration_label.setText(f"Нийт хугацаа: {self._format_duration(total_duration)}")
            
            # Одоогийн харагдацын статистик
            current_files = self.media_model.media_files if self.media_model else []
            current_count = len(current_files)
            current_duration = self.media_library.get_filtered_duration(current_files)
            
            if self.current_files_count_label:
                self.current_files_count_label.setText(f"Файлын тоо: {current_count}")
            
            if self.current_duration_label:
                self.current_duration_label.setText(f"Нийт хугацаа: {self._format_duration(current_duration)}")
                
        except Exception as e:
            self.logger.error(f"Статистикийг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _get_media_duration(self, file_path: str) -> float:
        """Get media file duration using FFprobe"""
        try:
            import subprocess
            import json
            
            # FFprobe ашиглаж хугацааг авна
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Format-аас хугацааг авна
                if 'format' in data and 'duration' in data['format']:
                    return float(data['format']['duration'])
                
                # Stream-аас хугацааг авна
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video' and 'duration' in stream:
                        return float(stream['duration'])
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Could not get duration for {file_path}: {e}")
            return 0.0
    
    def _format_duration(self, duration_seconds: float) -> str:
        """Format duration in HH:MM:SS"""
        if duration_seconds <= 0:
            return "00:00:00"
        
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _is_valid_media_file(self, file_path: str) -> bool:
        """Check if file is a valid media file - ENHANCED VERSION"""
        try:
            from pathlib import Path
            
            if not file_path or not Path(file_path).exists():
                return False
            
            # Зөвхөн видео файлуудыг зөвшөөрнө
            video_extensions = {
                '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v',
                '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob', '.ts'
            }
            
            file_ext = Path(file_path).suffix.lower()
            
            # Зөвхөн видео файл
            if file_ext not in video_extensions:
                return False
            
            # Python файл эсвэл __init__ файл биш эсэхийг шалгана
            if file_ext == '.py' or '__init__' in Path(file_path).name.lower():
                return False
            
            # Файлын хэмжээ (1KB-аас их байх ёстой)
            if Path(file_path).stat().st_size < 1024:
                return False
            
            # FFprobe ашиглан видео stream байгаа эсэхийг шалгана
            if not self._has_video_stream(file_path):
                return False
                
            return True
            
        except Exception as e:
            self.logger.warning(f"Media file validation error: {e}")
            return False

    def _has_video_stream(self, file_path: str) -> bool:
        """Check if file has video stream using FFprobe"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        return True
            
            return False
            
        except Exception:
            # FFprobe байхгүй бол extension-аар шалгана
            return True
    
    def _get_media_file_info(self, file_path: str) -> dict:
        """Get comprehensive media file information"""
        try:
            from pathlib import Path
            
            if not self._is_valid_media_file(file_path):
                return {'valid': False, 'error': 'Invalid media file'}
            
            file_info = Path(file_path).stat()
            duration = self._get_media_duration(file_path)
            
            # FFprobe ашиглан дэлгэрэнгүй мэдээлэл авна
            technical_info = self._get_technical_info(file_path)
            
            return {
                'valid': True,
                'name': Path(file_path).name,
                'size': file_info.st_size,
                'size_mb': round(file_info.st_size / (1024 * 1024), 2),
                'extension': Path(file_path).suffix.lower(),
                'duration': duration,
                'duration_formatted': self._format_duration(duration),
                'is_video': True,  # Зөвхөн видео файл зөвшөөрнө
                'is_audio': False,
                'width': technical_info.get('width', 0),
                'height': technical_info.get('height', 0),
                'fps': technical_info.get('fps', 0),
                'video_codec': technical_info.get('video_codec', 'unknown'),
                'audio_codec': technical_info.get('audio_codec', 'unknown'),
                'bitrate': technical_info.get('bitrate', 0)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def _get_technical_info(self, file_path: str) -> dict:
        """Get technical information using FFprobe"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                info = {}
                
                # Video stream мэдээлэл
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info['width'] = stream.get('width', 0)
                        info['height'] = stream.get('height', 0)
                        info['video_codec'] = stream.get('codec_name', 'unknown')
                        
                        # FPS тооцоолох
                        r_frame_rate = stream.get('r_frame_rate', '0/1')
                        if '/' in r_frame_rate:
                            num, den = r_frame_rate.split('/')
                            if int(den) > 0:
                                info['fps'] = round(int(num) / int(den), 2)
                    
                    elif stream.get('codec_type') == 'audio':
                        info['audio_codec'] = stream.get('codec_name', 'unknown')
                
                # Bitrate
                format_info = data.get('format', {})
                if 'bit_rate' in format_info:
                    info['bitrate'] = int(format_info['bit_rate'])
                
                return info
            
            return {}
            
        except Exception as e:
            self.logger.warning(f"Could not get technical info: {e}")
            return {}
    
    def _browse_source_file(self):
        """Browse for source file with enhanced validation"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Видео Файл Сонгох",
            "",
            "Видео Файлууд (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.m4v *.mpg *.mpeg);;Бүх Файлууд (*)"
        )
        
        if file_path:
            # Validate media file
            if not self._is_valid_media_file(file_path):
                QMessageBox.warning(
                    self,
                    "Файлын Алдаа",
                    f"Сонгосон файл видео файл биш байна:\n{Path(file_path).name}\n\n"
                    "Зөвхөн дараахь видео форматыг дэмжинэ:\n"
                    "mp4, avi, mkv, mov, flv, wmv, webm, m4v, mpg, mpeg"
                )
                return
            
            # Get comprehensive file info
            file_info = self._get_media_file_info(file_path)
            if not file_info['valid']:
                QMessageBox.critical(
                    self,
                    "Файлын Алдаа", 
                    f"Файлыг шинжлэхэд алдаа гарлаа:\n{file_info.get('error', 'Unknown error')}"
                )
                return
            
            self.source_input.setText(file_path)
            self.current_input_source = file_path
            
            # Show detailed file info
            info_text = (f"Видео файл сонгогдлоо:\n"
                        f"• Нэр: {file_info['name']}\n"
                        f"• Хэмжээ: {file_info['size_mb']} MB\n"
                        f"• Хугацаа: {file_info['duration_formatted']}\n"
                        f"• Нягтрал: {file_info['width']}x{file_info['height']}\n"
                        f"• FPS: {file_info['fps']}")
            
            self.status_message.emit(info_text, 5000)
            
            # Auto-configure optimal quality based on resolution
            self._auto_configure_quality(file_info)

    def _auto_configure_quality(self, file_info: dict):
        """Auto-configure quality based on file resolution"""
        try:
            if not hasattr(self, 'quality_combo') or not self.quality_combo:
                return
            
            width = file_info.get('width', 0)
            height = file_info.get('height', 0)
            
            # Quality selection logic
            if height >= 2160:  # 4K
                target_quality = "4K"
            elif height >= 1440:  # 1440p
                target_quality = "1440p"
            elif height >= 1080:  # 1080p
                target_quality = "1080p"
            elif height >= 720:   # 720p
                target_quality = "720p"
            elif height >= 480:   # 480p
                target_quality = "480p"
            else:  # 360p or lower
                target_quality = "360p"
            
            # Set quality combo
            for i in range(self.quality_combo.count()):
                item_text = self.quality_combo.itemText(i)
                if target_quality in item_text:
                    self.quality_combo.setCurrentIndex(i)
                    self.status_message.emit(f"Чанар автоматаар {target_quality} болгогдлоо", 2000)
                    break
                    
        except Exception as e:
            self.logger.warning(f"Auto quality configuration failed: {e}")
    
    def clear_media_selection(self):
        """Clear media selection and reset to default state"""
        try:
            # Clear table selection
            if self.media_table and self.media_table.selectionModel():
                self.media_table.selectionModel().clearSelection()
            
            # Clear metadata panel
            self._clear_metadata_panel()
            
            # Clear search
            if self.search_input:
                self.search_input.blockSignals(True)
                self.search_input.clear()
                self.search_input.blockSignals(False)
            
            # Reset filters
            if self.category_list:
                self.category_list.setCurrentRow(0)  # "Бүх медиа"
            
            if self.type_combo:
                self.type_combo.setCurrentIndex(0)  # "Бүх төрөл"
            
            # Reload all data
            self._load_media_data()
            
            self.status_message.emit("Медиа сонголт цэвэрлэгдлээ", 2000)
            
        except Exception as e:
            self.logger.error(f"Failed to clear media selection: {e}")
            
    def remove_media_from_library(self, media_id: str, remove_from_disk: bool = False):
        """Remove media file from library with option to delete from disk"""
        try:
            if media_id not in self.media_library._media_cache:
                self.status_message.emit("Файл олдсонгүй", 3000)
                return False
            
            media_file = self.media_library._media_cache[media_id]
            file_path = media_file.file_path
            
            # Remove from database
            if self.media_library.remove_media_file(media_id):
                # Remove from disk if requested
                if remove_from_disk and file_path.exists():
                    try:
                        file_path.unlink()
                        self.status_message.emit(f"Файл дискнээс устгагдлаа: {media_file.filename}", 3000)
                    except Exception as e:
                        self.logger.error(f"Could not delete file from disk: {e}")
                        self.status_message.emit(f"Файлыг дискнээс устгах амжилтгүй: {e}", 5000)
                else:
                    self.status_message.emit(f"Файл номын сангаас хасагдлаа: {media_file.filename}", 3000)
                
                # Update UI
                self._load_media_data()
                self._clear_metadata_panel()
                return True
            else:
                self.status_message.emit("Файл устгах амжилтгүй", 3000)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove media: {e}")
            self.status_message.emit(f"Файл устгахад алдаа: {e}", 5000)
            return False
    
    def _create_media_file_with_metadata(self, file_path: Path) -> Optional[MediaFile]:
        """Create MediaFile with enhanced metadata extraction"""
        try:
            # Validate file first
            if not self._is_valid_media_file(str(file_path)):
                return None
            
            # Create basic MediaFile
            media_file = MediaFile(file_path=file_path)
            
            # Enhanced metadata extraction for video files
            if media_file.is_video:
                try:
                    # Get duration using FFprobe
                    duration = self._get_media_duration(str(file_path))
                    if duration > 0:
                        media_file.metadata.duration = duration
                    
                    # Get technical info
                    tech_info = self._get_technical_info(str(file_path))
                    if tech_info:
                        media_file.metadata.width = tech_info.get('width', 0)
                        media_file.metadata.height = tech_info.get('height', 0)
                        media_file.metadata.fps = tech_info.get('fps', 0)
                    
                    # Generate title from filename if not set
                    if not media_file.metadata.title:
                        media_file.metadata.title = file_path.stem
                    
                    # Set default category for videos
                    if not media_file.metadata.category:
                        media_file.metadata.category = "Videos"
                    
                except Exception as e:
                    self.logger.warning(f"Could not extract enhanced metadata for {file_path}: {e}")
            
            return media_file
            
        except Exception as e:
            self.logger.error(f"Failed to create media file: {e}")
            return None
        
        
    # =============================================================================
    # ӨМНӨХ ФУНКЦУУДЫН ЗАСВАР
    # =============================================================================
    
    def _on_search_changed(self, text: str):
        """Хайлтын текстийн өөрчлөлтийг зохицуулна"""
        try:
            if len(text) >= 2 or text == "":
                QTimer.singleShot(300, self._apply_filters)
        except Exception as e:
            self.logger.error(f"Хайлт өөрчлөгдөхөд алдаа гарлаа: {e}")
    
    def _clear_search(self):
        """Хайлтын оролтыг цэвэрлэнэ"""
        try:
            if self.search_input:
                # textChanged сигналыг түр зогсооно
                self.search_input.blockSignals(True)
                self.search_input.clear()
                self.search_input.blockSignals(False)
            
            # Бүх медиа өгөгдлийг дахин ачаалахын оронд шүүлтүүрийг дахин хэрэглэнэ
            self._apply_filters()
            
        except Exception as e:
            self.logger.error(f"Хайлтыг цэвэрлэхэд алдаа гарлаа: {e}")
            self.status_message.emit("Хайлтыг цэвэрлэхэд алдаа гарлаа", 3000)
    
    def _on_category_changed(self, category: str):
        """Ангиллын сонголтын өөрчлөлтийг зохицуулна"""
        try:
            self._apply_filters()
        except Exception as e:
            self.logger.error(f"Ангилал өөрчлөгдөхөд алдаа гарлаа: {e}")
    
    def _on_type_filter_changed(self, type_filter: str):
        """Медиа төрлийн шүүлтүүрийн өөрчлөлтийг зохицуулна"""
        try:
            self._apply_filters()
        except Exception as e:
            self.logger.error(f"Төрлийн шүүлтүүр өөрчлөгдөхөд алдаа гарлаа: {e}")
    
    def _apply_filters(self):
        """Одоогийн шүүлтүүрүүдийг медиа жагсаалтад хэрэглэнэ"""
        if not self.media_library:
            return
            
        try:
            search_text = self.search_input.text().strip() if self.search_input else ""
            category = "Бүх медиа"
            type_filter = "Бүх төрөл"
            
            if self.category_list and self.category_list.currentItem():
                category = self.category_list.currentItem().text()
            
            if self.type_combo:
                type_filter = self.type_combo.currentText()
            
            filters = {}
            
            # Хайлтын текст хоосон бол шүүлтүүрт оруулахгүй
            if category != "Бүх медиа":
                filters["category"] = category
            
            if type_filter != "Бүх төрөл":
                type_map = {
                    "Видео": MediaType.VIDEO,
                    "Аудио": MediaType.AUDIO,
                    "Зураг": MediaType.IMAGE
                }
                if type_filter in type_map:
                    filters["media_type"] = type_map[type_filter]
            
            # Хайлтын текст байгаа эсэхийг шалгана
            query = search_text if search_text else ""
            results = self.media_library.search_media(query, filters if filters else None)
            
            if self.media_model:
                self.media_model.update_data(results)
            
            self._update_status_label(len(results))
            self._update_statistics()
            
        except Exception as e:
            self.logger.error(f"Шүүлтүүр хэрэглэхэд алдаа гарлаа: {e}")
            self.status_message.emit("Шүүлтүүр хэрэглэхэд алдаа гарлаа", 3000)
    
    def _update_status_label(self, count: int):
        """Файлын тоогоор төлөвийн шошгыг шинэчилнэ"""
        try:
            if self.status_label:
                self.status_label.setText(f"{count} файл")
        except Exception as e:
            self.logger.error(f"Төлөвийн шошгыг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _load_media_data(self):
        """Номын сангаас медиа файлуудыг ачаална"""
        if not self.media_library:
            return
            
        try:
            media_files = list(self.media_library)
            if self.media_model:
                self.media_model.update_data(media_files)
            self._update_status_label(len(media_files))
            self._update_statistics()  # Статистикийг шинэчилнэ
            
            if self.media_table:
                self.media_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Медиа өгөгдөл ачаалахад алдаа гарлаа: {e}")
            self.status_message.emit(f"Медиа ачаалахад алдаа гарлаа: {e}", 5000)
    
    def _update_category_combo(self):
        """Ангиллын комбо боксыг одоогийн ангиллуудаар шинэчилнэ"""
        try:
            if self.category_combo and self.media_library:
                current_text = self.category_combo.currentText()
                self.category_combo.clear()
                self.category_combo.addItems([""] + self.media_library.categories)
                
                index = self.category_combo.findText(current_text)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
        except Exception as e:
            self.logger.error(f"Ангиллын комбо боксыг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _on_metadata_changed(self):
        """Метадата талбарын өөрчлөлтийг зохицуулна"""
        try:
            if self.current_media_file and not self.metadata_changed:
                self.metadata_changed = True
                if self.save_metadata_btn:
                    self.save_metadata_btn.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Метадата өөрчлөгдөхөд алдаа гарлаа: {e}")
    
    def _on_rating_changed(self, value: int):
        """Үнэлгээний өөрчлөлтийг зохицуулна"""
        try:
            if self.rating_label:
                self.rating_label.setText(str(value))
            if self.current_media_file:
                self._on_metadata_changed()
        except Exception as e:
            self.logger.error(f"Үнэлгээ өөрчлөгдөхөд алдаа гарлаа: {e}")
    
    def _on_media_selected(self, current: QModelIndex, previous: QModelIndex):
        """Медиа файл сонголтыг зохицуулна"""
        try:
            if not self.media_model:
                return
                
            media_file = self.media_model.get_media_file(current)
            
            if media_file:
                self.current_media_file = media_file
                self._update_metadata_panel(media_file)
                self.media_selected.emit(media_file)
                
                # Урьдчилан харахыг шинэчилнэ
                if self.preview_handler:
                    self.preview_handler.update_preview(media_file)
                    
                # Тоглуулагчийн товчнуудыг идэвхжүүлнэ
                can_preview = (media_file.is_video or media_file.is_audio) and media_file.exists()
                if self.play_btn:
                    self.play_btn.setEnabled(can_preview)
                    
            else:
                self.current_media_file = None
                self._clear_metadata_panel()
                
        except Exception as e:
            self.logger.error(f"Медиа сонголтод алдаа гарлаа: {e}")
    
    def _on_media_double_clicked(self, index: QModelIndex):
        """Медиа файлд давхар товшилтыг зохицуулна - ЗАСВАРЛАСАН"""
        try:
            if not self.media_model:
                return
                
            media_file = self.media_model.get_media_file(index)
            if media_file:
                # Системийн програмаар нээхийн оронд дотоод тоглуулагчаар тоглуулна
                if media_file.is_video or media_file.is_audio:
                    self._play_preview()
                else:
                    # Зураг эсвэл бусад файлуудыг системийн програмаар нээнэ
                    self._open_file()
                    
        except Exception as e:
            self.logger.error(f"Медиа давхар товшиход алдаа гарлаа: {e}")
    
    def _update_metadata_panel(self, media_file):
        """Метадата самбарыг файлын мэдээллээр шинэчилнэ"""
        try:
            self.metadata_changed = False
            
            metadata = media_file.metadata
            
            widgets_to_block = [
                self.title_edit, self.artist_edit, self.album_edit, self.genre_edit,
                self.category_combo, self.rating_slider, self.description_edit, self.tags_edit
            ]
            
            for widget in widgets_to_block:
                if widget:
                    widget.blockSignals(True)
            
            if self.title_edit:
                self.title_edit.setText(metadata.title or "")
            if self.artist_edit:
                self.artist_edit.setText(metadata.artist or "")
            if self.album_edit:
                self.album_edit.setText(metadata.album or "")
            if self.genre_edit:
                self.genre_edit.setText(metadata.genre or "")
            
            if self.category_combo:
                category_text = metadata.category or ""
                index = self.category_combo.findText(category_text)
                self.category_combo.setCurrentIndex(max(0, index))
            
            if self.rating_slider:
                self.rating_slider.setValue(int(metadata.rating))
                self._on_rating_changed(int(metadata.rating))
            
            if self.description_edit:
                self.description_edit.setPlainText(metadata.description or "")
            
            if self.tags_edit:
                tags_text = ", ".join(metadata.tags) if metadata.tags else ""
                self.tags_edit.setText(tags_text)
            
            for widget in widgets_to_block:
                if widget:
                    widget.blockSignals(False)
            
            # Файлын мэдээллийг шинэчилнэ
            if self.file_path_label:
                self.file_path_label.setText(str(media_file.file_path))
            if self.file_size_label:
                self.file_size_label.setText(metadata.file_size_formatted)
            if self.duration_label:
                self.duration_label.setText(metadata.duration_formatted)
            
            if self.resolution_label:
                if metadata.width and metadata.height:
                    self.resolution_label.setText(f"{metadata.width}x{metadata.height}")
                else:
                    self.resolution_label.setText("-")
            
            if self.date_added_label:
                self.date_added_label.setText(metadata.date_added.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Товчны төлөвийг шинэчилнэ
            file_exists = media_file.exists()
            
            if self.save_metadata_btn:
                self.save_metadata_btn.setEnabled(False)
            if self.open_file_btn:
                self.open_file_btn.setEnabled(file_exists)
            if self.show_in_explorer_btn:
                self.show_in_explorer_btn.setEnabled(file_exists)
            
        except Exception as e:
            self.logger.error(f"Метадата самбарыг шинэчлэхэд алдаа гарлаа: {e}")
    
    def _clear_metadata_panel(self):
        """Метадата самбарыг цэвэрлэнэ"""
        try:
            widgets_to_clear = [
                self.title_edit, self.artist_edit, self.album_edit, self.genre_edit,
                self.category_combo, self.rating_slider, self.description_edit, self.tags_edit
            ]
            
            for widget in widgets_to_clear:
                if widget:
                    widget.blockSignals(True)
            
            if self.title_edit:
                self.title_edit.clear()
            if self.artist_edit:
                self.artist_edit.clear()
            if self.album_edit:
                self.album_edit.clear()
            if self.genre_edit:
                self.genre_edit.clear()
            if self.category_combo:
                self.category_combo.setCurrentIndex(0)
            if self.rating_slider:
                self.rating_slider.setValue(0)
            if self.description_edit:
                self.description_edit.clear()
            if self.tags_edit:
                self.tags_edit.clear()
            
            for widget in widgets_to_clear:
                if widget:
                    widget.blockSignals(False)
            
            # Мэдээллийн шошгыг цэвэрлэнэ
            info_labels = [
                (self.file_path_label, "-"),
                (self.file_size_label, "-"),
                (self.duration_label, "-"),
                (self.resolution_label, "-"),
                (self.date_added_label, "-")
            ]
            
            for label, default_text in info_labels:
                if label:
                    label.setText(default_text)
            
            # Товчнуудыг идэвхгүй болгоно
            buttons_to_disable = [
                self.save_metadata_btn, self.open_file_btn, 
                self.show_in_explorer_btn, self.play_btn, 
                self.pause_btn, self.stop_btn
            ]
            
            for button in buttons_to_disable:
                if button:
                    button.setEnabled(False)
            
            # Урьдчилан харахыг цэвэрлэнэ
            if self.preview_handler:
                self.preview_handler.clear_preview()
            
            # Тоглуулагчийн дэлгэцийг цэвэрлэнэ
            if self.current_time_label:
                self.current_time_label.setText("00:00")
            if self.total_time_label:
                self.total_time_label.setText("00:00")
            if self.position_slider:
                self.position_slider.setValue(0)
                
        except Exception as e:
            self.logger.error(f"Метадата самбарыг цэвэрлэхэд алдаа гарлаа: {e}")
    
    # Үргэлжлүүлэх функцуудтай зохих алдааг зохицуулах...
    def scan_media_library(self):
        """Медиа номын санг шинэ файлуудаар скан хийнэ"""
        if not self.media_library:
            self.status_message.emit("Медиа номын сан байхгүй", 3000)
            return

        self.status_message.emit("Номын санг скан хийж байна...", 0)
        QThreadPool.globalInstance().start(self._perform_scan)

    def _perform_scan(self):
        """Номын санг скан хийх бодит үйл явц - ENHANCED"""
        if not self.media_library:
            return

        added_count = 0
        updated_count = 0
        removed_count = 0
        
        found_files_on_disk = set()

        try:
            # Get all files recursively
            all_files_on_disk = []
            for file_path in self.media_library.library_path.rglob('*'):
                if file_path.is_file() and self._is_valid_media_file(str(file_path)):
                    all_files_on_disk.append(file_path)
            
            total_files_to_scan = len(all_files_on_disk)
            self.progress_update.emit(0)

            for i, file_path in enumerate(all_files_on_disk):
                found_files_on_disk.add(str(file_path.absolute()))
                
                media_id = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()[:12]
                existing_media = self.media_library._media_cache.get(media_id)

                if existing_media:
                    try:
                        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if existing_media.last_modified and current_mtime > existing_media.last_modified:
                            # Re-extract metadata for updated files
                            updated_media = self._create_media_file_with_metadata(file_path)
                            if updated_media:
                                updated_media.id = media_id  # Preserve ID
                                self.media_library.add_media_file(updated_media)
                                updated_count += 1
                    except Exception as e:
                        self.logger.warning(f"Файлын өөрчлөлтийг шалгахад алдаа гарлаа {file_path}: {e}")
                else:
                    # Create new media file with enhanced metadata
                    media_file = self._create_media_file_with_metadata(file_path)
                    if media_file and self.media_library.add_media_file(media_file):
                        added_count += 1
                
                self.progress_update.emit(int((i + 1) / total_files_to_scan * 100))

            # Remove files no longer on disk
            files_to_remove_from_db = []
            for media_id, media_file in list(self.media_library._media_cache.items()):
                if str(media_file.file_path.absolute()) not in found_files_on_disk:
                    files_to_remove_from_db.append(media_id)
            
            for media_id in files_to_remove_from_db:
                if self.media_library.remove_media_file(media_id):
                    removed_count += 1

            self.status_message.emit(
                f"Скан дууслаа: {added_count} нэмэгдсэн, {updated_count} шинэчлэгдсэн, {removed_count} устгагдсан.", 
                5000
            )
            self._load_media_data()
        except Exception as e:
            self.logger.error(f"Медиа номын санг скан хийхэд алдаа гарлаа: {e}")
            self.status_message.emit(f"Скан хийхэд алдаа гарлаа: {e}", 5000)
    
    def import_media_files(self):
        """Файлын харилцах цонхоос медиа файлуудыг импорт хийнэ"""
        if not self.media_library:
            self.status_message.emit("Медиа номын сан байхгүй", 3000)
            return
            
        options = QFileDialog.Option.DontUseNativeDialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Медиа файл импортлох", 
            "", 
            "Медиа файлууд (*.mp4 *.avi *.mkv *.mp3 *.wav *.jpg *.png);;Бүх файлууд (*)",
            options=options
        )

        if file_paths:
            self.status_message.emit(f"{len(file_paths)} файлыг импортлож байна...", 0)
            QThreadPool.globalInstance().start(
                lambda: self._perform_import(file_paths)
            )

    def _perform_import(self, file_paths: List[str]):
        """Файлуудыг импортлох бодит үйл явц - ENHANCED"""
        imported_count = 0
        skipped_count = 0
        total_count = len(file_paths)
        
        for i, file_path_str in enumerate(file_paths):
            try:
                file_path = Path(file_path_str)
                if not file_path.exists():
                    self.logger.warning(f"Импортлох файл олдсонгүй: {file_path_str}")
                    skipped_count += 1
                    continue

                # Validate before importing
                if not self._is_valid_media_file(str(file_path)):
                    self.logger.warning(f"Буруу медиа файл: {file_path_str}")
                    skipped_count += 1
                    continue

                # Create destination path
                destination_path = self.media_library.library_path / file_path.name
                
                # Handle duplicate names
                counter = 1
                original_destination = destination_path
                while destination_path.exists():
                    stem = original_destination.stem
                    suffix = original_destination.suffix
                    destination_path = original_destination.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

                # Copy file
                shutil.copy2(file_path, destination_path)

                # Create media file with enhanced metadata
                media_file = self._create_media_file_with_metadata(destination_path)
                
                if media_file and self.media_library.add_media_file(media_file):
                    imported_count += 1
                    self.logger.info(f"Imported: {media_file.filename} ({media_file.metadata.duration_formatted})")
                else:
                    self.logger.error(f"Медиа файлыг мэдээллийн санд нэмэхэд алдаа гарлаа: {file_path_str}")
                    skipped_count += 1
                    # Remove copied file if database insert failed
                    if destination_path.exists():
                        destination_path.unlink()
                        
            except Exception as e:
                self.logger.error(f"Файл импортлоход алдаа гарлаа {file_path_str}: {e}")
                skipped_count += 1
            
            self.progress_update.emit(int((i + 1) / total_count * 100))
        
        self.status_message.emit(
            f"Импорт дууслаа: {imported_count} амжилттай, {skipped_count} алгассан.", 
            5000
        )
        self._load_media_data()
    
    def _cleanup_missing_files(self):
        """Номын сангаас алга болсон файлуудыг цэвэрлэнэ"""
        if not self.media_library:
            self.status_message.emit("Медиа номын сан байхгүй", 3000)
            return
            
        self.status_message.emit("Алга болсон файлуудыг цэвэрлэж байна...", 0)
        removed_count = 0
        files_to_remove = []
        
        for media_file in list(self.media_library._media_cache.values()):
            if not media_file.exists():
                files_to_remove.append(media_file.id)
        
        for media_id in files_to_remove:
            if self.media_library.remove_media_file(media_id):
                removed_count += 1
        
        self.status_message.emit(f"{removed_count} алга болсон файл номын сангаас устгагдлаа.", 5000)
        self._load_media_data()
    
    def _change_view_mode(self, mode: str):
        """Харах горимыг өөрчилнө"""
        if mode != "Хүснэгтийн харагдац":
            self.status_message.emit("Сүлжээ болон жагсаалтын харагдац хараахан хэрэгжээгүй байна", 3000)
        else:
            self.status_message.emit(f"Харах горимыг '{mode}'-рүү өөрчиллөө.", 2000)
    
    def _on_sort_changed(self, sort_field: str):
        """Эрэмбэлэх талбарын өөрчлөлтийг зохицуулна"""
        self._apply_sort()
    
    def _toggle_sort_order(self, checked: bool):
        """Эрэмбэлэх дарааллыг сэлгэнэ"""
        if self.sort_order_btn:
            if checked:
                self.sort_order_btn.setText("↓ Буурах")
            else:
                self.sort_order_btn.setText("↑ Өсөх")
        self._apply_sort()
    
    def _apply_sort(self):
        """Одоогийн эрэмбэлэх тохиргоог хэрэглэнэ"""
        if not self.media_model:
            return

        sort_field = self.sort_combo.currentText() if self.sort_combo else "Гарчиг"
        sort_order_ascending = self.sort_order_btn.isChecked() if self.sort_order_btn else True

        def get_sort_key(media_file: MediaFile):
            if sort_field == "Гарчиг":
                return media_file.metadata.title or media_file.filename
            elif sort_field == "Уран бүтээлч":
                return media_file.metadata.artist or ""
            elif sort_field == "Цомог":
                return media_file.metadata.album or ""
            elif sort_field == "Хугацаа":
                return media_file.metadata.duration or 0.0
            elif sort_field == "Төрөл":
                return media_file.metadata.genre or ""
            elif sort_field == "Ангилал":
                return media_file.metadata.category or ""
            elif sort_field == "Үнэлгээ":
                return media_file.metadata.rating
            elif sort_field == "Нэмэгдсэн огноо":
                return media_file.metadata.date_added
            elif sort_field == "Файлын хэмжээ":
                return media_file.metadata.file_size
            return media_file.metadata.title or media_file.filename

        current_data = self.media_model.media_files
        try:
            sorted_data = sorted(current_data, key=get_sort_key, reverse=not sort_order_ascending)
            self.media_model.update_data(sorted_data)
        except Exception as e:
            self.logger.error(f"Медиаг эрэмбэлэхэд алдаа гарлаа: {e}")
            self.status_message.emit("Медиаг эрэмбэлэхэд алдаа гарлаа", 3000)
    
    def _save_metadata(self):
        """Метадата өөрчлөлтийг хадгална"""
        if not self.current_media_file or not self.media_library:
            self.status_message.emit("Хадгалах медиа файл сонгогдоогүй байна.", 3000)
            return

        try:
            new_title = self.title_edit.text() if self.title_edit else ""
            new_artist = self.artist_edit.text() if self.artist_edit else ""
            new_album = self.album_edit.text() if self.album_edit else ""
            new_genre = self.genre_edit.text() if self.genre_edit else ""
            new_category = self.category_combo.currentText() if self.category_combo else ""
            new_rating = float(self.rating_slider.value()) if self.rating_slider else 0.0
            new_description = self.description_edit.toPlainText() if self.description_edit else ""
            new_tags_str = self.tags_edit.text() if self.tags_edit else ""
            new_tags = [tag.strip() for tag in new_tags_str.split(',') if tag.strip()]

            self.current_media_file.metadata.title = new_title
            self.current_media_file.metadata.artist = new_artist
            self.current_media_file.metadata.album = new_album
            self.current_media_file.metadata.genre = new_genre
            self.current_media_file.metadata.category = new_category
            self.current_media_file.metadata.rating = new_rating
            self.current_media_file.metadata.description = new_description
            self.current_media_file.metadata.tags = new_tags
            self.current_media_file.metadata.last_modified = datetime.now()

            if self.media_library.add_media_file(self.current_media_file):
                self.status_message.emit("Метадата амжилттай хадгалагдлаа.", 3000)
                self.metadata_changed = False
                if self.save_metadata_btn:
                    self.save_metadata_btn.setEnabled(False)
                self._load_media_data()
            else:
                self.status_message.emit("Метадата хадгалахад алдаа гарлаа.", 5000)
        except Exception as e:
            self.logger.error(f"Метадата хадгалахад алдаа гарлаа: {e}")
            self.status_message.emit(f"Метадата хадгалахад алдаа гарлаа: {e}", 5000)
    
    def _refresh_all_metadata(self):
        """Бүх медиа файлын метадатаг шинэчлэнэ."""
        if not self.media_library:
            self.status_message.emit("Медиа номын сан байхгүй.", 3000)
            return

        try:
            self.status_message.emit("Бүх метадата шинэчлэж байна...", 0)
            updated_count = 0
            total_files = len(self.media_library)

            for media_file in list(self.media_library._media_cache.values()):
                updated_media = self._create_media_file_with_metadata(media_file.file_path)
                if updated_media:
                    updated_media.id = media_file.id  # ID-г хадгална
                    if self.media_library.add_media_file(updated_media):
                        updated_count += 1

            self.status_message.emit(f"{updated_count}/{total_files} метадат амжилттай шинэчлэгдлээ.", 5000)
            self._load_media_data()  # UI-г шинэчлэнэ
        except Exception as e:
            self.logger.error(f"Бүх метадатаг шинэчлэхэд алдаа гарлаа: {e}")
            self.status_message.emit(f"Метадат шинэчлэхэд алдаа гарлаа: {e}", 5000)
    
    def _open_file(self):
        """Файлыг анхдагч програмаар нээнэ"""
        if not self.current_media_file or not self.current_media_file.exists():
            self.status_message.emit("Нээх файл сонгогдоогүй эсвэл олдсонгүй.", 3000)
            return

        try:
            file_path = str(self.current_media_file.file_path)
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
            self.status_message.emit(f"Файлыг нээлээ: {self.current_media_file.filename}", 3000)
        except Exception as e:
            self.logger.error(f"Файл нээхэд алдаа гарлаа: {e}")
            self.status_message.emit(f"Файл нээхэд алдаа гарлаа: {e}", 5000)
    
    def _show_in_explorer(self):
        """Файлыг системийн файл explorer-т харуулна"""
        if not self.current_media_file or not self.current_media_file.exists():
            self.status_message.emit("Explorer-т харуулах файл сонгогдоогүй эсвэл олдсонгүй.", 3000)
            return

        try:
            file_path = str(self.current_media_file.file_path)
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", file_path])
            else:
                subprocess.Popen(["xdg-open", str(self.current_media_file.file_path.parent)])
            self.status_message.emit(f"Файлыг Explorer-т харууллаа: {self.current_media_file.filename}", 3000)
        except Exception as e:
            self.logger.error(f"Файлыг Explorer-т харуулахад алдаа гарлаа: {e}")
            self.status_message.emit(f"Файлыг Explorer-т харуулахад алдаа гарлаа: {e}", 5000)
    
    def _show_context_menu(self, position: QPoint):
        """Медиа хүснэгтийн контекст цэсийг харуулна - ENHANCED"""
        index = self.media_table.indexAt(position)
        if not index.isValid():
            return

        media_file = self.media_model.get_media_file(index)
        if not media_file:
            return

        menu = QMenu(self)
        
        # Primary actions
        play_action = menu.addAction("🎵 Дотоод тоглуулагчаар тоглуулах")
        open_action = menu.addAction("📁 Файл нээх")
        show_in_explorer_action = menu.addAction("🗂️ Explorer-т харуулах")
        
        menu.addSeparator()
        
        # Metadata actions
        edit_metadata_action = menu.addAction("✏️ Метадата засварлах")
        refresh_metadata_action = menu.addAction("🔄 Метадата шинэчлэх")
        
        menu.addSeparator()
        
        # Library actions
        add_to_scheduler_action = menu.addAction("➕ Scheduler-т нэмэх")
        copy_path_action = menu.addAction("📋 Замыг хуулах")
        
        menu.addSeparator()
        
        # Removal actions
        remove_from_library_action = menu.addAction("❌ Номын сангаас хасах")
        delete_action = menu.addAction("🗑️ Файлыг бүр мөсөн устгах")

        action = menu.exec(self.media_table.viewport().mapToGlobal(position))

        if action == play_action:
            self.current_media_file = media_file
            self._play_preview()
        elif action == open_action:
            self._open_file()
        elif action == show_in_explorer_action:
            self._show_in_explorer()
        elif action == edit_metadata_action:
            self._update_metadata_panel(media_file)
        elif action == refresh_metadata_action:
            self._refresh_metadata(media_file)
        elif action == add_to_scheduler_action:
            self._add_selected_to_scheduler()
        elif action == copy_path_action:
            self._copy_file_path(media_file)
        elif action == remove_from_library_action:
            self.remove_media_from_library(media_file.id, remove_from_disk=False)
        elif action == delete_action:
            self._confirm_and_delete_file(media_file)
    
    def _refresh_metadata(self, media_file: MediaFile):
        """Refresh metadata for selected file"""
        try:
            # Re-extract metadata using FFprobe
            updated_media = self._create_media_file_with_metadata(media_file.file_path)
            if updated_media:
                updated_media.id = media_file.id  # Preserve ID
                if self.media_library.add_media_file(updated_media):
                    self.status_message.emit(f"Метадата шинэчлэгдлээ: {media_file.filename}", 3000)
                    self._load_media_data()
                else:
                    self.status_message.emit("Метадата шинэчлэх амжилтгүй", 3000)
        except Exception as e:
            self.logger.error(f"Failed to refresh metadata: {e}")
            self.status_message.emit(f"Метадата шинэчлэхэд алдаа: {e}", 5000)
    
    def _copy_file_path(self, media_file: MediaFile):
        """Copy file path to clipboard"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(str(media_file.file_path))
            self.status_message.emit("Файлын зам хуулагдлаа", 2000)
        except Exception as e:
            self.logger.error(f"Failed to copy path: {e}")

    def _confirm_and_delete_file(self, media_file: MediaFile):
        """Confirm and delete file from disk"""
        reply = QMessageBox.question(
            self, 
            "Файл устгах", 
            f"Та '{media_file.filename}' файлыг дискнээс бүр мөсөн устгахдаа итгэлтэй байна уу?\n\n"
            f"⚠️ Энэ үйлдлийг буцаах боломжгүй!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_media_from_library(media_file.id, remove_from_disk=True)
    
    def _delete_media_file(self, media_id: str):
        """Номын сангаас медиа файлыг устгана"""
        reply = QMessageBox.question(self, "Файл устгах", 
                                     "Та энэ файлыг номын сангаас устгахдаа итгэлтэй байна уу? Энэ нь файлыг дискнээс устгахгүй.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.media_library.remove_media_file(media_id):
                    self.status_message.emit(f"Файл {media_id} номын сангаас устгагдлаа.", 3000)
                    self._load_media_data()
                    self._clear_metadata_panel()
                else:
                    self.status_message.emit(f"Файл {media_id} устгахад алдаа гарлаа.", 5000)
            except Exception as e:
                self.logger.error(f"Файл устгахад алдаа гарлаа: {e}")
                self.status_message.emit(f"Файл устгахад алдаа гарлаа: {e}", 5000)
    
    def _add_category(self):
        """Шинэ ангилал нэмнэ"""
        if not self.media_library:
            self.status_message.emit("Медиа номын сан байхгүй.", 3000)
            return

        text, ok = QInputDialog.getText(self, "Шинэ ангилал нэмэх", "Ангиллын нэрийг оруулна уу:")
        if ok and text:
            category_name = text.strip()
            if category_name and category_name not in self.media_library.categories:
                self.media_library.categories.append(category_name)
                try:
                    with sqlite3.connect(self.media_library.db_path, timeout=30.0) as conn:
                        conn.execute(
                            "INSERT OR IGNORE INTO categories (name, created_at) VALUES (?, ?)",
                            (category_name, datetime.now().isoformat())
                        )
                        conn.commit()
                except sqlite3.Error as e:
                    self.logger.error(f"Категорийг мэдээллийн санд нэмэхэд алдаа гарлаа: {e}")
                    self.status_message.emit(f"Категорийг нэмэхэд алдаа гарлаа: {e}", 5000)
                    return

                self._update_category_combo()
                if self.category_list:
                    self.category_list.addItem(category_name)
                self.status_message.emit(f"Ангилал '{category_name}' нэмэгдлээ.", 3000)
            else:
                self.status_message.emit("Буруу эсвэл давхардсан ангиллын нэр.", 3000)
    
    def _remove_category(self):
        """Сонгосон ангиллыг устгана"""
        if not self.media_library or not self.category_list:
            self.status_message.emit("Медиа номын сан эсвэл ангиллын жагсаалт байхгүй.", 3000)
            return

        current_item = self.category_list.currentItem()
        if not current_item or current_item.text() == "Бүх медиа":
            self.status_message.emit("Устгах ангилал сонгоно уу.", 3000)
            return

        category_name = current_item.text()
        reply = QMessageBox.question(self, "Ангилал устгах", 
                                     f"Та ангилал '{category_name}'-г устгахдаа итгэлтэй байна уу? Энэ нь энэ ангилалд хамаарах медиа файлуудын ангиллыг 'Default' болгоно.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if category_name in self.media_library.categories:
                    self.media_library.categories.remove(category_name)
                    
                    with sqlite3.connect(self.media_library.db_path, timeout=30.0) as conn:
                        conn.execute("DELETE FROM categories WHERE name = ?", (category_name,))
                        conn.execute("UPDATE media_files SET metadata_json = REPLACE(metadata_json, ?, ?) WHERE metadata_json LIKE ?",
                                     (f'"category": "{category_name}"', '"category": "Default"', f'%\"category\": \"{category_name}\"%'))
                        conn.commit()
                    
                    self.media_library._load_cache()
                    self._update_category_combo()
                    self._apply_filters()
                    self.status_message.emit(f"Ангилал '{category_name}' устгагдлаа.", 3000)
            except Exception as e:
                self.logger.error(f"Ангилал устгахад алдаа гарлаа: {e}")
                self.status_message.emit(f"Ангилал устгахад алдаа гарлаа: {e}", 5000)

    def _add_selected_to_scheduler(self):
        """Сонгосон медиа файлыг Scheduler-т нэмнэ."""
        if not self.current_media_file:
            self.status_message.emit("Scheduler-т нэмэх медиа файл сонгогдоогүй байна.", 3000)
            return
        
        try:
            self.scheduler_add_media.emit(self.current_media_file)
            self.status_message.emit(f"'{self.current_media_file.display_name}' файлыг Scheduler-т нэмлээ.", 3000)
        except Exception as e:
            self.logger.error(f"Scheduler-т медиа нэмэхэд алдаа гарлаа: {e}")
            self.status_message.emit(f"Scheduler-т медиа нэмэхэд алдаа гарлаа: {e}", 5000)
    
    def cleanup(self):
        """Таб хаагдах үед нөөцийг цэвэрлэнэ"""
        try:
            if self.preview_handler:
                self.preview_handler.cleanup()
        except Exception as e:
            self.logger.error(f"Цэвэрлэгээний үед алдаа гарлаа: {e}")

# =============================================================================
# МЕДИА ХҮСНЭГТИЙН ЗАГВАР
# =============================================================================

class MediaTableModel(QAbstractTableModel):
    """Медиа файлуудад зориулсан хүснэгтийн загвар"""
    
    def __init__(self, media_files: List[MediaFile] = None):
        super().__init__()
        self.media_files = media_files or []
        self.headers = [
            "Гарчиг", "Уран бүтээлч", "Цомог", "Хугацаа", "Төрөл", 
            "Ангилал", "Үнэлгээ", "Медиа төрөл", "Файлын хэмжээ", "Нэмэгдсэн огноо"
        ]
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.media_files)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return super().headerData(section, orientation, role)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.media_files):
            return None
        
        try:
            media_file = self.media_files[index.row()]
            col = index.column()
            
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0:  # Гарчиг
                    return media_file.metadata.title or media_file.display_name
                elif col == 1:  # Уран бүтээлч
                    return media_file.metadata.artist or ""
                elif col == 2:  # Цомог
                    return media_file.metadata.album or ""
                elif col == 3:  # Хугацаа
                    return media_file.metadata.duration_formatted
                elif col == 4:  # Төрөл
                    return media_file.metadata.genre or ""
                elif col == 5:  # Ангилал
                    return media_file.metadata.category or ""
                elif col == 6:  # Үнэлгээ
                    rating = int(media_file.metadata.rating)
                    return "★" * rating if rating > 0 else ""
                elif col == 7:  # Медиа төрөл
                    return media_file.media_type.value.title()
                elif col == 8:  # Файлын хэмжээ
                    return media_file.metadata.file_size_formatted
                elif col == 9:  # Нэмэгдсэн огноо
                    return media_file.metadata.date_added.strftime("%Y-%m-%d")
            
            elif role == Qt.ItemDataRole.UserRole:
                return media_file.id
            
            elif role == Qt.ItemDataRole.ToolTipRole:
                tooltip = f"Файл: {media_file.filename}\nЗам: {media_file.file_path}"
                if media_file.metadata.description:
                    tooltip += f"\nТайлбар: {media_file.metadata.description}"
                if media_file.metadata.duration:
                    tooltip += f"\nХугацаа: {media_file.metadata.duration_formatted}"
                return tooltip
            
            elif role == Qt.ItemDataRole.ForegroundRole:
                if not media_file.exists():
                    return QColor(255, 100, 100)  # Алга болсон файлуудад улаан
                return None
        
        except Exception as e:
            return None
        
        return None
    
    def update_data(self, media_files: List[MediaFile]):
        """Загварыг шинэ өгөгдлөөр шинэчилнэ"""
        try:
            self.beginResetModel()
            self.media_files = media_files or []
            self.endResetModel()
        except Exception as e:
            pass
    
    def get_media_file(self, index: QModelIndex) -> Optional[MediaFile]:
        """Индексийн медиа файлыг авна"""
        try:
            if index.isValid() and 0 <= index.row() < len(self.media_files):
                return self.media_files[index.row()]
        except Exception:
            pass
        return None

# =============================================================================
# ЭКСПОРТ БА АШИГЛАЛТ
# =============================================================================

__all__ = [
    'MediaLibraryTab',
    'MediaFile', 
    'MediaMetadata', 
    'MediaType',
    'MediaLibrary',
    'MediaPreviewHandler'
]