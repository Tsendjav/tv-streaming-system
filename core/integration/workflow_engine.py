#!/usr/bin/env python3
"""
core/integration/workflow_engine.py
Cross-tab workflow execution engine
"""

from datetime import datetime
from typing import Dict, List, Any

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# =============================================================================
# WORKFLOW SYSTEM
# =============================================================================

class WorkflowStep:
    """Single step in a workflow"""
    def __init__(self, name: str, tab: str, command: str, params: Dict[str, Any] = None, 
                 wait_for_completion: bool = True, timeout: int = 30):
        self.name = name
        self.tab = tab
        self.command = command
        self.params = params or {}
        self.wait_for_completion = wait_for_completion
        self.timeout = timeout

class Workflow:
    """Multi-tab workflow definition"""
    def __init__(self, name: str, steps: List[WorkflowStep], description: str = ""):
        self.name = name
        self.steps = steps
        self.description = description

class WorkflowEngine(QObject):
    """Executes cross-tab workflows with complete automation"""
    
    workflow_started = pyqtSignal(str)
    workflow_completed = pyqtSignal(str, bool)
    workflow_step_completed = pyqtSignal(str, str, bool)
    
    def __init__(self, integration_manager):
        super().__init__()
        self.integration_manager = integration_manager
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, Dict[str, Any]] = {}
        self.logger = self._get_logger()
        
        # Setup default workflows
        self._setup_default_workflows()
    
    def _get_logger(self):
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    def _setup_default_workflows(self):
        """Setup default cross-tab workflows"""
        
        # 1. Media to Air Workflow
        media_to_air = Workflow(
            name="media_to_air",
            description="Load media file and take to air automatically",
            steps=[
                WorkflowStep("load_media", "media_library", "load_file", wait_for_completion=True),
                WorkflowStep("cue_preview", "playout", "load_to_preview", wait_for_completion=True),
                WorkflowStep("take_to_air", "playout", "take_to_air", wait_for_completion=False)
            ]
        )
        self.register_workflow(media_to_air)
        
        # 2. Scheduled Stream Workflow
        scheduled_stream = Workflow(
            name="scheduled_stream",
            description="Start streaming at scheduled time",
            steps=[
                WorkflowStep("prepare_stream", "streaming", "prepare_stream_config", wait_for_completion=True),
                WorkflowStep("start_stream", "streaming", "start_stream", wait_for_completion=True),
                WorkflowStep("notify_live", "playout", "set_live_status", wait_for_completion=False)
            ]
        )
        self.register_workflow(scheduled_stream)
        
        # 3. Emergency Stop Workflow
        emergency_stop = Workflow(
            name="emergency_stop",
            description="Emergency stop all operations",
            steps=[
                WorkflowStep("stop_streams", "streaming", "stop_all_streams", wait_for_completion=False, timeout=5),
                WorkflowStep("stop_playout", "playout", "emergency_stop", wait_for_completion=False, timeout=5),
                WorkflowStep("disable_scheduler", "scheduler", "disable_automation", wait_for_completion=False, timeout=5)
            ]
        )
        self.register_workflow(emergency_stop)
        
        # 4. Quality Adaptive Workflow
        quality_adaptive = Workflow(
            name="quality_adaptive",
            description="Automatically adjust stream quality based on network conditions",
            steps=[
                WorkflowStep("check_network", "streaming", "check_network_status", wait_for_completion=True),
                WorkflowStep("adjust_quality", "streaming", "adjust_stream_quality", wait_for_completion=True),
                WorkflowStep("notify_change", "playout", "update_quality_display", wait_for_completion=False)
            ]
        )
        self.register_workflow(quality_adaptive)
    
    def register_workflow(self, workflow: Workflow):
        """Register a new workflow"""
        self.workflows[workflow.name] = workflow
        self.logger.info(f"Registered workflow: {workflow.name}")
    
    def execute_workflow(self, workflow_name: str, params: Dict[str, Any] = None) -> str:
        """Execute a workflow and return execution ID"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        workflow = self.workflows[workflow_name]
        execution_id = f"{workflow_name}_{int(datetime.now().timestamp())}"
        
        self.running_workflows[execution_id] = {
            "workflow": workflow,
            "params": params or {},
            "current_step": 0,
            "start_time": datetime.now(),
            "status": "running"
        }
        
        self.workflow_started.emit(execution_id)
        self.logger.info(f"Started workflow execution: {execution_id}")
        
        # Start first step
        QTimer.singleShot(100, lambda: self._execute_next_step(execution_id))
        
        return execution_id
    
    def _execute_next_step(self, execution_id: str):
        """Execute next step in workflow"""
        if execution_id not in self.running_workflows:
            return
        
        workflow_data = self.running_workflows[execution_id]
        workflow = workflow_data["workflow"]
        current_step_index = workflow_data["current_step"]
        
        if current_step_index >= len(workflow.steps):
            # Workflow completed
            self._complete_workflow(execution_id, True)
            return
        
        step = workflow.steps[current_step_index]
        
        try:
            # Execute step
            params = workflow_data["params"].copy()
            params.update(step.params)
            
            result = self.integration_manager.send_command_to_tab(
                step.tab, step.command, params
            )
            
            if result.get("error"):
                self.logger.error(f"Step {step.name} failed: {result['error']}")
                self.workflow_step_completed.emit(execution_id, step.name, False)
                self._complete_workflow(execution_id, False)
                return
            
            self.logger.info(f"Step {step.name} completed successfully")
            self.workflow_step_completed.emit(execution_id, step.name, True)
            
            # Move to next step
            workflow_data["current_step"] += 1
            
            if step.wait_for_completion:
                # Wait before next step
                QTimer.singleShot(500, lambda: self._execute_next_step(execution_id))
            else:
                # Execute immediately
                self._execute_next_step(execution_id)
                
        except Exception as e:
            self.logger.error(f"Error executing step {step.name}: {e}")
            self.workflow_step_completed.emit(execution_id, step.name, False)
            self._complete_workflow(execution_id, False)
    
    def _complete_workflow(self, execution_id: str, success: bool):
        """Complete workflow execution"""
        if execution_id in self.running_workflows:
            workflow_data = self.running_workflows[execution_id]
            workflow_data["status"] = "completed" if success else "failed"
            workflow_data["end_time"] = datetime.now()
            
            self.workflow_completed.emit(execution_id, success)
            self.logger.info(f"Workflow {execution_id} {'completed' if success else 'failed'}")
            
            # Clean up after some time
            QTimer.singleShot(60000, lambda: self.running_workflows.pop(execution_id, None))