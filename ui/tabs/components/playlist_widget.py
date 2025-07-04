#!/usr/bin/env python3
"""
Playlist Widget
Media playlist management with drag-drop support
"""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from models.media_metadata import MediaFile
   
def create_media_file_from_path(file_path, scan_metadata=False):
    """Simple fallback function to create MediaFile"""
    return MediaFile(file_path)


class PlaylistWidget(QWidget):
    """Media playlist widget with enhanced features"""
    
    item_selected = pyqtSignal(object)  # MediaFile
    playlist_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.media_files: List[MediaFile] = []
    
    def _init_ui(self):
        """Initialize playlist UI"""
        layout = QVBoxLayout(self)
        
        # Playlist list
        self.playlist = QListWidget()
        self.playlist.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #555;
            }
        """)
        self.playlist.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.playlist.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self.playlist)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self._add_media)
        add_btn.setToolTip("Add media files to playlist")
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Remove")
        remove_btn.clicked.connect(self._remove_media)
        remove_btn.setToolTip("Remove selected item")
        button_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.clicked.connect(self._clear_playlist)
        clear_btn.setToolTip("Clear entire playlist")
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("0 items")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def _add_media(self):
        """Add media files to playlist"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.mp3 *.wav *.flac *.aac *.ogg *.m4a);;All Files (*)"
        )
        
        for file_path in file_paths:
            try:
                media_file = create_media_file_from_path(file_path)
                self.add_media_file(media_file)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add media: {str(e)}")
    
    def add_media_file(self, media_file: MediaFile):
        """Add a media file to the playlist"""
        self.media_files.append(media_file)
        
        # Create list item
        item = QListWidgetItem()
        item.setText(media_file.display_name)
        item.setData(Qt.ItemDataRole.UserRole, media_file)
        
        # Set icon based on file type
        if hasattr(media_file, 'is_video') and media_file.is_video:
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        elif hasattr(media_file, 'is_audio') and media_file.is_audio:
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        else:
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        
        # Add tooltip
        item.setToolTip(str(media_file.file_path))
        
        self.playlist.addItem(item)
        self._update_status()
        self.playlist_changed.emit()
    
    def _remove_media(self):
        """Remove selected media from playlist"""
        current_item = self.playlist.currentItem()
        if current_item:
            row = self.playlist.row(current_item)
            self.playlist.takeItem(row)
            if 0 <= row < len(self.media_files):
                self.media_files.pop(row)
            self._update_status()
            self.playlist_changed.emit()
    
    def _clear_playlist(self):
        """Clear entire playlist"""
        reply = QMessageBox.question(
            self,
            "Clear Playlist",
            "Are you sure you want to clear the entire playlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.playlist.clear()
            self.media_files.clear()
            self._update_status()
            self.playlist_changed.emit()
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on playlist item"""
        media_file = item.data(Qt.ItemDataRole.UserRole)
        if media_file:
            self.item_selected.emit(media_file)
    
    def _update_status(self):
        """Update status label"""
        count = len(self.media_files)
        self.status_label.setText(f"{count} item{'s' if count != 1 else ''}")
    
    def get_current_media(self) -> Optional[MediaFile]:
        """Get currently selected media"""
        current_item = self.playlist.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def get_next_media(self) -> Optional[MediaFile]:
        """Get next media in playlist"""
        current_row = self.playlist.currentRow()
        if current_row < self.playlist.count() - 1:
            next_item = self.playlist.item(current_row + 1)
            return next_item.data(Qt.ItemDataRole.UserRole) if next_item else None
        return None
    
    def get_previous_media(self) -> Optional[MediaFile]:
        """Get previous media in playlist"""
        current_row = self.playlist.currentRow()
        if current_row > 0:
            prev_item = self.playlist.item(current_row - 1)
            return prev_item.data(Qt.ItemDataRole.UserRole) if prev_item else None
        return None
    
    def select_next(self):
        """Select next item in playlist"""
        current_row = self.playlist.currentRow()
        if current_row < self.playlist.count() - 1:
            self.playlist.setCurrentRow(current_row + 1)
    
    def select_previous(self):
        """Select previous item in playlist"""
        current_row = self.playlist.currentRow()
        if current_row > 0:
            self.playlist.setCurrentRow(current_row - 1)
    
    def load_playlist_file(self, file_path: str):
        """Load playlist from file"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)
            
            self._clear_playlist()
            
            for item_data in playlist_data.get('items', []):
                file_path = item_data.get('file_path')
                if file_path and Path(file_path).exists():
                    media_file = create_media_file_from_path(file_path)
                    self.add_media_file(media_file)
            
            QMessageBox.information(self, "Success", "Playlist loaded successfully")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load playlist: {str(e)}")
    
    def save_playlist_file(self, file_path: str):
        """Save playlist to file"""
        try:
            import json
            
            playlist_data = {
                'name': Path(file_path).stem,
                'created': datetime.now().isoformat(),
                'items': []
            }
            
            for media_file in self.media_files:
                item_data = {
                    'file_path': str(media_file.file_path),
                    'display_name': media_file.display_name
                }
                playlist_data['items'].append(item_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Success", "Playlist saved successfully")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save playlist: {str(e)}")
    
    def get_playlist_data(self) -> List[dict]:
        """Get playlist data as list of dictionaries"""
        return [
            {
                'file_path': str(media_file.file_path),
                'display_name': media_file.display_name,
                'exists': media_file.exists()
            }
            for media_file in self.media_files
        ]