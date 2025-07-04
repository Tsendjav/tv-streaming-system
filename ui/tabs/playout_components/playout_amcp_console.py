#!/usr/bin/env python3
from PyQt6.QtWidgets import *

class AMCPConsoleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMCP Console")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("AMCP Console (Fallback Mode)"))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
