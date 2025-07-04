"""
Professional TV Streaming Studio - Main Application Entry Point
A modular streaming and playout software inspired by CasparCG, OpenBroadcaster, and AzuraCast
Enhanced with comprehensive fallback systems for missing dependencies
Enhanced with Tab Integration System for complete workflow automation
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime
import configparser
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont

# Import audio system
from audio.tv_audio_engine import TVAudioSystem

# Add project root to Python path dynamically
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import centralized logging and constants from core
try:
    from core.logging import setup_logging, get_logger, log_manager
    from core.constants import (
        APP_NAME, APP_VERSION, APP_ORGANIZATION, APP_DESCRIPTION,
        DEFAULT_DIRECTORIES, APP_ICON_PATH, SPLASH_SCREEN_PATH, MESSAGES
    )
    from core.config_manager import ConfigManager
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import core modules. Please check your installation. {e}", file=sys.stderr)
    # Define minimal fallbacks to allow basic error reporting
    APP_NAME = "Professional Streaming Studio (Fallback)"
    APP_VERSION = "1.0.0"
    APP_ORGANIZATION = "TV Studio Corp"
    APP_DESCRIPTION = "Professional TV streaming and playout software with AMCP support"
    DEFAULT_DIRECTORIES = {"data": "data", "media": "data/media", "logs": "data/logs"}

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(), logging.FileHandler('streaming_studio_fallback.log')]
    )
    def get_logger(name): return logging.getLogger(name)
    class ConfigManager:
        def __init__(self, config_file="config.ini"):
            self.config_file = Path(config_file)
            self.servers = {}
            self.audio_system = None
        def get(self, section, key, default): return default
        def getint(self, section, key, default): return default
        def getboolean(self, section, key, default): return default
        def set_window_position(self, x, y): pass
        def set_window_size(self, w, h): pass
        def save_config(self): pass
        def get_theme(self): return "Dark"
        def get_window_position(self): return -1, -1
        def get_window_size(self): return 1280, 720
        def get_log_level(self): return "INFO"
        def get_all_servers(self): return {}
        def reset_to_defaults(self): return True
        def get_media_library_path(self): return Path("data/media")
        def set_media_library_path(self, path): pass
        def get_setting(self, key, default): return default
        def set_setting(self, key, value): pass
        def set_audio_system(self, audio_system): self.audio_system = audio_system
        def get_amcp_settings(self): return {
            'host': 'localhost',
            'port': 5250,
            'timeout': 5,
            'auto_connect': False
        }
    log_manager = None
    MESSAGES = {}

logger = get_logger(__name__)

# 🎯 TAB INTEGRATION SYSTEM IMPORT
try:
    from integration_usage_example import integrate_with_existing_main_window
    INTEGRATION_AVAILABLE = True
    print("✅ Tab Integration System available")
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    print(f"⚠️ Integration system import failed: {e}")

# 🎯 STREAMING INTEGRATION IMPORT - GLOBAL VARIABLE
try:
    from streaming.integration import create_streaming_tab
    STREAMING_INTEGRATION_AVAILABLE = True
    print("✅ Streaming integration available")
except ImportError:
    STREAMING_INTEGRATION_AVAILABLE = False
    print("⚠️ Streaming integration not available, using standard StreamingTab")

# =============================================================================
# FILE SYSTEM & INITIALIZATION UTILITIES
# =============================================================================

def _create_minimal_directories():
    """Create default application directories if they don't exist."""
    for key, path_str in DEFAULT_DIRECTORIES.items():
        path = Path(path_str)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created default directory: {path}")

def _create_init_files_in_subdirs(base_path: Path):
    """Recursively create __init__.py in all subdirectories."""
    for entry in base_path.iterdir():
        if entry.is_dir():
            init_file = entry / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                logger.debug(f"Created __init__.py in {entry}")
            _create_init_files_in_subdirs(entry)

