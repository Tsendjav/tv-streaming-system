#!/usr/bin/env python3
"""
Professional Streaming Studio - Main Window
Үндсэн цонхны файл - Integration system-тэй бүрэн хувилбар (ABC-гүй)
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
from PyQt6.QtGui import QShortcut

# PyQt6 импортууд - БҮХ шаардлагатай компонентууд
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QLabel, QPushButton,
    QMessageBox, QDialog, QSplitter, QGroupBox, QFormLayout,
    QTextEdit, QProgressBar, QSystemTrayIcon, QMenu, QFileDialog
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSettings, QSize, QPoint,
    QPropertyAnimation, QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QFont, QColor, QPalette,
    QAction, QKeySequence
)

# Fallback imports
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

try:
    from core.config_manager import ConfigManager
except ImportError:
    # Fallback config manager
    class ConfigManager:
        def __init__(self):
            self.config = {}

        def get_media_library_path(self):
            return Path("data/media")

        def save_config(self):
            pass

        def get_integration_settings(self):
            return {
                'enabled': True,
                'monitoring_enabled': True,
                'automation_enabled': True
            }

# Tab импортууд - Fallback системтэй
tabs_available = {}

# Media Library Tab
try:
    from ui.tabs.media_library_tab import MediaLibraryTab
    tabs_available['media_library'] = MediaLibraryTab
    print("✅ Media Library tab imported")
except ImportError as e:
    print(f"❌ Media Library tab import failed: {e}")
    tabs_available['media_library'] = None

# Streaming Tab - ЗАСВАРЛАСАН ХЭСЭГ
def import_streaming_tab():
    """Streaming Tab import with proper fallback logic"""
    try:
        # Try refactored streaming tab first
        from streaming.refactored_streaming_tab import RefactoredStreamingTab as StreamingTab
        print("✅ Using refactored streaming tab")
        return StreamingTab
    except ImportError:
        try:
            # Add project root to path if needed
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # Try refactored again after adding path
            from streaming.refactored_streaming_tab import RefactoredStreamingTab as StreamingTab
            print("✅ Using refactored streaming tab (after path fix)")
            return StreamingTab
        except ImportError:
            try:
                # Fallback to legacy streaming tab
                from streaming.integration import create_streaming_tab as StreamingTab
                print("⚠️ Using legacy streaming tab")
                return StreamingTab
            except ImportError as e:
                print(f"❌ All streaming tab imports failed: {e}")
                return None

# Import streaming tab
tabs_available['streaming'] = import_streaming_tab()

# Playout Tab - ЗАСВАРЛАСАН ХЭСЭГ
try:
    from ui.tabs.playout_tab import PlayoutTab, PLAYOUT_TAB_AVAILABLE
    if PLAYOUT_TAB_AVAILABLE:
        tabs_available['playout'] = PlayoutTab
        print("✅ Playout tab imported from ui.tabs.playout_tab")
    else:
        tabs_available['playout'] = None
        print("❌ Playout tab components not available")
except ImportError as e:
    print(f"❌ Playout tab import failed: {e}")
    tabs_available['playout'] = None

# Scheduler Tab
try:
    from ui.tabs.scheduler_tab import SchedulerTab
    tabs_available['scheduler'] = SchedulerTab
    print("✅ Scheduler tab imported")
except ImportError as e:
    print(f"❌ Scheduler tab import failed: {e}")
    tabs_available['scheduler'] = None

# Server Config Dialog
try:
    from ui.dialogs.server_config import ServerManagerDialog
    server_config_available = True
    print("✅ Server config dialog imported")
except ImportError as e:
    print(f"❌ Server config dialog import failed: {e}")
    server_config_available = False

# Integration System import
try:
    from core.integration import (
        setup_integration_system,
        IntegrationConfig,
        EventType,
        SystemEvent,
        EventBus,
        SharedDataManager,
        TabIntegrationManager,
        WorkflowEngine
    )
    integration_system_available = True
    print("✅ Integration system imported")
except ImportError as e:
    print(f"❌ Integration system import failed: {e}")
    integration_system_available = False

    class IntegrationConfig:
        def __init__(self):
            self.monitoring_enabled = True
            self.automation_enabled = True
            self.use_localized_messages = True

    class EventType:
        MEDIA_LOADED = "media_loaded"
        STREAM_STARTED = "stream_started"

    class SystemEvent:
        def __init__(self, event_type, data, source_tab="unknown"):
            self.event_type = event_type
            self.data = data
            self.source_tab = source_tab

    def setup_integration_system(main_window, config_manager, event_bus, shared_data_manager, tab_integration_manager, workflow_engine):
        print("⚠️ Using fallback setup_integration_system")
        main_window.event_bus = EventBus()
        main_window.shared_data_manager = SharedDataManager()
        main_window.tab_integration_manager = TabIntegrationManager()
        main_window.workflow_engine = WorkflowEngine()
        main_window.system_monitor = None
        return None

    class EventBus:
        global_event = pyqtSignal(SystemEvent)
        def emit_event(self, event):
            self.global_event.emit(event)
            print(f"FALLBACK EventBus emitted: {event.event_type}")

    class SharedDataManager:
        def get_data(self, key: str, default: Any = None) -> Any:
            print(f"FALLBACK SharedDataManager: get {key}")
            return default
        def set_data(self, key: str, value: Any):
            print(f"FALLBACK SharedDataManager: set {key} = {value}")

    class TabIntegrationManager:
        def register_integrated_tab(self, tab_id: str, tab_instance: Any):
            print(f"FALLBACK TabIntegrationManager: registered {tab_id}")
        def get_tab(self, tab_id: str) -> Optional[Any]:
            print(f"FALLBACK TabIntegrationManager: get tab {tab_id}")
            return None
        def execute_tab_command(self, tab_id: str, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
            print(f"FALLBACK TabIntegrationManager: execute command {command} on {tab_id}")
            return {"error": "Tab integration manager not available"}

    class WorkflowEngine:
        def __init__(self):
            self.workflows = {}
        def execute_workflow(self, workflow_name: str, params: Optional[Dict] = None) -> str:
            print(f"FALLBACK WorkflowEngine: execute {workflow_name}")
            return "mock_workflow_id_123"

# =============================================================================
# TAB INTEGRATION INTERFACE (ABC-гүй)
# =============================================================================

class ITabIntegration:
    """Simple interface for tab integration without ABC"""

    def get_tab_name(self) -> str:
        """Get tab name for identification"""
        return "unknown_tab"

    def handle_system_event(self, event):
        """Handle incoming system event"""
        pass

    def get_tab_status(self) -> Dict[str, Any]:
        """Get current tab status"""
        return {"status": "unknown"}

    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute tab-specific command"""
        return {"error": f"Command {command} not implemented"}

