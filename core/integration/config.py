#!/usr/bin/env python3
"""
core/integration/config.py
Configuration management for the integration system
"""

from typing import Dict, Any

# =============================================================================
# INTEGRATION CONFIGURATION
# =============================================================================

class IntegrationConfig:
    """Configuration class for integration system"""
    
    def __init__(self):
        # Core system settings
        self.monitoring_enabled = True
        self.monitoring_interval = 5000  # ms
        self.automation_enabled = True
        self.emergency_auto_recovery = True
        self.event_history_limit = 1000
        self.performance_history_limit = 1000
        
        # Alert thresholds
        self.alert_thresholds = {
            "audio_level_low": -40.0,      # dB
            "memory_usage_high": 85.0,     # %
            "cpu_usage_high": 80.0,        # %
            "network_latency_high": 500.0, # ms
            "stream_bitrate_drop": 0.8,    # ratio
            "dropped_frames_high": 5.0,    # %
            "disk_space_low": 90.0,        # % (high usage = low space)
            "stream_disconnect": 1,        # any disconnect
            "playout_stopped": 1           # unexpected stop
        }
        
        # Workflow settings
        self.workflow_timeout_default = 30  # seconds
        self.workflow_retry_attempts = 3
        self.workflow_retry_delay = 5000    # ms
        
        # Auto-recovery settings
        self.auto_recovery_enabled = True
        self.auto_recovery_max_attempts = 3
        self.auto_recovery_delay = 10000    # ms
        
        # Stream quality settings
        self.adaptive_quality_enabled = True
        self.quality_check_interval = 30000  # ms
        self.minimum_quality = "480p"
        self.maximum_quality = "1080p"
        self.default_quality = "720p"
        
        # Audio settings
        self.audio_monitoring_enabled = True
        self.audio_level_check_interval = 1000  # ms
        self.audio_silence_threshold = -60.0     # dB
        self.audio_peak_threshold = -3.0         # dB
        
        # Network settings
        self.network_monitoring_enabled = True
        self.network_check_interval = 10000      # ms
        self.connection_timeout = 5000           # ms
        self.bandwidth_test_servers = [
            "8.8.8.8",
            "1.1.1.1",
            "208.67.222.222"
        ]
        
        # Language settings
        self.language = "mongolian"
        self.use_localized_messages = True
        self.date_format = "%Y-%m-%d %H:%M:%S"
        
        # Logging settings
        self.log_level = "INFO"
        self.log_to_file = True
        self.log_file_max_size = 10 * 1024 * 1024  # 10MB
        self.log_backup_count = 5
        
        # Tab-specific settings
        self.tab_settings = {
            "media_library": {
                "auto_scan_enabled": True,
                "scan_interval": 300000,  # 5 minutes
                "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
                "thumbnail_generation": True
            },
            "playout": {
                "auto_cue_enabled": True,
                "fade_duration": 1.0,  # seconds
                "preview_auto_load": True,
                "audio_monitoring": True
            },
            "streaming": {
                "auto_start_on_take": False,
                "quality_adaptation": True,
                "backup_streams": True,
                "stream_health_check": True
            },
            "scheduler": {
                "automation_enabled": True,
                "look_ahead_time": 300,  # seconds
                "auto_execute": True,
                "conflict_resolution": "warn"
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "monitoring_interval": self.monitoring_interval,
            "automation_enabled": self.automation_enabled,
            "emergency_auto_recovery": self.emergency_auto_recovery,
            "event_history_limit": self.event_history_limit,
            "performance_history_limit": self.performance_history_limit,
            "alert_thresholds": self.alert_thresholds,
            "workflow_timeout_default": self.workflow_timeout_default,
            "workflow_retry_attempts": self.workflow_retry_attempts,
            "workflow_retry_delay": self.workflow_retry_delay,
            "auto_recovery_enabled": self.auto_recovery_enabled,
            "auto_recovery_max_attempts": self.auto_recovery_max_attempts,
            "auto_recovery_delay": self.auto_recovery_delay,
            "adaptive_quality_enabled": self.adaptive_quality_enabled,
            "quality_check_interval": self.quality_check_interval,
            "minimum_quality": self.minimum_quality,
            "maximum_quality": self.maximum_quality,
            "default_quality": self.default_quality,
            "audio_monitoring_enabled": self.audio_monitoring_enabled,
            "audio_level_check_interval": self.audio_level_check_interval,
            "audio_silence_threshold": self.audio_silence_threshold,
            "audio_peak_threshold": self.audio_peak_threshold,
            "network_monitoring_enabled": self.network_monitoring_enabled,
            "network_check_interval": self.network_check_interval,
            "connection_timeout": self.connection_timeout,
            "bandwidth_test_servers": self.bandwidth_test_servers,
            "language": self.language,
            "use_localized_messages": self.use_localized_messages,
            "date_format": self.date_format,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_file_max_size": self.log_file_max_size,
            "log_backup_count": self.log_backup_count,
            "tab_settings": self.tab_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntegrationConfig':
        """Create config from dictionary"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    def get_tab_setting(self, tab_name: str, setting_name: str, default: Any = None) -> Any:
        """Get tab-specific setting"""
        if tab_name in self.tab_settings:
            return self.tab_settings[tab_name].get(setting_name, default)
        return default
    
    def set_tab_setting(self, tab_name: str, setting_name: str, value: Any):
        """Set tab-specific setting"""
        if tab_name not in self.tab_settings:
            self.tab_settings[tab_name] = {}
        self.tab_settings[tab_name][setting_name] = value
    
    def get_alert_threshold(self, alert_type: str, default: float = 0.0) -> float:
        """Get alert threshold value"""
        return self.alert_thresholds.get(alert_type, default)
    
    def set_alert_threshold(self, alert_type: str, threshold: float):
        """Set alert threshold value"""
        self.alert_thresholds[alert_type] = threshold
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        feature_mapping = {
            "monitoring": self.monitoring_enabled,
            "automation": self.automation_enabled,
            "auto_recovery": self.auto_recovery_enabled,
            "adaptive_quality": self.adaptive_quality_enabled,
            "audio_monitoring": self.audio_monitoring_enabled,
            "network_monitoring": self.network_monitoring_enabled,
            "localized_messages": self.use_localized_messages
        }
        return feature_mapping.get(feature_name, False)
    
    def validate(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate intervals
        if self.monitoring_interval < 1000:
            issues.append("Monitoring interval too low (minimum: 1000ms)")
        
        if self.workflow_timeout_default < 5:
            issues.append("Workflow timeout too low (minimum: 5 seconds)")
        
        # Validate thresholds
        if self.alert_thresholds.get("audio_level_low", 0) > -10:
            issues.append("Audio level threshold too high")
        
        if self.alert_thresholds.get("memory_usage_high", 0) > 95:
            issues.append("Memory usage threshold too high")
        
        # Validate quality settings
        quality_levels = ["480p", "720p", "1080p", "1440p", "2160p"]
        if self.minimum_quality not in quality_levels:
            issues.append(f"Invalid minimum quality: {self.minimum_quality}")
        
        if self.maximum_quality not in quality_levels:
            issues.append(f"Invalid maximum quality: {self.maximum_quality}")
        
        # Validate language
        supported_languages = ["mongolian", "english"]
        if self.language not in supported_languages:
            issues.append(f"Unsupported language: {self.language}")
        
        return issues
    
    def apply_defaults_for_broadcasting(self):
        """Apply optimized defaults for broadcasting environment"""
        # More strict monitoring for broadcast
        self.monitoring_interval = 2000  # 2 seconds
        self.alert_thresholds["audio_level_low"] = -35.0  # Stricter audio monitoring
        self.alert_thresholds["stream_bitrate_drop"] = 0.9  # Less tolerance for bitrate drops
        
        # Enable all critical features
        self.monitoring_enabled = True
        self.automation_enabled = True
        self.auto_recovery_enabled = True
        self.audio_monitoring_enabled = True
        self.network_monitoring_enabled = True
        
        # Conservative workflow settings
        self.workflow_timeout_default = 45  # More time for critical operations
        self.workflow_retry_attempts = 5    # More retries for broadcast
        
        # Tab-specific broadcast settings
        self.tab_settings["playout"]["fade_duration"] = 0.5  # Faster fades
        self.tab_settings["streaming"]["auto_start_on_take"] = True  # Auto-stream on take
        self.tab_settings["scheduler"]["look_ahead_time"] = 600  # 10 minutes lookahead
    
    def apply_defaults_for_testing(self):
        """Apply relaxed defaults for testing environment"""
        # Relaxed monitoring for testing
        self.monitoring_interval = 10000  # 10 seconds
        self.alert_thresholds["audio_level_low"] = -50.0  # Relaxed audio monitoring
        self.alert_thresholds["memory_usage_high"] = 95.0  # Higher memory tolerance
        
        # Disable auto-recovery for predictable testing
        self.auto_recovery_enabled = False
        
        # Faster workflows for testing
        self.workflow_timeout_default = 15  # Shorter timeouts
        self.workflow_retry_attempts = 1    # Fewer retries
        
        # Test-friendly tab settings
        self.tab_settings["media_library"]["auto_scan_enabled"] = False
        self.tab_settings["streaming"]["quality_adaptation"] = False