def create_minimal_files():
    """
    Creates essential files and directories for a minimal application startup.
    This includes core modules and basic UI placeholders.
    """
    logger.info("Creating minimal required files and directories...")
    _create_minimal_directories()
    _create_init_files_in_subdirs(project_root)

    # Core files
    (project_root / "core").mkdir(exist_ok=True)
    (project_root / "core" / "__init__.py").touch()
    (project_root / "core" / "amcp_protocol.py").touch()
    (project_root / "core" / "stream_server.py").touch()
    (project_root / "core" / "media_library.py").touch()
    (project_root / "core" / "ffmpeg_processor.py").touch()
    
    # Integration system files
    if not (project_root / "tab_integration_system.py").exists():
        logger.warning("tab_integration_system.py not found. Integration will be disabled.")
    if not (project_root / "integration_usage_example.py").exists():
        logger.warning("integration_usage_example.py not found. Integration will be disabled.")

    # Audio files
    (project_root / "audio").mkdir(exist_ok=True)
    (project_root / "audio" / "__init__.py").touch()
    (project_root / "audio" / "jack_backend.py").touch()
    (project_root / "audio" / "lv2_plugins.py").touch()
    (project_root / "audio" / "carla_host.py").touch()
    (project_root / "audio" / "tv_audio_engine.py").touch()
    (project_root / "audio" / "audio_profiles.py").touch()
    (project_root / "audio" / "realtime_processor.py").touch()

    # UI files
    (project_root / "ui").mkdir(exist_ok=True)
    (project_root / "ui" / "__init__.py").touch()
    (project_root / "ui" / "tabs").mkdir(exist_ok=True)
    (project_root / "ui" / "tabs" / "__init__.py").touch()
    (project_root / "ui" / "tabs" / "playout_tab.py").touch()
    (project_root / "ui" / "tabs" / "media_library_tab.py").touch()
    (project_root / "ui" / "tabs" / "streaming_tab.py").touch()
    (project_root / "ui" / "tabs" / "scheduler_tab.py").touch()
    (project_root / "ui" / "tabs" / "logs_tab.py").touch()

    (project_root / "ui" / "dialogs").mkdir(exist_ok=True)
    (project_root / "ui" / "dialogs" / "__init__.py").touch()
    (project_root / "ui" / "dialogs" / "server_config.py").touch()

    # Model files
    (project_root / "models").mkdir(exist_ok=True)
    (project_root / "models" / "__init__.py").touch()
    (project_root / "models" / "server_config.py").touch()
    (project_root / "models" / "stream_quality.py").touch()

    if not (project_root / "ui" / "main_window.py").exists():
        logger.warning("ui/main_window.py not found. This will be an issue. Copying a minimal placeholder.")

    logger.info("Minimal file creation complete.")

def test_imports():
    """Tests if all major components can be imported successfully."""
    logger.info("Running component import tests...")
    test_results = {}
    components_to_test = {
        "core.config_manager": "from core.config_manager import ConfigManager",
        "core.constants": "from core.constants import APP_NAME",
        "core.logging": "from core.logging import get_logger",
        "core.amcp_protocol": "from core.amcp_protocol import AMCPProtocol",
        "core.stream_server": "from core.stream_server import StreamServer",
        "core.media_library": "from core.media_library import MediaLibrary",
        "core.ffmpeg_processor": "from core.ffmpeg_processor import FFmpegProcessor",
        "models.server_config": "from models.server_config import ServerConfig",
        "models.stream_quality": "from models.stream_quality import StreamQuality",
        "ui.main_window": "from ui.main_window import ProfessionalStreamingStudio",
        "ui.tabs.playout_tab": "from ui.tabs.playout_tab import PlayoutTab",
        "ui.tabs.media_library_tab": "from ui.tabs.media_library_tab import MediaLibraryTab",
        "ui.tabs.streaming_tab": "from streaming.integration import create_streaming_tab as StreamingTab",
        "ui.tabs.scheduler_tab": "from ui.tabs.scheduler_tab import SchedulerTab",
        "ui.tabs.logs_tab": "from ui.tabs.logs_tab import LogsTab",
        "ui.dialogs.server_config": "from ui.dialogs.server_config import ServerManagerDialog",
        "audio.jack_backend": "from audio.jack_backend import JackBackend",
        "audio.lv2_plugins": "from audio.lv2_plugins import LV2PluginManager",
        "audio.carla_host": "from audio.carla_host import CarlaHost",
        "audio.tv_audio_engine": "from audio.tv_audio_engine import TVAudioSystem",
        "audio.audio_profiles": "from audio.audio_profiles import AudioProfileManager",
        "audio.realtime_processor": "from audio.realtime_processor import RealtimeAudioProcessor",
    }
    
    # Add integration system test if available
    if INTEGRATION_AVAILABLE:
        components_to_test["integration_system"] = "from tab_integration_system import setup_integration_system"
        components_to_test["integration_usage"] = "from integration_usage_example import integrate_with_existing_main_window"

    for name, import_statement in components_to_test.items():
        try:
            exec(import_statement)
            test_results[name] = "SUCCESS"
        except ImportError as e:
            test_results[name] = f"FAILED: {e}"
            logger.error(f"Import test for {name} failed: {e}")
        except Exception as e:
            test_results[name] = f"ERROR: {e}"
            logger.error(f"Error during import test for {name}: {e}")

    print("\n--- Component Import Test Results ---")
    all_passed = True
    for name, result in test_results.items():
        status = "PASSED" if result == "SUCCESS" else f"FAILED ({result})"
        print(f"{name:<30} {status}")
        if result != "SUCCESS":
            all_passed = False
    print("-------------------------------------\n")

    if all_passed:
        logger.info("All essential components imported successfully.")
        print("All essential components imported successfully.")
    else:
        logger.error("Some components failed to import. Check logs for details.")
        print("Some components failed to import. Check logs for details.")
        
        # Don't exit if only integration system failed
        critical_failures = [name for name, result in test_results.items() 
                            if result != "SUCCESS" and not name.startswith("integration")]
        if critical_failures:
            sys.exit(1)


