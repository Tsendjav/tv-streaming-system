#!/usr/bin/env python3
"""
ui/components/media_preview_handler.py
Handles media file previews and thumbnails
"""

import os
import tempfile
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from models.media_metadata import MediaFile, MediaType

try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

try:
    from models.media_metadata import MediaFile
except ImportError:
    from fixed_media_metadata import MediaFile


class MediaPreviewHandler(QObject):
    """Handles media file previews and playback"""
    
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str, int)
    
    def __init__(self, preview_label, parent=None):
        super().__init__(parent)
        self.preview_label = preview_label
        self.logger = get_logger(__name__)
        
        # VLC components
        self.vlc_instance = None
        self.media_player = None
        self.vlc_available = False
        
        self._init_vlc()
    
    def _init_vlc(self):
        """Initialize VLC components"""
        try:
            import vlc
            self.vlc_instance = vlc.Instance('--no-xlib')
            self.media_player = self.vlc_instance.media_player_new()
            self.vlc_available = True
            self.logger.debug("VLC initialized successfully")
        except ImportError:
            self.vlc_available = False
            self.logger.warning("VLC not available - preview functionality disabled")
    
    def update_preview(self, media_file: MediaFile):
        """Update preview area with media file"""
        try:
            if media_file.is_image:
                self._load_image_preview(media_file)
            elif media_file.is_video:
                self._load_video_thumbnail(media_file)
            else:
                file_type = media_file.media_type.value.title()
                self.preview_label.setText(f"{file_type} File\n\n{media_file.filename}")
                self.preview_label.setPixmap(QPixmap())  # Clear any existing pixmap
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
            self.preview_label.setText("Preview error")
    
    def _load_image_preview(self, media_file: MediaFile):
        """Load image preview"""
        try:
            if not media_file.exists():
                self.preview_label.setText("File not found")
                return
                
            pixmap = QPixmap(str(media_file.file_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")  # Clear text when showing image
            else:
                self.preview_label.setText("Cannot load image")
                self.preview_label.setPixmap(QPixmap())
        except Exception as e:
            self.logger.error(f"Error loading image preview: {e}")
            self.preview_label.setText("Preview error")
            self.preview_label.setPixmap(QPixmap())
    
    def _load_video_thumbnail(self, media_file: MediaFile):
        """Load video thumbnail"""
        try:
            if not media_file.exists():
                self.preview_label.setText("File not found")
                return
            
            # Try to generate thumbnail with FFmpeg
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                output_path = temp_file.name
            
            try:
                # Generate thumbnail at 1 second mark
                cmd = [
                    "ffmpeg", "-i", str(media_file.file_path), 
                    "-ss", "1", "-vframes", "1", 
                    "-vf", "scale=320:240:force_original_aspect_ratio=decrease",
                    "-y", output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    pixmap = QPixmap(output_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.preview_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.preview_label.setPixmap(scaled_pixmap)
                        self.preview_label.setText("")  # Clear text when showing image
                    else:
                        raise Exception("Generated thumbnail is invalid")
                else:
                    raise Exception("FFmpeg failed to generate thumbnail")
                    
            finally:
                # Clean up temporary file
                if os.path.exists(output_path):
                    try:
                        os.unlink(output_path)
                    except:
                        pass
                        
        except subprocess.TimeoutExpired:
            self.logger.warning("Thumbnail generation timed out")
            self.preview_label.setText(f"Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
        except FileNotFoundError:
            self.logger.debug("FFmpeg not found for thumbnail generation")
            self.preview_label.setText(f"Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
        except Exception as e:
            self.logger.error(f"Error loading video thumbnail: {e}")
            self.preview_label.setText(f"Video File\n\n{media_file.filename}\n\nClick 'Play' to preview")
            self.preview_label.setPixmap(QPixmap())
    
    def play_preview(self, media_file: MediaFile) -> bool:
        """Play preview of media file"""
        if not self.vlc_available:
            self.error_occurred.emit("VLC not available for preview")
            return False
            
        if not (media_file.is_video or media_file.is_audio):
            self.error_occurred.emit("Cannot preview this file type")
            return False
            
        if not media_file.exists():
            self.error_occurred.emit("File not found")
            return False
        
        try:
            # Stop any existing playback
            if self.media_player.is_playing():
                self.media_player.stop()
            
            # Create new media with proper validation
            file_path = str(media_file.file_path.resolve())
            
            # Use file:// protocol for local files
            if not file_path.startswith(('http://', 'https://', 'file://')):
                if file_path.startswith('/') or (len(file_path) > 1 and file_path[1] == ':'):
                    file_path = f"file:///{file_path}" if file_path.startswith('/') else f"file:///{file_path.replace('\\', '/')}"
            
            media = self.vlc_instance.media_new(file_path)
            
            if not media:
                self.error_occurred.emit(f"Failed to create VLC media for: {media_file.file_path}")
                return False
            
            # Parse media to get duration and other info
            media.parse()
            
            # Set media to player
            result = self.media_player.set_media(media)
            if result != 0:
                self.error_occurred.emit(f"Failed to set media in player: {result}")
                return False
            
            # Start playback
            result = self.media_player.play()
            if result == 0:  # Success
                self.status_message.emit("Playing preview", 3000)
                return True
            else:
                self.error_occurred.emit(f"VLC play() failed with code: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error playing preview: {e}")
            self.error_occurred.emit(f"Error playing preview: {str(e)}")
            return False
    
    def stop_preview(self):
        """Stop preview playback"""
        try:
            if self.vlc_available and self.media_player:
                self.media_player.stop()
            
            self.status_message.emit("Preview stopped", 2000)
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping preview: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Check if preview is currently playing"""
        if self.vlc_available and self.media_player:
            return self.media_player.is_playing()
        return False
    
    def clear_preview(self):
        """Clear preview area"""
        self.preview_label.setText("No preview available")
        self.preview_label.setPixmap(QPixmap())
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.vlc_available and self.media_player:
                if self.media_player.is_playing():
                    self.media_player.stop()
                self.media_player.release()
            
            if self.vlc_instance:
                self.vlc_instance.release()
                
        except Exception as e:
            self.logger.error(f"Error during preview handler cleanup: {e}")