# =============================================================================
# PLACEHOLDER TAB CLASS
# =============================================================================

class PlaceholderTab(QWidget):
    """Placeholder tab for missing modules"""

    status_message = pyqtSignal(str, int)

    def __init__(self, tab_name: str, error_message: str = "Module not available"):
        super().__init__()
        self.tab_name = tab_name
        self.error_message = error_message

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("⚠️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; margin: 30px;")
        layout.addWidget(icon_label)

        title_label = QLabel(f"{tab_name} Not Available")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #666; margin-bottom: 15px;")
        layout.addWidget(title_label)

        error_label = QLabel(error_message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #999; font-size: 14px; margin-bottom: 30px;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

        instructions = QLabel("""
        <b>To enable this tab:</b><br>
        1. Check that all required files are present<br>
        2. Install missing dependencies<br>
        3. Restart the application
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #777; font-size: 12px; background: #f5f5f5; padding: 15px; border-radius: 8px;")
        layout.addWidget(instructions)

        retry_btn = QPushButton("🔄 Retry Loading")
        retry_btn.clicked.connect(self._retry_loading)
        retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        layout.addWidget(retry_btn)

    def _retry_loading(self):
        """Placeholder retry function"""
        self.status_message.emit(f"Cannot reload {self.tab_name} - restart application required", 5000)

    def refresh(self):
        """Placeholder refresh function"""
        pass

    def cleanup(self):
        """Placeholder cleanup function"""
        pass

    def get_tab_name(self) -> str:
        """Get tab name for integration"""
        return self.tab_name.lower().replace(" ", "_")

    def handle_system_event(self, event):
        """Handle system event"""
        pass

    def get_tab_status(self) -> Dict[str, Any]:
        """Get tab status"""
        return {
            "name": self.tab_name,
            "status": "placeholder",
            "available": False,
            "error": self.error_message
        }

    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute command"""
        return {"error": f"Tab {self.tab_name} is not available"}

# =============================================================================
# MAIN WINDOW CLASS
# =============================================================================

class ProfessionalStreamingStudio(QMainWindow):
    """Main application window with full integration support"""

    def __init__(self, config_manager: ConfigManager, app: QApplication):
        super().__init__()
        self.config_manager = config_manager
        self.app = app
        self.logger = get_logger(__name__)

        # Tab storage
        self.tabs = {}
        self.tabs_instances = {}

        # UI state
        self.is_fullscreen = False
        self.normal_geometry = None

        # Integration system components
        self.integration_system = None
        self.system_monitor = None
        self.event_bus = EventBus() if not integration_system_available else None
        self.shared_data_manager = SharedDataManager() if not integration_system_available else None
        self.tab_integration_manager = TabIntegrationManager() if not integration_system_available else None
        self.workflow_engine = WorkflowEngine() if not integration_system_available else None

        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._create_tabs()
        self._setup_shortcuts()
        self._apply_styling()
        self._setup_integration_system()
        self._finalize_tab_setup()  # Added new method
        self._setup_streaming_shortcuts()  # Added new method

        # Start status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_bar_with_streaming_info)
        self.status_timer.start(2000)  # Update every 2 seconds

        self.logger.info("Main window initialized")

    def _init_ui(self):
        """Initialize main UI"""
        self.setWindowTitle("Professional TV Streaming Studio")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self._center_window()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)
        main_layout.addWidget(self.tab_widget)

    def _center_window(self):
        """Center window on screen"""
        screen = self.app.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def _create_menu_bar(self):
        """Create menu bar"""
        self.menubar = self.menuBar()  # Changed to self.menubar to be accessible

        file_menu = self.menubar.addMenu("&File")
        import_action = QAction("📥 &Import Media", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._import_media)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        settings_action = QAction("⚙️ &Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menubar.addMenu("&View")
        fullscreen_action = QAction("🖥️ &Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        view_menu.addSeparator()

        refresh_action = QAction("🔄 &Refresh All", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_all_tabs)
        view_menu.addAction(refresh_action)

        tools_menu = self.menubar.addMenu("&Tools")

        if integration_system_available:
            tools_menu.addSeparator()
            status_action = QAction("📊 &System Status", self)
            status_action.triggered.connect(self._show_integration_status)
            tools_menu.addAction(status_action)

            workflow_action = QAction("🔄 Execute &Workflow", self)
            workflow_action.triggered.connect(self._show_workflow_dialog)
            tools_menu.addAction(workflow_action)

            emergency_action = QAction("🛑 &Emergency Stop", self)
            emergency_action.setShortcut(QKeySequence("Ctrl+Alt+E"))
            emergency_action.triggered.connect(self._emergency_stop)
            tools_menu.addAction(emergency_action)

        server_action = QAction("🖥️ &Server Management", self)
        server_action.triggered.connect(self._open_server_management)
        tools_menu.addAction(server_action)

        audio_action = QAction("🔊 &Audio Settings", self)
        audio_action.triggered.connect(self._open_audio_settings)
        tools_menu.addAction(audio_action)

        tools_menu.addSeparator()

        deps_action = QAction("🔍 Check &Dependencies", self)
        deps_action.triggered.connect(self._check_dependencies)
        tools_menu.addAction(deps_action)

        help_menu = self.menubar.addMenu("&Help")
        about_action = QAction("ℹ️ &About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("📖 &Documentation", self)
        docs_action.triggered.connect(self._open_documentation)
        help_menu.addAction(docs_action)

        # Add integration menu
        self._create_integration_menu()

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.connection_status = QLabel("🔴 Offline")
        self.status_bar.addPermanentWidget(self.connection_status)

        if integration_system_available:
            self.integration_status = QLabel("🔄 Integration Ready")
            self.status_bar.addPermanentWidget(self.integration_status)

        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)
        self._update_time()

    def _update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def _create_tabs(self):
        """Create and add tabs"""
        # Media Library Tab
        if tabs_available['media_library']:
            try:
                media_tab = tabs_available['media_library'](self.config_manager)
                media_tab.status_message.connect(self._show_status_message)
                self.tabs['media_library'] = media_tab
                self.tabs_instances['media_library'] = media_tab
                self.tab_widget.addTab(media_tab, "📁 Media Library")
                self.logger.info("Media Library tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Media Library tab: {e}")
                placeholder = PlaceholderTab("Media Library", f"Failed to initialize: {e}")
                placeholder.status_message.connect(self._show_status_message)
                self.tabs['media_library'] = placeholder
                self.tabs_instances['media_library'] = placeholder
                self.tab_widget.addTab(placeholder, "📁 Media Library")
        else:
            placeholder = PlaceholderTab("Media Library", "Media library module not available")
            placeholder.status_message.connect(self._show_status_message)
            self.tabs['media_library'] = placeholder
            self.tabs_instances['media_library'] = placeholder
            self.tab_widget.addTab(placeholder, "📁 Media Library")

        # Store media_tab for later reference
        media_tab = self.tabs['media_library']

        # Playout Tab
        if tabs_available['playout']:
            try:
                playout_tab = tabs_available['playout'](self.config_manager)
                playout_tab.status_message.connect(self._show_status_message)
                if hasattr(playout_tab, 'media_loaded'):
                    playout_tab.media_loaded.connect(self._on_media_loaded)
                if hasattr(playout_tab, 'server_config_requested'):
                    playout_tab.server_config_requested.connect(self._open_server_management)

                # Connect media_selected signal if both tabs are real (not placeholders)
                if hasattr(media_tab, 'media_selected') and not isinstance(media_tab, PlaceholderTab):
                    media_tab.media_selected.connect(self.on_media_selected)
                    self.logger.info("Connected media_selected signal from Media Library to Main Window")

                if hasattr(playout_tab, 'media_library_requested'):
                    playout_tab.media_library_requested.connect(self.on_media_library_requested)
                    self.logger.info("Connected media_library_requested signal from Playout to Main Window")

                if hasattr(playout_tab, 'set_media_library_tab') and not isinstance(media_tab, PlaceholderTab):
                    playout_tab.set_media_library_tab(media_tab)
                    self.logger.info("Set Media Library tab reference in Playout tab")

                self.tabs['playout'] = playout_tab
                self.tabs_instances['playout'] = playout_tab
                self.tab_widget.addTab(playout_tab, "🎬 Playout")
                self.logger.info("Playout tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Playout tab: {e}")
                placeholder = PlaceholderTab("Playout", f"Failed to initialize: {e}")
                placeholder.status_message.connect(self._show_status_message)
                self.tabs['playout'] = placeholder
                self.tabs_instances['playout'] = placeholder
                self.tab_widget.addTab(placeholder, "🎬 Playout")
        else:
            placeholder = PlaceholderTab("Playout", "Playout module not available")
            placeholder.status_message.connect(self._show_status_message)
            self.tabs['playout'] = placeholder
            self.tabs_instances['playout'] = placeholder
            self.tab_widget.addTab(placeholder, "🎬 Playout")

        # Streaming Tab
        if tabs_available['streaming']:
            try:
                streaming_tab = tabs_available['streaming'](self.config_manager)
                streaming_tab.status_message.connect(self._show_status_message)
                if hasattr(streaming_tab, 'stream_status_changed'):
                    streaming_tab.stream_status_changed.connect(self._on_stream_status_changed)
                self.tabs['streaming'] = streaming_tab
                self.tabs_instances['streaming'] = streaming_tab
                self.tab_widget.addTab(streaming_tab, "📡 Streaming")
                self.logger.info("Streaming tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Streaming tab: {e}")
                placeholder = PlaceholderTab("Streaming", f"Failed to initialize: {e}")
                placeholder.status_message.connect(self._show_status_message)
                self.tabs['streaming'] = placeholder
                self.tabs_instances['streaming'] = placeholder
                self.tab_widget.addTab(placeholder, "📡 Streaming")
        else:
            placeholder = PlaceholderTab("Streaming", "Streaming module not available")
            placeholder.status_message.connect(self._show_status_message)
            self.tabs['streaming'] = placeholder
            self.tabs_instances['streaming'] = placeholder
            self.tab_widget.addTab(placeholder, "📡 Streaming")

        # Scheduler Tab
        if tabs_available['scheduler']:
            try:
                scheduler_tab = tabs_available['scheduler'](self.config_manager)
                scheduler_tab.status_message.connect(self._show_status_message)
                self.tabs['scheduler'] = scheduler_tab
                self.tabs_instances['scheduler'] = scheduler_tab
                self.tab_widget.addTab(scheduler_tab, "⏰ Scheduler")
                self.logger.info("Scheduler tab created")
            except Exception as e:
                self.logger.error(f"Failed to create Scheduler tab: {e}")
                placeholder = PlaceholderTab("Scheduler", f"Failed to initialize: {e}")
                placeholder.status_message.connect(self._show_status_message)
                self.tabs['scheduler'] = placeholder
                self.tabs_instances['scheduler'] = placeholder
                self.tab_widget.addTab(placeholder, "⏰ Scheduler")
        else:
            placeholder = PlaceholderTab("Scheduler", "Scheduler module not available")
            placeholder.status_message.connect(self._show_status_message)
            self.tabs['scheduler'] = placeholder
            self.tabs_instances['scheduler'] = placeholder
            self.tab_widget.addTab(placeholder, "⏰ Scheduler")

        # Logs Tab
        try:
            logs_tab = self._create_logs_tab()
            self.tabs['logs'] = logs_tab
            self.tabs_instances['logs'] = logs_tab
            self.tab_widget.addTab(logs_tab, "📋 Logs")
            self.logger.info("Logs tab created")
        except Exception as e:
            self.logger.error(f"Failed to create Logs tab: {e}")
            placeholder = PlaceholderTab("Logs", f"Failed to initialize: {e}")
            placeholder.status_message.connect(self._show_status_message)
            self.tabs['logs'] = placeholder
            self.tabs_instances['logs'] = placeholder
            self.tab_widget.addTab(placeholder, "📋 Logs")

        self.tab_widget.setCurrentIndex(0)

    def _create_logs_tab(self) -> QWidget:
        """Create simple logs tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header_label = QLabel("📋 Application Logs")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_display)

        controls_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.log_display.clear)
        controls_layout.addWidget(clear_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._save_logs)
        controls_layout.addWidget(save_btn)

        controls_layout.addStretch()

        auto_scroll_cb = QLabel("Auto-scroll enabled")
        auto_scroll_cb.setStyleSheet("color: #666;")
        controls_layout.addWidget(auto_scroll_cb)

        layout.addLayout(controls_layout)

        self.log_display.append("🟢 Application started successfully")
        if integration_system_available:
            self.log_display.append("🔄 Integration system available")
        else:
            self.log_display.append("⚠️ Integration system not available")
        self.log_display.append("ℹ️ Logs will appear here...")

        return tab

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        for i in range(min(9, self.tab_widget.count())):
            shortcut = QKeySequence(f"Ctrl+{i+1}")
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, index=i: self.tab_widget.setCurrentIndex(index))
            self.addAction(action)

    def _apply_styling(self):
        """Apply application styling"""
        tab_style = """
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }

            QTabWidget::pane {
                border: 2px solid #404040;
                background-color: #1a1a1a;
                border-radius: 8px;
            }

            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #404040, stop:1 #2a2a2a);
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00bcd4, stop:1 #0097a7);
                color: #ffffff;
            }

            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #505050, stop:1 #3a3a3a);
                color: #00bcd4;
            }

            QStatusBar {
                background-color: #2a2a2a;
                color: #ffffff;
                border-top: 2px solid #404040;
                font-weight: bold;
            }

            QMenuBar {
                background-color: #2a2a2a;
                color: #ffffff;
                border-bottom: 2px solid #404040;
                font-weight: bold;
            }

            QMenuBar::item {
                padding: 8px 12px;
                background: transparent;
            }

            QMenuBar::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00bcd4, stop:1 #0097a7);
                border-radius: 4px;
            }

            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 6px;
            }

            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00bcd4, stop:1 #0097a7);
                border-radius: 4px;
            }
        """
        self.setStyleSheet(tab_style)

    def _setup_integration_system(self):
        """Integration system тохируулах"""
        if not integration_system_available:
            self.logger.warning("Integration system module not available. Skipping setup.")
            self.event_bus = EventBus()
            self.shared_data_manager = SharedDataManager()
            self.tab_integration_manager = TabIntegrationManager()
            self.workflow_engine = WorkflowEngine()
            return

        try:
            integration_config = IntegrationConfig()
            integration_config.monitoring_enabled = True
            integration_config.automation_enabled = True
            integration_config.use_localized_messages = True

            self.integration_system, self.event_bus, self.shared_data_manager, \
            self.tab_integration_manager, self.workflow_engine, self.system_monitor = setup_integration_system(
                self.app,
                self.config_manager,
                integration_config
            )

            if self.integration_system:
                if self.event_bus:
                    self.event_bus.global_event.connect(self._on_integration_event)

                if self.system_monitor:
                    self.system_monitor.alert_triggered.connect(self._on_integration_alert)
                    self.system_monitor.system_health_changed.connect(self._on_health_change)

                    if hasattr(self, 'integration_status'):
                        self.integration_status.setText("🟢 Integration Active")

                if self.tab_integration_manager:
                    for tab_id, tab_instance in list(self.tabs_instances.items()):
                        self.tab_integration_manager.register_integrated_tab(tab_id, tab_instance)

                self.logger.info("🎉 Integration system setup successful.")
                self._show_status_message("🎉 Integration system активлагдлаа!")

                if hasattr(self, 'log_display'):
                    self.log_display.append("🎉 Tab Integration System activated!")
                    self.log_display.append("📊 Cross-tab communication enabled")
                    self.log_display.append("🔄 Workflow automation ready")
                    self.log_display.append("📈 Real-time monitoring active")

            else:
                self.logger.warning("Integration system setup returned None or failed to initialize components")
                if hasattr(self, 'integration_status'):
                    self.integration_status.setText("🔴 Integration Failed (No System)")

        except Exception as e:
            self.logger.error(f"Integration setup failed: {e}")
            self._show_status_message(f"Integration system error: {e}")
            if hasattr(self, 'integration_status'):
                self.integration_status.setText("🔴 Integration Failed")
            self.integration_system = None
            self.event_bus = EventBus()
            self.shared_data_manager = SharedDataManager()
            self.tab_integration_manager = TabIntegrationManager()
            self.workflow_engine = WorkflowEngine()

    def _setup_tab_integrations(self):
        """Setup integrations between tabs"""
        try:
            playout_tab = None
            streaming_tab = None
            
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                tab_name = self.tab_widget.tabText(i)
                
                if "playout" in tab_name.lower() or hasattr(tab, 'get_tab_name') and tab.get_tab_name() == "playout":
                    playout_tab = tab
                elif "streaming" in tab_name.lower() or hasattr(tab, 'get_tab_name') and tab.get_tab_name() == "streaming":
                    streaming_tab = tab
            
            if playout_tab and streaming_tab:
                self._connect_playout_to_streaming(playout_tab, streaming_tab)
                print("✅ Tab integrations setup successfully")
                
        except Exception as e:
            print(f"❌ Failed to setup tab integrations: {e}")

    def _connect_playout_to_streaming(self, playout_tab, streaming_tab):
        """Connect playout tab to streaming tab"""
        try:
            if hasattr(playout_tab, 'stream_program_requested'):
                playout_tab.stream_program_requested.connect(
                    lambda file_path: self._handle_stream_program_request(file_path, streaming_tab)
                )
            
            if hasattr(streaming_tab, 'stream_status_changed'):
                streaming_tab.stream_status_changed.connect(
                    lambda is_streaming, stream_key: self._update_playout_streaming_status(
                        playout_tab, is_streaming, stream_key
                    )
                )
            
            if hasattr(playout_tab, 'stream_status_changed'):
                playout_tab.stream_status_changed.connect(
                    lambda is_streaming, message: self._handle_playout_stream_control(
                        streaming_tab, is_streaming, message
                    )
                )
            
            print("🔗 Playout and Streaming tabs connected")
            
        except Exception as e:
            print(f"❌ Failed to connect playout to streaming: {e}")

    def _handle_stream_program_request(self, file_path, streaming_tab):
        """Handle request to stream program content"""
        try:
            print(f"📺 Received stream request for: {file_path}")
            
            if not Path(file_path).exists():
                print(f"❌ File not found: {file_path}")
                return False
            
            if not hasattr(streaming_tab, '_build_stream_config') or not hasattr(streaming_tab, 'stream_manager'):
                print("❌ Streaming tab not properly initialized")
                return False
            
            success = self._auto_configure_stream_for_program(file_path, streaming_tab)
            
            if success:
                print(f"✅ Successfully started streaming: {Path(file_path).name}")
                return True
            else:
                print(f"❌ Failed to start streaming: {Path(file_path).name}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling stream request: {e}")
            return False

    def _auto_configure_stream_for_program(self, file_path, streaming_tab):
        """Automatically configure and start streaming for program content"""
        try:
            if hasattr(streaming_tab, 'source_input') and streaming_tab.source_input:
                streaming_tab.source_input.setText(file_path)
                streaming_tab.current_input_source = file_path
            
            if hasattr(streaming_tab, 'source_type_combo') and streaming_tab.source_type_combo:
                streaming_tab.source_type_combo.setCurrentText("Медиа Файл")
            
            if hasattr(streaming_tab, 'stream_key_input') and streaming_tab.stream_key_input:
                current_key = streaming_tab.stream_key_input.text().strip()
                if not current_key:
                    auto_key = f"program_{int(time.time())}"
                    streaming_tab.stream_key_input.setText(auto_key)
            
            if hasattr(streaming_tab, 'quality_combo') and streaming_tab.quality_combo:
                for i in range(streaming_tab.quality_combo.count()):
                    if "720p" in streaming_tab.quality_combo.itemText(i):
                        streaming_tab.quality_combo.setCurrentIndex(i)
                        break
            
            if hasattr(streaming_tab, 'loop_input_cb') and streaming_tab.loop_input_cb:
                streaming_tab.loop_input_cb.setChecked(True)
            
            QTimer.singleShot(500, lambda: self._start_program_stream(streaming_tab))
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to auto-configure stream: {e}")
            return False

    def _start_program_stream(self, streaming_tab):
        """Start the configured program stream"""
        try:
            if hasattr(streaming_tab, '_validate_stream_inputs'):
                if not streaming_tab._validate_stream_inputs():
                    print("❌ Stream validation failed")
                    return False
            
            if hasattr(streaming_tab, '_build_stream_config') and hasattr(streaming_tab, 'stream_manager'):
                stream_config = streaming_tab._build_stream_config()
                if stream_config:
                    success = streaming_tab.stream_manager.start_stream(stream_config)
                    if success:
                        streaming_tab.active_streams[stream_config.stream_key] = stream_config
                        print(f"✅ Program stream started: {stream_config.stream_key}")
                        return True
                    else:
                        print("❌ Failed to start stream manager")
                        return False
                else:
                    print("❌ Failed to build stream config")
                    return False
            else:
                print("❌ Streaming tab missing required methods")
                return False
                
        except Exception as e:
            print(f"❌ Error starting program stream: {e}")
            return False

    def _update_playout_streaming_status(self, playout_tab, is_streaming, stream_key):
        """Update playout tab with streaming status"""
        try:
            if hasattr(playout_tab, '_on_streaming_status_changed'):
                playout_tab._on_streaming_status_changed(is_streaming, stream_key)
            
            if hasattr(playout_tab, '_update_streaming_status'):
                playout_tab._update_streaming_status(is_streaming)
                
        except Exception as e:
            print(f"❌ Failed to update playout streaming status: {e}")

    def _handle_playout_stream_control(self, streaming_tab, is_streaming, message):
        """Handle stream control from playout tab"""
        try:
            if not is_streaming and hasattr(streaming_tab, 'stream_manager'):
                streaming_tab.stream_manager.stop_all_streams()
                print(f"🛑 Stopped streaming from playout: {message}")
                
        except Exception as e:
            print(f"❌ Failed to handle playout stream control: {e}")

    def _create_integration_menu(self):
        """Create integration menu in main window"""
        try:
            integration_menu = self.menubar.addMenu("Integration")
            
            stream_program_action = QAction("📺 Stream Current Program", self)
            stream_program_action.setShortcut("Ctrl+Shift+S")
            stream_program_action.triggered.connect(self._stream_current_program)
            integration_menu.addAction(stream_program_action)
            
            stop_streaming_action = QAction("🛑 Stop All Streaming", self)
            stop_streaming_action.setShortcut("Ctrl+Shift+X")
            stop_streaming_action.triggered.connect(self._stop_all_streaming)
            integration_menu.addAction(stop_streaming_action)
            
            integration_menu.addSeparator()
            
            take_to_air_action = QAction("🚨 Take to Air & Stream", self)
            take_to_air_action.setShortcut("F12")
            take_to_air_action.triggered.connect(self._take_to_air_and_stream)
            integration_menu.addAction(take_to_air_action)
            
        except Exception as e:
            print(f"❌ Failed to create integration menu: {e}")

    def _stream_current_program(self):
        """Stream current program content via menu"""
        try:
            playout_tab = self._get_tab_by_name("playout")
            if playout_tab and hasattr(playout_tab, '_stream_program_content'):
                playout_tab._stream_program_content()
            else:
                print("❌ Playout tab not found or not properly configured")
                
        except Exception as e:
            print(f"❌ Failed to stream current program: {e}")

    def _stop_all_streaming(self):
        """Stop all streaming via menu"""
        try:
            streaming_tab = self._get_tab_by_name("streaming")
            if streaming_tab and hasattr(streaming_tab, '_stop_all_streams'):
                streaming_tab._stop_all_streams()
            else:
                print("❌ Streaming tab not found")
                
        except Exception as e:
            print(f"❌ Failed to stop all streaming: {e}")

    def _take_to_air_and_stream(self):
        """Take to air and stream via menu"""
        try:
            playout_tab = self._get_tab_by_name("playout")
            if playout_tab and hasattr(playout_tab, '_take_to_air'):
                playout_tab._take_to_air()
            else:
                print("❌ Playout tab not found")
                
        except Exception as e:
            print(f"❌ Failed to take to air and stream: {e}")

    def _get_tab_by_name(self, tab_name):
        """Get tab by name"""
        try:
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'get_tab_name') and tab.get_tab_name() == tab_name:
                    return tab
                elif tab_name.lower() in self.tab_widget.tabText(i).lower():
                    return tab
            return None
        except Exception as e:
            print(f"❌ Error getting tab by name: {e}")
            return None

    def _finalize_tab_setup(self):
        """Finalize tab setup with integrations (call after all tabs are added)"""
        try:
            QTimer.singleShot(1000, self._setup_tab_integrations)
            self._create_integration_menu()
            print("✅ Tab integration setup completed")
            
        except Exception as e:
            print(f"❌ Failed to finalize tab setup: {e}")

    def _setup_streaming_shortcuts(self):
        """Setup keyboard shortcuts for streaming operations"""
        try:
            take_to_air_shortcut = QShortcut(QKeySequence("F12"), self)
            take_to_air_shortcut.activated.connect(self._take_to_air_and_stream)
            
            stream_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
            stream_shortcut.activated.connect(self._stream_current_program)
            
            emergency_stop_shortcut = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
            emergency_stop_shortcut.activated.connect(self._emergency_stop_all)
            
            print("⌨️ Streaming shortcuts setup completed")
            
        except Exception as e:
            print(f"❌ Failed to setup streaming shortcuts: {e}")

    def _emergency_stop_all(self):
        """Emergency stop for both playout and streaming"""
        try:
            playout_tab = self._get_tab_by_name("playout")
            if playout_tab and hasattr(playout_tab, 'emergency_stop'):
                playout_tab.emergency_stop()
            
            streaming_tab = self._get_tab_by_name("streaming")
            if streaming_tab and hasattr(streaming_tab, '_stop_all_streams'):
                streaming_tab._stop_all_streams()
            
            print("🚨 EMERGENCY STOP executed for all systems")
            
        except Exception as e:
            print(f"❌ Error during emergency stop: {e}")

    def _update_status_bar_with_streaming_info(self):
        """Update status bar with streaming information"""
        try:
            streaming_info = ""
            
            streaming_tab = self._get_tab_by_name("streaming")
            if streaming_tab and hasattr(streaming_tab, 'get_active_streams_count'):
                stream_count = streaming_tab.get_active_streams_count()
                if stream_count > 0:
                    streaming_info = f"📡 {stream_count} stream(s) active"
            
            playout_tab = self._get_tab_by_name("playout")
            if playout_tab and hasattr(playout_tab, 'is_on_air') and playout_tab.is_on_air:
                if streaming_info:
                    streaming_info += " | 🔴 ON AIR"
                else:
                    streaming_info = "🔴 ON AIR"
            
            if hasattr(self, 'status_bar') and self.status_bar:
                if streaming_info:
                    self.status_bar.showMessage(streaming_info)
            
        except Exception as e:
            print(f"❌ Failed to update status bar: {e}")

    def _show_status_message(self, message: str, timeout: int = 5000):
        """Show status message"""
        self.status_bar.showMessage(message, timeout)
        self.logger.info(f"Status: {message}")

        if hasattr(self, 'log_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.append(f"[{timestamp}] {message}")
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _on_media_loaded(self, media_file):
        """Handle media loaded signal"""
        self._show_status_message(f"Media loaded: {media_file}")

        if self.integration_system and self.event_bus:
            try:
                event = SystemEvent(
                    event_type=EventType.MEDIA_LOADED,
                    data={"file_path": media_file},
                    source_tab="playout"
                )
                self.event_bus.emit_event(event)
            except Exception as e:
                self.logger.error(f"Failed to emit integration event: {e}")

    def _on_stream_status_changed(self, streaming: bool, stream_key: str):
        """Handle stream status change"""
        if streaming:
            self.connection_status.setText("🔴 Streaming")
            self._show_status_message(f"Stream started: {stream_key}")

            if self.integration_system and self.event_bus:
                try:
                    event = SystemEvent(
                        event_type=EventType.STREAM_STARTED,
                        data={"stream_key": stream_key},
                        source_tab="streaming"
                    )
                    self.event_bus.emit_event(event)
                except Exception as e:
                    self.logger.error(f"Failed to emit integration event: {e}")
        else:
            self.connection_status.setText("🟡 Connected")
            self._show_status_message(f"Stream stopped: {stream_key}")

    def _on_integration_event(self, event):
        """Handle integration system events"""
        try:
            event_msg = f"🔄 Event: {event.event_type} from {event.source_tab}"
            if hasattr(self, 'log_display'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log_display.append(f"[{timestamp}] {event_msg}")
        except Exception as e:
            self.logger.error(f"Error handling integration event: {e}")

    def _on_integration_alert(self, alert_type: str, message: str, severity: int):
        """Handle integration system alerts"""
        severity_icons = {1: "ℹ️", 2: "⚠️", 3: "🚨"}
        icon = severity_icons.get(severity, "❓")

        alert_msg = f"{icon} ALERT: {message}"
        self._show_status_message(alert_msg, severity * 2000)

        if hasattr(self, 'log_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.append(f"[{timestamp}] {alert_msg}")

        if severity >= 3:
            QMessageBox.critical(self, "Critical Alert", message)

    def _on_health_change(self, health_status: str):
        """Handle system health changes"""
        health_icons = {
            "excellent": "🟢",
            "good": "🟡",
            "warning": "🟠",
            "critical": "🔴"
        }

        icon = health_icons.get(health_status, "❓")
        if hasattr(self, 'integration_status'):
            self.integration_status.setText(f"{icon} System {health_status.title()}")

        health_msg = f"💊 System Health: {health_status.upper()}"
        if hasattr(self, 'log_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.append(f"[{timestamp}] {health_msg}")

    def _show_integration_status(self):
        """Show comprehensive integration status"""
        if not self.integration_system:
            QMessageBox.information(self, "Integration Status", "Integration system is not available.")
            return

        try:
            status = self.integration_system.get_system_status()
            dialog = QDialog(self)
            dialog.setWindowTitle("Integration System Status")
            dialog.setModal(True)
            dialog.resize(700, 500)

            layout = QVBoxLayout(dialog)
            status_text = QTextEdit()
            status_text.setReadOnly(True)
            status_text.setFont(QFont("Consolas", 9))
            formatted_status = json.dumps(status, indent=2, ensure_ascii=False)
            status_text.setPlainText(formatted_status)

            layout.addWidget(QLabel("📊 Real-time System Status:"))
            layout.addWidget(status_text)

            button_layout = QHBoxLayout()
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self._refresh_integration_status(status_text))
            button_layout.addWidget(refresh_btn)

            button_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get integration status: {e}")

    def _refresh_integration_status(self, text_widget):
        """Refresh integration status display"""
        try:
            status = self.integration_system.get_system_status()
            formatted_status = json.dumps(status, indent=2, ensure_ascii=False)
            text_widget.setPlainText(formatted_status)
        except Exception as e:
            text_widget.setPlainText(f"Error refreshing status: {e}")

    def _show_workflow_dialog(self):
        """Show workflow execution dialog"""
        if not self.integration_system or not self.workflow_engine:
            QMessageBox.information(self, "Workflows", "Integration system or Workflow Engine is not available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Execute Workflow")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("🔄 Available Workflows:"))

        try:
            workflows = list(self.workflow_engine.workflows.keys())
        except:
            workflows = ["media_to_air", "live_streaming_setup", "emergency_procedures"]

        for workflow in workflows:
            btn = QPushButton(f"▶️ {workflow.replace('_', ' ').title()}")
            btn.clicked.connect(lambda checked, w=workflow: self._execute_workflow(w, dialog))
            layout.addWidget(btn)

        layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def _execute_workflow(self, workflow_name: str, parent_dialog=None):
        """Execute a workflow"""
        try:
            if self.integration_system and self.workflow_engine:
                execution_id = self.integration_system.execute_workflow(workflow_name)
                self._show_status_message(f"🔄 Started workflow: {workflow_name}")

                if hasattr(self, 'log_display'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.log_display.append(f"[{timestamp}] 🔄 Workflow '{workflow_name}' started (ID: {execution_id})")

                if parent_dialog:
                    parent_dialog.close()
            else:
                QMessageBox.warning(self, "Error", "Integration system or Workflow Engine not available")

        except Exception as e:
            error_msg = f"Failed to execute workflow '{workflow_name}': {e}"
            QMessageBox.critical(self, "Workflow Error", error_msg)
            self.logger.error(error_msg)

    def _emergency_stop(self):
        """Trigger emergency stop"""
        if not self.integration_system:
            QMessageBox.information(self, "Emergency Stop", "Integration system is not available.")
            return

        reply = QMessageBox.question(
            self, "Emergency Stop - Яаралтай зогсоолт",
            "Та бүх үйл ажиллагааг яаралтай зогсоохдоо итгэлтэй байна уу?\n\n"
            "Энэ нь дараах зүйлсийг зогсооно:\n"
            "• Бүх стрим\n"
            "• Плейаут систем\n"
            "• Автомат хуваарь\n"
            "• Бусад үйл ажиллагаа",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.integration_system.trigger_emergency_stop("Manual emergency stop from main window")
                self._show_status_message("🛑 EMERGENCY STOP ACTIVATED!", 10000)

                if hasattr(self, 'log_display'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.log_display.append(f"[{timestamp}] 🛑 EMERGENCY STOP TRIGGERED!")

                self.connection_status.setText("🛑 Emergency Stop")
                if hasattr(self, 'integration_status'):
                    self.integration_status.setText("🛑 Emergency Mode")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Emergency stop failed: {e}")

    def on_media_selected(self, media_item: Any):
        """Handle media file selection from Media Library tab"""
        try:
            playout_tab = self.tabs_instances.get('playout')
            if playout_tab and hasattr(playout_tab, 'load_preview_media'):
                file_path = str(media_item.file_path) if hasattr(media_item, 'file_path') else str(media_item)
                display_name = media_item.display_name if hasattr(media_item, 'display_name') else os.path.basename(file_path)

                playout_tab.load_preview_media(file_path)
                self.logger.info(f"Loaded '{display_name}' to playout preview from Media Library.")
                self._show_status_message(f"Loaded '{display_name}' to Playout Preview")

                if self.integration_system and self.event_bus:
                    event = SystemEvent(
                        event_type=EventType.MEDIA_LOADED,
                        data={"file_path": file_path, "display_name": display_name, "origin": "media_library_selection"},
                        source_tab="main_window"
                    )
                    self.event_bus.emit_event(event)

            else:
                self.logger.warning("Playout tab or load_preview_media method not found for media selection.")
                self._show_status_message("Cannot load media to preview: Playout tab not ready.")
        except Exception as e:
            self.logger.error(f"Failed to handle media selected event: {e}")
            self._show_status_message(f"Error loading media to playout: {e}")

    def on_media_library_requested(self):
        """Handle request for media library files from Playout tab"""
        try:
            self.logger.info("Media library files requested by playout tab.")
            self._show_status_message("Playout tab requested Media Library files.")

            media_library_tab_index = self.tab_widget.indexOf(self.tabs_instances.get('media_library'))
            if media_library_tab_index != -1:
                self.tab_widget.setCurrentIndex(media_library_tab_index)
                self._show_status_message("Switched to Media Library tab.")

            if self.integration_system and self.event_bus:
                event = SystemEvent(
                    event_type="media_library_requested",
                    data={"requested_by": "playout_tab"},
                    source_tab="main_window"
                )
                self.event_bus.emit_event(event)

        except Exception as e:
            self.logger.error(f"Failed to handle media library request: {e}")
            self._show_status_message(f"Error handling media library request: {e}")

    # Menu action methods
    def _import_media(self):
        """Import media files"""
        try:
            media_tab = self.tabs.get('media_library')
            if media_tab and hasattr(media_tab, 'import_media'):
                media_tab.import_media()
            else:
                self._show_status_message("Media import not available")
        except Exception as e:
            self._show_status_message(f"Import error: {e}")

    def _open_settings(self):
        """Open settings dialog"""
        QMessageBox.information(self, "Settings", "Settings dialog not implemented yet.")

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self.showNormal()
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen = False
        else:
            self.normal_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True

    def _refresh_all_tabs(self):
        """Refresh all tabs"""
        for tab_name, tab in self.tabs.items():
            try:
                if hasattr(tab, 'refresh'):
                    tab.refresh()
                    self.logger.info(f"Refreshed {tab_name} tab")
            except Exception as e:
                self.logger.error(f"Failed to refresh {tab_name} tab: {e}")

        self._show_status_message("All tabs refreshed")

    def _open_server_management(self):
        """Open server management dialog"""
        if server_config_available:
            try:
                dialog = ServerManagerDialog(self.config_manager, self)
                dialog.exec()
            except Exception as e:
                self.logger.error(f"Failed to open server management: {e}")
                self._show_status_message(f"Server management error: {e}")
        else:
            QMessageBox.warning(self, "Not Available", "Server management dialog not available.")

    def _open_audio_settings(self):
        """Open audio settings"""
        QMessageBox.information(self, "Audio Settings", "Audio settings dialog not implemented yet.")

    def _check_dependencies(self):
        deps_info = []
        try:
            import vlc
            deps_info.append("✅ VLC Python bindings - Available")
        except ImportError:
            deps_info.append("❌ VLC Python bindings - Not available")
        try:
            import ffmpeg
            deps_info.append("✅ FFmpeg Python bindings - Available")
        except ImportError:
            deps_info.append("❌ FFmpeg Python bindings - Not available")

        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                deps_info.append("✅ FFmpeg - Available")
            else:
                deps_info.append("❌ FFmpeg - Not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            deps_info.append("❌ FFmpeg - Not found")

        for tab_name, tab_class in tabs_available.items():
            status = "✅" if tab_class else "❌"
            deps_info.append(f"{status} {tab_name.replace('_', ' ').title()} Tab")

        status = "✅" if server_config_available else "❌"
        deps_info.append(f"{status} Server Configuration Dialog")

        status = "✅" if integration_system_available else "❌"
        deps_info.append(f"{status} Integration System")

        if integration_system_available and self.integration_system:
            deps_info.append(f"   📊 Event Bus: Active")
            deps_info.append(f"   📡 Shared Data: Active")
            deps_info.append(f"   🔄 Workflow Engine: Active")
            if self.system_monitor:
                deps_info.append(f"   📈 System Monitor: Active")

        dialog = QDialog(self)
        dialog.setWindowTitle("Dependencies Status")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText("\n".join(deps_info))
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def _show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>Professional TV Streaming Studio</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Build Date:</b> {datetime.now().strftime('%Y-%m-%d')}</p>
        <br>
        <p>A professional streaming and playout software with support for:</p>
        <ul>
        <li>📁 Media Library Management</li>
        <li>🎬 AMCP Playout Control</li>
        <li>📡 Multi-server Streaming</li>
        <li>⏰ Advanced Scheduling</li>
        <li>🔊 Professional Audio Processing</li>
        """

        if integration_system_available:
            about_text += """
        <li>🔄 Tab Integration System</li>
        <li>📊 Real-time Monitoring</li>
        <li>🤖 Workflow Automation</li>
        <li>🇲🇳 Mongolian Language Support</li>
            """

        about_text += """
        </ul>
        <br>
        <p><small>Built with PyQt6 and modern streaming technologies</small></p>
        """

        QMessageBox.about(self, "About", about_text)

    def _open_documentation(self):
        """Open documentation"""
        self._show_status_message("Documentation not implemented yet")

    def _save_logs(self):
        """Save logs to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Logs",
                f"streaming_studio_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())

                self._show_status_message(f"Logs saved to: {file_path}")

        except Exception as e:
            self._show_status_message(f"Failed to save logs: {e}")

    def closeEvent(self, event):
        """Handle application close"""
        self.logger.info("Application closing...")

        if self.integration_system:
            try:
                if self.system_monitor:
                    self.system_monitor.stop_monitoring()
                self.logger.info("Integration system cleaned up")
            except Exception as e:
                self.logger.error(f"Integration cleanup failed: {e}")

        for tab_name, tab in self.tabs.items():
            try:
                if hasattr(tab, 'cleanup'):
                    tab.cleanup()
                    self.logger.info(f"Cleaned up {tab_name} tab")
            except Exception as e:
                self.logger.error(f"Failed to cleanup {tab_name} tab: {e}")

        try:
            if hasattr(self.config_manager, 'save_config'):
                self.config_manager.save_config()
                self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

        event.accept()

# =============================================================================
# EXPORT FOR INTEGRATION
# =============================================================================

__all__ = [
    'ProfessionalStreamingStudio',
    'PlaceholderTab',
    'ITabIntegration'
]

# =============================================================================
# TESTING AND STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    """Test the main window standalone"""
    import sys

    class TestConfigManager:
        """Simple config manager for testing"""
        def __init__(self):
            pass

        def get_media_library_path(self):
            return Path("data/media")

        def save_config(self):
            pass

        def get_integration_settings(self):
            return {
                'enabled': True,
                'monitoring_enabled': True,
                'automation_enabled': True
            }

    app = QApplication(sys.argv)
    config = TestConfigManager()
    window = ProfessionalStreamingStudio(config, app)
    window.show()
    sys.exit(app.exec())