def show_structure(path=project_root, indent=0):
    """Recursively prints the directory structure."""
    if indent == 0:
        print(f"\n--- Current Project Structure ({path.name}/) ---")
    for item in sorted(path.iterdir()):
        if item.name in ["__pycache__", ".git", ".idea", ".vscode", "*.pyc"]:
            continue
        print('    ' * indent + ('📁 ' if item.is_dir() else '📄 ') + item.name)
        if item.is_dir():
            show_structure(item, indent + 1)
    if indent == 0:
        print("-------------------------------------\n")

# =============================================================================
# CONFIG MANAGER (Enhanced for Integration)
# =============================================================================

class ConfigManager:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.servers: Dict[str, 'ServerConfig'] = {}
        self.audio_system: Optional[TVAudioSystem] = None
        self.load_config()

    def set_audio_system(self, audio_system: TVAudioSystem):
        """Set the reference to the main audio system."""
        self.audio_system = audio_system

    def _create_default_config(self):
        """Create default configuration settings."""
        self.config['DEFAULT'] = {
            'log_level': 'INFO',
            'media_library_path': 'data/media',
            'plugin_directory': 'plugins',
            'backup_directory': 'data/backups',
            'auto_scan_on_startup': 'True',
            'theme': 'Dark',
            'default_video_quality': '720p',
            'default_encoder': 'libx264',
            'default_audio_bitrate': '128k',
            'audio_night_mode': 'False',
            'audio_voice_clarity': 'False',
            'audio_bass_boost_db': '0',
            'audio_current_profile': 'default'
        }
        
        # Integration system settings
        self.config['integration'] = {
            'enabled': 'True',
            'monitoring_enabled': 'True',
            'automation_enabled': 'True',
            'auto_stream_on_take': 'False',
            'auto_recover_streams': 'True',
            'emergency_auto_recovery': 'True',
            'use_localized_messages': 'True',
            'monitoring_interval': '5000'
        }
        
        self.config['amcp'] = {
            'host': 'localhost',
            'port': '5250',
            'timeout': '5',
            'auto_connect': 'False'
        }
        self.save_config()

    def load_config(self):
        """Load configuration from file or create default."""
        if not self.config_file.exists():
            logger.info(f"Configuration file {self.config_file} not found. Creating default.")
            self._create_default_config()
        try:
            self.config.read(self.config_file)
            logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_config()

    def get(self, section: str, key: str, default: str) -> str:
        """Get a configuration value as a string."""
        try:
            return self.config.get(section, key, fallback=default)
        except Exception as e:
            logger.warning(f"Error getting {section}.{key}: {e}. Using default: {default}")
            return default

    def getint(self, section: str, key: str, default: int) -> int:
        """Get a configuration value as an integer."""
        try:
            return self.config.getint(section, key, fallback=default)
        except Exception as e:
            logger.warning(f"Error getting {section}.{key} as int: {e}. Using default: {default}")
            return default

    def getboolean(self, section: str, key: str, default: bool) -> bool:
        """Get a configuration value as a boolean."""
        try:
            return self.config.getboolean(section, key, fallback=default)
        except Exception as e:
            logger.warning(f"Error getting {section}.{key} as boolean: {e}. Using default: {default}")
            return default

    def get_setting(self, key: str, default: any) -> any:
        """Get a setting from the DEFAULT section."""
        return self.get('DEFAULT', key, default)

    def set_setting(self, key: str, value: any):
        """Set a setting in the DEFAULT section."""
        if 'DEFAULT' not in self.config:
            self.config['DEFAULT'] = {}
        self.config['DEFAULT'][key] = str(value)

    def set_window_position(self, x: int, y: int):
        """Set window position in config."""
        self.set_setting('window_x', x)
        self.set_setting('window_y', y)

    def set_window_size(self, width: int, height: int):
        """Set window size in config."""
        self.set_setting('window_width', width)
        self.set_setting('window_height', height)

    def get_window_position(self) -> tuple:
        """Get window position from config."""
        return (
            self.getint('DEFAULT', 'window_x', -1),
            self.getint('DEFAULT', 'window_y', -1)
        )

    def get_window_size(self) -> tuple:
        """Get window size from config."""
        return (
            self.getint('DEFAULT', 'window_width', 1280),
            self.getint('DEFAULT', 'window_height', 720)
        )

    def get_log_level(self) -> str:
        """Get logging level from config."""
        return self.get('DEFAULT', 'log_level', 'INFO')

    def get_media_library_path(self) -> Path:
        """Get media library path from config."""
        return Path(self.get('DEFAULT', 'media_library_path', 'data/media'))

    def set_media_library_path(self, path: str):
        """Set media library path in config."""
        self.set_setting('media_library_path', path)

    def get_theme(self) -> str:
        """Get UI theme from config."""
        return self.get('DEFAULT', 'theme', 'Dark')

    def get_all_servers(self) -> Dict[str, 'ServerConfig']:
        """Get all server configurations."""
        return self.servers

    def get_amcp_settings(self) -> dict:
        """Get AMCP connection settings."""
        return {
            'host': self.get('amcp', 'host', 'localhost'),
            'port': self.getint('amcp', 'port', 5250),
            'timeout': self.getint('amcp', 'timeout', 5),
            'auto_connect': self.getboolean('amcp', 'auto_connect', False)
        }
    
    # Integration-specific settings
    def get_integration_settings(self) -> dict:
        """Get integration system settings."""
        return {
            'enabled': self.getboolean('integration', 'enabled', True),
            'monitoring_enabled': self.getboolean('integration', 'monitoring_enabled', True),
            'automation_enabled': self.getboolean('integration', 'automation_enabled', True),
            'auto_stream_on_take': self.getboolean('integration', 'auto_stream_on_take', False),
            'auto_recover_streams': self.getboolean('integration', 'auto_recover_streams', True),
            'emergency_auto_recovery': self.getboolean('integration', 'emergency_auto_recovery', True),
            'use_localized_messages': self.getboolean('integration', 'use_localized_messages', True),
            'monitoring_interval': self.getint('integration', 'monitoring_interval', 5000)
        }

    def reset_to_defaults(self) -> bool:
        """Reset configuration to default settings."""
        try:
            self._create_default_config()
            if self.audio_system:
                self.audio_system.load_profile(self.get_setting('audio_current_profile', 'default'))
                self.audio_system.enable_night_mode(self.getboolean('DEFAULT', 'audio_night_mode', False))
                self.audio_system.enhance_dialogue(self.getboolean('DEFAULT', 'audio_voice_clarity', False))
                self.audio_system.set_bass_boost(float(self.get_setting('audio_bass_boost_db', 0)))
            logger.info("Configuration reset to defaults.")
            return True
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

