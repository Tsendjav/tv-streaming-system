#!/usr/bin/env python3
"""
Tab Integration System - Minimal Working Version
"""

try:
    from abc import ABC, abstractmethod
except ImportError:
    # Fallback for systems without ABC
    class ABC:
        pass
    def abstractmethod(func):
        return func

from typing import Dict, List, Optional, Any, Callable, Union
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
from enum import Enum
from datetime import datetime
import json

class EventType(Enum):
    """System event types"""
    MEDIA_LOADED = "media_loaded"
    MEDIA_PLAYED = "media_played"
    MEDIA_STOPPED = "media_stopped"
    STREAM_STARTED = "stream_started"
    STREAM_STOPPED = "stream_stopped"
    AUDIO_CHANGED = "audio_changed"
    EMERGENCY_STOP = "emergency_stop"
    SYSTEM_STATUS = "system_status"

class SystemEvent:
    """System event data container"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any], source_tab: str = "unknown"):
        self.event_type = event_type
        self.data = data
        self.source_tab = source_tab
        self.timestamp = datetime.now()

class EventBus(QObject):
    """Central event bus for tab communication"""
    
    global_event = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.subscribers = {}
        print("🚌 Event Bus initialized")
    
    def emit_event(self, event: SystemEvent):
        """Emit an event to all subscribers"""
        try:
            self.global_event.emit(event)
            
            # Notify specific subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Error in event callback: {e}")
                        
        except Exception as e:
            print(f"Error emitting event: {e}")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

class SharedDataManager:
    """Shared data storage between tabs"""
    
    def __init__(self):
        self.data = {}
        print("📊 Shared Data Manager initialized")
    
    def set_data(self, key: str, value: Any):
        """Set shared data"""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get shared data"""
        return self.data.get(key, default)
    
    def clear_data(self):
        """Clear all shared data"""
        self.data.clear()

class TabIntegrationManager:
    """Manages tab integration and communication"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.shared_data = shared_data
        self.integrated_tabs = {}
        print("🔗 Tab Integration Manager initialized")
    
    def register_tab(self, tab_id: str, tab_instance):
        """Register a tab for integration"""
        self.integrated_tabs[tab_id] = tab_instance
        print(f"📝 Registered tab: {tab_id}")
    
    def get_tab(self, tab_id: str):
        """Get tab instance by ID"""
        return self.integrated_tabs.get(tab_id)
    
    def broadcast_to_tabs(self, event: SystemEvent):
        """Broadcast event to all integrated tabs"""
        for tab_id, tab in self.integrated_tabs.items():
            if hasattr(tab, 'handle_system_event'):
                try:
                    tab.handle_system_event(event)
                except Exception as e:
                    print(f"Error broadcasting to {tab_id}: {e}")

class WorkflowEngine:
    """Workflow automation engine"""
    
    def __init__(self, event_bus: EventBus, shared_data: SharedDataManager):
        self.event_bus = event_bus
        self.shared_data = shared_data
        self.workflows = {}
        self.execution_history = []
        print("⚙️ Workflow Engine initialized")
    
    def register_workflow(self, name: str, workflow_func: Callable):
        """Register a workflow"""
        self.workflows[name] = workflow_func
        print(f"📋 Registered workflow: {name}")
    
    def execute_workflow(self, name: str, params: Dict[str, Any] = None) -> str:
        """Execute a workflow"""
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found")
        
        execution_id = f"{name}_{len(self.execution_history)}"
        
        try:
            result = self.workflows[name](params or {})
            self.execution_history.append({
                'id': execution_id,
                'name': name,
                'params': params,
                'result': result,
                'timestamp': datetime.now()
            })
            print(f"✅ Executed workflow '{name}' -> {execution_id}")
            return execution_id
        except Exception as e:
            print(f"❌ Workflow '{name}' failed: {e}")
            raise

class IntegrationConfig:
    """Configuration for integration system"""
    
    def __init__(self):
        self.monitoring_enabled = True
        self.automation_enabled = True
        self.use_localized_messages = True
        self.monitoring_interval = 5000
        self.auto_stream_on_take = False
        self.auto_recover_streams = True
        self.emergency_auto_recovery = True

class StreamingStudioIntegration:
    """Main integration system class"""
    
    def __init__(self, app, config_manager, event_bus, shared_data, tab_manager, workflow_engine):
        self.app = app
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.shared_data = shared_data
        self.tab_manager = tab_manager
        self.workflow_engine = workflow_engine
        self.system_monitor = None
        print("🎯 Streaming Studio Integration initialized")
    
    def register_integrated_tab(self, tab_id: str, tab_instance):
        """Register a tab with the integration system"""
        self.tab_manager.register_tab(tab_id, tab_instance)
    
    def execute_workflow(self, workflow_name: str, params: Dict[str, Any] = None) -> str:
        """Execute a workflow"""
        return self.workflow_engine.execute_workflow(workflow_name, params)
    
    def trigger_emergency_stop(self, reason: str = "Manual emergency stop"):
        """Trigger emergency stop"""
        event = SystemEvent(EventType.EMERGENCY_STOP, {"reason": reason}, "integration_system")
        self.event_bus.emit_event(event)
        print(f"🛑 Emergency stop triggered: {reason}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "tabs": list(self.tab_manager.integrated_tabs.keys()),
            "workflows": list(self.workflow_engine.workflows.keys()),
            "events_processed": len(self.workflow_engine.execution_history),
            "timestamp": datetime.now().isoformat()
        }

def setup_integration_system(app, config_manager, event_bus, shared_data, tab_manager, workflow_engine):
    """Setup complete integration system"""
    try:
        integration = StreamingStudioIntegration(
            app, config_manager, event_bus, shared_data, tab_manager, workflow_engine
        )
        
        # Register default workflows
        def media_to_air_workflow(params):
            return {"status": "completed", "message": "Media taken to air"}
        
        def live_streaming_workflow(params):
            return {"status": "completed", "message": "Live stream started"}
        
        workflow_engine.register_workflow("media_to_air", media_to_air_workflow)
        workflow_engine.register_workflow("live_streaming_setup", live_streaming_workflow)
        
        print("✅ Integration system setup completed")
        return integration
        
    except Exception as e:
        print(f"❌ Integration system setup failed: {e}")
        return None

# Export all classes
__all__ = [
    'EventType', 'SystemEvent', 'EventBus', 'SharedDataManager',
    'TabIntegrationManager', 'WorkflowEngine', 'IntegrationConfig',
    'StreamingStudioIntegration', 'setup_integration_system'
]

print("✅ Tab Integration System module loaded successfully")

