#!/usr/bin/env python3
"""
Dark Theme Styles
Professional dark theme for the streaming studio application
"""

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from core.constants import DARK_THEME_COLORS, UI_CONSTANTS


def apply_dark_theme(app_or_widget):
    """Apply dark theme to application or widget"""
    
    if isinstance(app_or_widget, QApplication):
        _apply_dark_palette(app_or_widget)
    
    # Apply stylesheet to widget or application
    stylesheet = get_dark_stylesheet()
    app_or_widget.setStyleSheet(stylesheet)


def _apply_dark_palette(app: QApplication):
    """Apply dark color palette to application"""
    
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(DARK_THEME_COLORS["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_THEME_COLORS["text_primary"]))
    
    # Base colors (for input fields)
    palette.setColor(QPalette.ColorRole.Base, QColor(DARK_THEME_COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK_THEME_COLORS["surface_variant"]))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(DARK_THEME_COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(DARK_THEME_COLORS["surface_variant"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_THEME_COLORS["text_primary"]))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_THEME_COLORS["primary"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    
    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, 
                    QColor(DARK_THEME_COLORS["text_disabled"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, 
                    QColor(DARK_THEME_COLORS["text_disabled"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, 
                    QColor(DARK_THEME_COLORS["text_disabled"]))
    
    app.setPalette(palette)


def get_dark_stylesheet() -> str:
    """Get complete dark theme stylesheet"""
    
    colors = DARK_THEME_COLORS
    ui = UI_CONSTANTS
    
    return f"""
    /* Main Application Styling */
    QMainWindow {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
        font-size: 12px;
    }}
    
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        selection-background-color: {colors["selection"]};
        selection-color: white;
    }}
    
    /* Tab Widget Styling */
    QTabWidget::pane {{
        border: 1px solid {colors["border"]};
        background-color: {colors["background"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    
    QTabBar::tab {{
        background-color: {colors["surface_variant"]};
        color: {colors["text_primary"]};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: {ui["BORDER_RADIUS"]}px;
        border-top-right-radius: {ui["BORDER_RADIUS"]}px;
        border: 1px solid {colors["border"]};
        border-bottom: none;
        min-width: 80px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors["primary"]};
        color: white;
        font-weight: bold;
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {colors["hover"]};
    }}
    
    QTabBar::tab:disabled {{
        color: {colors["text_disabled"]};
        background-color: {colors["surface"]};
    }}
    
    /* Group Box Styling */
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {colors["border"]};
        border-radius: 8px;
        margin-top: 1ex;
        padding-top: 15px;
        color: {colors["text_primary"]};
        background-color: {colors["surface"]};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: {colors["text_primary"]};
        background-color: {colors["surface"]};
    }}
    
    /* Button Styling */
    QPushButton {{
        background-color: {colors["primary"]};
        border: none;
        padding: 8px 16px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: white;
        font-weight: bold;
        min-width: 80px;
        min-height: {ui["BUTTON_HEIGHT"]}px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["primary_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["primary_pressed"]};
    }}
    
    QPushButton:disabled {{
        background-color: {colors["surface"]};
        color: {colors["text_disabled"]};
    }}
    
    QPushButton:checked {{
        background-color: {colors["primary_pressed"]};
        border: 2px solid {colors["primary"]};
    }}
    
    /* Special Button Styles */
    QPushButton.success {{
        background-color: {colors["success"]};
    }}
    
    QPushButton.success:hover {{
        background-color: #218838;
    }}
    
    QPushButton.warning {{
        background-color: {colors["warning"]};
        color: #212529;
    }}
    
    QPushButton.warning:hover {{
        background-color: #e0a800;
    }}
    
    QPushButton.error {{
        background-color: {colors["error"]};
    }}
    
    QPushButton.error:hover {{
        background-color: #c82333;
    }}
    
    QPushButton.secondary {{
        background-color: {colors["secondary"]};
    }}
    
    QPushButton.secondary:hover {{
        background-color: #545b62;
    }}
    
    /* Input Field Styling */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {colors["surface_variant"]};
        border: 1px solid {colors["border"]};
        padding: 6px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: {colors["text_primary"]};
        selection-background-color: {colors["primary"]};
        min-height: {ui["INPUT_HEIGHT"]}px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {colors["border_focus"]};
        background-color: {colors["surface"]};
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {colors["surface"]};
        color: {colors["text_disabled"]};
    }}
    
    /* ComboBox Styling */
    QComboBox {{
        background-color: {colors["surface_variant"]};
        border: 1px solid {colors["border"]};
        padding: 6px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: {colors["text_primary"]};
        min-height: {ui["INPUT_HEIGHT"]}px;
        padding-right: 20px;
    }}
    
    QComboBox:hover {{
        background-color: {colors["hover"]};
    }}
    
    QComboBox:focus {{
        border-color: {colors["border_focus"]};
    }}
    
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid {colors["border"]};
        background-color: {colors["surface_variant"]};
        border-top-right-radius: {ui["BORDER_RADIUS"]}px;
        border-bottom-right-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid {colors["text_primary"]};
        margin: 0 2px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        selection-background-color: {colors["primary"]};
        color: {colors["text_primary"]};
        outline: none;
    }}
    
    /* SpinBox Styling */
    QSpinBox, QDoubleSpinBox {{
        background-color: {colors["surface_variant"]};
        border: 1px solid {colors["border"]};
        padding: 6px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: {colors["text_primary"]};
        min-height: {ui["INPUT_HEIGHT"]}px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {colors["border_focus"]};
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        width: 16px;
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {colors["hover"]};
    }}
    
    /* Table Widget Styling */
    QTableWidget, QTreeWidget, QListWidget {{
        background-color: {colors["surface"]};
        alternate-background-color: {colors["surface_variant"]};
        gridline-color: {colors["border"]};
        border: 1px solid {colors["border"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
        selection-background-color: {colors["primary"]};
        selection-color: white;
        outline: none;
    }}
    
    QTableWidget::item, QTreeWidget::item, QListWidget::item {{
        padding: 8px;
        border: none;
        min-height: {ui["TABLE_ROW_HEIGHT"]}px;
    }}
    
    QTableWidget::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
        background-color: {colors["primary"]};
        color: white;
    }}
    
    QTableWidget::item:hover, QTreeWidget::item:hover, QListWidget::item:hover {{
        background-color: {colors["hover"]};
    }}
    
    /* Header Styling */
    QHeaderView::section {{
        background-color: {colors["surface_variant"]};
        color: {colors["text_primary"]};
        padding: 8px;
        border: 1px solid {colors["border"]};
        font-weight: bold;
        border-radius: 0px;
    }}
    
    QHeaderView::section:hover {{
        background-color: {colors["hover"]};
    }}
    
    QHeaderView::section:pressed {{
        background-color: {colors["primary"]};
        color: white;
    }}
    
    /* Slider Styling */
    QSlider::groove:horizontal {{
        border: 1px solid {colors["border"]};
        background: {colors["surface_variant"]};
        height: 8px;
        border-radius: 4px;
    }}
    
    QSlider::sub-page:horizontal {{
        background: {colors["primary"]};
        border: 1px solid {colors["border"]};
        height: 8px;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: white;
        border: 2px solid {colors["primary"]};
        width: 16px;
        margin: -4px 0;
        border-radius: 8px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {colors["primary"]};
    }}
    
    QSlider::groove:vertical {{
        border: 1px solid {colors["border"]};
        background: {colors["surface_variant"]};
        width: 8px;
        border-radius: 4px;
    }}
    
    QSlider::sub-page:vertical {{
        background: {colors["primary"]};
        border: 1px solid {colors["border"]};
        width: 8px;
        border-radius: 4px;
    }}
    
    QSlider::handle:vertical {{
        background: white;
        border: 2px solid {colors["primary"]};
        height: 16px;
        margin: 0 -4px;
        border-radius: 8px;
    }}
    
    /* Progress Bar Styling */
    QProgressBar {{
        border: 1px solid {colors["border"]};
        border-radius: 4px;
        text-align: center;
        background-color: {colors["surface"]};
        color: {colors["text_primary"]};
        font-weight: bold;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors["primary"]};
        border-radius: 3px;
    }}
    
    /* CheckBox and RadioButton Styling */
    QCheckBox, QRadioButton {{
        color: {colors["text_primary"]};
        spacing: 8px;
    }}
    
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {colors["border"]};
        background-color: {colors["surface"]};
    }}
    
    QCheckBox::indicator {{
        border-radius: 3px;
    }}
    
    QRadioButton::indicator {{
        border-radius: 8px;
    }}
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {colors["primary"]};
        border-color: {colors["primary"]};
    }}
    
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {colors["primary"]};
    }}
    
    /* ScrollBar Styling */
    QScrollBar:vertical {{
        background-color: {colors["surface"]};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors["border"]};
        border-radius: 6px;
        min-height: 20px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors["text_secondary"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {colors["surface"]};
        height: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors["border"]};
        border-radius: 6px;
        min-width: 20px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {colors["text_secondary"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* Menu and MenuBar Styling */
    QMenuBar {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        border-bottom: 1px solid {colors["border"]};
        spacing: 3px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors["hover"]};
    }}
    
    QMenuBar::item:pressed {{
        background-color: {colors["primary"]};
        color: white;
    }}
    
    QMenu {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
        padding: 4px;
        color: {colors["text_primary"]};
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors["primary"]};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {colors["border"]};
        margin: 4px 8px;
    }}
    
    /* Status Bar Styling */
    QStatusBar {{
        background-color: {colors["surface"]};
        border-top: 1px solid {colors["border"]};
        color: {colors["text_primary"]};
        padding: 4px;
    }}
    
    QStatusBar::item {{
        border: none;
    }}
    
    /* ToolTip Styling */
    QToolTip {{
        background-color: {colors["surface_variant"]};
        color: {colors["text_primary"]};
        border: 1px solid {colors["border"]};
        padding: 6px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        font-size: 11px;
    }}
    
    /* Dialog Styling */
    QDialog {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
    }}
    
    /* Splitter Styling */
    QSplitter::handle {{
        background-color: {colors["border"]};
        border: 1px solid {colors["border"]};
    }}
    
    QSplitter::handle:horizontal {{
        width: 3px;
    }}
    
    QSplitter::handle:vertical {{
        height: 3px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {colors["primary"]};
    }}
    
    /* Special Widget Styling */
    .log-widget {{
        background-color: #1a1a1a;
        color: #00ff00;
        font-family: 'Courier New', 'Monaco', 'Consolas', monospace;
        font-size: 11px;
        border: 1px solid {colors["border"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    .media-preview {{
        background-color: black;
        border: 2px solid {colors["border"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    .status-connected {{
        color: {colors["success"]};
        font-weight: bold;
    }}
    
    .status-disconnected {{
        color: {colors["error"]};
        font-weight: bold;
    }}
    
    .status-streaming {{
        color: {colors["error"]};
        font-weight: bold;
        animation: blink 1s infinite;
    }}
    
    .quality-indicator {{
        background-color: {colors["info"]};
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
    }}
    
    /* Animation for streaming indicator */
    @keyframes blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0.5; }}
    }}
    """


def get_light_stylesheet() -> str:
    """Get light theme stylesheet (alternative theme)"""
    
    # Import light theme colors
    from core.constants import LIGHT_THEME_COLORS
    colors = LIGHT_THEME_COLORS
    ui = UI_CONSTANTS
    
    return f"""
    /* Light Theme - Main Application */
    QMainWindow {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
    }}
    
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text_primary"]};
        selection-background-color: {colors["selection"]};
        selection-color: white;
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {colors["primary"]};
        border: 1px solid {colors["border"]};
        padding: 8px 16px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: white;
        font-weight: bold;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["primary_hover"]};
    }}
    
    /* Input fields */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        padding: 6px;
        border-radius: {ui["BORDER_RADIUS"]}px;
        color: {colors["text_primary"]};
    }}
    
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {colors["border_focus"]};
    }}
    
    /* Tables */
    QTableWidget {{
        background-color: {colors["surface"]};
        alternate-background-color: {colors["surface_variant"]};
        gridline-color: {colors["border"]};
        border: 1px solid {colors["border"]};
        border-radius: {ui["BORDER_RADIUS"]}px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors["primary"]};
        color: white;
    }}
    """


def apply_custom_styles(widget: QWidget, style_class: str):
    """Apply custom styles to specific widgets"""
    
    custom_styles = {
        "success-button": f"""
            QPushButton {{
                background-color: {DARK_THEME_COLORS["success"]};
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
        """,
        
        "error-button": f"""
            QPushButton {{
                background-color: {DARK_THEME_COLORS["error"]};
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """,
        
        "warning-button": f"""
            QPushButton {{
                background-color: {DARK_THEME_COLORS["warning"]};
                color: #212529;
                font-weight: bold;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #e0a800;
            }}
        """,
        
        "stream-control": f"""
            QPushButton {{
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 120px;
            }}
        """,
        
        "media-info-panel": f"""
            QWidget {{
                background-color: {DARK_THEME_COLORS["surface"]};
                border: 1px solid {DARK_THEME_COLORS["border"]};
                border-radius: 8px;
                padding: 12px;
            }}
        """,
        
        "status-indicator": f"""
            QLabel {{
                padding: 4px 8px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
            }}
        """,
        
        "log-console": f"""
            QTextEdit {{
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid {DARK_THEME_COLORS["border"]};
                border-radius: 4px;
                selection-background-color: #333333;
            }}
        """,
        
        "toolbar": f"""
            QWidget {{
                background-color: {DARK_THEME_COLORS["surface_variant"]};
                border-bottom: 1px solid {DARK_THEME_COLORS["border"]};
                padding: 8px;
            }}
        """,
        
        "card": f"""
            QWidget {{
                background-color: {DARK_THEME_COLORS["surface"]};
                border: 1px solid {DARK_THEME_COLORS["border"]};
                border-radius: 8px;
                padding: 16px;
                margin: 4px;
            }}
        """
    }
    
    if style_class in custom_styles:
        widget.setStyleSheet(custom_styles[style_class])


def create_status_style(status_type: str) -> str:
    """Create status-specific styles"""
    
    status_styles = {
        "connected": f"color: {DARK_THEME_COLORS['success']}; font-weight: bold;",
        "disconnected": f"color: {DARK_THEME_COLORS['error']}; font-weight: bold;",
        "streaming": f"color: {DARK_THEME_COLORS['error']}; font-weight: bold; text-decoration: blink;",
        "warning": f"color: {DARK_THEME_COLORS['warning']}; font-weight: bold;",
        "info": f"color: {DARK_THEME_COLORS['info']}; font-weight: bold;",
        "normal": f"color: {DARK_THEME_COLORS['text_primary']};"
    }
    
    return status_styles.get(status_type, status_styles["normal"])


def apply_theme_to_dialog(dialog: QWidget):
    """Apply theme specifically to dialogs"""
    
    dialog_style = f"""
    QDialog {{
        background-color: {DARK_THEME_COLORS["background"]};
        color: {DARK_THEME_COLORS["text_primary"]};
        border: 1px solid {DARK_THEME_COLORS["border"]};
    }}
    
    QDialogButtonBox QPushButton {{
        min-width: 80px;
        padding: 8px 16px;
    }}
    """
    
    dialog.setStyleSheet(dialog_style)


def get_icon_style(icon_type: str) -> str:
    """Get styles for icon buttons"""
    
    icon_styles = {
        "play": f"background-color: {DARK_THEME_COLORS['success']};",
        "stop": f"background-color: {DARK_THEME_COLORS['error']};",
        "pause": f"background-color: {DARK_THEME_COLORS['warning']};",
        "record": f"background-color: #dc143c;",
        "settings": f"background-color: {DARK_THEME_COLORS['secondary']};",
        "info": f"background-color: {DARK_THEME_COLORS['info']};"
    }
    
    base_style = f"""
    QPushButton {{
        border: none;
        border-radius: 20px;
        padding: 8px;
        color: white;
        font-weight: bold;
        min-width: 40px;
        min-height: 40px;
    }}
    """
    
    return base_style + icon_styles.get(icon_type, "")


def create_gradient_background(start_color: str, end_color: str, direction: str = "vertical") -> str:
    """Create gradient background style"""
    
    if direction == "horizontal":
        return f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {start_color}, stop:1 {end_color});"
    else:
        return f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {start_color}, stop:1 {end_color});"


def apply_animation_style(widget: QWidget, animation_type: str):
    """Apply CSS animations to widgets"""
    
    animations = {
        "pulse": """
            animation: pulse 2s infinite;
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
        """,
        
        "blink": """
            animation: blink 1s infinite;
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0.5; }
            }
        """,
        
        "fadeIn": """
            animation: fadeIn 0.5s;
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        """
    }
    
    if animation_type in animations:
        current_style = widget.styleSheet()
        widget.setStyleSheet(current_style + animations[animation_type])


def get_responsive_font_size(base_size: int = 12) -> str:
    """Get responsive font size based on screen DPI"""
    
    from PyQt6.QtWidgets import QApplication
    
    try:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            dpi = screen.logicalDotsPerInch()
            
            # Scale font based on DPI
            if dpi > 120:
                return f"{int(base_size * 1.2)}px"
            elif dpi < 96:
                return f"{int(base_size * 0.9)}px"
            else:
                return f"{base_size}px"
    except:
        pass
    
    return f"{base_size}px"


def create_theme_manager():
    """Create a theme manager for dynamic theme switching"""
    
    class ThemeManager:
        def __init__(self):
            self.current_theme = "dark"
            self.themes = {
                "dark": get_dark_stylesheet,
                "light": get_light_stylesheet
            }
        
        def apply_theme(self, theme_name: str, target=None):
            """Apply theme to target widget or application"""
            if theme_name in self.themes:
                stylesheet = self.themes[theme_name]()
                
                if target is None:
                    app = QApplication.instance()
                    if app:
                        app.setStyleSheet(stylesheet)
                else:
                    target.setStyleSheet(stylesheet)
                
                self.current_theme = theme_name
        
        def get_current_theme(self) -> str:
            return self.current_theme
        
        def toggle_theme(self, target=None):
            """Toggle between dark and light themes"""
            new_theme = "light" if self.current_theme == "dark" else "dark"
            self.apply_theme(new_theme, target)
        
        def add_custom_theme(self, name: str, stylesheet_func):
            """Add custom theme"""
            self.themes[name] = stylesheet_func
    
    return ThemeManager()


# Global theme manager instance
theme_manager = create_theme_manager()


def setup_theme_for_application(app: QApplication, theme_name: str = "dark"):
    """Setup theme for the entire application"""
    
    # Apply palette first
    if theme_name == "dark":
        _apply_dark_palette(app)
    
    # Apply stylesheet
    theme_manager.apply_theme(theme_name, app)
    
    # Set additional application properties
    app.setProperty("theme", theme_name)


def get_theme_colors(theme_name: str = None) -> dict:
    """Get color palette for specified theme"""
    
    if theme_name is None:
        theme_name = theme_manager.get_current_theme()
    
    if theme_name == "light":
        from core.constants import LIGHT_THEME_COLORS
        return LIGHT_THEME_COLORS
    else:
        return DARK_THEME_COLORS


def create_custom_widget_style(widget_type: str, **style_overrides) -> str:
    """Create custom widget styles with overrides"""
    
    base_styles = {
        "button": f"""
            QPushButton {{
                background-color: {DARK_THEME_COLORS["primary"]};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """,
        
        "input": f"""
            QLineEdit {{
                background-color: {DARK_THEME_COLORS["surface_variant"]};
                border: 1px solid {DARK_THEME_COLORS["border"]};
                padding: 6px;
                border-radius: 4px;
                color: {DARK_THEME_COLORS["text_primary"]};
            }}
        """,
        
        "table": f"""
            QTableWidget {{
                background-color: {DARK_THEME_COLORS["surface"]};
                alternate-background-color: {DARK_THEME_COLORS["surface_variant"]};
                gridline-color: {DARK_THEME_COLORS["border"]};
                border: 1px solid {DARK_THEME_COLORS["border"]};
                border-radius: 4px;
            }}
        """
    }
    
    base_style = base_styles.get(widget_type, "")
    
    # Apply overrides
    for property_name, value in style_overrides.items():
        # Simple override implementation
        # In a real implementation, you'd parse and modify the CSS properly
        override = f"{property_name}: {value};"
        base_style = base_style.replace("}", f"{override}}}")
    
    return base_style