# =============================================================================
# MAIN APPLICATION LOGIC (Enhanced with Integration)
# =============================================================================

def setup_main_window_with_integration(config_manager, app):
    """Setup main window with optional integration system"""
    
    # Import main window class
    try:
        from ui.main_window import ProfessionalStreamingStudio
    except ImportError as e:
        logger.error(f"Failed to import main window: {e}")
        raise
    
    # Ensure streaming tab fallback import
    if not STREAMING_INTEGRATION_AVAILABLE:
        logger.warning("Streaming integration not available, using standard StreamingTab")
        
        # Try legacy streaming tab
        try:
            from ui.tabs.streaming_tab import StreamingTab
        except ImportError:
            # Create a mock streaming tab as last resort
            from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
            
            class StreamingTab(QWidget):
                def __init__(self, config_manager, parent=None):
                    super().__init__(parent)
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel("Streaming Tab (Placeholder)"))
                    layout.addWidget(QLabel("Streaming integration not available"))

    # Try to setup with integration
    if INTEGRATION_AVAILABLE and config_manager.getboolean('integration', 'enabled', True):
        try:
            logger.info("Setting up main window with Tab Integration System...")
            
            # Create enhanced main window class
            EnhancedStudio = integrate_with_existing_main_window(ProfessionalStreamingStudio)
            main_win = EnhancedStudio(config_manager, app)
            
            # Set up streaming tab based on integration availability
            if STREAMING_INTEGRATION_AVAILABLE:
                main_win.streaming_tab = create_streaming_tab(config_manager, main_win)
            else:
                main_win.streaming_tab = StreamingTab(config_manager, main_win)
            
            logger.info("🎉 Tab Integration System activated successfully!")
            print("🎉 Integration system идэвхжлээ!")
            print(f"📊 Автомат tab харилцаа холбоо идэвхтэй")
            print(f"🔄 Workflow automation бэлэн")
            print(f"📈 Real-time monitoring идэвхтэй")
            
            return main_win
            
        except Exception as e:
            logger.error(f"Integration system setup failed: {e}")
            print(f"⚠️ Integration setup failed: {e}")
            print("📄 Fallback-аар анхны main window ашиглана")
    
    # Fallback to original main window
    logger.info("Setting up main window without integration system")
    main_win = ProfessionalStreamingStudio(config_manager, app)
    
    # Set up streaming tab based on integration availability
    if STREAMING_INTEGRATION_AVAILABLE:
        main_win.streaming_tab = create_streaming_tab(config_manager, main_win)
    else:
        main_win.streaming_tab = StreamingTab(config_manager, main_win)
    
    if not INTEGRATION_AVAILABLE:
        print("📄 Tab Integration System боломжгүй - анхны режимээр ажиллана")
    
    return main_win


