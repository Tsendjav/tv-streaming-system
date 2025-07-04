"""
UI Package
User interface components and widgets
"""

# ui/tabs/__init__.py
"""
UI Tabs Package
Main application tabs and their components
"""

from .tabs.playout_tab import PlayoutTab

try:
    from .tabs.media_library_tab import MediaLibraryTab
except ImportError:
    from .tabs.media_library_tab import MediaLibraryTab

__all__ = ['PlayoutTab', 'MediaLibraryTab']