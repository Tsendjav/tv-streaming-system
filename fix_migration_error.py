#!/usr/bin/env python3
"""
Fix Migration Import Error
Алдааг засварлах скрипт
"""

import os
import shutil
from pathlib import Path


def fix_main_py_imports(project_root: str = None):
    """Fix main.py import errors"""
    
    if not project_root:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)
    
    main_py = project_root / "main.py"
    backup_file = main_py.with_suffix('.py.backup')
    
    print("🔧 Fixing main.py import errors...")
    
    # Restore from backup if it exists
    if backup_file.exists():
        print("📦 Restoring from backup...")
        shutil.copy2(backup_file, main_py)
        print("✅ Restored main.py from backup")
    
    # Read current content
    try:
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and fix the problematic import line
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if 'from ui.tabs.streaming_tab import StreamingTab' in line:
                # Replace with proper import
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                replacement = f"""{indent_str}# Streaming Tab with automatic fallback
{indent_str}try:
{indent_str}    from streaming.refactored_streaming_tab import RefactoredStreamingTab as StreamingTab
{indent_str}    print("✅ Using refactored streaming tab")
{indent_str}except ImportError:
{indent_str}    from ui.tabs.streaming_tab import StreamingTab
{indent_str}    print("⚠️ Using legacy streaming tab")"""
                
                fixed_lines.append(replacement)
                print(f"✅ Fixed import at line {i+1}")
            else:
                fixed_lines.append(line)
        
        # Write fixed content
        with open(main_py, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print("✅ main.py imports fixed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix imports: {e}")
        return False


def fix_main_window_py_imports(project_root: str = None):
    """Fix main_window.py import errors"""
    
    if not project_root:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)
    
    main_window_py = project_root / "main_window.py"
    
    if not main_window_py.exists():
        print("⚠️ main_window.py not found, skipping...")
        return True
    
    try:
        with open(main_window_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if import needs fixing
        if 'from ui.tabs.streaming_tab import StreamingTab' in content:
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                if 'from ui.tabs.streaming_tab import StreamingTab' in line:
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    
                    replacement = f"""{indent_str}# Streaming Tab with automatic fallback
{indent_str}try:
{indent_str}    from streaming.refactored_streaming_tab import RefactoredStreamingTab as StreamingTab
{indent_str}    print("✅ Using refactored streaming tab")
{indent_str}except ImportError:
{indent_str}    from ui.tabs.streaming_tab import StreamingTab
{indent_str}    print("⚠️ Using legacy streaming tab")"""
                    
                    fixed_lines.append(replacement)
                else:
                    fixed_lines.append(line)
            
            with open(main_window_py, 'w', encoding='utf-8') as f:
                f.write('\n'.join(fixed_lines))
            
            print("✅ main_window.py imports fixed")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix main_window.py: {e}")
        return False


def create_simple_integration():
    """Create simple integration file"""
    
    project_root = Path.cwd()
    streaming_dir = project_root / "streaming"
    
    if not streaming_dir.exists():
        print("❌ Streaming directory not found")
        return False
    
    integration_file = streaming_dir / "integration.py"
    
    integration_content = '''"""
Simple Streaming Integration
"""

def create_streaming_tab(config_manager, parent=None):
    """Create streaming tab with fallback"""
    try:
        from streaming.refactored_streaming_tab import RefactoredStreamingTab
        print("✅ Using refactored streaming tab")
        return RefactoredStreamingTab(config_manager, parent)
    except ImportError as e:
        print(f"⚠️ Refactored tab import failed: {e}")
        try:
            from ui.tabs.streaming_tab import StreamingTab
            print("⚠️ Using legacy streaming tab")
            return StreamingTab(config_manager, parent)
        except ImportError as e2:
            print(f"❌ Both streaming tabs failed to import: {e2}")
            return None

def get_streaming_tab_class():
    """Get streaming tab class"""
    try:
        from streaming.refactored_streaming_tab import RefactoredStreamingTab
        return RefactoredStreamingTab, "refactored"
    except ImportError:
        from ui.tabs.streaming_tab import StreamingTab
        return StreamingTab, "legacy"
'''
    
    try:
        with open(integration_file, 'w', encoding='utf-8') as f:
            f.write(integration_content)
        
        print("✅ Created simple integration file")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create integration: {e}")
        return False


def test_imports():
    """Test if imports work"""
    
    print("\n🧪 Testing imports...")
    
    try:
        # Test streaming integration
        from streaming.integration import create_streaming_tab
        print("✅ streaming.integration import successful")
        
        # Test refactored tab
        from streaming.refactored_streaming_tab import RefactoredStreamingTab
        print("✅ refactored_streaming_tab import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Main function"""
    
    print("🔧 Fixing Migration Import Errors")
    print("=" * 40)
    
    # Fix main.py
    if not fix_main_py_imports():
        print("❌ Failed to fix main.py")
        return False
    
    # Fix main_window.py
    if not fix_main_window_py_imports():
        print("❌ Failed to fix main_window.py")
        return False
    
    # Create simple integration
    if not create_simple_integration():
        print("❌ Failed to create integration")
        return False
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return False
    
    print("\n🎉 All fixes applied successfully!")
    print("\n✅ You can now run: python main.py")
    
    return True


if __name__ == "__main__":
    main()