def main():
    """Main entry point for the application."""
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_imports()
            sys.exit(0)
        elif sys.argv[1] == "structure":
            show_structure()
            sys.exit(0)
        elif sys.argv[1] == "create-minimal":
            create_minimal_files()
            sys.exit(0)
        elif sys.argv[1] == "help":
            print(f"""
{APP_NAME} - Command Line Options

Usage: python main.py [option]

Options:
  (no args)        - Start the application
  test            - Test component imports and dependencies
  structure       - Show current file structure
  create-minimal  - Create minimal required files (directories and empty .py files)
  help            - Show this help message

Examples:
  python main.py              # Start the application
  python main.py test         # Test all components
  python main.py structure    # Show file structure

🎯 Tab Integration System Features:
  - Automatic tab communication
  - Real-time system monitoring  
  - Cross-tab workflow automation
  - Emergency stop coordination
  - Mongolian language support
            """)
            sys.exit(0)

    # Create essential directories and files
    _create_minimal_directories()
    _create_init_files_in_subdirs(project_root)

    # Check for essential UI files
    essential_ui_files = [
        project_root / "ui" / "main_window.py",
        project_root / "ui" / "tabs" / "playout_tab.py",
        project_root / "ui" / "tabs" / "media_library_tab.py",
        project_root / "ui" / "tabs" / "streaming_tab.py",
        project_root / "ui" / "tabs" / "scheduler_tab.py",
        project_root / "ui" / "tabs" / "logs_tab.py",
        project_root / "ui" / "dialogs" / "server_config.py",
        project_root / "models" / "server_config.py",
        project_root / "models" / "stream_quality.py",
    ]

    missing_files = [f.relative_to(project_root) for f in essential_ui_files if not f.exists()]

    if missing_files:
        print("Error: Essential application files are missing:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nMake sure your project structure is complete or run 'python main.py create-minimal' to create placeholders.")
        sys.exit(1)

    # Initialize configuration
    config_manager = ConfigManager()
    config_manager.load_config()

    # Setup logging
    if not setup_logging(level=config_manager.get_log_level()):
        print("Failed to setup logging, exiting.", file=sys.stderr)
        sys.exit(1)

    # Log startup
    logger.info(MESSAGES.get("app_started", "Application started").format(version=APP_VERSION))
    logger.info(f"Using configuration file: {config_manager.config_file.resolve()}")
    
    if INTEGRATION_AVAILABLE:
        logger.info("Tab Integration System is available")
    else:
        logger.warning("Tab Integration System is not available")

    try:
        # Initialize Qt Application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName(APP_ORGANIZATION)

        # Initialize audio system
        try:
            audio_system = TVAudioSystem()
            config_manager.set_audio_system(audio_system)
            audio_system.load_profile(config_manager.get_setting('audio_current_profile', 'default'))
            audio_system.enable_night_mode(config_manager.getboolean('DEFAULT', 'audio_night_mode', False))
            audio_system.enhance_dialogue(config_manager.getboolean('DEFAULT', 'audio_voice_clarity', False))
            audio_system.set_bass_boost(float(config_manager.get_setting('audio_bass_boost_db', 0)))
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            audio_system = None

        # Show splash screen
        try:
            splash_pix = QPixmap(str(SPLASH_SCREEN_PATH))
            if splash_pix.isNull():
                # Create a simple splash screen if image not found
                splash_pix = QPixmap(400, 300)
                splash_pix.fill(Qt.GlobalColor.darkBlue)
                painter = QPainter(splash_pix)
                painter.setPen(Qt.GlobalColor.white)
                painter.setFont(QFont("Arial", 16))
                painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, f"{APP_NAME}\nv{APP_VERSION}")
                painter.end()
                
            splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
            splash.setMask(splash_pix.mask())
            
            splash_message = f"Loading {APP_NAME}..."
            if INTEGRATION_AVAILABLE:
                splash_message += "\n🔄 Tab Integration System Loading..."
            
            splash.showMessage(splash_message, 
                             Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, 
                             Qt.GlobalColor.white)
            splash.show()
            app.processEvents()
        except Exception as e:
            logger.warning(f"Failed to show splash screen: {e}")
            splash = None

        # 🎯 SETUP MAIN WINDOW WITH INTEGRATION
        try:
            main_win = setup_main_window_with_integration(config_manager, app)
        except Exception as e:
            logger.critical(f"Failed to setup main window: {e}")
            if splash:
                splash.close()
            QMessageBox.critical(None, "Critical Error", 
                               f"Failed to initialize main window: {e}\n\n"
                               "Please check your installation and try again.")
            sys.exit(1)

        # Close splash screen
        if splash:
            QTimer.singleShot(2000, splash.close)
            app.processEvents()

        # Show main window
        main_win.show()
        
        # Restore window position and size if available
        try:
            x, y = config_manager.get_window_position()
            width, height = config_manager.get_window_size()
            
            if x >= 0 and y >= 0:
                main_win.move(x, y)
            
            if width > 0 and height > 0:
                main_win.resize(width, height)
                
        except Exception as e:
            logger.warning(f"Failed to restore window geometry: {e}")

        # Show integration status in console
        if hasattr(main_win, 'integration_system'):
            print("\n" + "="*60)
            print("🎉 PROFESSIONAL TV STREAMING STUDIO")
            print(f"📺 Version {APP_VERSION} with Tab Integration System")
            print("="*60)
            print("✅ Integration Features Active:")
            print("   🔄 Cross-tab workflow automation")
            print("   📊 Real-time system monitoring")
            print("   📡 Event-driven tab communication")
            print("   🛑 Emergency stop coordination")
            print("   🇲🇳 Mongolian language support")
            print(f"   {'✅' if STREAMING_INTEGRATION_AVAILABLE else '❌'} Streaming Integration")
            print("="*60)
            print("🎯 Available Workflows:")
            
            try:
                workflows = list(main_win.integration_system.workflow_engine.workflows.keys())
                for workflow in workflows:
                    print(f"   • {workflow}")
            except:
                print("   • media_to_air")
                print("   • live_streaming_setup")
                print("   • scheduled_broadcast")
                print("   • emergency_procedures")
            
            print("="*60)
            print("📖 Quick Commands:")
            print("   Tools > System Status - View system health")
            print("   Tools > Execute Workflow - Run automation")
            print("   Ctrl+Alt+E - Emergency stop")
            print("="*60 + "\n")
        else:
            print("\n" + "="*60)
            print("🎉 PROFESSIONAL TV STREAMING STUDIO")
            print(f"📺 Version {APP_VERSION} - Standard Mode")
            print("="*60)
            print("📄 Running in standard mode without integration")
            print(f"   {'✅' if STREAMING_INTEGRATION_AVAILABLE else '❌'} Streaming Integration")
            print("   All basic features are available")
            print("="*60 + "\n")

        # Save window state on close
        def save_window_state():
            try:
                pos = main_win.pos()
                size = main_win.size()
                config_manager.set_window_position(pos.x(), pos.y())
                config_manager.set_window_size(size.width(), size.height())
                config_manager.save_config()
            except Exception as e:
                logger.error(f"Failed to save window state: {e}")

        # Connect cleanup handlers
        app.aboutToQuit.connect(save_window_state)
        
        if hasattr(main_win, 'integration_system'):
            def cleanup_integration():
                try:
                    if hasattr(main_win, 'system_monitor') and main_win.system_monitor:
                        main_win.system_monitor.stop_monitoring()
                    logger.info("Integration system cleanup completed")
                except Exception as e:
                    logger.error(f"Integration cleanup failed: {e}")
            
            app.aboutToQuit.connect(cleanup_integration)

        # Start the application event loop
        logger.info("Starting application event loop...")
        exit_code = app.exec()
        
        # Application shutdown
        logger.info(MESSAGES.get("app_shutdown", "Application shutting down."))
        
        # Final cleanup
        try:
            if audio_system:
                # Cleanup audio system if needed
                pass
        except Exception as e:
            logger.error(f"Audio system cleanup failed: {e}")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Unhandled application error: {e}", exc_info=True)
        
        # Try to show error dialog
        try:
            QMessageBox.critical(None, "Application Error",
                               f"An unhandled error occurred: {e}\n\n"
                               "Please check the application logs for more details.\n\n"
                               f"Log file: {project_root / 'data' / 'logs' / 'streaming_studio.log'}")
        except:
            print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        
        sys.exit(1)

