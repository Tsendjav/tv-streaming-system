#!/usr/bin/env python3
"""
Enhanced Professional Playout Tab - Modular & Responsive Version
Complete playout system with scheduler integration and responsive design
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# Import modular components
try:
    from playout_components import (
        ResponsiveVideoPlayer, ResponsiveAudioControlPanel,
        AMCPControlSection, LogSection, TransportControls,
        ResponsiveGroupBox, PlayoutManager, COMPONENTS_AVAILABLE
    )
    print("✅ Playout components imported successfully")
except ImportError as e:
    print(f"⚠️ Failed to import playout components: {e}")
    # Fallback to original components if available
    try:
        from playout_components.video_player import ResponsiveVideoPlayer
        from playout_components.audio_control import ResponsiveAudioControlPanel
        from playout_components.ui_components import AMCPControlSection, LogSection, TransportControls, ResponsiveGroupBox
        from playout_components.playout_manager import PlayoutManager
        COMPONENTS_AVAILABLE = True
    except ImportError:
        COMPONENTS_AVAILABLE = False
        print("❌ No playout components available - using fallback")

# Set up logging
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# Check availability flags
PLAYOUT_TAB_AVAILABLE = COMPONENTS_AVAILABLE


class ResponsivePlayoutTab(QWidget):
    """Enhanced responsive playout tab with scheduler integration"""
    
    # Signals for main window integration
    status_message = pyqtSignal(str, int)
    media_taken_to_air = pyqtSignal(str)
    audio_profile_changed = pyqtSignal(str)
    media_loaded = pyqtSignal(str)
    server_config_requested = pyqtSignal()
    media_library_requested = pyqtSignal()
    stream_program_requested = pyqtSignal(str)
    stream_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize core manager
        self.playout_manager = PlayoutManager(config_manager)
        
        # Component references
        self.preview_player = None
        self.program_player = None
        self.audio_control_panel = None
        self.amcp_control = None
        self.log_section = None
        self.transport_controls = None
        
        # External references
        self.media_library_tab = None
        self.scheduler_tab = None
        
        # Responsive state
        self.is_compact_mode = False
        self.current_layout = None
        
        # Set minimum size for responsive behavior
        self.setMinimumSize(800, 600)
        
        # Initialize UI and connections
        self._init_ui()
        self._setup_connections()
        self._setup_responsive_behavior()
        
        # Start with initial status
        self._add_log_entry("SYSTEM", "Enhanced Professional Playout System initialized", "#00BCD4")
        
        self.logger.info("Responsive playout tab initialized")
    
    def _init_ui(self):
        """Initialize responsive user interface"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        
        # Create responsive sections
        self._create_top_section()
        self._create_main_section()
        self._create_bottom_section()
        
        # Apply professional styling
        self._apply_responsive_styling()
    
    def _create_top_section(self):
        """Create top section with AMCP controls"""
        if not COMPONENTS_AVAILABLE:
            # Fallback for missing components
            top_section = QLabel("AMCP Controls - Components not available")
            top_section.setFixedHeight(70)
            self.main_layout.addWidget(top_section)
            return
        
        # AMCP Control Section
        self.amcp_control = AMCPControlSection()
        self.main_layout.addWidget(self.amcp_control)
    
    def _create_main_section(self):
        """Create main section with players and controls"""
        # Main content area with responsive splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        
        # Left section - Video players and transport
        self._create_video_section()
        
        # Right section - Audio control panel  
        self._create_audio_section()
        
        # Set initial proportions
        self.main_splitter.setSizes([700, 350])
        self.main_layout.addWidget(self.main_splitter)
    
    def _create_video_section(self):
        """Create video players and transport controls section"""
        video_section = QWidget()
        video_layout = QVBoxLayout(video_section)
        video_layout.setSpacing(4)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Players area
        self._create_players_area(video_layout)
        
        # Add to main splitter
        self.main_splitter.addWidget(video_section)
    
    def _create_players_area(self, parent_layout):
        """Create responsive players area"""
        # Players container with responsive layout
        players_container = QWidget()
        self.players_layout = QHBoxLayout(players_container)
        self.players_layout.setSpacing(4)
        self.players_layout.setContentsMargins(0, 0, 0, 0)
        
        if COMPONENTS_AVAILABLE:
            # Preview player
            self._create_preview_section()
            
            # Transport controls
            self._create_transport_section()
            
            # Program player
            self._create_program_section()
        else:
            # Fallback
            fallback_label = QLabel("Video Players - Components not available")
            fallback_label.setMinimumHeight(400)
            fallback_label.setStyleSheet("background-color: #333; color: white; border: 1px solid #666;")
            self.players_layout.addWidget(fallback_label)
        
        parent_layout.addWidget(players_container)
    
    def _create_preview_section(self):
        """Create preview player section"""
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setSpacing(2)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview header
        preview_header = QLabel("🎬 PREVIEW")
        preview_header.setFixedHeight(30)
        preview_header.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px 6px 0 0;
            }
        """)
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)
        
        # Preview player
        self.preview_player = ResponsiveVideoPlayer("Preview Player")
        self.preview_player.setStyleSheet("""
            ResponsiveVideoPlayer {
                border-left: 2px solid #2196F3;
                border-right: 2px solid #2196F3;
                border-bottom: 2px solid #2196F3;
                border-radius: 0 0 6px 6px;
            }
        """)
        preview_layout.addWidget(self.preview_player)
        
        # Preview controls
        self._create_preview_controls(preview_layout)
        
        self.players_layout.addWidget(preview_container)
    
    def _create_preview_controls(self, parent_layout):
        """Create preview control buttons"""
        controls_widget = QWidget()
        controls_widget.setFixedHeight(40)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        controls_layout.setSpacing(4)
        
        # CUE button
        cue_btn = QPushButton("🎯 CUE")
        cue_btn.setFixedHeight(30)
        cue_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        cue_btn.clicked.connect(self._cue_preview)
        controls_layout.addWidget(cue_btn)
        
        # Auto Audio button
        self.auto_audio_btn = QPushButton("🎵 Auto Audio")
        self.auto_audio_btn.setCheckable(True)
        self.auto_audio_btn.setChecked(True)
        self.auto_audio_btn.setFixedHeight(30)
        self.auto_audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        self.auto_audio_btn.toggled.connect(self._toggle_auto_audio)
        controls_layout.addWidget(self.auto_audio_btn)
        
        controls_layout.addStretch()
        parent_layout.addWidget(controls_widget)
    
    def _create_transport_section(self):
        """Create transport controls section"""
        if COMPONENTS_AVAILABLE:
            self.transport_controls = TransportControls()
        else:
            # Fallback
            self.transport_controls = QWidget()
            self.transport_controls.setFixedWidth(80)
            transport_layout = QVBoxLayout(self.transport_controls)
            transport_layout.addWidget(QLabel("Transport\nControls"))
        
        self.players_layout.addWidget(self.transport_controls)
    
    def _create_program_section(self):
        """Create program player section"""
        program_container = QWidget()
        program_layout = QVBoxLayout(program_container)
        program_layout.setSpacing(2)
        program_layout.setContentsMargins(0, 0, 0, 0)
        
        # Program header
        program_header = QLabel("📺 PROGRAM")
        program_header.setFixedHeight(30)
        program_header.setStyleSheet("""
            QLabel {
                background-color: #F44336;
                color: white;
                padding: 6px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px 6px 0 0;
            }
        """)
        program_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        program_layout.addWidget(program_header)
        
        # Program player
        self.program_player = ResponsiveVideoPlayer("Program Player")
        self.program_player.setStyleSheet("""
            ResponsiveVideoPlayer {
                border-left: 2px solid #F44336;
                border-right: 2px solid #F44336;
                border-bottom: 2px solid #F44336;
                border-radius: 0 0 6px 6px;
            }
        """)
        program_layout.addWidget(self.program_player)
        
        # Program status
        self._create_program_status(program_layout)
        
        self.players_layout.addWidget(program_container)
    
    def _create_program_status(self, parent_layout):
        """Create program status section"""
        status_widget = QWidget()
        status_widget.setFixedHeight(40)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(8)
        
        # Audio status
        self.audio_status_label = QLabel("🟢 Audio Ready")
        self.audio_status_label.setFixedHeight(30)
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba(76, 175, 80, 0.15);
                border-radius: 4px;
                border: 1px solid #4CAF50;
                font-size: 10px;
            }
        """)
        status_layout.addWidget(self.audio_status_label)
        
        # Streaming status
        self.streaming_status_label = QLabel("🔴 Not Streaming")
        self.streaming_status_label.setFixedHeight(30)
        self.streaming_status_label.setStyleSheet("""
            QLabel {
                color: #757575;
                font-weight: bold;
                padding: 4px 8px;
                background-color: rgba(117, 117, 117, 0.15);
                border-radius: 4px;
                border: 1px solid #757575;
                font-size: 10px;
            }
        """)
        status_layout.addWidget(self.streaming_status_label)
        
        status_layout.addStretch()
        
        # ON AIR indicator
        self.on_air_label = QLabel("🔴 OFF AIR")
        self.on_air_label.setFixedHeight(30)
        self.on_air_label.setStyleSheet("""
            QLabel {
                color: #757575; 
                font-weight: bold; 
                padding: 4px 8px;
                background-color: rgba(117, 117, 117, 0.15);
                border-radius: 4px;
                border: 1px solid #757575;
                font-size: 10px;
            }
        """)
        status_layout.addWidget(self.on_air_label)
        
        parent_layout.addWidget(status_widget)
    
    def _create_audio_section(self):
        """Create audio control panel section"""
        if COMPONENTS_AVAILABLE:
            self.audio_control_panel = ResponsiveAudioControlPanel(
                config_manager=self.config_manager
            )
        else:
            # Fallback
            self.audio_control_panel = QWidget()
            self.audio_control_panel.setFixedWidth(350)
            audio_layout = QVBoxLayout(self.audio_control_panel)
            audio_layout.addWidget(QLabel("Audio Control Panel - Components not available"))
        
        self.main_splitter.addWidget(self.audio_control_panel)
    
    def _create_bottom_section(self):
        """Create bottom section with log"""
        if COMPONENTS_AVAILABLE:
            self.log_section = LogSection()
        else:
            # Fallback
            self.log_section = QWidget()
            self.log_section.setFixedHeight(120)
            log_layout = QVBoxLayout(self.log_section)
            log_layout.addWidget(QLabel("Log Section - Components not available"))
        
        self.main_layout.addWidget(self.log_section)
    
    def _setup_connections(self):
        """Setup signal connections between components"""
        try:
            # Connect playout manager signals
            self.playout_manager.status_changed.connect(self._handle_status_message)
            self.playout_manager.media_loaded.connect(self.media_loaded.emit)
            self.playout_manager.on_air_status_changed.connect(self._update_on_air_status)
            self.playout_manager.streaming_status_changed.connect(self._update_streaming_status)
            self.playout_manager.audio_profile_changed.connect(self.audio_profile_changed.emit)
            
            if COMPONENTS_AVAILABLE:
                # Connect video players
                if self.preview_player:
                    self.preview_player.media_library_requested.connect(self._handle_media_library_request)
                    self.preview_player.scheduler_playlist_requested.connect(self._handle_scheduler_request)
                    self.preview_player.media_loaded.connect(self._on_preview_loaded)
                
                if self.program_player:
                    self.program_player.media_library_requested.connect(self._handle_media_library_request)
                    self.program_player.scheduler_playlist_requested.connect(self._handle_scheduler_request)
                    self.program_player.media_loaded.connect(self._on_program_loaded)
                
                # Connect transport controls
                if self.transport_controls:
                    self.transport_controls.send_to_program.connect(self._send_to_program)
                    self.transport_controls.take_to_air.connect(self._take_to_air)
                    self.transport_controls.stream_program.connect(self._stream_program)
                    self.transport_controls.fade_program.connect(lambda: self._fade_program(True))
                    self.transport_controls.cut_program.connect(lambda: self._fade_program(False))
                
                # Connect AMCP controls
                if self.amcp_control:
                    self.amcp_control.connect_requested.connect(self._connect_amcp)
                    self.amcp_control.disconnect_requested.connect(self._disconnect_amcp)
                    self.amcp_control.command_requested.connect(self._send_amcp_command)
                    self.amcp_control.console_requested.connect(self._open_console)
                
                # Connect audio control panel
                if self.audio_control_panel:
                    self.audio_control_panel.profile_changed.connect(self._on_audio_profile_changed)
                    self.audio_control_panel.night_mode_toggled.connect(self._on_night_mode_changed)
                    self.audio_control_panel.parameter_changed.connect(self._on_audio_parameter_changed)
            
            self.logger.info("Signal connections established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup connections: {e}")
    
    def _setup_responsive_behavior(self):
        """Setup responsive behavior"""
        # Install event filter for resize detection
        self.installEventFilter(self)
        
        # Setup responsive timer
        self.responsive_timer = QTimer()
        self.responsive_timer.timeout.connect(self._check_responsive_state)
        self.responsive_timer.start(1000)  # Check every second
    
    def eventFilter(self, obj, event):
        """Handle resize events for responsive behavior"""
        if event.type() == event.Type.Resize:
            self._handle_resize(event.size())
        return super().eventFilter(obj, event)
    
    def _handle_resize(self, size):
        """Handle widget resize for responsive behavior"""
        width = size.width()
        height = size.height()
        
        # Determine if compact mode is needed
        is_compact = width < 1000 or height < 700
        
        if is_compact != self.is_compact_mode:
            self.is_compact_mode = is_compact
            self._update_layout_for_responsive()
    
    def _update_layout_for_responsive(self):
        """Update layout for responsive behavior"""
        try:
            if self.is_compact_mode:
                # Compact mode - stack sections vertically
                self._switch_to_compact_layout()
            else:
                # Full mode - side by side layout
                self._switch_to_full_layout()
            
            self._add_log_entry("SYSTEM", f"Switched to {'compact' if self.is_compact_mode else 'full'} layout", "#00BCD4")
            
        except Exception as e:
            self.logger.error(f"Failed to update responsive layout: {e}")
    
    def _switch_to_compact_layout(self):
        """Switch to compact layout for small screens"""
        if self.main_splitter:
            # Change to vertical orientation
            self.main_splitter.setOrientation(Qt.Orientation.Vertical)
            self.main_splitter.setSizes([400, 200])
            
            # Update players layout for compact mode
            if hasattr(self, 'players_layout'):
                # Stack players vertically in compact mode
                self.players_layout.setDirection(QBoxLayout.Direction.TopToBottom)
    
    def _switch_to_full_layout(self):
        """Switch to full layout for large screens"""
        if self.main_splitter:
            # Change to horizontal orientation
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.main_splitter.setSizes([700, 350])
            
            # Update players layout for full mode
            if hasattr(self, 'players_layout'):
                # Side by side players in full mode
                self.players_layout.setDirection(QBoxLayout.Direction.LeftToRight)
    
    def _check_responsive_state(self):
        """Check and update responsive state"""
        try:
            current_size = self.size()
            self._handle_resize(current_size)
        except Exception as e:
            self.logger.error(f"Responsive state check failed: {e}")
    
    def _apply_responsive_styling(self):
        """Apply responsive professional styling"""
        self.setStyleSheet("""
            /* Main widget styling */
            QWidget {
                background-color: #2b2b2b;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            
            /* Responsive button styling */
            QPushButton {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-weight: bold;
                font-size: 10px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00BCD4;
            }
            
            QPushButton:pressed {
                background-color: #353535;
            }
            
            QPushButton:checked {
                background-color: #00BCD4;
                border-color: #00ACC1;
                color: white;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                border-color: #333;
                color: #666;
            }
            
            /* Responsive labels */
            QLabel {
                color: #E0E0E0;
                font-size: 10px;
            }
            
            /* Responsive splitter */
            QSplitter::handle {
                background-color: #555;
                border: 1px solid #777;
            }
            
            QSplitter::handle:horizontal {
                width: 6px;
            }
            
            QSplitter::handle:vertical {
                height: 6px;
            }
            
            /* Responsive group boxes */
            QGroupBox {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 1ex;
                font-weight: bold;
                font-size: 11px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
                color: #00BCD4;
            }
        """)
    
    # ===========================================
    # EXTERNAL INTEGRATION METHODS
    # ===========================================
    
    def set_media_library_tab(self, media_library_tab):
        """Set reference to media library tab"""
        self.media_library_tab = media_library_tab
        self.playout_manager.set_media_library_tab(media_library_tab)
        self.logger.info("Media library tab reference set")
    
    def set_scheduler_tab(self, scheduler_tab):
        """Set reference to scheduler tab"""
        self.scheduler_tab = scheduler_tab
        self.playout_manager.set_scheduler_tab(scheduler_tab)
        self.logger.info("Scheduler tab reference set")
    
    def _handle_media_library_request(self):
        """Handle request for media library files"""
        try:
            media_files = self.playout_manager.get_media_library_files()
            
            # Send to requesting player
            sender = self.sender()
            if sender:
                sender.set_media_library_files(media_files)
                self._add_log_entry("LIBRARY", f"Loaded {len(media_files)} files from Media Library", "#9C27B0")
            
        except Exception as e:
            self.logger.error(f"Failed to handle media library request: {e}")
            self._add_log_entry("ERROR", f"Media Library request failed: {e}", "#F44336")
    
    def _handle_scheduler_request(self):
        """Handle request for scheduler playlist"""
        try:
            playlist = self.playout_manager.get_scheduler_playlist()
            
            # Send to requesting player
            sender = self.sender()
            if sender:
                sender.set_scheduler_playlist(playlist)
                self._add_log_entry("SCHEDULER", f"Loaded {len(playlist)} events from Scheduler", "#9C27B0")
            
        except Exception as e:
            self.logger.error(f"Failed to handle scheduler request: {e}")
            self._add_log_entry("ERROR", f"Scheduler request failed: {e}", "#F44336")
    
    # ===========================================
    # PLAYER CONTROL METHODS
    # ===========================================
    
    def _cue_preview(self):
        """Cue preview to first frame"""
        if self.preview_player:
            self.preview_player.stop()
            self._add_log_entry("SYSTEM", "Preview cued to first frame", "#00BCD4")
    
    def _toggle_auto_audio(self, enabled):
        """Toggle automatic audio profile detection"""
        self.playout_manager.set_auto_audio(enabled)
        self._add_log_entry("AUDIO", f"Auto audio detection {'enabled' if enabled else 'disabled'}", "#9C27B0")
    
    def _send_to_program(self):
        """Send preview content to program player"""
        result = self.playout_manager.execute_command("send_to_program")
        if result["status"] == "success":
            self._add_log_entry("SUCCESS", "Media sent to program", "#4CAF50")
        else:
            self._add_log_entry("ERROR", "Failed to send media to program", "#F44336")
    
    def _take_to_air(self):
        """Take program content to air"""
        result = self.playout_manager.execute_command("take_to_air")
        if result["status"] == "success":
            self._add_log_entry("SUCCESS", "🚨 TAKEN TO AIR", "#E91E63")
        else:
            self._add_log_entry("ERROR", "Failed to take to air", "#F44336")
    
    def _stream_program(self):
        """Stream current program content"""
        # This would integrate with streaming tab
        self.stream_program_requested.emit(self.playout_manager.program_state.get("file", ""))
        self._add_log_entry("SYSTEM", "🚀 Program streaming requested", "#9C27B0")
    
    def _fade_program(self, fade=True):
        """Fade or cut program off air"""
        result = self.playout_manager.execute_command("fade_program", {"fade": fade})
        if result["status"] == "success":
            action = "FADED" if fade else "CUT"
            self._add_log_entry("SYSTEM", f"Program {action} off air", "#FF5722")
        else:
            self._add_log_entry("ERROR", "Failed to fade program", "#F44336")
    
    # ===========================================
    # AMCP CONTROL METHODS
    # ===========================================
    
    def _connect_amcp(self):
        """Connect to AMCP server"""
        self.playout_manager.set_amcp_connection(True)
        if self.amcp_control:
            self.amcp_control.set_connection_status(True)
        self._add_log_entry("AMCP", "Connected to AMCP server", "#2196F3")
    
    def _disconnect_amcp(self):
        """Disconnect from AMCP server"""
        self.playout_manager.set_amcp_connection(False)
        if self.amcp_control:
            self.amcp_control.set_connection_status(False)
        self._add_log_entry("AMCP", "Disconnected from AMCP server", "#2196F3")
    
    def _send_amcp_command(self, command):
        """Send AMCP command"""
        if self.amcp_control:
            settings = self.amcp_control.get_current_settings()
            if settings['connected']:
                full_command = f"{command} {settings['channel']}-{settings['layer']}"
                if command == "LOAD" and settings['media']:
                    full_command += f" {settings['media']}"
                self._add_log_entry("AMCP", f"SENT: {full_command}", "#2196F3")
            else:
                self._add_log_entry("ERROR", "Not connected to AMCP server", "#F44336")
    
    def _open_console(self):
        """Open AMCP console dialog"""
        self._add_log_entry("SYSTEM", "AMCP console opened", "#00BCD4")
    
    # ===========================================
    # SIGNAL HANDLERS
    # ===========================================
    
    def _handle_status_message(self, message, level):
        """Handle status message from playout manager"""
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800",
            "info": "#00BCD4"
        }
        color = colors.get(level, "#E0E0E0")
        self._add_log_entry(level.upper(), message, color)
        
        # Emit to main window
        timeout = 3000 if level == "success" else 5000
        self.status_message.emit(message, timeout)
    
    def _on_preview_loaded(self, file_path):
        """Handle preview media loaded"""
        self.playout_manager.load_preview_media(file_path)
    
    def _on_program_loaded(self, file_path):
        """Handle program media loaded"""
        self.playout_manager.load_program_media(file_path)
    
    def _update_on_air_status(self, on_air):
        """Update ON AIR visual indicators"""
        if self.on_air_label:
            if on_air:
                self.on_air_label.setText("🔴 ON AIR")
                self.on_air_label.setStyleSheet("""
                    QLabel {
                        color: white; 
                        font-weight: bold; 
                        padding: 4px 8px;
                        background-color: #F44336;
                        border-radius: 4px;
                        border: 1px solid #F44336;
                        font-size: 10px;
                    }
                """)
            else:
                self.on_air_label.setText("🔴 OFF AIR")
                self.on_air_label.setStyleSheet("""
                    QLabel {
                        color: #757575; 
                        font-weight: bold; 
                        padding: 4px 8px;
                        background-color: rgba(117, 117, 117, 0.15);
                        border-radius: 4px;
                        border: 1px solid #757575;
                        font-size: 10px;
                    }
                """)
    
    def _update_streaming_status(self, is_streaming, stream_info):
        """Update streaming status display"""
        if self.streaming_status_label:
            if is_streaming:
                self.streaming_status_label.setText("🟢 Streaming")
                self.streaming_status_label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: rgba(76, 175, 80, 0.15);
                        border-radius: 4px;
                        border: 1px solid #4CAF50;
                        font-size: 10px;
                    }
                """)
            else:
                self.streaming_status_label.setText("🔴 Not Streaming")
                self.streaming_status_label.setStyleSheet("""
                    QLabel {
                        color: #757575;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: rgba(117, 117, 117, 0.15);
                        border-radius: 4px;
                        border: 1px solid #757575;
                        font-size: 10px;
                    }
                """)
    
    def _on_audio_profile_changed(self, profile_name):
        """Handle audio profile change"""
        self._add_log_entry("AUDIO", f"Audio profile changed to: {profile_name}", "#9C27B0")
        self.audio_profile_changed.emit(profile_name)
    
    def _on_night_mode_changed(self, enabled):
        """Handle night mode toggle"""
        status = "enabled" if enabled else "disabled"
        self._add_log_entry("AUDIO", f"Night mode {status}", "#9C27B0")
    
    def _on_audio_parameter_changed(self, param_name, value):
        """Handle audio parameter changes"""
        self.logger.debug(f"Audio parameter {param_name} changed to {value}")
    
    # ===========================================
    # UTILITY METHODS
    # ===========================================
    
    def _add_log_entry(self, level, message, color="#E0E0E0"):
        """Add entry to log"""
        if self.log_section and hasattr(self.log_section, 'add_log_entry'):
            self.log_section.add_log_entry(level, message, color)
    
    # ===========================================
    # PUBLIC INTERFACE METHODS
    # ===========================================
    
    def get_current_state(self):
        """Get current playout state"""
        return self.playout_manager.get_current_state()
    
    def load_preview_media(self, file_path):
        """Load media to preview player"""
        return self.playout_manager.load_preview_media(file_path)
    
    def load_program_media(self, file_path):
        """Load media to program player"""
        return self.playout_manager.load_program_media(file_path)
    
    def emergency_stop(self):
        """Emergency stop - immediately cut all output"""
        result = self.playout_manager.execute_command("emergency_stop")
        if result["status"] == "success":
            self._add_log_entry("ERROR", "🚨 EMERGENCY STOP executed", "#F44336")
        return result["status"] == "success"
    
    def cleanup(self):
        """Clean up resources when closing"""
        try:
            # Stop responsive timer
            if hasattr(self, 'responsive_timer'):
                self.responsive_timer.stop()
            
            # Cleanup playout manager
            if self.playout_manager:
                self.playout_manager.cleanup()
            
            # Cleanup components
            if COMPONENTS_AVAILABLE:
                if self.preview_player:
                    self.preview_player.cleanup()
                if self.program_player:
                    self.program_player.cleanup()
                if self.audio_control_panel:
                    self.audio_control_panel.cleanup()
            
            self._add_log_entry("SYSTEM", "Responsive playout system shutdown complete", "#00BCD4")
            self.logger.info("Responsive playout tab cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def refresh(self):
        """Refresh tab"""
        self._add_log_entry("SYSTEM", "Responsive playout tab refreshed", "#00BCD4")
    
    def get_tab_name(self):
        """Get tab name for integration"""
        return "playout"
    
    def get_tab_status(self):
        """Get enhanced tab status"""
        return {
            "name": "playout",
            "status": "ready",
            "responsive": True,
            "compact_mode": self.is_compact_mode,
            "components_available": COMPONENTS_AVAILABLE,
            "scheduler_integration": self.scheduler_tab is not None,
            "media_library_integration": self.media_library_tab is not None,
            **self.get_current_state()
        }
    
    def execute_command(self, command, params=None):
        """Execute tab-specific command"""
        return self.playout_manager.execute_command(command, params)
    
    def handle_system_event(self, event):
        """Handle incoming system event"""
        try:
            if hasattr(event, 'event_type') and hasattr(event, 'data'):
                if event.event_type == "media_loaded":
                    if event.data.get("file_path"):
                        self.load_preview_media(event.data["file_path"])
                elif event.event_type == "scheduler_playlist_updated":
                    self._add_log_entry("SCHEDULER", "Scheduler playlist updated", "#9C27B0")
                elif event.event_type == "media_library_updated":
                    self._add_log_entry("LIBRARY", "Media library updated", "#9C27B0")
                elif event.event_type == "emergency_stop":
                    self.emergency_stop()
                elif event.event_type == "resize_request":
                    # Handle external resize requests
                    if event.data.get("compact_mode") is not None:
                        self.is_compact_mode = event.data["compact_mode"]
                        self._update_layout_for_responsive()
        except Exception as e:
            self.logger.error(f"Error handling system event: {e}")


# For backwards compatibility
PlayoutTab = ResponsivePlayoutTab

# Export classes for main window
__all__ = ['ResponsivePlayoutTab', 'PlayoutTab', 'PLAYOUT_TAB_AVAILABLE']
