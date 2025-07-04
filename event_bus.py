#!/usr/bin/env python3
"""
core/integration/event_bus.py
Event Bus система - табуудын хоорондын харилцаа холбоо
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

# =============================================================================
# EVENT TYPES AND MODELS
# =============================================================================

class EventType(Enum):
    """System-wide event types"""
    # Media events
    MEDIA_SELECTED = "media_selected"
    MEDIA_LOADED = "media_loaded"
    MEDIA_PLAYED = "media_played"
    MEDIA_STOPPED = "media_stopped"
    
    # Streaming events
    STREAM_STARTED = "stream_started"
    STREAM_STOPPED = "stream_stopped"
    STREAM_ERROR = "stream_error"
    STREAM_QUALITY_CHANGED = "stream_quality_changed"
    
    # Playout events
    PLAYOUT_CUE = "playout_cue"
    PLAYOUT_TAKE = "playout_take"
    PLAYOUT_FADE = "playout_fade"
    PREVIEW_TO_PROGRAM = "preview_to_program"
    
    # Schedule events
    SCHEDULE_EVENT_TRIGGERED = "schedule_event_triggered"
    SCHEDULE_EVENT_COMPLETED = "schedule_event_completed"
    AUTO_PLAY_REQUEST = "auto_play_request"
    
    # System events
    TAB_ACTIVATED = "tab_activated"
    TAB_DEACTIVATED = "tab_deactivated"
    CONFIG_CHANGED = "config_changed"
    EMERGENCY_STOP = "emergency_stop"
    
    # Audio events
    AUDIO_PROFILE_CHANGED = "audio_profile_changed"
    AUDIO_LEVELS_UPDATE = "audio_levels_update"
    AUDIO_MUTE = "audio_mute"
    AUDIO_UNMUTE = "audio_unmute"

@dataclass
class SystemEvent:
    """System event data structure"""
    event_type: EventType
    source_tab: str
    target_tab: Optional[str] = None  # None means broadcast to all
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5  # 1-10, higher = more important
    requires_response: bool = False
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "source_tab": self.source_tab,
            "target_tab": self.target_tab,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "requires_response": self.requires_response,
            "correlation_id": self.correlation_id
        }

# =============================================================================
# EVENT BUS
# =============================================================================

class EventBus(QObject):
    """Central event bus for inter-tab communication"""
    
    # PyQt signals for different event types
    media_event = pyqtSignal(object)
    streaming_event = pyqtSignal(object)
    playout_event = pyqtSignal(object)
    schedule_event = pyqtSignal(object)
    system_event = pyqtSignal(object)
    audio_event = pyqtSignal(object)
    
    # Global event signal
    global_event = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[SystemEvent] = []
        self.max_history = 1000
        self.logger = self._get_logger()
        
        # Connect typed signals to global handler
        self.media_event.connect(self._handle_typed_event)
        self.streaming_event.connect(self._handle_typed_event)
        self.playout_event.connect(self._handle_typed_event)
        self.schedule_event.connect(self._handle_typed_event)
        self.system_event.connect(self._handle_typed_event)
        self.audio_event.connect(self._handle_typed_event)
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    def emit_event(self, event: SystemEvent):
        """Emit system event to appropriate channels"""
        try:
            # Store in history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # Emit to appropriate typed signal
            event_category = self._get_event_category(event.event_type)
            
            if event_category == "media":
                self.media_event.emit(event)
            elif event_category == "streaming":
                self.streaming_event.emit(event)
            elif event_category == "playout":
                self.playout_event.emit(event)
            elif event_category == "schedule":
                self.schedule_event.emit(event)
            elif event_category == "audio":
                self.audio_event.emit(event)
            else:
                self.system_event.emit(event)
            
            # Always emit to global
            self.global_event.emit(event)
            
            self.logger.debug(f"Event emitted: {event.event_type.value} from {event.source_tab}")
            
        except Exception as e:
            self.logger.error(f"Error emitting event: {e}")
    
    def _get_event_category(self, event_type: EventType) -> str:
        """Get event category from event type"""
        event_name = event_type.value
        
        if event_name.startswith("media_"):
            return "media"
        elif event_name.startswith("stream_"):
            return "streaming"
        elif event_name.startswith("playout_") or event_name.startswith("preview_"):
            return "playout"
        elif event_name.startswith("schedule_") or event_name.startswith("auto_"):
            return "schedule"
        elif event_name.startswith("audio_"):
            return "audio"
        else:
            return "system"
    
    def _handle_typed_event(self, event: SystemEvent):
        """Handle typed event and notify subscribers"""
        event_key = event.event_type.value
        
        if event_key in self.subscribers:
            for callback in self.subscribers[event_key]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event_key}: {e}")
    
    def subscribe(self, event_type: EventType, callback: Callable[[SystemEvent], None]):
        """Subscribe to specific event type"""
        event_key = event_type.value
        
        if event_key not in self.subscribers:
            self.subscribers[event_key] = []
        
        self.subscribers[event_key].append(callback)
        self.logger.debug(f"Subscribed to event: {event_key}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[SystemEvent], None]):
        """Unsubscribe from event type"""
        event_key = event_type.value
        
        if event_key in self.subscribers and callback in self.subscribers[event_key]:
            self.subscribers[event_key].remove(callback)
            self.logger.debug(f"Unsubscribed from event: {event_key}")
    
    def get_event_history(self, event_types: List[EventType] = None, 
                         since: datetime = None, limit: int = 100) -> List[SystemEvent]:
        """Get filtered event history"""
        events = self.event_history.copy()
        
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'EventType',
    'SystemEvent', 
    'EventBus'
]