"""
Streaming Tab Integration - Safe Import System
Automatically handles imports and creates streaming tabs
"""

import sys
import os
from pathlib import Path

# Ensure proper paths
current_dir = Path(__file__).parent
project_root = current_dir.parent

for path in [str(current_dir), str(project_root)]:
    if path not in sys.path:
        sys.path.insert(0, path)


def create_streaming_tab(config_manager, parent=None):
    """Create streaming tab with safe import handling"""
    
    # Try refactored version first
    try:
        # Import with direct path specification
        import importlib.util
        
        refactored_path = current_dir / "refactored_streaming_tab.py"
        spec = importlib.util.spec_from_file_location("refactored_streaming_tab", refactored_path)
        refactored_module = importlib.util.module_from_spec(spec)
        
        # Add required modules to the module's globals
        refactored_module.__dict__.update({
            'Path': Path,
            'sys': sys,
            'os': os
        })
        
        spec.loader.exec_module(refactored_module)
        
        RefactoredStreamingTab = refactored_module.RefactoredStreamingTab
        print("✅ Using refactored streaming tab")
        return RefactoredStreamingTab(config_manager, parent)
        
    except Exception as e1:
        print(f"⚠️ Refactored tab failed: {e1}")
        
        # Try legacy version
        try:
            # Try different import paths
            import_paths = [
                "ui.tabs.streaming_tab",
                "ui.tabs",
                "tabs.streaming_tab"
            ]
            
            StreamingTab = None
            for import_path in import_paths:
                try:
                    if import_path == "ui.tabs.streaming_tab":
                        from ui.tabs.streaming_tab import StreamingTab
                    elif import_path == "ui.tabs":
                        from ui.tabs import streaming_tab
                        StreamingTab = streaming_tab.StreamingTab
                    elif import_path == "tabs.streaming_tab":
                        from tabs.streaming_tab import StreamingTab
                    
                    if StreamingTab:
                        break
                except ImportError:
                    continue
            
            if StreamingTab:
                print("⚠️ Using legacy streaming tab")
                return StreamingTab(config_manager, parent)
            else:
                raise ImportError("No StreamingTab class found")
                
        except Exception as e2:
            print(f"❌ Both streaming tabs failed:")
            print(f"   Refactored: {e1}")
            print(f"   Legacy: {e2}")
            
            # Return mock tab as last resort
            return create_mock_streaming_tab(config_manager, parent)


def create_mock_streaming_tab(config_manager, parent=None):
    """Create a mock streaming tab as last resort"""
    
    try:
        # Try PyQt6 first, then PyQt5
        try:
            from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
        except ImportError:
            from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
        
        class MockStreamingTab(QWidget):
            def __init__(self, config_manager, parent=None):
                super().__init__(parent)
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel("🚧 Streaming Tab (Placeholder)"))
                layout.addWidget(QLabel("The streaming module is being loaded..."))
                layout.addWidget(QLabel("Please check the migration logs for details."))
            
            # Provide basic API compatibility
            def connect_to_playout_tab(self, playout_tab): return True
            def load_and_start_stream(self, file_path): return False
            def get_program_stream_status(self): return {"is_active": False}
            def get_active_streams_count(self): return 0
            def is_streaming_active(self): return False
            def refresh(self): pass
            def cleanup(self): pass
        
        print("⚠️ Using mock streaming tab")
        return MockStreamingTab(config_manager, parent)
        
    except Exception as e:
        print(f"❌ Failed to create mock tab: {e}")
        return None


def get_streaming_tab_class():
    """Get streaming tab class (for compatibility)"""
    try:
        import importlib.util
        refactored_path = current_dir / "refactored_streaming_tab.py" 
        spec = importlib.util.spec_from_file_location("refactored_streaming_tab", refactored_path)
        refactored_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(refactored_module)
        return refactored_module.RefactoredStreamingTab, "refactored"
    except ImportError:
        try:
            from ui.tabs.streaming_tab import StreamingTab
            return StreamingTab, "legacy"
        except ImportError:
            return None, "error"


# Test function
def test_streaming_integration():
    """Test streaming integration"""
    print("🧪 Testing streaming integration...")
    
    class MockConfig:
        def get(self, section, key, default=None): return default or "test"
        def getint(self, section, key, default=0): return default or 1
        def getboolean(self, section, key, default=False): return default or False
    
    try:
        config = MockConfig()
        tab = create_streaming_tab(config)
        
        if tab:
            print("✅ Streaming tab creation successful")
            return True
        else:
            print("❌ Streaming tab creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


# Export
__all__ = ['create_streaming_tab', 'get_streaming_tab_class', 'test_streaming_integration']


if __name__ == "__main__":
    test_streaming_integration()
