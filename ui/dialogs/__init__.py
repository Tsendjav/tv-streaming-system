"""Dialogs for TV Streaming Studio"""

try:
    from .server_config import ServerManagerDialog, ServerEditDialog, ServerConfig
except ImportError:
    # Fallback for missing dialog
    class ServerManagerDialog:
        def __init__(self, config_manager, parent=None):
            pass
        
        def show(self):
            print("Server config dialog not implemented")

__all__ = ['ServerManagerDialog', 'ServerEditDialog', 'ServerConfig']
