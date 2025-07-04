#!/usr/bin/env python3
"""
core/integration/base_tab.py
Base class for integrated tabs with common functionality (ABC-Ð³Ò¯Ð¹)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

from .event_bus import EventType, SystemEvent

# =============================================================================
# TAB INTEGRATION INTERFACE (ABC-Ð³Ò¯Ð¹)
# =============================================================================

class ITabIntegration:
    """Simple interface for tab integration without ABC"""
    
    def get_tab_name(self) -> str:
        """Get tab name for identification"""
        raise NotImplementedError("Subclasses must implement get_tab_name")
    
    def handle_system_event(self, event: SystemEvent):
        """Handle incoming system event"""
        raise NotImplementedError("Subclasses must implement handle_system_event")
    
    def get_tab_status(self) -> Dict[str, Any]:
        """Get current tab status"""
        raise NotImplementedError("Subclasses must implement get_tab_status")
    
    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute tab-specific command"""
        raise NotImplementedError("Subclasses must implement execute_command")

# =============================================================================
# INTEGRATED TAB BASE CLASS
# =============================================================================

class IntegratedTabBase(QWidget, ITabIntegration):
    """Base class for tabs with integration support"""
    
    # Common signals
    status_message = pyqtSignal(str, int)
    command_executed = pyqtSignal(str, dict)
    
    def __init__(self, tab_name: str, config_manager, parent=None):
        super().__init__(parent)
        self.tab_name = tab_name
        self.config_manager = config_manager
        self.logger = self._get_logger()
        
        # Integration components (set later by integration system)
        self.event_bus = None
        self.shared_data = None
        self.integration_manager = None
        
        # Command handlers
        self.command_handlers: Dict[str, Callable] = {}
        self._register_command_handlers()
        
        # Tab status
        self.tab_status = {
            "initialized": False,
            "active": False,
            "last_activity": datetime.now().isoformat()
        }
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(f"{__name__}.{self.tab_name}")
        except ImportError:
            import logging
            return logging.getLogger(f"{__name__}.{self.tab_name}")
    
    def set_integration_components(self, event_bus, shared_data, integration_manager):
        """Set integration components"""
        self.event_bus = event_bus
        self.shared_data = shared_data
        self.integration_manager = integration_manager
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        self.tab_status["initialized"] = True
        self.logger.info(f"Integration components set for {self.tab_name}")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events - to be overridden by subclasses"""
        pass
    
    def _register_command_handlers(self):
        """Register command handlers - to be overridden by subclasses"""
        # Common commands
        self.command_handlers.update({
            "get_status": self._handle_get_status,
            "refresh": self._handle_refresh,
            "activate": self._handle_activate,
            "deactivate": self._handle_deactivate
        })
    
    def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get status command"""
        return self.get_tab_status()
    
    def _handle_refresh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refresh command"""
        try:
            if hasattr(self, 'refresh'):
                self.refresh()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_activate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle activate command"""
        self.tab_status["active"] = True
        self.tab_status["last_activity"] = datetime.now().isoformat()
        return {"success": True}
    
    def _handle_deactivate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deactivate command"""
        self.tab_status["active"] = False
        return {"success": True}
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any], target_tab: str = None):
        """Emit system event"""
        if self.event_bus:
            event = SystemEvent(
                event_type=event_type,
                source_tab=self.tab_name,
                target_tab=target_tab,
                data=data
            )
            self.event_bus.emit_event(event)
    
    def send_command_to_tab(self, tab_name: str, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to another tab"""
        if self.integration_manager:
            return self.integration_manager.send_command_to_tab(tab_name, command, params or {})
        return {"error": "Integration manager not available"}
    
    # ITabIntegration implementation
    def get_tab_name(self) -> str:
        return self.tab_name
    
    def handle_system_event(self, event: SystemEvent):
        """Handle incoming system event - to be overridden by subclasses"""
        self.tab_status["last_activity"] = datetime.now().isoformat()
        self.logger.debug(f"Received event: {event.event_type.value} from {event.source_tab}")
    
    def get_tab_status(self) -> Dict[str, Any]:
        """Get current tab status"""
        return self.tab_status.copy()
    
    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute tab-specific command"""
        try:
            if command in self.command_handlers:
                result = self.command_handlers[command](params or {})
                self.command_executed.emit(command, result)
                return result
            else:
                return {"error": f"Unknown command: {command}"}
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return {"error": str(e)}
