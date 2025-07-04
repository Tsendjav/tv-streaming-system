#!/usr/bin/env python3
"""
ui/components/media_table_model.py
Custom table model for media files in the library
"""

from typing import List, Optional
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from models.media_metadata import MediaFile, MediaType

try:
    from models.media_metadata import MediaFile, MediaType
except ImportError:
    # Fallback imports
    from fixed_media_metadata import MediaFile, MediaType


class MediaTableModel(QAbstractTableModel):
    """Custom table model for media files with enhanced functionality"""
    
    def __init__(self, media_files: List[MediaFile] = None):
        super().__init__()
        self.media_files = media_files or []
        self.headers = [
            "Title", "Artist", "Album", "Duration", "Genre", 
            "Category", "Rating", "Type", "File Size", "Date Added"
        ]
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.media_files)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.media_files):
            return None
        
        media_file = self.media_files[index.row()]
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:  # Title
                return media_file.metadata.title or media_file.display_name
            elif col == 1:  # Artist
                return media_file.metadata.artist or ""
            elif col == 2:  # Album
                return media_file.metadata.album or ""
            elif col == 3:  # Duration
                return media_file.metadata.duration_formatted
            elif col == 4:  # Genre
                return media_file.metadata.genre or ""
            elif col == 5:  # Category
                return media_file.metadata.category or ""
            elif col == 6:  # Rating
                rating = int(media_file.metadata.rating)
                return "★" * rating if rating > 0 else ""
            elif col == 7:  # Type
                return media_file.media_type.value.title()
            elif col == 8:  # File Size
                return media_file.metadata.file_size_formatted
            elif col == 9:  # Date Added
                return media_file.metadata.date_added.strftime("%Y-%m-%d")
        
        elif role == Qt.ItemDataRole.UserRole:
            return media_file.id
        
        elif role == Qt.ItemDataRole.ToolTipRole:
            tooltip = f"File: {media_file.filename}\nPath: {media_file.file_path}"
            if media_file.metadata.description:
                tooltip += f"\nDescription: {media_file.metadata.description}"
            return tooltip
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color coding based on file existence
            if not media_file.exists():
                return QColor(255, 100, 100)  # Red for missing files
            return None
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Alternate row colors
            if index.row() % 2 == 0:
                return QColor(250, 250, 250)
            return None
        
        return None
    
    def sort(self, column, order):
        """Sort the model data"""
        self.layoutAboutToBeChanged.emit()
        
        reverse = order == Qt.SortOrder.DescendingOrder
        
        if column == 0:  # Title
            self.media_files.sort(key=lambda m: (m.metadata.title or m.display_name).lower(), reverse=reverse)
        elif column == 1:  # Artist
            self.media_files.sort(key=lambda m: (m.metadata.artist or "").lower(), reverse=reverse)
        elif column == 2:  # Album
            self.media_files.sort(key=lambda m: (m.metadata.album or "").lower(), reverse=reverse)
        elif column == 3:  # Duration
            self.media_files.sort(key=lambda m: m.metadata.duration or 0, reverse=reverse)
        elif column == 4:  # Genre
            self.media_files.sort(key=lambda m: (m.metadata.genre or "").lower(), reverse=reverse)
        elif column == 5:  # Category
            self.media_files.sort(key=lambda m: (m.metadata.category or "").lower(), reverse=reverse)
        elif column == 6:  # Rating
            self.media_files.sort(key=lambda m: m.metadata.rating, reverse=reverse)
        elif column == 7:  # Type
            self.media_files.sort(key=lambda m: m.media_type.value, reverse=reverse)
        elif column == 8:  # File Size
            self.media_files.sort(key=lambda m: m.metadata.file_size, reverse=reverse)
        elif column == 9:  # Date Added
            self.media_files.sort(key=lambda m: m.metadata.date_added, reverse=reverse)
        
        self.layoutChanged.emit()
    
    def update_data(self, media_files: List[MediaFile]):
        """Update the model with new data"""
        self.beginResetModel()
        self.media_files = media_files
        self.endResetModel()
    
    def get_media_file(self, index: QModelIndex) -> Optional[MediaFile]:
        """Get media file at index"""
        if index.isValid() and index.row() < len(self.media_files):
            return self.media_files[index.row()]
        return None
    
    def add_media_file(self, media_file: MediaFile):
        """Add a media file to the model"""
        row = len(self.media_files)
        self.beginInsertRows(QModelIndex(), row, row)
        self.media_files.append(media_file)
        self.endInsertRows()
    
    def remove_media_file(self, media_id: str) -> bool:
        """Remove a media file from the model"""
        for i, media_file in enumerate(self.media_files):
            if media_file.id == media_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.media_files.pop(i)
                self.endRemoveRows()
                return True
        return False
    
    def update_media_file(self, updated_file: MediaFile) -> bool:
        """Update a media file in the model"""
        for i, media_file in enumerate(self.media_files):
            if media_file.id == updated_file.id:
                self.media_files[i] = updated_file
                # Emit data changed for the entire row
                top_left = self.index(i, 0)
                bottom_right = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(top_left, bottom_right)
                return True
        return False
    
    def get_statistics(self) -> dict:
        """Get statistics about the current data"""
        if not self.media_files:
            return {}
        
        stats = {
            'total_files': len(self.media_files),
            'total_size': sum(f.metadata.file_size for f in self.media_files),
            'media_types': {},
            'categories': {},
            'total_duration': 0
        }
        
        for media_file in self.media_files:
            # Count by media type
            media_type = media_file.media_type.value
            stats['media_types'][media_type] = stats['media_types'].get(media_type, 0) + 1
            
            # Count by category
            category = media_file.metadata.category or "Uncategorized"
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Sum duration
            if media_file.metadata.duration:
                stats['total_duration'] += media_file.metadata.duration
        
        return stats