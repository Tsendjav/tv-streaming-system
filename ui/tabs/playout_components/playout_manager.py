#!/usr/bin/env python3
"""
Playout Manager
Core playout logic and state management
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

try:
    from core.logging import get_logger
except ImportError:
    def get_logger(name):
        return logging.getLogger(name)


class PlayoutManager(QObject):
    """Core playout management and state tracking"""
    
    # Signals
    status_changed = pyqtSignal(str, str)  # message, level
    media_loaded = pyqtSignal(str)
    playback_state_changed = pyqtSignal(str, str)  # player, state
    on_air_status_changed = pyqtSignal(bool)
    streaming_status_changed = pyqtSignal(bool, str)
    audio_profile_changed = pyqtSignal(str)
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # State tracking
        self.is_on_air = False
        self.is_streaming = False
        self.auto_audio_enabled = True
        self.amcp_connected = False
        self.current_audio_profile = "default"
        
        # Players state
        self.preview_state = {"file": None, "playing": False}
        self.program_state = {"file": None, "playing": False}
        
        # Media library and scheduler references
        self.media_library_tab = None
        self.scheduler_tab = None
        
        # Initialize timers
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        self.logger.info("Playout manager initialized")
    
    def set_media_library_tab(self, media_library_tab):
        """Set reference to media library tab"""
        self.media_library_tab = media_library_tab
        self.logger.info("Media library tab reference set")
    
    def set_scheduler_tab(self, scheduler_tab):
        """Set reference to scheduler tab"""
        self.scheduler_tab = scheduler_tab
        self.logger.info("Scheduler tab reference set")
    
    def get_media_library_files(self) -> List[Any]:
        """Get media files from media library"""
        try:
            if self.media_library_tab and hasattr(self.media_library_tab, 'media_library'):
                # Get current filtered files from media library
                current_search = ""
                current_filters = {}
                
                # Try to get current search text
                if hasattr(self.media_library_tab, 'search_input') and self.media_library_tab.search_input:
                    current_search = self.media_library_tab.search_input.text().strip()
                
                # Try to get current category filter
                if hasattr(self.media_library_tab, 'category_list') and self.media_library_tab.category_list:
                    current_item = self.media_library_tab.category_list.currentItem()
                    if current_item and current_item.text() != "Бүх медиа":
                        current_filters["category"] = current_item.text()
                
                # Try to get current type filter
                if hasattr(self.media_library_tab, 'type_combo') and self.media_library_tab.type_combo:
                    type_filter = self.media_library_tab.type_combo.currentText()
                    if type_filter != "Бүх төрөл":
                        # Import here to avoid circular imports
                        try:
                            from media_library_tab import MediaType
                            type_map = {
                                "Видео": MediaType.VIDEO,
                                "Аудио": MediaType.AUDIO,
                                "Зураг": MediaType.IMAGE
                            }
                            if type_filter in type_map:
                                current_filters["media_type"] = type_map[type_filter]
                        except ImportError:
                            pass
                
                # Get filtered media files
                media_files = self.media_library_tab.media_library.search_media(
                    current_search, current_filters
                )
                
                self.logger.info(f"Retrieved {len(media_files)} files from media library")
                return media_files
                
        except Exception as e:
            self.logger.error(f"Failed to get media library files: {e}")
        
        return []
    
    def get_scheduler_playlist(self) -> List[Any]:
        """Get playlist from scheduler events"""
        try:
            if self.scheduler_tab and hasattr(self.scheduler_tab, 'schedule_manager'):
                # Get upcoming events that have media content
                upcoming_events = self.scheduler_tab.schedule_manager.get_upcoming_events(24)
                
                # Filter events that have media content
                media_events = []
                for event in upcoming_events:
                    if (hasattr(event, 'content') and event.content and 
                        event.event_type.value in ['media_play', 'playlist']):
                        # Check if file exists
                        if Path(event.content).exists():
                            media_events.append(event)
                
                self.logger.info(f"Retrieved {len(media_events)} media events from scheduler")
                return media_events
                
        except Exception as e:
            self.logger.error(f"Failed to get scheduler playlist: {e}")
        
        return []
    
    def load_preview_media(self, file_path: str) -> bool:
        """Load media to preview player"""
        try:
            if not Path(file_path).exists():
                self.status_changed.emit(f"File not found: {file_path}", "error")
                return False
            
            self.preview_state["file"] = file_path
            self.preview_state["playing"] = False
            
            # Auto-sync audio if enabled
            if self.auto_audio_enabled:
                self._sync_audio_to_content(file_path)
            
            self.media_loaded.emit(file_path)
            self.status_changed.emit(f"Preview loaded: {Path(file_path).name}", "success")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load preview media: {e}")
            self.status_changed.emit(f"Failed to load preview: {e}", "error")
            return False
    
    def load_program_media(self, file_path: str) -> bool:
        """Load media to program player"""
        try:
            if not Path(file_path).exists():
                self.status_changed.emit(f"File not found: {file_path}", "error")
                return False
            
            self.program_state["file"] = file_path
            self.program_state["playing"] = False
            
            # Auto-sync audio if enabled
            if self.auto_audio_enabled:
                self._sync_audio_to_content(file_path)
            
            self.media_loaded.emit(file_path)
            self.status_changed.emit(f"Program loaded: {Path(file_path).name}", "success")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load program media: {e}")
            self.status_changed.emit(f"Failed to load program: {e}", "error")
            return False
    
    def send_to_program(self) -> bool:
        """Send preview content to program player"""
        try:
            if not self.preview_state["file"]:
                self.status_changed.emit("No media in preview to send", "warning")
                return False
            
            if self.load_program_media(self.preview_state["file"]):
                self.status_changed.emit("Media sent to program", "success")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to send to program: {e}")
            self.status_changed.emit(f"Failed to send to program: {e}", "error")
            return False
    
    def take_to_air(self) -> bool:
        """Take program content to air"""
        try:
            if not self.program_state["file"]:
                self.status_changed.emit("No program content to take to air", "warning")
                return False
            
            self.is_on_air = True
            self.program_state["playing"] = True
            
            # Emit signals
            self.on_air_status_changed.emit(True)
            self.playback_state_changed.emit("program", "playing")
            
            # Auto-start streaming if available
            self._start_streaming()
            
            self.status_changed.emit(f"🚨 TAKEN TO AIR: {Path(self.program_state['file']).name}", "success")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to take to air: {e}")
            self.status_changed.emit(f"Failed to take to air: {e}", "error")
            return False
    
    def fade_program(self, fade: bool = True) -> bool:
        """Fade or cut program off air"""
        try:
            if not self.is_on_air:
                self.status_changed.emit("No program on air to fade", "warning")
                return False
            
            self.is_on_air = False
            self.program_state["playing"] = False
            
            # Stop streaming
            self._stop_streaming()
            
            # Emit signals
            self.on_air_status_changed.emit(False)
            self.playback_state_changed.emit("program", "stopped")
            
            action = "FADED" if fade else "CUT"
            self.status_changed.emit(f"Program {action} off air", "info")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fade program: {e}")
            self.status_changed.emit(f"Failed to fade program: {e}", "error")
            return False
    
    def emergency_stop(self) -> bool:
        """Emergency stop - immediately cut all output"""
        try:
            # Stop all playback
            self.preview_state["playing"] = False
            self.program_state["playing"] = False
            
            # Stop streaming
            self._stop_streaming()
            
            # Update status
            self.is_on_air = False
            
            # Emit signals
            self.on_air_status_changed.emit(False)
            self.playback_state_changed.emit("preview", "stopped")
            self.playback_state_changed.emit("program", "stopped")
            
            self.status_changed.emit("🚨 EMERGENCY STOP executed", "error")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
            self.status_changed.emit(f"Emergency stop failed: {e}", "error")
            return False
    
    def _sync_audio_to_content(self, file_path: str):
        """Automatically sync audio profile to content type"""
        if not self.auto_audio_enabled:
            return
        
        try:
            file_name = Path(file_path).name.lower()
            
            # Determine content type based on filename
            if any(word in file_name for word in ['movie', 'film', 'cinema']):
                profile = "movie"
            elif any(word in file_name for word in ['music', 'song', 'audio']):
                profile = "music"
            elif any(word in file_name for word in ['news', 'report', 'interview']):
                profile = "news"
            elif any(word in file_name for word in ['sport', 'game', 'match']):
                profile = "sports"
            else:
                profile = "default"
            
            if profile != self.current_audio_profile:
                self.current_audio_profile = profile
                self.audio_profile_changed.emit(profile)
                self.status_changed.emit(f"Auto-applied audio profile: {profile}", "info")
                
        except Exception as e:
            self.logger.error(f"Failed to sync audio to content: {e}")
    
    def _start_streaming(self):
        """Start streaming program content"""
        try:
            if not self.program_state["file"]:
                return
            
            # Here we would integrate with streaming component
            # For now, just update state
            self.is_streaming = True
            self.streaming_status_changed.emit(True, self.program_state["file"])
            
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
    
    def _stop_streaming(self):
        """Stop streaming"""
        try:
            self.is_streaming = False
            self.streaming_status_changed.emit(False, "")
            
        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
    
    def _update_status(self):
        """Update periodic status"""
        try:
            # Check for any issues
            if self.is_on_air and not self.program_state["file"]:
                self.status_changed.emit("⚠️ ON AIR but no program content", "warning")
            
            # Update timestamps or other periodic checks here
            
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
    
    def set_auto_audio(self, enabled: bool):
        """Set auto audio detection"""
        self.auto_audio_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.status_changed.emit(f"Auto audio detection {status}", "info")
    
    def set_amcp_connection(self, connected: bool):
        """Set AMCP connection status"""
        self.amcp_connected = connected
        status = "connected" if connected else "disconnected"
        self.status_changed.emit(f"AMCP server {status}", "info")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current playout state"""
        return {
            'on_air': self.is_on_air,
            'streaming': self.is_streaming,
            'auto_audio': self.auto_audio_enabled,
            'amcp_connected': self.amcp_connected,
            'current_audio_profile': self.current_audio_profile,
            'preview_state': self.preview_state.copy(),
            'program_state': self.program_state.copy(),
            'media_library_available': self.media_library_tab is not None,
            'scheduler_available': self.scheduler_tab is not None
        }
    
    def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute playout command"""
        try:
            params = params or {}
            
            if command == "take_to_air":
                success = self.take_to_air()
                return {"status": "success" if success else "error", "message": "Take to air"}
            
            elif command == "emergency_stop":
                success = self.emergency_stop()
                return {"status": "success" if success else "error", "message": "Emergency stop"}
            
            elif command == "send_to_program":
                success = self.send_to_program()
                return {"status": "success" if success else "error", "message": "Send to program"}
            
            elif command == "load_preview" and "file_path" in params:
                success = self.load_preview_media(params["file_path"])
                return {"status": "success" if success else "error", "message": "Load preview"}
            
            elif command == "load_program" and "file_path" in params:
                success = self.load_program_media(params["file_path"])
                return {"status": "success" if success else "error", "message": "Load program"}
            
            elif command == "fade_program":
                fade = params.get("fade", True)
                success = self.fade_program(fade)
                return {"status": "success" if success else "error", "message": "Fade program"}
            
            elif command == "set_auto_audio":
                enabled = params.get("enabled", True)
                self.set_auto_audio(enabled)
                return {"status": "success", "message": f"Auto audio {enabled}"}
            
            elif command == "get_state":
                return {"status": "success", "data": self.get_current_state()}
            
            elif command == "get_media_library":
                files = self.get_media_library_files()
                return {"status": "success", "data": files}
            
            elif command == "get_scheduler_playlist":
                playlist = self.get_scheduler_playlist()
                return {"status": "success", "data": playlist}
            
            else:
                return {"status": "error", "message": f"Unknown command: {command}"}
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {"status": "error", "message": f"Command failed: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop timers
            if self.status_timer:
                self.status_timer.stop()
            
            # Emergency stop if on air
            if self.is_on_air:
                self.emergency_stop()
            
            self.logger.info("Playout manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


__all__ = ['PlayoutManager']
