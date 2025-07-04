#!/usr/bin/env python3
"""
core/integration/workflows.py
Practical workflow definitions for TV streaming operations
"""

from .workflow_engine import Workflow, WorkflowStep

# =============================================================================
# PRACTICAL WORKFLOWS FOR TV STREAMING
# =============================================================================

class PracticalWorkflows:
    """Practical workflow examples for TV streaming"""
    
    @staticmethod
    def create_media_to_air_workflow() -> Workflow:
        """Complete media-to-air workflow"""
        return Workflow(
            name="complete_media_to_air",
            description="Load media, prepare audio, cue preview, and take to air",
            steps=[
                WorkflowStep("load_media", "media_library", "load_file", 
                           {"auto_metadata": True}, wait_for_completion=True),
                WorkflowStep("setup_audio", "playout", "setup_audio_profile", 
                           {"profile": "broadcast"}, wait_for_completion=True),
                WorkflowStep("cue_preview", "playout", "load_to_preview", 
                           wait_for_completion=True),
                WorkflowStep("audio_check", "playout", "verify_audio_levels", 
                           wait_for_completion=True, timeout=10),
                WorkflowStep("take_to_air", "playout", "take_to_air", 
                           {"fade_duration": 1.0}, wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_live_streaming_workflow() -> Workflow:
        """Live streaming preparation workflow"""
        return Workflow(
            name="live_streaming_setup",
            description="Prepare and start live streaming with quality adaptation",
            steps=[
                WorkflowStep("check_network", "streaming", "check_network_status", 
                           wait_for_completion=True, timeout=15),
                WorkflowStep("optimize_quality", "streaming", "optimize_stream_quality", 
                           {"adaptive": True}, wait_for_completion=True),
                WorkflowStep("prepare_servers", "streaming", "prepare_all_servers", 
                           wait_for_completion=True, timeout=20),
                WorkflowStep("start_primary", "streaming", "start_stream", 
                           {"server": "primary", "priority": "high"}, wait_for_completion=True),
                WorkflowStep("start_backup", "streaming", "start_stream", 
                           {"server": "backup", "priority": "medium"}, wait_for_completion=False),
                WorkflowStep("notify_live", "playout", "set_live_indicator", 
                           {"status": "streaming"}, wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_scheduled_broadcast_workflow() -> Workflow:
        """Scheduled broadcast workflow"""
        return Workflow(
            name="scheduled_broadcast",
            description="Execute scheduled broadcast with full automation",
            steps=[
                WorkflowStep("pre_check", "scheduler", "verify_schedule", 
                           wait_for_completion=True, timeout=10),
                WorkflowStep("load_playlist", "media_library", "load_playlist", 
                           wait_for_completion=True),
                WorkflowStep("audio_setup", "playout", "configure_broadcast_audio", 
                           wait_for_completion=True),
                WorkflowStep("start_streaming", "streaming", "start_scheduled_streams", 
                           wait_for_completion=True),
                WorkflowStep("begin_playout", "playout", "start_automated_playout", 
                           wait_for_completion=False),
                WorkflowStep("monitor_streams", "streaming", "enable_stream_monitoring", 
                           {"interval": 30}, wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_emergency_procedures_workflow() -> Workflow:
        """Emergency procedures workflow"""
        return Workflow(
            name="emergency_procedures",
            description="Emergency stop and fallback procedures",
            steps=[
                WorkflowStep("stop_all_streams", "streaming", "emergency_stop_streams", 
                           wait_for_completion=False, timeout=5),
                WorkflowStep("stop_playout", "playout", "emergency_stop", 
                           wait_for_completion=False, timeout=5),
                WorkflowStep("load_fallback", "media_library", "load_emergency_content", 
                           wait_for_completion=True, timeout=10),
                WorkflowStep("restore_playout", "playout", "load_to_program", 
                           {"content": "emergency_slate"}, wait_for_completion=True),
                WorkflowStep("take_emergency", "playout", "take_to_air", 
                           {"immediate": True}, wait_for_completion=False),
                WorkflowStep("notify_operators", "scheduler", "send_emergency_alert", 
                           wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_quality_adaptive_workflow() -> Workflow:
        """Quality adaptation workflow for poor network conditions"""
        return Workflow(
            name="quality_adaptive_streaming",
            description="Automatically adapt streaming quality based on network conditions",
            steps=[
                WorkflowStep("network_test", "streaming", "test_network_bandwidth", 
                           wait_for_completion=True, timeout=10),
                WorkflowStep("calculate_optimal", "streaming", "calculate_optimal_quality", 
                           wait_for_completion=True),
                WorkflowStep("adjust_encoder", "streaming", "adjust_encoder_settings", 
                           wait_for_completion=True),
                WorkflowStep("update_bitrate", "streaming", "update_stream_bitrate", 
                           wait_for_completion=True),
                WorkflowStep("verify_stability", "streaming", "verify_stream_stability", 
                           wait_for_completion=True, timeout=15),
                WorkflowStep("notify_quality_change", "playout", "show_quality_indicator", 
                           wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_auto_recovery_workflow() -> Workflow:
        """Auto-recovery workflow for stream failures"""
        return Workflow(
            name="stream_auto_recovery",
            description="Automatically recover from stream failures",
            steps=[
                WorkflowStep("detect_failure", "streaming", "detect_stream_failure", 
                           wait_for_completion=True, timeout=5),
                WorkflowStep("stop_failed_stream", "streaming", "stop_failed_stream", 
                           wait_for_completion=True, timeout=5),
                WorkflowStep("switch_to_backup", "streaming", "activate_backup_stream", 
                           wait_for_completion=True, timeout=10),
                WorkflowStep("restart_primary", "streaming", "restart_primary_stream", 
                           wait_for_completion=True, timeout=15),
                WorkflowStep("monitor_recovery", "streaming", "monitor_stream_health", 
                           {"duration": 60}, wait_for_completion=False),
                WorkflowStep("log_incident", "scheduler", "log_recovery_incident", 
                           wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_daily_startup_workflow() -> Workflow:
        """Daily system startup and checks workflow"""
        return Workflow(
            name="daily_system_startup",
            description="Complete daily system startup with all checks",
            steps=[
                WorkflowStep("system_check", "scheduler", "perform_system_health_check", 
                           wait_for_completion=True, timeout=30),
                WorkflowStep("load_schedule", "scheduler", "load_daily_schedule", 
                           wait_for_completion=True),
                WorkflowStep("prepare_media", "media_library", "scan_and_verify_media", 
                           wait_for_completion=True, timeout=60),
                WorkflowStep("test_streaming", "streaming", "test_all_stream_servers", 
                           wait_for_completion=True, timeout=45),
                WorkflowStep("audio_calibration", "playout", "calibrate_audio_levels", 
                           wait_for_completion=True, timeout=20),
                WorkflowStep("enable_automation", "scheduler", "enable_daily_automation", 
                           wait_for_completion=False),
                WorkflowStep("notify_ready", "scheduler", "send_system_ready_notification", 
                           wait_for_completion=False)
            ]
        )
    
    @staticmethod
    def create_end_of_day_workflow() -> Workflow:
        """End of day shutdown and archival workflow"""
        return Workflow(
            name="end_of_day_shutdown",
            description="Safe shutdown with data archival and cleanup",
            steps=[
                WorkflowStep("disable_automation", "scheduler", "disable_automation", 
                           wait_for_completion=True),
                WorkflowStep("finish_scheduled", "scheduler", "complete_remaining_events", 
                           wait_for_completion=True, timeout=300),
                WorkflowStep("stop_streams_graceful", "streaming", "graceful_stream_shutdown", 
                           wait_for_completion=True, timeout=30),
                WorkflowStep("archive_logs", "scheduler", "archive_daily_logs", 
                           wait_for_completion=True, timeout=60),
                WorkflowStep("backup_settings", "scheduler", "backup_system_configuration", 
                           wait_for_completion=True, timeout=30),
                WorkflowStep("cleanup_temp", "media_library", "cleanup_temporary_files", 
                           wait_for_completion=True),
                WorkflowStep("system_shutdown", "scheduler", "prepare_system_shutdown", 
                           wait_for_completion=False)
            ]
        )