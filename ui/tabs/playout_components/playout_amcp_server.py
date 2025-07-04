#!/usr/bin/env python3
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

class AMCPServerControl(QWidget):
    amcp_command_sent = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)
    media_list_updated = pyqtSignal(list)
    
    def __init__(self, casparcg_client=None, parent=None):
        super().__init__(parent)
        self.connected = False
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📡 AMCP Server Control (Fallback)"))
        
        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)
        
        self.status_label = QLabel("⚫ Disconnected")
        layout.addWidget(self.status_label)
    
    def _toggle_connection(self):
        self.connected = not self.connected
        if self.connected:
            self.connect_btn.setText("🔌 Disconnect")
            self.status_label.setText("🟢 Connected (Mock)")
        else:
            self.connect_btn.setText("🔗 Connect")
            self.status_label.setText("⚫ Disconnected")
        self.connection_status_changed.emit(self.connected)
    
    def send_custom_command(self, command):
        self.amcp_command_sent.emit(f"MOCK: {command}")
    
    def set_media(self, media_name): pass
    def is_connected(self): return self.connected
