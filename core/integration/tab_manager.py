#!/usr/bin/env python3
"""
core/integration/tab_manager.py
Tab integration and coordination management
"""

from datetime import datetime
from typing import Dict, List, Any

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .event_bus import EventType, SystemEvent

# =============================================================================
# TAB INTEGRATION MANAGER
# =============================================================================

class TabIntegrationManager(QObject):
    """Manages integration between all tabs"""
    
    # Global status signals
    global_status_update = pyqtSignal(dict)
    emergency_stop_triggered = pyqtSignal()
    
    def __init__(self, event_bus, shared_data):
        super().__init__()
        
        self.event_bus = event_bus
        self.shared_data = shared_data
        self.registered_tabs: Dict[str, Any] = {}
        self.tab_status: Dict[str, Dict[str, Any]] = {}
        
        # Auto-scheduling system
        self.auto_scheduler_enabled = True
        self.automation_rules: List[Dict[str, Any]] = []
        
        # Emergency systems
        self.emergency_stop_active = False
        
        self.logger = self._get_logger()
        
        # Setup default automation rules
        self._setup_automation_rules()
        
        # Connect to event bus
        self._connect_event_handlers()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_global_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    def register_tab(self, tab):
        """Register tab for integration"""
        tab_name = tab.get_tab_name()
        self.registered_tabs[tab_name] = tab
        self.tab_status[tab_name] = tab.get_tab_status()
        
        self.logger.info(f"Registered tab: {tab_name}")
        
        # Send welcome event
        welcome_event = SystemEvent(
            event_type=EventType.TAB_ACTIVATED,
            source_tab="system",
            target_tab=tab_name,
            data={"message": "Tab registered successfully"}
        )
        self.event_bus.emit_event(welcome_event)
    
    def unregister_tab(self, tab_name: str):
        """Unregister tab"""
        if tab_name in self.registered_tabs:
            del self.registered_tabs[tab_name]
            del self.tab_status[tab_name]
            self.logger.info(f"Unregistered tab: {tab_name}")
    
    def _connect_event_handlers(self):
        """Connect event handlers"""
        self.event_bus.global_event.connect(self._handle_global_event)
        
        # Connect specific event types to automation
        self.event_bus.media_event.connect(self._handle_media_automation)
        self.event_bus.schedule_event.connect(self._handle_schedule_automation)
        self.event_bus.playout_event.connect(self._handle_playout_automation)
        self.event_bus.streaming_event.connect(self._handle_streaming_automation)
    
    def _handle_global_event(self, event: SystemEvent):
        """Handle global events and route to appropriate tabs"""
        try:
            # Route to specific tab if target specified
            if event.target_tab and event.target_tab in self.registered_tabs:
                tab = self.registered_tabs[event.target_tab]
                tab.handle_system_event(event)
            else:
                # Broadcast to all tabs except source
                for tab_name, tab in self.registered_tabs.items():
                    if tab_name != event.source_tab:
                        tab.handle_system_event(event)
            
            # Handle emergency stop
            if event.event_type == EventType.EMERGENCY_STOP:
                self._handle_emergency_stop(event)
            
        except Exception as e:
            self.logger.error(f"Error handling global event: {e}")
    
    def _handle_emergency_stop(self, event: SystemEvent):
        """Handle emergency stop event"""
        self.emergency_stop_active = True
        self.emergency_stop_triggered.emit()
        
        # Stop all critical operations
        stop_commands = [
            ("streaming", "stop_all_streams", {}),
            ("playout", "emergency_stop", {}),
            ("scheduler", "disable_automation", {})
        ]
        
        for tab_name, command, params in stop_commands:
            if tab_name in self.registered_tabs:
                try:
                    self.registered_tabs[tab_name].execute_command(command, params)
                except Exception as e:
                    self.logger.error(f"Emergency stop failed for {tab_name}: {e}")
        
        self.logger.critical("Emergency stop activated")
    
    def _setup_automation_rules(self):
        """Setup default automation rules"""
        self.automation_rules = [
            {
                "name": "Auto Stream Start",
                "trigger": EventType.PLAYOUT_TAKE,
                "conditions": ["playout.is_live == True"],
                "actions": [
                    {
                        "tab": "streaming",
                        "command": "start_auto_stream",
                        "params": {"source": "program_output"}
                    }
                ]
            },
            {
                "name": "Auto Media Load",
                "trigger": EventType.SCHEDULE_EVENT_TRIGGERED,
                "conditions": ["event.data.event_type == 'media_play'"],
                "actions": [
                    {
                        "tab": "media_library",
                        "command": "load_scheduled_media",
                        "params": {"file_path": "event.data.content"}
                    },
                    {
                        "tab": "playout",
                        "command": "cue_preview",
                        "params": {"auto_take": True}
                    }
                ]
            }
        ]
    
    def _handle_media_automation(self, event: SystemEvent):
        """Handle media-related automation"""
        if not self.auto_scheduler_enabled:
            return
        
        if event.event_type == EventType.MEDIA_SELECTED:
            # Auto-load to preview if playout is available
            if "playout" in self.registered_tabs:
                self._execute_automation_action(
                    "playout", "load_to_preview", event.data
                )
        
        elif event.event_type == EventType.MEDIA_LOADED:
            # Update shared data
            media_info = self._create_media_info_from_event(event)
            self.shared_data.set_current_media(media_info)
    
    def _handle_schedule_automation(self, event: SystemEvent):
        """Handle schedule-related automation"""
        if not self.auto_scheduler_enabled:
            return
        
        if event.event_type == EventType.SCHEDULE_EVENT_TRIGGERED:
            # Execute scheduled actions based on event type
            event_data = event.data
            
            if event_data.get("event_type") == "media_play":
                # Auto-load and play media
                self._execute_scheduled_media_play(event_data)
            
            elif event_data.get("event_type") == "stream_start":
                # Auto-start streaming
                self._execute_scheduled_stream_start(event_data)
    
    def _handle_playout_automation(self, event: SystemEvent):
        """Handle playout-related automation"""
        if event.event_type == EventType.PLAYOUT_TAKE:
            # Update playout state
            self.shared_data.update_playout_state(is_live=True)
            
            # Auto-start streaming if configured
            if self.shared_data.get_config("auto_stream_on_take", False):
                self._execute_automation_action(
                    "streaming", "start_auto_stream", 
                    {"source": "program_output"}
                )
        
        elif event.event_type == EventType.PREVIEW_TO_PROGRAM:
            # Update program media info
            preview_media = self.shared_data.get_playout_state().preview_media
            self.shared_data.update_playout_state(program_media=preview_media)
    
    def _handle_streaming_automation(self, event: SystemEvent):
        """Handle streaming-related automation"""
        if event.event_type == EventType.STREAM_STARTED:
            # Update stream info in shared data
            from .shared_data import StreamInfo
            stream_info = StreamInfo(
                stream_key=event.data.get("stream_key", ""),
                server_name=event.data.get("server_name", ""),
                quality=event.data.get("quality", ""),
                status="streaming",
                bitrate=event.data.get("bitrate", "0kbps"),
                fps=event.data.get("fps", 0.0),
                uptime="00:00:00"
            )
            self.shared_data.update_stream_info(stream_info.stream_key, stream_info)
        
        elif event.event_type == EventType.STREAM_ERROR:
            # Handle stream errors with auto-recovery
            if self.shared_data.get_config("auto_recover_streams", True):
                self._execute_automation_action(
                    "streaming", "auto_recover_stream", event.data
                )
    
    def _execute_scheduled_media_play(self, event_data: Dict[str, Any]):
        """Execute scheduled media play"""
        file_path = event_data.get("content")
        if not file_path:
            return
        
        # Load to preview first
        self._execute_automation_action(
            "playout", "load_to_preview", {"file_path": file_path}
        )
        
        # Auto-take if specified
        if event_data.get("auto_take", False):
            QTimer.singleShot(1000, lambda: self._execute_automation_action(
                "playout", "take_to_air", {}
            ))
    
    def _execute_scheduled_stream_start(self, event_data: Dict[str, Any]):
        """Execute scheduled stream start"""
        stream_config = event_data.get("stream_config", {})
        
        self._execute_automation_action(
            "streaming", "start_scheduled_stream", stream_config
        )
    
    def _execute_automation_action(self, tab_name: str, command: str, params: Dict[str, Any]):
        """Execute automation action on specific tab"""
        try:
            if tab_name in self.registered_tabs:
                tab = self.registered_tabs[tab_name]
                result = tab.execute_command(command, params)
                
                self.logger.debug(f"Executed automation: {tab_name}.{command} -> {result}")
                return result
            else:
                self.logger.warning(f"Tab {tab_name} not available for automation")
                return {"error": f"Tab {tab_name} not registered"}
        
        except Exception as e:
            self.logger.error(f"Automation action failed: {tab_name}.{command} - {e}")
            return {"error": str(e)}
    
    def _create_media_info_from_event(self, event: SystemEvent):
        """Create MediaInfo from event data"""
        from .shared_data import MediaInfo
        data = event.data
        return MediaInfo(
            file_path=data.get("file_path", ""),
            title=data.get("title"),
            duration=data.get("duration"),
            format=data.get("format"),
            resolution=data.get("resolution"),
            file_size=data.get("file_size"),
            metadata=data.get("metadata", {})
        )
    
    def _update_global_status(self):
        """Update global system status"""
        try:
            global_status = {
                "timestamp": datetime.now().isoformat(),
                "tabs": {},
                "emergency_stop": self.emergency_stop_active,
                "auto_scheduler": self.auto_scheduler_enabled,
                "active_streams": len(self.shared_data.get_active_streams()),
                "current_media": self.shared_data.get_current_media() is not None,
                "playout_live": self.shared_data.get_playout_state().is_live
            }
            
            # Get status from each tab
            for tab_name, tab in self.registered_tabs.items():
                try:
                    self.tab_status[tab_name] = tab.get_tab_status()
                    global_status["tabs"][tab_name] = self.tab_status[tab_name]
                except Exception as e:
                    global_status["tabs"][tab_name] = {"error": str(e)}
            
            self.global_status_update.emit(global_status)
            
        except Exception as e:
            self.logger.error(f"Error updating global status: {e}")
    
    # Public API methods
    def send_command_to_tab(self, tab_name: str, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to specific tab"""
        return self._execute_automation_action(tab_name, command, params or {})
    
    def broadcast_event(self, event_type: EventType, data: Dict[str, Any], source_tab: str = "system"):
        """Broadcast event to all tabs"""
        event = SystemEvent(
            event_type=event_type,
            source_tab=source_tab,
            data=data
        )
        self.event_bus.emit_event(event)
    
    def enable_automation(self):
        """Enable automation system"""
        self.auto_scheduler_enabled = True
        self.logger.info("Automation system enabled")
    
    def disable_automation(self):
        """Disable automation system"""
        self.auto_scheduler_enabled = False
        self.logger.info("Automation system disabled")
    
    def trigger_emergency_stop(self, reason: str = "Manual trigger"):
        """Trigger emergency stop"""
        event = SystemEvent(
            event_type=EventType.EMERGENCY_STOP,
            source_tab="system",
            data={"reason": reason}
        )
        self.event_bus.emit_event(event)
    
    def reset_emergency_stop(self):
        """Reset emergency stop state"""
        self.emergency_stop_active = False
        self.logger.info("Emergency stop reset")