# =============================================================================
# INTEGRATION SYSTEM STATUS CHECK
# =============================================================================

def check_integration_system():
    """Check integration system availability and components"""
    print("\n🔍 Tab Integration System Status Check:")
    print("="*50)
    
    # Check main integration files
    integration_files = {
        "tab_integration_system.py": "Main integration system",
        "integration_usage_example.py": "Usage example and enhancement",
        "streaming/integration.py": "Streaming integration module"
    }
    
    for filename, description in integration_files.items():
        file_path = project_root / filename
        if file_path.exists():
            print(f"✅ {filename:<30} - {description}")
        else:
            print(f"❌ {filename:<30} - {description} (MISSING)")
    
    # Check import capability
    print("\n📦 Import Tests:")
    try:
        from tab_integration_system import (
            EventType, SystemEvent, EventBus, 
            SharedDataManager, TabIntegrationManager,
            WorkflowEngine, StreamingStudioIntegration,
            setup_integration_system, IntegrationConfig
        )
        print("✅ Core integration components imported successfully")
    except ImportError as e:
        print(f"❌ Core integration import failed: {e}")
    
    try:
        from integration_usage_example import integrate_with_existing_main_window
        print("✅ Integration usage example imported successfully")
    except ImportError as e:
        print(f"❌ Integration usage import failed: {e}")
    
    try:
        from streaming.integration import create_streaming_tab
        print("✅ Streaming integration imported successfully")
    except ImportError as e:
        print(f"❌ Streaming integration import failed: {e}")
    
    print("="*50)
    
    if INTEGRATION_AVAILABLE:
        print("🎉 Integration System: READY")
        print("   Tab communication and workflows will be available")
    else:
        print("⚠️  Integration System: NOT AVAILABLE")
        print("   Application will run in standard mode")
    
    print("="*50 + "\n")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Special command to check integration status
    if len(sys.argv) > 1 and sys.argv[1] == "check-integration":
        check_integration_system()
        sys.exit(0)
    
    # Show integration status at startup
    if "--verbose" in sys.argv or "--debug" in sys.argv:
        check_integration_system()
    
    # Run main application
    main()