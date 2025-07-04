# =============================================================================
# core/integration/__init__.py
# =============================================================================

"""
Tab Integration System for TV Streaming Studio

This package provides comprehensive integration between all tabs in the streaming studio,
enabling cross-tab communication, automated workflows, and system monitoring.

Main Components:
- EventBus: Central communication hub
- SharedDataManager: Cross-tab data sharing
- TabIntegrationManager: Tab coordination
- WorkflowEngine: Automated multi-tab workflows
- SystemMonitor: Real-time monitoring and alerts
- IntegrationConfig: System configuration
"""

from .event_bus import EventBus, EventType, SystemEvent
from .shared_data import SharedDataManager, MediaInfo, StreamInfo, PlayoutState
from .tab_manager import TabIntegrationManager
from .workflow_engine import WorkflowEngine, Workflow, WorkflowStep
from .monitoring import SystemMonitor
from .base_tab import IntegratedTabBase, ITabIntegration
from .mixins import (
    MediaLibraryIntegration,
    PlayoutIntegration, 
    StreamingIntegration,
    SchedulerIntegration
)
from .workflows import PracticalWorkflows
from .messages import MongolianSystemMessages
from .config import IntegrationConfig
from .setup import (
    StreamingStudioIntegration,
    setup_integration_system,
    create_integrated_media_library_tab,
    create_integrated_playout_tab,
    create_integrated_streaming_tab,
    create_integrated_scheduler_tab,
    create_basic_integrated_tab
)

__version__ = "1.0.0"
__author__ = "TV Streaming Studio Team"

# Quick setup function for easy integration
def quick_setup(main_window, config_manager):
    """Quick setup with default configuration"""
    config = IntegrationConfig()
    config.apply_defaults_for_broadcasting()
    return setup_integration_system(main_window, config_manager, config)

__all__ = [
    # Core components
    'EventBus', 'EventType', 'SystemEvent',
    'SharedDataManager', 'MediaInfo', 'StreamInfo', 'PlayoutState',
    'TabIntegrationManager',
    'WorkflowEngine', 'Workflow', 'WorkflowStep',
    'SystemMonitor',
    
    # Tab integration
    'IntegratedTabBase', 'ITabIntegration',
    'MediaLibraryIntegration', 'PlayoutIntegration',
    'StreamingIntegration', 'SchedulerIntegration',
    
    # Workflows and messages
    'PracticalWorkflows',
    'MongolianSystemMessages',
    
    # Configuration and setup
    'IntegrationConfig',
    'StreamingStudioIntegration',
    'setup_integration_system',
    'quick_setup',
    
    # Tab creators
    'create_integrated_media_library_tab',
    'create_integrated_playout_tab',
    'create_integrated_streaming_tab', 
    'create_integrated_scheduler_tab',
    'create_basic_integrated_tab'
]

# =============================================================================
# ui/integration/__init__.py  
# =============================================================================

"""
UI Integration Components

This package provides enhanced UI components and dialogs for the integration system.
"""

# This would be populated when you create the UI integration components

__all__ = []

# =============================================================================
# examples/__init__.py
# =============================================================================

"""
Integration System Examples

This package contains example implementations and usage patterns for the integration system.
"""

# This would be populated when you create the example files

__all__ = []

