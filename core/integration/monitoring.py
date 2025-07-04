#!/usr/bin/env python3
"""
core/integration/monitoring.py
Real-time system monitoring and alerting
"""

import time
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Conditional import for psutil
try:
    import psutil
except ImportError:
    psutil = None

# =============================================================================
# SYSTEM MONITORING
# =============================================================================

class SystemMonitor(QObject):
    """Real-time system monitoring with alerts and auto-recovery capabilities."""

    # Monitoring signals
    alert_triggered = pyqtSignal(str, str, int)  # alert_type, message, severity
    performance_update = pyqtSignal(dict)
    system_health_changed = pyqtSignal(str)  # health_status

    def __init__(self, integration_system):
        super().__init__()
        self.integration_system = integration_system
        self.logger = self._get_logger()

        # Monitoring state
        self.monitoring_active = False
        self.performance_metrics = {}
        self.alert_thresholds = self._setup_alert_thresholds()
        self.last_health_check = datetime.now()

        # Monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._perform_monitoring_cycle)

        # Performance tracking
        self.performance_history = []
        self.max_history_size = 1000

    def _get_logger(self):
        """Initializes and returns a logger instance."""
        try:
            from core.logging import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            return logging.getLogger(__name__)

    def _setup_alert_thresholds(self) -> Dict[str, Any]:
        """Configures and returns a dictionary of alert thresholds."""
        return {
            "stream_bitrate_drop": {"threshold": 0.8, "severity": 2},  # 80% of target
            "audio_level_low": {"threshold": -40, "severity": 1},      # -40dB
            "network_latency_high": {"threshold": 500, "severity": 2}, # 500ms
            "dropped_frames_high": {"threshold": 5.0, "severity": 3},  # 5% drop rate
            "disk_space_low": {"threshold": 90.0, "severity": 3},      # 90% usage (low space means high usage)
            "memory_usage_high": {"threshold": 85.0, "severity": 2},   # 85% usage
            "stream_disconnect": {"threshold": 1, "severity": 3},      # Any disconnect
            "playout_stopped": {"threshold": 1, "severity": 3}         # Unexpected stop
        }

    def start_monitoring(self, interval_ms: int = 5000):
        """Start the real-time system monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_timer.start(interval_ms)
            self.logger.info(f"System monitoring started (interval: {interval_ms}ms)")
        else:
            self.logger.info("System monitoring is already active.")

    def stop_monitoring(self):
        """Stop the real-time system monitoring."""
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitor_timer.stop()
            self.logger.info("System monitoring stopped")
        else:
            self.logger.info("System monitoring is not active.")

    def _perform_monitoring_cycle(self):
        """Perform one complete cycle of monitoring."""
        try:
            current_time = datetime.now()

            # Collect metrics
            metrics = self._collect_system_metrics()

            # Update performance metrics
            self.performance_metrics.update(metrics)
            self.performance_metrics["timestamp"] = current_time.isoformat()

            # Store in history
            self.performance_history.append(self.performance_metrics.copy())
            if len(self.performance_history) > self.max_history_size:
                self.performance_history.pop(0)

            # Check alerts
            self._check_alerts(metrics)

            # Emit performance update
            self.performance_update.emit(self.performance_metrics.copy())

            # Update health status
            health_status = self._calculate_health_status(metrics)
            self.system_health_changed.emit(health_status)

            self.last_health_check = current_time

        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics from various sources."""
        metrics = {}
        try:
            # Stream metrics
            streams = self.integration_system.shared_data.get_active_streams()
            metrics["active_streams"] = len(streams)
            metrics["total_bitrate"] = sum(
                self._parse_bitrate(stream.bitrate) for stream in streams.values()
            )

            # Playout metrics
            playout_state = self.integration_system.shared_data.get_playout_state()
            metrics["playout_live"] = playout_state.is_live
            metrics["preview_loaded"] = playout_state.preview_media is not None
            metrics["program_loaded"] = playout_state.program_media is not None

            # Audio metrics
            audio_state = self.integration_system.shared_data.get_audio_state()
            metrics["audio_levels"] = audio_state.get("levels", {"left": 0, "right": 0})
            metrics["audio_muted"] = audio_state.get("muted", False)

            # Internal system metrics
            metrics["event_queue_size"] = len(self.integration_system.event_bus.event_history)
            metrics["registered_tabs"] = len(self.integration_system.tabs)
            metrics["running_workflows"] = len(self.integration_system.workflow_engine.running_workflows)

            # Performance metrics
            metrics["cpu_usage"] = self._get_cpu_usage()
            metrics["memory_usage"] = self._get_memory_usage()
            metrics["disk_usage"] = self._get_disk_usage()
            metrics["network_latency"] = self._get_network_latency()

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            metrics["collection_error"] = str(e)

        return metrics

    def _parse_bitrate(self, bitrate_str: str) -> float:
        """Parse a bitrate string into float in kbps."""
        try:
            if "kbps" in bitrate_str.lower():
                return float(bitrate_str.lower().replace("kbps", "").strip())
            elif "mbps" in bitrate_str.lower():
                return float(bitrate_str.lower().replace("mbps", "").strip()) * 1000
            return 0.0
        except ValueError:
            self.logger.warning(f"Failed to parse bitrate string: '{bitrate_str}'. Returning 0.0.")
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage using psutil."""
        if psutil:
            return psutil.cpu_percent(interval=0.1)
        return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage using psutil."""
        if psutil:
            return psutil.virtual_memory().percent
        return 0.0

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage using psutil."""
        if psutil:
            return psutil.disk_usage('/').percent
        return 0.0

    def _get_network_latency(self) -> float:
        """Measure network latency by connecting to a reliable server."""
        try:
            start_time = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            latency_ms = (time.time() - start_time) * 1000
            return latency_ms
        except Exception as e:
            self.logger.warning(f"Network latency measurement failed: {e}")
            return 50.0

    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check collected metrics against alert thresholds."""
        try:
            from .messages import MongolianSystemMessages
            
            expected_bitrate = self.integration_system.shared_data.get_config("expected_bitrate", 2500)

            # Stream bitrate drop
            if metrics.get("total_bitrate", 0) < expected_bitrate * self.alert_thresholds["stream_bitrate_drop"]["threshold"]:
                self._trigger_alert(
                    "stream_bitrate_drop",
                    MongolianSystemMessages.get_message("alert_stream_disconnect", stream_key="Бүх стрим"),
                    self.alert_thresholds["stream_bitrate_drop"]["severity"]
                )

            # Audio levels
            audio_levels = metrics.get("audio_levels", {})
            for channel, level in audio_levels.items():
                if level < self.alert_thresholds["audio_level_low"]["threshold"]:
                    self._trigger_alert(
                        "audio_level_low",
                        MongolianSystemMessages.get_message("alert_audio_low", level=level, channel=channel.capitalize()),
                        self.alert_thresholds["audio_level_low"]["severity"]
                    )

            # Network latency
            latency = metrics.get("network_latency", 0)
            if latency > self.alert_thresholds["network_latency_high"]["threshold"]:
                self._trigger_alert(
                    "network_latency_high",
                    MongolianSystemMessages.get_message("alert_network_slow", latency=f"{latency:.1f}"),
                    self.alert_thresholds["network_latency_high"]["severity"]
                )

            # Memory usage
            memory_usage = metrics.get("memory_usage", 0)
            if memory_usage > self.alert_thresholds["memory_usage_high"]["threshold"]:
                self._trigger_alert(
                    "memory_usage_high",
                    MongolianSystemMessages.get_message("alert_memory_high", usage=memory_usage),
                    self.alert_thresholds["memory_usage_high"]["severity"]
                )

        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")

    def _trigger_alert(self, alert_type: str, message: str, severity: int):
        """Trigger a system alert."""
        self.logger.warning(f"ALERT [{alert_type}] Severity {severity}: {message}")
        self.alert_triggered.emit(alert_type, message, severity)

        # Attempt auto-recovery for critical alerts
        if severity >= 3:
            self._attempt_auto_recovery(alert_type)

    def _attempt_auto_recovery(self, alert_type: str):
        """Attempt automatic recovery for critical alerts."""
        try:
            if alert_type == "stream_disconnect":
                self.logger.info("Attempting stream recovery workflow.")
                self.integration_system.execute_workflow("emergency_stream_recovery")
            elif alert_type == "playout_stopped":
                self.logger.info("Attempting playout recovery workflow.")
                self.integration_system.execute_workflow("emergency_playout_recovery")
            
        except Exception as e:
            self.logger.error(f"Auto-recovery failed for {alert_type}: {e}")

    def _calculate_health_status(self, metrics: Dict[str, Any]) -> str:
        """Calculate the overall system health status."""
        try:
            # Check for critical conditions
            if metrics.get("active_streams", 0) == 0 and metrics.get("program_loaded", False):
                return "critical"
            
            if not metrics.get("playout_live", False) and metrics.get("program_loaded", False):
                return "critical"

            # Check for warning conditions
            if (metrics.get("memory_usage", 0) > self.alert_thresholds["memory_usage_high"]["threshold"] or
                metrics.get("network_latency", 0) > self.alert_thresholds["network_latency_high"]["threshold"] or
                metrics.get("cpu_usage", 0) > 80):
                return "warning"

            # Check for good conditions
            expected_bitrate = self.integration_system.shared_data.get_config("expected_bitrate", 2500)
            if (metrics.get("total_bitrate", 0) < expected_bitrate * 0.9 or
                any(level < -30 for level in metrics.get("audio_levels", {}).values())):
                return "good"
            
            return "excellent"

        except Exception as e:
            self.logger.error(f"Error calculating health status: {e}")
            return "unknown"

    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary over the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_metrics = [
            m for m in self.performance_history
            if "timestamp" in m and datetime.fromisoformat(m["timestamp"]) >= cutoff_time
        ]

        if not recent_metrics:
            return {"error": "No metrics available for specified period"}

        # Calculate averages and statistics
        summary = {
            "period_hours": hours,
            "sample_count": len(recent_metrics),
            "avg_cpu_usage": sum(m.get("cpu_usage", 0) for m in recent_metrics) / len(recent_metrics),
            "avg_memory_usage": sum(m.get("memory_usage", 0) for m in recent_metrics) / len(recent_metrics),
            "max_active_streams": max(m.get("active_streams", 0) for m in recent_metrics),
            "total_uptime_minutes": (len(recent_metrics) * 5) / 60,  # Assuming 5-second intervals
            "stream_stability_percentage": self._calculate_stream_stability(recent_metrics),
            "playout_uptime_percentage": self._calculate_playout_uptime(recent_metrics)
        }

        return summary

    def _calculate_stream_stability(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate the percentage of time active streams were detected."""
        if not metrics:
            return 0.0

        stable_samples = sum(1 for m in metrics if m.get("active_streams", 0) > 0)
        return (stable_samples / len(metrics)) * 100

    def _calculate_playout_uptime(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate the percentage of time playout was live."""
        if not metrics:
            return 0.0

        live_samples = sum(1 for m in metrics if m.get("playout_live", False))
        return (live_samples / len(metrics)) * 100