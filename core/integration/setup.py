#!/usr/bin/env python3
"""
core/integration/setup.py
Main integration system setup and initialization
"""

from typing import Dict, Any, Optional

from .event_bus import EventBus
from .shared_data import SharedDataManager  
from .tab_manager import TabIntegrationManager
from .workflow_engine import WorkflowEngine
from .monitoring import SystemMonitor
from .config import IntegrationConfig
from .workflows import PracticalWorkflows
from .messages import MongolianSystemMessages
from .base_tab import IntegratedTabBase
from .mixins import (
    MediaLibraryIntegration, 
    PlayoutIntegration, 
    StreamingIntegration, 
    SchedulerIntegration
)

# =============================================================================
# MAIN INTEGRATION SYSTEM
# =============================================================================

class StreamingStudioIntegration:
    """Main integration system for the streaming studio"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = self._get_logger()
        
        # Core components
        self.event_bus = EventBus()
        self.shared_data = SharedDataManager()
        self.integration_manager = TabIntegrationManager(self.event_bus, self.shared_data)
        self.workflow_engine = WorkflowEngine(self.integration_manager)
        
        # Tab registry
        self.tabs: Dict[str, Any] = {}
        
        # Connect signals
        self._connect_signals()
        
        self.logger.info("Streaming Studio Integration System initialized")
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    def _connect_signals(self):
        """Connect integration signals"""
        self.workflow_engine.workflow_completed.connect(self._on_workflow_completed)
        self.integration_manager.emergency_stop_triggered.connect(self._on_emergency_stop)
        self.shared_data.media_library_updated.connect(self._on_media_library_updated)
        self.shared_data.playout_state_changed.connect(self._on_playout_state_changed)
        self.shared_data.stream_status_changed.connect(self._on_stream_status_changed)
    
    def register_tab(self, tab):
        """Register a tab with the integration system"""
        tab_name = tab.get_tab_name()
        
        # Set integration components
        if hasattr(tab, 'set_integration_components'):
            tab.set_integration_components(
                self.event_bus, self.shared_data, self.integration_manager
            )
        
        # Register with integration manager
        self.integration_manager.register_tab(tab)
        
        # Store reference
        self.tabs[tab_name] = tab
        
        self.logger.info(f"Registered integrated tab: {tab_name}")
    
    def unregister_tab(self, tab_name: str):
        """Unregister a tab"""
        if tab_name in self.tabs:
            self.integration_manager.unregister_tab(tab_name)
            del self.tabs[tab_name]
            self.logger.info(f"Unregistered tab: {tab_name}")
    
    def execute_workflow(self, workflow_name: str, params: Dict[str, Any] = None) -> str:
        """Execute a cross-tab workflow"""
        return self.workflow_engine.execute_workflow(workflow_name, params)
    
    def trigger_emergency_stop(self, reason: str = "Manual trigger"):
        """Trigger emergency stop across all tabs"""
        self.integration_manager.trigger_emergency_stop(reason)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "event_bus": {
                "subscribers": len(self.event_bus.subscribers),
                "event_history_count": len(self.event_bus.event_history)
            },
            "shared_data": {
                "media_library_count": len(self.shared_data.get_media_library()),
                "active_streams": len(self.shared_data.get_active_streams()),
                "current_media": self.shared_data.get_current_media() is not None,
                "playout_live": self.shared_data.get_playout_state().is_live
            },
            "tabs": {name: tab.get_tab_status() for name, tab in self.tabs.items() if hasattr(tab, 'get_tab_status')},
            "workflows": {
                "registered": list(self.workflow_engine.workflows.keys()),
                "running": len(self.workflow_engine.running_workflows)
            }
        }
    
    def _on_workflow_completed(self, execution_id: str, success: bool):
        """Handle workflow completion"""
        status = "completed successfully" if success else "failed"
        message = MongolianSystemMessages.get_message(
            "workflow_completed" if success else "workflow_failed",
            workflow_name=execution_id
        )
        self.logger.info(f"Workflow {execution_id} {status}")
    
    def _on_emergency_stop(self):
        """Handle emergency stop"""
        message = MongolianSystemMessages.get_message("emergency_stop")
        self.logger.critical(message)
    
    def _on_media_library_updated(self):
        """Handle media library update"""
        message = MongolianSystemMessages.get_message("shared_data_updated")
        self.logger.debug(message)
    
    def _on_playout_state_changed(self, playout_state):
        """Handle playout state change"""
        if playout_state.is_live:
            message = MongolianSystemMessages.get_message("playout_live")
            self.logger.info(message)
    
    def _on_stream_status_changed(self, streams):
        """Handle stream status change"""
        self.logger.debug(f"Stream status changed: {len(streams)} active streams")

# =============================================================================
# TAB WRAPPER CREATION FUNCTIONS
# =============================================================================

def create_integrated_media_library_tab(original_tab, config_manager):
    """Create integrated media library tab"""
    class IntegratedMediaLibraryTab(IntegratedTabBase, MediaLibraryIntegration):
        def __init__(self, original_tab, config_manager):
            super().__init__("media_library", config_manager)
            self.original_tab = original_tab
            self._register_media_commands()
            if hasattr(original_tab, 'status_message'):
                original_tab.status_message.connect(self.status_message.emit)
        
        def _subscribe_to_events(self):
            self._subscribe_to_media_events()
        
        def refresh(self):
            if hasattr(self.original_tab, 'refresh'):
                self.original_tab.refresh()
    
    return IntegratedMediaLibraryTab(original_tab, config_manager)

def create_integrated_playout_tab(original_tab, config_manager):
    """Create integrated playout tab"""
    class IntegratedPlayoutTab(IntegratedTabBase, PlayoutIntegration):
        def __init__(self, original_tab, config_manager):
            super().__init__("playout", config_manager)
            self.original_tab = original_tab
            self._register_playout_commands()
            if hasattr(original_tab, 'status_message'):
                original_tab.status_message.connect(self.status_message.emit)
        
        def _subscribe_to_events(self):
            self._subscribe_to_playout_events()
        
        def refresh(self):
            if hasattr(self.original_tab, 'refresh'):
                self.original_tab.refresh()
    
    return IntegratedPlayoutTab(original_tab, config_manager)

def create_integrated_streaming_tab(original_tab, config_manager):
    """Create integrated streaming tab"""
    class IntegratedStreamingTab(IntegratedTabBase, StreamingIntegration):
        def __init__(self, original_tab, config_manager):
            super().__init__("streaming", config_manager)
            self.original_tab = original_tab
            self._register_streaming_commands()
            if hasattr(original_tab, 'status_message'):
                original_tab.status_message.connect(self.status_message.emit)
        
        def _subscribe_to_events(self):
            self._subscribe_to_streaming_events()
        
        def refresh(self):
            if hasattr(self.original_tab, 'refresh'):
                self.original_tab.refresh()
    
    return IntegratedStreamingTab(original_tab, config_manager)

def create_integrated_scheduler_tab(original_tab, config_manager):
    """Create integrated scheduler tab"""
    class IntegratedSchedulerTab(IntegratedTabBase, SchedulerIntegration):
        def __init__(self, original_tab, config_manager):
            super().__init__("scheduler", config_manager)
            self.original_tab = original_tab
            self._register_scheduler_commands()
            if hasattr(original_tab, 'status_message'):
                original_tab.status_message.connect(self.status_message.emit)
        
        def _subscribe_to_events(self):
            self._subscribe_to_scheduler_events()
        
        def refresh(self):
            if hasattr(self.original_tab, 'refresh'):
                self.original_tab.refresh()
    
    return IntegratedSchedulerTab(original_tab, config_manager)

def create_basic_integrated_tab(original_tab, tab_name: str, config_manager):
    """Create basic integrated tab for unknown tab types"""
    class BasicIntegratedTab(IntegratedTabBase):
        def __init__(self, original_tab, tab_name: str, config_manager):
            super().__init__(tab_name, config_manager)
            self.original_tab = original_tab
            if hasattr(original_tab, 'status_message'):
                original_tab.status_message.connect(self.status_message.emit)
        
        def refresh(self):
            if hasattr(self.original_tab, 'refresh'):
                self.original_tab.refresh()
    
    return BasicIntegratedTab(original_tab, tab_name, config_manager)

# =============================================================================
# MAIN SETUP FUNCTION
# =============================================================================

def setup_integration_system(main_window, config_manager, integration_config: IntegrationConfig = None):
    """Complete setup function for the integration system"""
    
    if integration_config is None:
        integration_config = IntegrationConfig()
    
    try:
        # Initialize integration system
        integration = StreamingStudioIntegration(config_manager)
        
        # Configure system based on config
        integration.integration_manager.auto_scheduler_enabled = integration_config.automation_enabled
        integration.event_bus.max_history = integration_config.event_history_limit
        
        # Setup monitoring if enabled
        monitor = None
        if integration_config.monitoring_enabled:
            monitor = SystemMonitor(integration)
            monitor.alert_thresholds.update(integration_config.alert_thresholds)
            monitor.max_history_size = integration_config.performance_history_limit
            
            # Connect monitoring to main window if it has status methods
            if hasattr(main_window, '_show_status_message'):
                monitor.alert_triggered.connect(
                    lambda alert_type, message, severity: 
                    main_window._show_status_message(
                        MongolianSystemMessages.get_message("alert_" + alert_type, message=message),
                        severity * 2000  # Convert severity to timeout
                    )
                )
            
            monitor.start_monitoring(integration_config.monitoring_interval)
        
        # Integrate existing tabs if they exist
        if hasattr(main_window, 'tabs'):
            for tab_name, tab_widget in main_window.tabs.items():
                try:
                    wrapped_tab = create_integrated_tab(tab_widget, tab_name, config_manager)
                    integration.register_tab(wrapped_tab)
                    
                    # Store reference in main window
                    main_window.tabs[tab_name + "_integrated"] = wrapped_tab
                    
                except Exception as e:
                    print(f"Failed to integrate {tab_name} tab: {e}")
        
        # Setup practical workflows
        practical_workflows = [
            PracticalWorkflows.create_media_to_air_workflow(),
            PracticalWorkflows.create_live_streaming_workflow(),
            PracticalWorkflows.create_scheduled_broadcast_workflow(),
            PracticalWorkflows.create_emergency_procedures_workflow(),
            PracticalWorkflows.create_quality_adaptive_workflow(),
            PracticalWorkflows.create_auto_recovery_workflow(),
            PracticalWorkflows.create_daily_startup_workflow(),
            PracticalWorkflows.create_end_of_day_workflow()
        ]
        
        for workflow in practical_workflows:
            integration.workflow_engine.register_workflow(workflow)
        
        # Store integration system in main window
        main_window.integration_system = integration
        main_window.system_monitor = monitor
        main_window.integration_config = integration_config
        
        # Add integration methods to main window
        main_window.execute_workflow = integration.execute_workflow
        main_window.trigger_emergency_stop = integration.trigger_emergency_stop
        main_window.get_system_status = integration.get_system_status
        
        # Success messages
        print("✅ " + MongolianSystemMessages.get_message("integration_initialized"))
        print("📊 " + MongolianSystemMessages.get_message("tabs_connected", count=len(integration.tabs)))
        print(f"🔄 {len(integration.workflow_engine.workflows)} workflow бэлэн боллоо")
        if monitor:
            print(f"📈 " + MongolianSystemMessages.get_message("monitoring_started") + f" ({integration_config.monitoring_interval}ms)")
        
        return integration, monitor
        
    except Exception as e:
        error_msg = MongolianSystemMessages.get_message("integration_failed")
        print(f"❌ {error_msg}: {e}")
        raise

def create_integrated_tab(tab_widget, tab_name: str, config_manager):
    """Create integrated tab based on tab name"""
    if tab_name == "media_library":
        return create_integrated_media_library_tab(tab_widget, config_manager)
    elif tab_name == "playout":
        return create_integrated_playout_tab(tab_widget, config_manager)
    elif tab_name == "streaming":
        return create_integrated_streaming_tab(tab_widget, config_manager)
    elif tab_name == "scheduler":
        return create_integrated_scheduler_tab(tab_widget, config_manager)
    else:
        return create_basic_integrated_tab(tab_widget, tab_name, config_manager)

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'StreamingStudioIntegration',
    'setup_integration_system',
    'create_integrated_media_library_tab',
    'create_integrated_playout_tab', 
    'create_integrated_streaming_tab',
    'create_integrated_scheduler_tab',
    'create_basic_integrated_tab',
    'create_integrated_tab'
]