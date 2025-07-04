#!/usr/bin/env python3
"""
Complete Main.py Fix Script
main.py файлын бүх алдааг засварлах
"""

import os
import shutil
from pathlib import Path


def fix_test_imports_function():
    """Fix the corrupted test_imports function"""
    
    # Fixed test_imports function
    fixed_test_imports = '''def test_imports():
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

    print("\\n--- Component Import Test Results ---")
    all_passed = True
    for name, result in test_results.items():
        status = "PASSED" if result == "SUCCESS" else f"FAILED ({result})"
        print(f"{name:<30} {status}")
        if result != "SUCCESS":
            all_passed = False
    print("-------------------------------------\\n")

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
            sys.exit(1)'''
    
    return fixed_test_imports


def fix_setup_main_window_function():
    """Fix the corrupted setup_main_window_with_integration function"""
    
    # Fixed setup_main_window_with_integration function
    fixed_setup_function = '''def setup_main_window_with_integration(config_manager, app):
    """Setup main window with optional integration system"""
    
    # Import main window class
    try:
        from ui.main_window import ProfessionalStreamingStudio
    except ImportError as e:
        logger.error(f"Failed to import main window: {e}")
        raise
    
    # Try to import streaming integration
    try:
        from streaming.integration import create_streaming_tab
        STREAMING_INTEGRATION_AVAILABLE = True
        logger.info("Streaming integration available")
    except ImportError:
        STREAMING_INTEGRATION_AVAILABLE = False
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
    
    return main_win'''
    
    return fixed_setup_function


def fix_main_py_complete():
    """Complete fix for main.py file"""
    
    project_root = Path.cwd()
    main_py = project_root / "main.py"
    
    print("🔧 Completely fixing main.py file...")
    
    # 1. First backup the current file
    backup_file = main_py.with_suffix('.py.corrupted')
    try:
        shutil.copy2(main_py, backup_file)
        print(f"📦 Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠️ Could not create backup: {e}")
    
    # 2. Read the current content
    try:
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read main.py: {e}")
        return False
    
    # 3. Find and replace the corrupted test_imports function
    print("🔧 Fixing test_imports function...")
    
    # Find the start of test_imports function
    test_imports_start = content.find('def test_imports():')
    if test_imports_start == -1:
        print("❌ Could not find test_imports function")
        return False
    
    # Find the end of test_imports function (next function definition)
    next_function_start = content.find('\ndef ', test_imports_start + 1)
    if next_function_start == -1:
        # If no next function, find end of file or class
        next_function_start = len(content)
    
    # Replace the entire test_imports function
    before_test_imports = content[:test_imports_start]
    after_test_imports = content[next_function_start:]
    
    fixed_test_imports = fix_test_imports_function()
    
    content = before_test_imports + fixed_test_imports + "\n\n" + after_test_imports
    print("✅ Fixed test_imports function")
    
    # 4. Find and replace the corrupted setup_main_window_with_integration function
    print("🔧 Fixing setup_main_window_with_integration function...")
    
    # Find the start of setup function
    setup_function_start = content.find('def setup_main_window_with_integration(config_manager, app):')
    if setup_function_start == -1:
        print("❌ Could not find setup_main_window_with_integration function")
        return False
    
    # Find the end of setup function (next function definition)
    next_function_start = content.find('\ndef ', setup_function_start + 1)
    if next_function_start == -1:
        # Find other possible ending points
        next_function_start = content.find('\nclass ', setup_function_start + 1)
        if next_function_start == -1:
            next_function_start = len(content)
    
    # Replace the entire setup function
    before_setup = content[:setup_function_start]
    after_setup = content[next_function_start:]
    
    fixed_setup_function = fix_setup_main_window_function()
    
    content = before_setup + fixed_setup_function + "\n\n" + after_setup
    print("✅ Fixed setup_main_window_with_integration function")
    
    # 5. Clean up any remaining corruption patterns
    print("🧹 Cleaning remaining corruption...")
    
    corruption_patterns = [
        'print("⚠️ Using legacy streaming tab")\n        print("⚠️ Using legacy streaming tab")',
        'print("✅ Using refactored streaming tab")\nexcept ImportError:\n    # Streaming Tab with automatic fallback\ntry:',
        'except ImportError:\n    # Streaming Tab with automatic fallback\ntry:',
        'print("⚠️ Using legacy streaming tab")\n            print("⚠️ Using legacy streaming tab")',
        '            print("⚠️ Using legacy streaming tab")\n            print("⚠️ Using legacy streaming tab")',
        '    print("⚠️ Using legacy streaming tab")\n    print("⚠️ Using legacy streaming tab")'
    ]
    
    for pattern in corruption_patterns:
        if pattern in content:
            content = content.replace(pattern, '')
            print(f"✅ Removed corruption pattern")
    
    # 6. Write the fixed content
    try:
        with open(main_py, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Written fixed content to main.py")
    except Exception as e:
        print(f"❌ Could not write fixed content: {e}")
        return False
    
    return True


def test_main_py_syntax():
    """Test if main.py has valid syntax"""
    
    print("🧪 Testing main.py syntax...")
    
    try:
        import ast
        
        main_py = Path.cwd() / "main.py"
        
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        print("✅ main.py syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in main.py: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error testing main.py: {e}")
        return False


def main():
    """Main function"""
    
    print("🔧 Complete Main.py Fix Tool")
    print("=" * 45)
    
    # Step 1: Complete fix
    if not fix_main_py_complete():
        print("❌ Failed to fix main.py completely")
        return False
    
    # Step 2: Test syntax
    if not test_main_py_syntax():
        print("❌ main.py still has syntax errors")
        return False
    
    print("\n🎉 main.py completely fixed!")
    print("\n✅ Functions fixed:")
    print("   • test_imports()")
    print("   • setup_main_window_with_integration()")
    print("   • All corruption patterns removed")
    
    print("\n✅ You can now run:")
    print("   python main.py")
    print("   python main.py test")
    print("   python main.py structure")
    
    return True


if __name__ == "__main__":
    main()
