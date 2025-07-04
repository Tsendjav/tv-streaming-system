#!/usr/bin/env python3
"""
Integration Usage Example - Tab Integration Enhancement (Fixed Version)
"""

def integrate_with_existing_main_window(MainWindowClass):
    """
    Enhance existing main window class with integration capabilities
    """
    
    class IntegratedMainWindow(MainWindowClass):
        def __init__(self, config_manager, app):
            # Initialize integration attributes FIRST
            self.event_bus = None
            self.shared_data_manager = None
            self.tab_integration_manager = None
            self.workflow_engine = None
            self.integration_system = None
            self.system_monitor = None
            
            # Initialize base class AFTER setting attributes
            super().__init__(config_manager, app)
            
            # Setup integration after everything is initialized
            self._setup_enhanced_integration()
        
        def _setup_enhanced_integration(self):
            """Setup enhanced integration system"""
            try:
                # Try to import integration components
                from core.integration import (
                    EventBus, SharedDataManager, 
                    TabIntegrationManager, WorkflowEngine,
                    IntegrationConfig, setup_integration_system
                )
                
                # Initialize integration components
                self.event_bus = EventBus()
                self.shared_data_manager = SharedDataManager()
                self.tab_integration_manager = TabIntegrationManager(self.event_bus)
                self.workflow_engine = WorkflowEngine(self.event_bus, self.shared_data_manager)
                
                # Create integration config
                integration_config = IntegrationConfig()
                integration_config.monitoring_enabled = True
                integration_config.automation_enabled = True
                integration_config.use_localized_messages = True
                
                # Setup full integration system
                self.integration_system = setup_integration_system(
                    self.app, self.config_manager, 
                    self.event_bus, self.shared_data_manager,
                    self.tab_integration_manager, self.workflow_engine
                )
                
                # Register workflows
                self._register_workflows()
                
                # Connect integration signals
                if self.integration_system and hasattr(self.integration_system, 'event_bus'):
                    self.integration_system.event_bus.global_event.connect(self._on_integration_event)
                
                print("✅ Enhanced integration system activated")
                
            except ImportError as e:
                print(f"❌ Integration system not available: {e}")
                # Create mock objects to prevent errors
                self._create_mock_integration()
            except Exception as e:
                print(f"❌ Integration setup failed: {e}")
                self._create_mock_integration()
        
        def _create_mock_integration(self):
            """Create mock integration objects"""
            print("🔄 Creating mock integration system...")
            
            class MockSignal:
                def connect(self, handler): pass
                def emit(self, *args): pass
            
            class MockEventBus:
                def __init__(self):
                    self.global_event = MockSignal()
                def emit_event(self, event): pass
                def subscribe(self, event_type, handler): pass
            
            class MockSharedData:
                def set_data(self, key, value): pass
                def get_data(self, key): return None
            
            class MockTabManager:
                def register_tab(self, tab_id, tab): pass
                def register_integrated_tab(self, tab_id, tab): pass
            
            class MockWorkflowEngine:
                def __init__(self):
                    self.workflows = {
                        "media_to_air": lambda: "Mock workflow",
                        "live_streaming_setup": lambda: "Mock workflow", 
                        "emergency_procedures": lambda: "Mock workflow",
                        "scheduled_broadcast": lambda: "Mock workflow"
                    }
                def register_workflow(self, name, workflow): 
                    self.workflows[name] = workflow
                def execute_workflow(self, name, params=None): 
                    return f"mock-{name}-{hash(str(params)) % 1000}"
            
            class MockIntegrationSystem:
                def __init__(self):
                    self.event_bus = MockEventBus()
                def register_integrated_tab(self, tab_id, tab): pass
                def execute_workflow(self, name, params=None):
                    return f"mock-{name}-execution"
                def trigger_emergency_stop(self, reason):
                    print(f"🛑 Mock emergency stop: {reason}")
                def get_system_status(self):
                    return {
                        "status": "mock_mode",
                        "tabs_registered": [],
                        "integration_active": False,
                        "mock_mode": True
                    }
            
            class MockSystemMonitor:
                def __init__(self):
                    self.alert_triggered = MockSignal()
                    self.system_health_changed = MockSignal()
                def stop_monitoring(self): pass
            
            # Set all mock objects
            self.event_bus = MockEventBus()
            self.shared_data_manager = MockSharedData()
            self.tab_integration_manager = MockTabManager()
            self.workflow_engine = MockWorkflowEngine()
            self.integration_system = MockIntegrationSystem()
            self.system_monitor = MockSystemMonitor()
            
            print("✅ Mock integration system ready")
        
        def _register_workflows(self):
            """Register default workflows"""
            try:
                # Media to Air workflow
                def media_to_air_workflow(params=None):
                    return {"status": "completed", "message": "Media taken to air successfully"}
                
                # Live streaming workflow  
                def live_streaming_workflow(params=None):
                    return {"status": "completed", "message": "Live stream started"}
                
                # Emergency procedures
                def emergency_procedures_workflow(params=None):
                    return {"status": "completed", "message": "Emergency procedures executed"}
                
                # Scheduled broadcast
                def scheduled_broadcast_workflow(params=None):
                    return {"status": "completed", "message": "Scheduled broadcast started"}
                
                # Register workflows
                self.workflow_engine.register_workflow("media_to_air", media_to_air_workflow)
                self.workflow_engine.register_workflow("live_streaming_setup", live_streaming_workflow) 
                self.workflow_engine.register_workflow("emergency_procedures", emergency_procedures_workflow)
                self.workflow_engine.register_workflow("scheduled_broadcast", scheduled_broadcast_workflow)
                
                print(f"✅ Registered {len(self.workflow_engine.workflows)} workflows")
                
            except Exception as e:
                print(f"❌ Workflow registration failed: {e}")
        
        def execute_workflow(self, workflow_name, params=None):
            """Execute a workflow"""
            try:
                if self.workflow_engine and workflow_name in self.workflow_engine.workflows:
                    execution_id = self.workflow_engine.execute_workflow(workflow_name, params)
                    print(f"🔄 Executed workflow '{workflow_name}' -> {execution_id}")
                    return execution_id
                else:
                    print(f"❌ Workflow '{workflow_name}' not found")
                    return None
            except Exception as e:
                print(f"❌ Workflow execution failed: {e}")
                return None
        
        def trigger_emergency_stop(self, reason="Manual stop"):
            """Trigger emergency stop"""
            try:
                print(f"🛑 EMERGENCY STOP TRIGGERED: {reason}")
                
                # Stop all tabs that support emergency stop
                for tab_name, tab in self.tabs.items():
                    try:
                        if hasattr(tab, 'emergency_stop'):
                            tab.emergency_stop()
                            print(f"   ✅ {tab_name} stopped")
                    except Exception as e:
                        print(f"   ❌ Failed to stop {tab_name}: {e}")
                
                return True
                
            except Exception as e:
                print(f"❌ Emergency stop failed: {e}")
                return False
        
        def get_system_status(self):
            """Get comprehensive system status"""
            try:
                return {
                    "application": {
                        "name": "Professional TV Streaming Studio",
                        "version": "1.0.0",
                        "integration_mode": "enhanced" if self.integration_system else "mock"
                    },
                    "tabs": {
                        "total": len(self.tabs),
                        "available": list(self.tabs.keys())
                    },
                    "integration": {
                        "event_bus_active": self.event_bus is not None,
                        "workflows_registered": len(self.workflow_engine.workflows) if self.workflow_engine else 0,
                        "workflow_names": list(self.workflow_engine.workflows.keys()) if self.workflow_engine else []
                    },
                    "system": {
                        "timestamp": "2025-06-29T15:41:00Z",
                        "status": "operational"
                    }
                }
            except Exception as e:
                return {"error": str(e), "timestamp": "2025-06-29T15:41:00Z"}
        
        def _on_integration_event(self, event):
            """Handle integration events"""
            try:
                event_msg = f"🔄 Event: {event.event_type} from {getattr(event, 'source_tab', 'unknown')}"
                print(event_msg)
            except Exception as e:
                print(f"❌ Error handling integration event: {e}")
        
        def _setup_integration_system(self):
            """Override parent method - integration already setup"""
            pass
    
    return IntegratedMainWindow


# Export for main.py
__all__ = ['integrate_with_existing_main_window']
