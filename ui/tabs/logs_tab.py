#!/usr/bin/env python3
"""
Logs Tab
Real-time log viewing and management
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from core.logging import get_logger, log_manager
from datetime import datetime
import os


class LogsTab(QWidget):
    """Logs viewing and management tab"""
    
    status_message = pyqtSignal(str, int)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.last_log_position = 0  # Track last read position
        
        self._init_ui()
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_logs)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls = QHBoxLayout()
        
        # Log level filter
        controls.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self._filter_logs)
        controls.addWidget(self.log_level_combo)
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto Scroll")
        self.auto_scroll_cb.setChecked(True)
        controls.addWidget(self.auto_scroll_cb)
        
        # Search box
        controls.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search logs...")
        self.search_edit.textChanged.connect(self._filter_logs)
        controls.addWidget(self.search_edit)
        
        controls.addStretch()
        
        # Clear logs button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_logs)
        clear_btn.setToolTip("Clear log display")
        controls.addWidget(clear_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_logs)
        refresh_btn.setToolTip("Refresh logs")
        controls.addWidget(refresh_btn)
        
        # Export logs button
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self._export_logs)
        export_btn.setToolTip("Export logs to file")
        controls.addWidget(export_btn)
        
        layout.addLayout(controls)
        
        # Log display
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.logs_display)
        
        # Log statistics
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Lines: 0 | Errors: 0 | Warnings: 0")
        self.stats_label.setStyleSheet("color: #888; font-size: 10px;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Status
        self.log_status = QLabel("Monitoring logs...")
        self.log_status.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        stats_layout.addWidget(self.log_status)
        
        layout.addLayout(stats_layout)
        
        # Store all log lines for filtering
        self.all_log_lines = []
        
        # Load initial logs
        self._load_recent_logs()
    
    def _load_recent_logs(self):
        """Load recent log entries"""
        try:
            # Get log files
            log_files = log_manager.get_log_files()
            
            if 'application_streaming_studio' in log_files:
                log_file = log_files['application_streaming_studio']
                
                if os.path.exists(log_file):
                    # Read last 100 lines
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                        self.all_log_lines = []
                        for line in recent_lines:
                            stripped_line = line.strip()
                            if stripped_line:
                                self.all_log_lines.append(stripped_line)
                        
                        self._update_display()
                        self.last_log_position = len(lines)
                        
                        self.log_status.setText(f"Loaded {len(recent_lines)} recent log entries")
                else:
                    self.log_status.setText("Log file not found")
            else:
                self.log_status.setText("No application log file configured")
            
        except Exception as e:
            self.logger.error(f"Error loading recent logs: {e}")
            self.log_status.setText(f"Error loading logs: {e}")
    
    def _update_logs(self):
        """Update logs display with new entries"""
        try:
            log_files = log_manager.get_log_files()
            
            if 'application_streaming_studio' in log_files:
                log_file = log_files['application_streaming_studio']
                
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        # Check if new lines were added
                        if len(lines) > self.last_log_position:
                            new_lines = lines[self.last_log_position:]
                            
                            for line in new_lines:
                                stripped_line = line.strip()
                                if stripped_line:
                                    self.all_log_lines.append(stripped_line)
                            
                            self._update_display()
                            self.last_log_position = len(lines)
                            
                            self.log_status.setText(f"Added {len(new_lines)} new log entries")
                        
        except Exception as e:
            self.logger.error(f"Error updating logs: {e}")
    
    def _update_display(self):
        """Update the log display based on current filters"""
        current_scroll_pos = self.logs_display.verticalScrollBar().value()
        max_scroll_pos = self.logs_display.verticalScrollBar().maximum()
        was_at_bottom = current_scroll_pos >= max_scroll_pos - 10
        
        self.logs_display.clear()
        
        filtered_lines = self._get_filtered_lines()
        
        # Statistics
        error_count = sum(1 for line in filtered_lines if "ERROR" in line or "CRITICAL" in line)
        warning_count = sum(1 for line in filtered_lines if "WARNING" in line)
        
        self.stats_label.setText(f"Lines: {len(filtered_lines)} | Errors: {error_count} | Warnings: {warning_count}")
        
        # Display filtered lines
        for line in filtered_lines:
            self._add_log_line(line)
        
        # Auto-scroll to bottom if we were at the bottom or auto-scroll is enabled
        if self.auto_scroll_cb.isChecked() or was_at_bottom:
            scrollbar = self.logs_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _get_filtered_lines(self):
        """Get log lines filtered by level and search term"""
        filtered_lines = []
        current_level = self.log_level_combo.currentText()
        search_term = self.search_edit.text().lower()
        
        for line in self.all_log_lines:
            # Filter by log level
            if current_level != "ALL":
                if current_level not in line:
                    continue
            
            # Filter by search term
            if search_term and search_term not in line.lower():
                continue
            
            filtered_lines.append(line)
        
        return filtered_lines
    
    def _add_log_line(self, line: str):
        """Add a log line to display with color coding"""
        if not line:
            return
        
        # Color coding based on log level
        if "ERROR" in line or "CRITICAL" in line:
            color = "#ff4444"
        elif "WARNING" in line:
            color = "#ffaa00"
        elif "INFO" in line:
            color = "#00ff00"
        elif "DEBUG" in line:
            color = "#00aaff"
        else:
            color = "#ffffff"
        
        # Escape HTML characters
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Add with color
        self.logs_display.append(f'<span style="color: {color};">{escaped_line}</span>')
    
    def _filter_logs(self):
        """Filter logs based on current settings"""
        self._update_display()
    
    def _clear_logs(self):
        """Clear logs display"""
        self.logs_display.clear()
        self.all_log_lines.clear()
        self.last_log_position = 0
        self.stats_label.setText("Lines: 0 | Errors: 0 | Warnings: 0")
        self.log_status.setText("Logs cleared")
        self.status_message.emit("Logs cleared", 2000)
    
    def _refresh_logs(self):
        """Refresh logs from file"""
        self.all_log_lines.clear()
        self.last_log_position = 0
        self._load_recent_logs()
        self.status_message.emit("Logs refreshed", 2000)
    
    def _export_logs(self):
        """Export logs to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Logs",
                f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                filtered_lines = self._get_filtered_lines()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Log Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for line in filtered_lines:
                        f.write(line + "\n")
                
                self.status_message.emit(f"Logs exported to {filename}", 3000)
                self.log_status.setText(f"Exported {len(filtered_lines)} lines to {os.path.basename(filename)}")
                
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            self.status_message.emit(f"Export failed: {e}", 5000)
    
    def closeEvent(self, event):
        """Handle tab close event"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        event.accept()
