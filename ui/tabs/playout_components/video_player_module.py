#!/usr/bin/env python3
"""
Enhanced Video Player Component
Professional video player with VLC support and playlist integration
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# Check VLC availability
VLC_AVAILABLE = False
try:
    import vlc
    VLC_AVAILABLE = True
    print("✅ VLC Python bindings available for playout")
except ImportError:
    print("⚠️ VLC Python bindings not available for playout")


class MediaPlaylist:
    """Enhanced playlist management for media files"""
    
    def __init__(self):
        self.media_files = []
        self.current_index = -1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.auto_advance = True
        
    def load_from_media_library(self, media_files_list):
        """Load playlist from media library"""
        self.media_files = media_files_list.copy()
        self.current_index = 0 if self.media_files else -1
        return len(self.media_files)
    
    def load_from_schedule(self, schedule_events):
        """Load playlist from scheduler events"""
        self.media_files = []
        for event in schedule_events:
            if hasattr(event, 'content') and event.content:
                if Path(event.content).exists():
                    self.media_files.append(event)
        self.current_index = 0 if self.media_files else -1
        return len(self.media_files)
    
    def add_media(self, media_file):
        """Add single media file to playlist"""
        self.media_files.append(media_file)
        if self.current_index == -1:
            self.current_index = 0
    
    def clear(self):
        """Clear playlist"""
        self.media_files.clear()
        self.current_index = -1
    
    def get_current(self):
        """Get current media file"""
        if 0 <= self.current_index < len(self.media_files):
            return self.media_files[self.current_index]
        return None
    
    def get_next(self):
        """Get next media file"""
        if not self.media_files:
            return None
            
        if self.current_index + 1 < len(self.media_files):
            return self.media_files[self.current_index + 1]
        elif self.repeat_mode:
            return self.media_files[0]
        return None
    
    def advance_to_next(self):
        """Advance to next media file"""
        if not self.media_files:
            return False
            
        if self.current_index + 1 < len(self.media_files):
            self.current_index += 1
            return True
        elif self.repeat_mode:
            self.current_index = 0
            return True
        return False
    
    def get_previous(self):
        """Get previous media file"""
        if not self.media_files:
            return None
            
        if self.current_index > 0:
            return self.media_files[self.current_index - 1]
        elif self.repeat_mode:
            return self.media_files[-1]
        return None
    
    def advance_to_previous(self):
        """Advance to previous media file"""
        if not self.media_files:
            return False
            
        if self.current_index > 0:
            self.current_index -= 1
            return True
        elif self.repeat_mode:
            self.current_index = len(self.media_files) - 1
            return True
        return False
    
    def get_playlist_info(self):
        """Get playlist information"""
        return {
            'total_files': len(self.media_files),
            'current_position': self.current_index + 1 if self.current_index >= 0 else 0,
            'repeat_mode': self.repeat_mode,
            'shuffle_mode': self.shuffle_mode,
            'auto_advance': self.auto_advance
        }


class ResponsiveVideoPlayer(QWidget):
    """Responsive video player with VLC support and playlist integration"""
    
    # Signals
    media_loaded = pyqtSignal(str)
    playback_state_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    media_ended = pyqtSignal()
    media_library_requested = pyqtSignal()
    scheduler_playlist_requested = pyqtSignal()
    
    def __init__(self, player_name="Player", parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.current_media_path = None
        self.is_playing = False
        self.vlc_instance = None
        self.vlc_player = None
        
        # Playlist integration
        self.playlist = MediaPlaylist()
        self.playlist_enabled = False
        
        # Responsive settings
        self.min_width = 400
        self.min_height = 300
        self.is_compact = False
        
        self.setMinimumSize(self.min_width, self.min_height)
        self._init_ui()
        self._init_vlc()
        self._connect_resize_signals()
    
    def _init_ui(self):
        """Initialize UI with responsive layout"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(4)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create responsive video frame
        self._create_video_frame()
        
        # Create responsive controls
        self._create_controls()
        
        # Create playlist controls
        self._create_playlist_controls()
        
        # Create status
        self._create_status()
    
    def _create_video_frame(self):
        """Create responsive video display area"""
        self.video_frame = QFrame()
        self.video_frame.setMinimumHeight(200)
        self.video_frame.setStyleSheet("""
            QFrame {
                background: #1a1a1a; 
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        
        frame_layout = QVBoxLayout(self.video_frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Player icon and info
        self.player_icon = QLabel("📹")
        self.player_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_icon.setStyleSheet("font-size: 36px; color: #555;")
        frame_layout.addWidget(self.player_icon)
        
        self.player_label = QLabel(f"{self.player_name}")
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_label.setStyleSheet("color: #888; font-size: 12px; font-weight: bold;")
        frame_layout.addWidget(self.player_label)
        
        # VLC status
        vlc_status = QLabel(f"VLC: {'Available' if VLC_AVAILABLE else 'Not Available'}")
        vlc_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlc_color = "#4CAF50" if VLC_AVAILABLE else "#F44336"
        vlc_status.setStyleSheet(f"color: {vlc_color}; font-size: 9px;")
        frame_layout.addWidget(vlc_status)
        
        self.main_layout.addWidget(self.video_frame)
    
    def _create_controls(self):
        """Create responsive control buttons"""
        self.controls_widget = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(4, 4, 4, 4)
        self.controls_layout.setSpacing(4)
        
        # Load buttons
        self.load_library_btn = QPushButton("📚 Library")
        self.load_library_btn.setStyleSheet(self._get_button_style("#4CAF50"))
        self.load_library_btn.clicked.connect(self._request_media_library)
        
        self.load_schedule_btn = QPushButton("📅 Schedule")
        self.load_schedule_btn.setStyleSheet(self._get_button_style("#9C27B0"))
        self.load_schedule_btn.clicked.connect(self._request_scheduler_playlist)
        
        self.load_file_btn = QPushButton("📁 File")
        self.load_file_btn.setStyleSheet(self._get_button_style("#2196F3"))
        self.load_file_btn.clicked.connect(self.load_media_dialog)
        
        # Playback controls
        self.play_btn = QPushButton("▶️")
        self.play_btn.setStyleSheet(self._get_button_style("#2196F3"))
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setStyleSheet(self._get_button_style("#F44336"))
        self.stop_btn.clicked.connect(self.stop)
        
        # Add buttons to layout
        self.controls_layout.addWidget(self.load_library_btn)
        self.controls_layout.addWidget(self.load_schedule_btn)
        self.controls_layout.addWidget(self.load_file_btn)
        self.controls_layout.addWidget(self.play_btn)
        self.controls_layout.addWidget(self.stop_btn)
        self.controls_layout.addStretch()
        
        self.main_layout.addWidget(self.controls_widget)
    
    def _create_playlist_controls(self):
        """Create responsive playlist controls"""
        self.playlist_widget = QWidget()
        self.playlist_layout = QHBoxLayout(self.playlist_widget)
        self.playlist_layout.setContentsMargins(4, 4, 4, 4)
        self.playlist_layout.setSpacing(4)
        
        # Navigation buttons
        self.prev_btn = QPushButton("⏮️")
        self.prev_btn.setFixedSize(40, 25)
        self.prev_btn.clicked.connect(self.play_previous)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("⏭️")
        self.next_btn.setFixedSize(40, 25)
        self.next_btn.clicked.connect(self.play_next)
        self.next_btn.setEnabled(False)
        
        # Mode buttons
        self.repeat_btn = QPushButton("🔁")
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setFixedSize(40, 25)
        self.repeat_btn.toggled.connect(self._toggle_repeat)
        
        self.auto_advance_btn = QPushButton("🚀")
        self.auto_advance_btn.setCheckable(True)
        self.auto_advance_btn.setChecked(True)
        self.auto_advance_btn.setFixedSize(40, 25)
        self.auto_advance_btn.toggled.connect(self._toggle_auto_advance)
        
        # Playlist info
        self.playlist_info_label = QLabel("0/0")
        self.playlist_info_label.setStyleSheet("font-size: 9px; color: #888;")
        
        # Add to layout
        self.playlist_layout.addWidget(self.prev_btn)
        self.playlist_layout.addWidget(self.next_btn)
        self.playlist_layout.addWidget(self.repeat_btn)
        self.playlist_layout.addWidget(self.auto_advance_btn)
        self.playlist_layout.addStretch()
        self.playlist_layout.addWidget(self.playlist_info_label)
        
        self.main_layout.addWidget(self.playlist_widget)
    
    def _create_status(self):
        """Create responsive status bar"""
        self.status_label = QLabel(f"{self.player_name} - Ready")
        self.status_label.setStyleSheet("color: #E0E0E0; font-size: 10px; padding: 4px;")
        self.main_layout.addWidget(self.status_label)
    
    def _get_button_style(self, color="#404040"):
        """Get responsive button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10px;
                min-width: 50px;
                min-height: 25px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #424242;
                color: #757575;
            }}
        """
    
    def _connect_resize_signals(self):
        """Connect resize signals for responsive behavior"""
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle resize events for responsive behavior"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle widget resize for responsive behavior"""
        width = size.width()
        height = size.height()
        
        # Determine if compact mode is needed
        is_compact = width < 500 or height < 400
        
        if is_compact != self.is_compact:
            self.is_compact = is_compact
            self._update_layout_for_size()
    
    def _update_layout_for_size(self):
        """Update layout based on size"""
        if self.is_compact:
            # Compact mode - hide some buttons, make text smaller
            self.player_icon.setStyleSheet("font-size: 24px; color: #555;")
            self.player_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
            
            # Make buttons smaller
            for btn in [self.load_library_btn, self.load_schedule_btn, self.load_file_btn]:
                btn.setText(btn.text().split()[0])  # Keep only icon
                btn.setMinimumWidth(35)
        else:
            # Normal mode - show full buttons
            self.player_icon.setStyleSheet("font-size: 36px; color: #555;")
            self.player_label.setStyleSheet("color: #888; font-size: 12px; font-weight: bold;")
            
            # Restore full button text
            buttons_text = [("📚 Library", self.load_library_btn),
                           ("📅 Schedule", self.load_schedule_btn),
                           ("📁 File", self.load_file_btn)]
            
            for text, btn in buttons_text:
                btn.setText(text)
                btn.setMinimumWidth(70)
    
    def _init_vlc(self):
        """Initialize VLC if available"""
        if VLC_AVAILABLE:
            try:
                self.vlc_instance = vlc.Instance('--no-xlib')
                self.vlc_player = self.vlc_instance.media_player_new()
                
                # Set up event handling for media end
                if self.vlc_player:
                    event_manager = self.vlc_player.event_manager()
                    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end)
                
                if sys.platform.startswith('linux'):
                    self.vlc_player.set_xwindow(self.video_frame.winId())
                elif sys.platform == "win32":
                    self.vlc_player.set_hwnd(self.video_frame.winId())
                elif sys.platform == "darwin":
                    self.vlc_player.set_nsobject(int(self.video_frame.winId()))
                
                print(f"✅ VLC initialized for {self.player_name}")
            except Exception as e:
                print(f"❌ Failed to initialize VLC: {e}")
                self.vlc_instance = None
                self.vlc_player = None
    
    def _on_media_end(self, event):
        """Handle media end event"""
        self.media_ended.emit()
        if self.playlist.auto_advance and self.playlist_enabled:
            QTimer.singleShot(500, self.play_next)  # Small delay before advancing
    
    def _request_media_library(self):
        """Request media library files"""
        self.media_library_requested.emit()
    
    def _request_scheduler_playlist(self):
        """Request scheduler playlist"""
        self.scheduler_playlist_requested.emit()
    
    def set_media_library_files(self, media_files):
        """Set media files from media library"""
        if not media_files:
            self.status_label.setText("No media files available in library")
            return
            
        count = self.playlist.load_from_media_library(media_files)
        self.playlist_enabled = True
        self._update_playlist_controls()
        self._update_playlist_info()
        
        # Load first file
        current_media = self.playlist.get_current()
        if current_media:
            self.load_media(str(current_media.file_path))
            self.status_label.setText(f"Loaded library playlist with {count} files")
    
    def set_scheduler_playlist(self, schedule_events):
        """Set playlist from scheduler events"""
        if not schedule_events:
            self.status_label.setText("No scheduled media events available")
            return
            
        count = self.playlist.load_from_schedule(schedule_events)
        self.playlist_enabled = True
        self._update_playlist_controls()
        self._update_playlist_info()
        
        # Load first file
        current_media = self.playlist.get_current()
        if current_media:
            self.load_media(str(current_media.content))
            self.status_label.setText(f"Loaded schedule playlist with {count} events")
    
    def play_next(self):
        """Play next media in playlist"""
        if not self.playlist_enabled or not self.playlist.advance_to_next():
            self.status_label.setText("End of playlist reached")
            return
            
        current_media = self.playlist.get_current()
        if current_media:
            # Handle both media library files and schedule events
            if hasattr(current_media, 'file_path'):
                self.load_media(str(current_media.file_path))
            elif hasattr(current_media, 'content'):
                self.load_media(str(current_media.content))
            
            if self.is_playing:
                self.play()
            self._update_playlist_info()
    
    def play_previous(self):
        """Play previous media in playlist"""
        if not self.playlist_enabled or not self.playlist.advance_to_previous():
            self.status_label.setText("At beginning of playlist")
            return
            
        current_media = self.playlist.get_current()
        if current_media:
            # Handle both media library files and schedule events
            if hasattr(current_media, 'file_path'):
                self.load_media(str(current_media.file_path))
            elif hasattr(current_media, 'content'):
                self.load_media(str(current_media.content))
            
            if self.is_playing:
                self.play()
            self._update_playlist_info()
    
    def _toggle_repeat(self, enabled):
        """Toggle repeat mode"""
        self.playlist.repeat_mode = enabled
        status = "enabled" if enabled else "disabled"
        self.status_label.setText(f"Repeat mode {status}")
    
    def _toggle_auto_advance(self, enabled):
        """Toggle auto advance mode"""
        self.playlist.auto_advance = enabled
        status = "enabled" if enabled else "disabled"
        self.status_label.setText(f"Auto advance {status}")
    
    def _update_playlist_controls(self):
        """Update playlist control buttons"""
        has_playlist = self.playlist_enabled and len(self.playlist.media_files) > 0
        
        self.prev_btn.setEnabled(has_playlist)
        self.next_btn.setEnabled(has_playlist)
        self.repeat_btn.setEnabled(has_playlist)
        self.auto_advance_btn.setEnabled(has_playlist)
    
    def _update_playlist_info(self):
        """Update playlist information display"""
        if self.playlist_enabled:
            info = self.playlist.get_playlist_info()
            self.playlist_info_label.setText(f"{info['current_position']}/{info['total_files']}")
        else:
            self.playlist_info_label.setText("0/0")
    
    def load_media_dialog(self):
        """Load media file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Load Media for {self.player_name}",
            "", "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flv *.wmv);;All Files (*)"
        )
        if file_path:
            # Disable playlist when loading single file
            self.playlist_enabled = False
            self._update_playlist_controls()
            self._update_playlist_info()
            self.load_media(file_path)
    
    def load_media(self, file_path):
        """Load media file"""
        self.current_media_path = Path(file_path)
        self.play_btn.setEnabled(True)
        self.status_label.setText(f"Loaded: {self.current_media_path.name}")
        
        # Load in VLC if available
        if self.vlc_player:
            try:
                media = self.vlc_instance.media_new(str(file_path))
                self.vlc_player.set_media(media)
                print(f"✅ Media loaded in VLC: {self.current_media_path.name}")
            except Exception as e:
                print(f"❌ Failed to load media in VLC: {e}")
        
        self.media_loaded.emit(str(file_path))
        return True
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Play media"""
        self.is_playing = True
        self.play_btn.setText("⏸️")
        if self.current_media_path:
            self.status_label.setText(f"Playing: {self.current_media_path.name}")
        
        # Play in VLC if available
        if self.vlc_player:
            self.vlc_player.play()
        
        self.playback_state_changed.emit("playing")
    
    def pause(self):
        """Pause media"""
        self.is_playing = False
        self.play_btn.setText("▶️")
        if self.current_media_path:
            self.status_label.setText(f"Paused: {self.current_media_path.name}")
        
        # Pause in VLC if available
        if self.vlc_player:
            self.vlc_player.pause()
        
        self.playback_state_changed.emit("paused")
    
    def stop(self):
        """Stop media"""
        self.is_playing = False
        self.play_btn.setText("▶️")
        self.status_label.setText("Stopped")
        
        # Stop in VLC if available
        if self.vlc_player:
            self.vlc_player.stop()
        
        self.playback_state_changed.emit("stopped")
    
    def get_current_file(self):
        """Get current file path"""
        return str(self.current_media_path) if self.current_media_path else None
    
    def get_playback_state(self):
        """Get current playback state"""
        return {"file": self.get_current_file(), "playing": self.is_playing}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.vlc_player:
            self.vlc_player.stop()


# For backwards compatibility
EnhancedVideoPlayer = ResponsiveVideoPlayer

__all__ = ['ResponsiveVideoPlayer', 'MediaPlaylist', 'EnhancedVideoPlayer']
