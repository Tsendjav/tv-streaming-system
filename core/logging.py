# tv_streaming_system/core/logging.py
#!/usr/bin/env python3
"""
Logging Setup and Configuration
Provides centralized logging configuration for the application
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import os
import re

# constants.py-г core.constants-руу шилжүүлсэн тул импортыг өөрчилсөн.
from core.constants import LOG_LEVELS, DEFAULT_DIRECTORIES, MAX_LOG_FILE_SIZE_MB, MAX_LOG_FILES


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class LogManager:
    """Centralized logging manager for the application"""

    def __init__(self, app_name: str = "StreamingStudio"):
        self.app_name = app_name
        self.log_dir = Path(DEFAULT_DIRECTORIES["logs"])
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        self._setup_directories()

    def _setup_directories(self):
        """Ensure log directories exist"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self, level: str = "INFO", console_output: bool = True,
                      file_output: bool = True, performance_log: bool = True,
                      audit_log: bool = True, debug_log: bool = False) -> bool:
        """
        Set up the main logging configuration for the application.

        Args:
            level (str): The default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            console_output (bool): Enable/disable console output.
            file_output (bool): Enable/disable main file output.
            performance_log (bool): Enable/disable separate performance log.
            audit_log (bool): Enable/disable separate audit log.
            debug_log (bool): Enable/disable detailed debug log (can be verbose).
        Returns:
            bool: True if logging setup was successful, False otherwise.
        """
        try:
            # Clear existing handlers to prevent duplicates if called multiple times
            for logger in self.loggers.values():
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
            self.handlers.clear()
            self.loggers.clear()

            # Root logger configuration
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG) # Set root to DEBUG to capture all messages

            # Formatters
            console_formatter = ColoredFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                                                 datefmt='%Y-%m-%d %H:%M:%S')
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            detailed_formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s',
                                                   datefmt='%Y-%m-%d %H:%M:%S')

            # Console Handler
            if console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)
                self.handlers['console'] = console_handler

            # Main File Handler (Rotating)
            if file_output:
                main_log_path = self.log_dir / f"{self.app_name.lower().replace(' ', '_')}.log"
                main_file_handler = logging.handlers.RotatingFileHandler(
                    main_log_path,
                    maxBytes=MAX_LOG_FILE_SIZE_MB * 1024 * 1024,
                    backupCount=MAX_LOG_FILES,
                    encoding='utf-8'
                )
                main_file_handler.setLevel(level)
                main_file_handler.setFormatter(file_formatter)
                root_logger.addHandler(main_file_handler)
                self.handlers['main_file'] = main_file_handler

            # Performance Log Handler
            if performance_log:
                perf_log_path = self.log_dir / "performance.log"
                perf_file_handler = logging.handlers.RotatingFileHandler(
                    perf_log_path,
                    maxBytes=MAX_LOG_FILE_SIZE_MB * 1024 * 1024,
                    backupCount=MAX_LOG_FILES,
                    encoding='utf-8'
                )
                perf_file_handler.setLevel(logging.INFO) # Performance logs are usually INFO
                perf_file_handler.setFormatter(file_formatter)
                performance_logger = logging.getLogger('performance')
                performance_logger.addHandler(perf_file_handler)
                performance_logger.propagate = False # Prevent performance logs from going to root
                self.loggers['performance'] = performance_logger
                self.handlers['performance'] = perf_file_handler

            # Audit Log Handler
            if audit_log:
                audit_log_path = self.log_dir / "audit.log"
                audit_file_handler = logging.handlers.RotatingFileHandler(
                    audit_log_path,
                    maxBytes=MAX_LOG_FILE_SIZE_MB * 1024 * 1024,
                    backupCount=MAX_LOG_FILES,
                    encoding='utf-8'
                )
                audit_file_handler.setLevel(logging.INFO) # Audit logs are usually INFO
                audit_file_handler.setFormatter(file_formatter)
                audit_logger = logging.getLogger('audit')
                audit_logger.addHandler(audit_file_handler)
                audit_logger.propagate = False # Prevent audit logs from going to root
                self.loggers['audit'] = audit_logger
                self.handlers['audit'] = audit_file_handler

            # Debug Log Handler (more verbose, separate file)
            if debug_log:
                debug_log_path = self.log_dir / "debug.log"
                debug_file_handler = logging.handlers.RotatingFileHandler(
                    debug_log_path,
                    maxBytes=MAX_LOG_FILE_SIZE_MB * 1024 * 1024 * 5, # Larger debug log
                    backupCount=MAX_LOG_FILES,
                    encoding='utf-8'
                )
                debug_file_handler.setLevel(logging.DEBUG)
                debug_file_handler.setFormatter(detailed_formatter)
                debug_logger = logging.getLogger('debug')
                debug_logger.addHandler(debug_file_handler)
                debug_logger.propagate = False
                self.loggers['debug'] = debug_logger
                self.handlers['debug'] = debug_file_handler

            logging.info(f"{self.app_name} logging system initialized at level {level}")
            return True
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to set up logging: {e}", file=sys.stderr)
            return False

    def get_logger(self, name: str, level: Optional[str] = None) -> logging.Logger:
        """
        Get a specific logger instance.
        If the logger is not yet configured, it will inherit from the root logger.
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            if level:
                logger.setLevel(level)
            self.loggers[name] = logger
        return self.loggers[name]

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        perf_logger = self.get_logger('performance')
        details = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        perf_logger.info(f"Operation: {operation}, Duration: {duration:.4f}s. {details}".strip())

    def log_audit(self, user: str, action: str, resource: str, result: str, details: str = ""):
        """Log audit events."""
        audit_logger = self.get_logger('audit')
        audit_logger.info(f"User: {user}, Action: {action}, Resource: {resource}, Result: {result}. Details: {details}".strip())

    def export_logs(self, output_dir: Optional[Path] = None, log_type: str = "all") -> bool:
        """
        Exports current log files to a specified directory.
        Args:
            output_dir (Path, optional): Directory to export logs to. Defaults to a timestamped folder in backups.
            log_type (str): 'all', 'main', 'performance', 'audit', 'debug'.
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            if not output_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = Path(DEFAULT_DIRECTORIES["backups"]) / f"logs_export_{timestamp}"

            output_dir.mkdir(parents=True, exist_ok=True)

            log_files_to_copy = []
            if log_type == "all":
                for handler_name, handler in self.handlers.items():
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        log_files_to_copy.append(Path(handler.baseFilename))
                        # Also include backup files if they exist
                        for i in range(1, handler.backupCount + 1):
                            backup_file = Path(f"{handler.baseFilename}.{i}")
                            if backup_file.exists():
                                log_files_to_copy.append(backup_file)
            else:
                handler_names = {
                    "main": "main_file",
                    "performance": "performance",
                    "audit": "audit",
                    "debug": "debug"
                }
                if log_type in handler_names and handler_names[log_type] in self.handlers:
                    handler = self.handlers[handler_names[log_type]]
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        log_files_to_copy.append(Path(handler.baseFilename))
                        for i in range(1, handler.backupCount + 1):
                            backup_file = Path(f"{handler.baseFilename}.{i}")
                            if backup_file.exists():
                                log_files_to_copy.append(backup_file)
                else:
                    logging.warning(f"Unknown log type '{log_type}' for export or handler not found.")
                    return False

            for log_file in set(log_files_to_copy): # Use set to avoid duplicates
                if log_file.exists():
                    try:
                        dest_path = output_dir / log_file.name
                        import shutil
                        shutil.copy2(log_file, dest_path)
                        logging.info(f"Exported {log_file.name} to {dest_path}")
                    except Exception as e:
                        logging.error(f"Failed to copy {log_file.name}: {e}")
            logging.info(f"Logs exported to {output_dir}")
            return True

        except Exception as e:
            logging.error(f"Error exporting logs: {e}")
            return False

    def shutdown(self):
        """Shutdown logging system gracefully"""
        try:
            logging.info(f"{self.app_name} logging system shutting down")

            # Close all handlers
            for handler in self.handlers.values():
                handler.close()

            # Clear references
            self.handlers.clear()
            self.loggers.clear()

            # Shutdown logging
            logging.shutdown()

        except Exception as e:
            print(f"Error shutting down logging: {e}")


# Global log manager instance
log_manager = LogManager()

def setup_logging(level: str = "INFO", **kwargs) -> bool:
    """Convenience function to setup logging"""
    return log_manager.setup_logging(level=level, **kwargs)

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Convenience function to get a logger"""
    return log_manager.get_logger(name, level)

def log_performance(operation: str, duration: float, **kwargs):
    """Convenience function for performance logging"""
    log_manager.log_performance(operation, duration, **kwargs)

def log_audit(user: str, action: str, resource: str, result: str, details: str = ""):
    """Convenience function for audit logging"""
    log_manager.log_audit(user, action, resource, result, details)