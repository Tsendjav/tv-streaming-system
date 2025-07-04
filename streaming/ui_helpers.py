"""
TV Stream - UI Helper Classes
UI utilities and helper functions
"""

# PyQt compatibility
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

from typing import Dict, List, Optional, Any, Callable

# Safe import with fallback
try:
    from .utils import LoggerManager, ErrorHandler
except ImportError:
    try:
        from utils import LoggerManager, ErrorHandler
    except ImportError:
        # Fallback implementations
        class LoggerManager:
            @classmethod
            def get_logger(cls, name): 
                import logging
                return logging.getLogger(name)
        
        class ErrorHandler:
            @staticmethod
            def safe_execute(func, error_msg="", logger=None):
                try:
                    return func()
                except Exception as e:
                    if logger:
                        logger.error(f"{error_msg}: {e}")
                    return None


class UIUpdateManager:
    """UI update management"""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = LoggerManager.get_logger(__name__)
        self.error_handler = ErrorHandler()
    
    def safe_update(self, update_func: Callable, error_msg: str = "Update failed") -> bool:
        """Safely execute UI update"""
        return self.error_handler.safe_execute(update_func, error_msg, self.logger) is not None
    
    def update_combo_box(self, combo: QComboBox, items: List[Dict[str, Any]], 
                        key_field='name', data_field='data'):
        """Update combo box items"""
        def _update():
            combo.clear()
            for item in items:
                display_text = item.get(key_field, 'Unknown')
                item_data = item.get(data_field, item)
                combo.addItem(display_text, item_data)
        
        return self.safe_update(_update, "Failed to update combo box")
    
    def enable_controls(self, controls: Dict[QWidget, bool]):
        """Enable/disable multiple controls"""
        def _update():
            for control, enabled in controls.items():
                if control:
                    control.setEnabled(enabled)
        
        return self.safe_update(_update, "Failed to update control states")


class FormBuilder:
    """Form building utilities"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def create_group_box(self, title: str, layout_type='vertical') -> QGroupBox:
        """Create group box with layout"""
        group = QGroupBox(title)
        
        if layout_type == 'vertical':
            layout = QVBoxLayout(group)
        elif layout_type == 'horizontal':
            layout = QHBoxLayout(group)
        elif layout_type == 'form':
            layout = QFormLayout(group)
        else:
            layout = QVBoxLayout(group)
        
        return group
    
    def create_button_row(self, buttons: List[Dict[str, Any]]) -> QWidget:
        """Create row of buttons"""
        container = QWidget()
        layout = QHBoxLayout(container)
        
        for button_config in buttons:
            button = QPushButton(button_config.get('text', 'Button'))
            
            if 'clicked' in button_config:
                button.clicked.connect(button_config['clicked'])
            
            if 'enabled' in button_config:
                button.setEnabled(button_config['enabled'])
            
            layout.addWidget(button)
            button_config['button_ref'] = button
        
        return container


class DialogHelper:
    """Dialog utilities"""
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_question(parent, title: str, message: str) -> bool:
        reply = QMessageBox.question(parent, title, message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def get_text_input(parent, title: str, label: str, default_text: str = "") -> Optional[str]:
        text, ok = QInputDialog.getText(parent, title, label, text=default_text)
        return text if ok else None
