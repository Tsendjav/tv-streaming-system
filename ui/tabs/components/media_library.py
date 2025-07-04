#!/usr/bin/env python3
"""
ui/components/media_library_ui.py
UI components for the media library tab
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class MediaLibraryUI:
    """UI component factory for media library"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.logger = get_logger(__name__)
    
    def create_left_panel(self, media_library) -> QWidget:
        """Create left panel with categories and filters"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Search section
        search_group = QGroupBox("🔍 Search")
        search_layout = QVBoxLayout(search_group)
        
        self.parent.search_input = QLineEdit()
        self.parent.search_input.setPlaceholderText("Search media files...")
        self.parent.search_input.textChanged.connect(self.parent._on_search_changed)
        search_layout.addWidget(self.parent.search_input)
        
        # Clear search button
        clear_search_btn = QPushButton("Clear")
        clear_search_btn.clicked.connect(self.parent._clear_search)
        search_layout.addWidget(clear_search_btn)
        
        layout.addWidget(search_group)
        
        # Categories section
        categories_group = QGroupBox("📁 Categories")
        categories_layout = QVBoxLayout(categories_group)
        
        self.parent.category_list = QListWidget()
        self.parent.category_list.addItem("All Media")
        self.parent.category_list.addItems(media_library.categories)
        self.parent.category_list.setCurrentRow(0)
        self.parent.category_list.currentTextChanged.connect(self.parent._on_category_changed)
        categories_layout.addWidget(self.parent.category_list)
        
        # Category management buttons
        cat_buttons = QHBoxLayout()
        add_cat_btn = QPushButton("Add")
        add_cat_btn.clicked.connect(self.parent._add_category)
        cat_buttons.addWidget(add_cat_btn)
        
        remove_cat_btn = QPushButton("Remove")
        remove_cat_btn.clicked.connect(self.parent._remove_category)
        cat_buttons.addWidget(remove_cat_btn)
        
        categories_layout.addLayout(cat_buttons)
        layout.addWidget(categories_group)
        
        # Media type filter
        type_group = QGroupBox("🎬 Media Type")
        type_layout = QVBoxLayout(type_group)
        
        self.parent.type_combo = QComboBox()
        self.parent.type_combo.addItems(["All Types", "Video", "Audio", "Image"])
        self.parent.type_combo.currentTextChanged.connect(self.parent._on_type_filter_changed)
        type_layout.addWidget(self.parent.type_combo)
        
        layout.addWidget(type_group)
        
        # Actions section
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        scan_btn = QPushButton("🔄 Scan Library")
        scan_btn.clicked.connect(self.parent.scan_media_library)
        actions_layout.addWidget(scan_btn)
        
        import_btn = QPushButton("📥 Import Files")
        import_btn.clicked.connect(self.parent.import_media_files)
        actions_layout.addWidget(import_btn)
        
        cleanup_btn = QPushButton("🧹 Cleanup Missing")
        cleanup_btn.clicked.connect(self.parent._cleanup_missing_files)
        actions_layout.addWidget(cleanup_btn)
        
        stats_btn = QPushButton("📊 Show Statistics")
        stats_btn.clicked.connect(self.parent._show_statistics)
        actions_layout.addWidget(stats_btn)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Create center panel with media table"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.parent.view_combo = QComboBox()
        self.parent.view_combo.addItems(["Table View", "Grid View", "List View"])
        self.parent.view_combo.currentTextChanged.connect(self.parent._change_view_mode)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self.parent.view_combo)
        
        toolbar.addStretch()
        
        self.parent.sort_combo = QComboBox()
        self.parent.sort_combo.addItems([
            "Title", "Artist", "Album", "Duration", "Genre", 
            "Category", "Rating", "Date Added", "File Size"
        ])
        self.parent.sort_combo.currentTextChanged.connect(self.parent._on_sort_changed)
        toolbar.addWidget(QLabel("Sort by:"))
        toolbar.addWidget(self.parent.sort_combo)
        
        self.parent.sort_order_btn = QPushButton("↑ Asc")
        self.parent.sort_order_btn.setCheckable(True)
        self.parent.sort_order_btn.clicked.connect(self.parent._toggle_sort_order)
        toolbar.addWidget(self.parent.sort_order_btn)
        
        layout.addLayout(toolbar)
        
        # Media table
        from ui.components.media_table_model import MediaTableModel
        
        self.parent.media_table = QTableView()
        self.parent.media_model = MediaTableModel()
        self.parent.media_table.setModel(self.parent.media_model)
        
        self.parent.media_table.setSortingEnabled(True)
        self.parent.media_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.parent.media_table.setAlternatingRowColors(True)
        self.parent.media_table.verticalHeader().setVisible(False)
        
        self.parent.media_table.selectionModel().currentRowChanged.connect(self.parent._on_media_selected)
        self.parent.media_table.doubleClicked.connect(self.parent._on_media_double_clicked)
        
        self.parent.media_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parent.media_table.customContextMenuRequested.connect(self.parent._show_context_menu)
        
        layout.addWidget(self.parent.media_table)
        
        # Status
        self.parent.status_label = QLabel("0 files")
        self.parent.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.parent.status_label)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with metadata editor"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Preview section
        preview_group = QGroupBox("🎥 Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.parent.preview_label = QLabel()
        self.parent.preview_label.setMinimumSize(280, 160)
        self.parent.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #555;
                border-radius: 4px;
                color: #888;
            }
        """)
        self.parent.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parent.preview_label.setText("No preview available")
        preview_layout.addWidget(self.parent.preview_label)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        
        self.parent.play_preview_btn = QPushButton("▶️ Play")
        self.parent.play_preview_btn.clicked.connect(self.parent._play_preview)
        self.parent.play_preview_btn.setEnabled(False)
        preview_controls.addWidget(self.parent.play_preview_btn)
        
        self.parent.stop_preview_btn = QPushButton("⏹ Stop")
        self.parent.stop_preview_btn.clicked.connect(self.parent._stop_preview)
        self.parent.stop_preview_btn.setEnabled(False)
        preview_controls.addWidget(self.parent.stop_preview_btn)
        
        preview_layout.addLayout(preview_controls)
        layout.addWidget(preview_group)
        
        # Metadata editor
        metadata_group = QGroupBox("📝 Metadata")
        metadata_layout = QFormLayout(metadata_group)
        
        self.parent.title_edit = QLineEdit()
        self.parent.title_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Title:", self.parent.title_edit)
        
        self.parent.artist_edit = QLineEdit()
        self.parent.artist_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Artist:", self.parent.artist_edit)
        
        self.parent.album_edit = QLineEdit()
        self.parent.album_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Album:", self.parent.album_edit)
        
        self.parent.genre_edit = QLineEdit()
        self.parent.genre_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Genre:", self.parent.genre_edit)
        
        self.parent.category_combo = QComboBox()
        self.parent.category_combo.currentTextChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Category:", self.parent.category_combo)
        
        self.parent.rating_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.rating_slider.setRange(0, 5)
        self.parent.rating_slider.valueChanged.connect(self.parent._on_rating_changed)
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(self.parent.rating_slider)
        self.parent.rating_label = QLabel("0")
        rating_layout.addWidget(self.parent.rating_label)
        metadata_layout.addRow("Rating:", rating_layout)
        
        self.parent.description_edit = QTextEdit()
        self.parent.description_edit.setMaximumHeight(80)
        self.parent.description_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Description:", self.parent.description_edit)
        
        self.parent.tags_edit = QLineEdit()
        self.parent.tags_edit.setPlaceholderText("Comma-separated tags")
        self.parent.tags_edit.textChanged.connect(self.parent._on_metadata_changed)
        metadata_layout.addRow("Tags:", self.parent.tags_edit)
        
        layout.addWidget(metadata_group)
        
        # File info section
        info_group = QGroupBox("ℹ️ File Information")
        info_layout = QFormLayout(info_group)
        
        self.parent.file_path_label = QLabel("-")
        self.parent.file_path_label.setWordWrap(True)
        info_layout.addRow("Path:", self.parent.file_path_label)
        
        self.parent.file_size_label = QLabel("-")
        info_layout.addRow("Size:", self.parent.file_size_label)
        
        self.parent.duration_label = QLabel("-")
        info_layout.addRow("Duration:", self.parent.duration_label)
        
        self.parent.resolution_label = QLabel("-")
        info_layout.addRow("Resolution:", self.parent.resolution_label)
        
        self.parent.date_added_label = QLabel("-")
        info_layout.addRow("Date Added:", self.parent.date_added_label)
        
        layout.addWidget(info_group)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        
        self.parent.save_metadata_btn = QPushButton("💾 Save Metadata")
        self.parent.save_metadata_btn.clicked.connect(self.parent._save_metadata)
        self.parent.save_metadata_btn.setEnabled(False)
        actions_layout.addWidget(self.parent.save_metadata_btn)
        
        self.parent.open_file_btn = QPushButton("📁 Open File")
        self.parent.open_file_btn.clicked.connect(self.parent._open_file)
        self.parent.open_file_btn.setEnabled(False)
        actions_layout.addWidget(self.parent.open_file_btn)
        
        self.parent.show_in_explorer_btn = QPushButton("🗂️ Show in Explorer")
        self.parent.show_in_explorer_btn.clicked.connect(self.parent._show_in_explorer)
        self.parent.show_in_explorer_btn.setEnabled(False)
        actions_layout.addWidget(self.parent.show_in_explorer_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        return panel