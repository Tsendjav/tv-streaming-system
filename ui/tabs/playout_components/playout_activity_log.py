#!/usr/bin/env python3
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal
from datetime import datetime

class ActivityLogComponent(QWidget):
    log_message_added = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        header = QLabel("📋 Activity Log")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #9C27B0;")
        layout.addWidget(header)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(120)
        layout.addWidget(self.log_display)
        
        self.add_system_event("Activity log initialized")
    
    def add_system_event(self, message): self._add_log_entry("SYSTEM", message)
    def add_success(self, message): self._add_log_entry("SUCCESS", message)
    def add_warning(self, message): self._add_log_entry("WARNING", message)
    def add_error(self, message): self._add_log_entry("ERROR", message)
    def add_audio_event(self, message): self._add_log_entry("AUDIO", message)
    def add_amcp_command(self, command): self._add_log_entry("AMCP", command)
    
    def _add_log_entry(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {level}: {message}"
        self.log_display.append(entry)
        self.log_message_added.emit(message, level)
    
    def export_log_data(self): return {}
    def import_log_data(self, data): pass
