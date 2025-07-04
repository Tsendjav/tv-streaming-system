#!/usr/bin/env python3
"""
Integration Example: Scheduler Tab with Playout Tab
Demonstrates how to connect scheduler events to playout system
"""

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer

# Import both tabs
try:
    from playout_tab import ResponsivePlayoutTab
    from scheduler_tab import SchedulerTab, ScheduleEvent, EventType
    TABS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import tabs: {e}")
    TABS_AVAILABLE = False


class IntegratedBroadcastSystem(QMainWindow):
    """Example of integrated broadcast system with scheduler and playout"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Broadcast System - Scheduler + Playout")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.config_manager = self._create_mock_config()
        self.scheduler_tab = None
        self.playout_tab = None
        
        self._init_ui()
        self._setup_integration()
        self._create_demo_events()
        
        # Auto-refresh timer
        self.integration_timer = QTimer()
        self.integration_timer.timeout.connect(self._check_integration)
        self.integration_timer.start(10000)  # Check every 10 seconds
    
    def _create_mock_config(self):
        """Create mock configuration manager"""
        class MockConfig:
            def get(self, key, default=None):
                return default
        return MockConfig()
    
    def _init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Integration controls
        self._create_integration_controls(layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        if TABS_AVAILABLE:
            # Scheduler tab
            self.scheduler_tab = SchedulerTab(self.config_manager)
            self.tab_widget.addTab(self.scheduler_tab, "📅 Scheduler")
            
            # Playout tab
            self.playout_tab = ResponsivePlayoutTab(self.config_manager)
            self.tab_widget.addTab(self.playout_tab, "📺 Playout")
        else:
            # Fallback if tabs not available
            from PyQt6.QtWidgets import QLabel
            fallback_label = QLabel("Tabs not available - please ensure all dependencies are installed")
            fallback_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.tab_widget.addTab(fallback_label, "Error")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Integrated broadcast system ready")
    
    def _create_integration_controls(self, parent_layout):
        """Create integration control buttons"""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        
        # Demo buttons
        demo_btn = QPushButton("🎬 Create Demo Events")
        demo_btn.clicked.connect(self._create_demo_events)
        controls_layout.addWidget(demo_btn)
        
        sync_btn = QPushButton("🔄 Sync Scheduler to Playout")
        sync_btn.clicked.connect(self._sync_scheduler_to_playout)
        controls_layout.addWidget(sync_btn)
        
        load_playlist_btn = QPushButton("📋 Load Scheduler Playlist")
        load_playlist_btn.clicked.connect(self._load_scheduler_playlist)
        controls_layout.addWidget(load_playlist_btn)
        
        auto_sync_btn = QPushButton("🤖 Auto-Sync Mode")
        auto_sync_btn.setCheckable(True)
        auto_sync_btn.setChecked(True)
        auto_sync_btn.toggled.connect(self._toggle_auto_sync)
        controls_layout.addWidget(auto_sync_btn)
        
        controls_layout.addStretch()
        
        # Status label
        self.integration_status = QPushButton("🟢 Integration Active")
        self.integration_status.setEnabled(False)
        self.integration_status.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        controls_layout.addWidget(self.integration_status)
        
        parent_layout.addWidget(controls_widget)
    
    def _setup_integration(self):
        """Setup integration between scheduler and playout"""
        if not TABS_AVAILABLE or not self.scheduler_tab or not self.playout_tab:
            return
        
        try:
            # Connect scheduler to playout
            self.playout_tab.set_scheduler_tab(self.scheduler_tab)
            
            # Connect scheduler events to playout actions
            self.scheduler_tab.schedule_manager.event_triggered.connect(self._handle_scheduler_event)
            self.scheduler_tab.schedule_manager.event_completed.connect(self._handle_event_completed)
            
            # Connect playout status to scheduler
            self.playout_tab.status_message.connect(self._handle_playout_status)
            self.playout_tab.media_taken_to_air.connect(self._handle_media_on_air)
            
            print("✅ Integration setup complete")
            
        except Exception as e:
            print(f"❌ Integration setup failed: {e}")
    
    def _create_demo_events(self):
        """Create demo scheduler events"""
        if not TABS_AVAILABLE or not self.scheduler_tab:
            return
        
        try:
            # Create demo media events
            now = datetime.now()
            
            # Demo events
            demo_events = [
                {
                    "name": "Morning News Bulletin",
                    "type": EventType.MEDIA_PLAY,
                    "time": now + timedelta(minutes=2),
                    "content": "/path/to/morning_news.mp4",
                    "duration": timedelta(minutes=5),
                    "notes": "Automated morning news broadcast"
                },
                {
                    "name": "Weather Update",
                    "type": EventType.MEDIA_PLAY,
                    "time": now + timedelta(minutes=8),
                    "content": "/path/to/weather_update.mp4",
                    "duration": timedelta(minutes=2),
                    "notes": "Daily weather forecast"
                },
                {
                    "name": "Music Playlist",
                    "type": EventType.PLAYLIST,
                    "time": now + timedelta(minutes=11),
                    "content": "/path/to/music_playlist.m3u",
                    "duration": timedelta(minutes=30),
                    "notes": "Background music playlist"
                },
                {
                    "name": "Emergency Broadcast Test",
                    "type": EventType.MEDIA_PLAY,
                    "time": now + timedelta(minutes=45),
                    "content": "/path/to/emergency_test.mp4",
                    "duration": timedelta(minutes=1),
                    "notes": "Weekly emergency broadcast test"
                },
                {
                    "name": "Evening News",
                    "type": EventType.MEDIA_PLAY,
                    "time": now + timedelta(hours=2),
                    "content": "/path/to/evening_news.mp4",
                    "duration": timedelta(minutes=30),
                    "notes": "Main evening news program"
                }
            ]
            
            # Add events to scheduler
            for event_data in demo_events:
                event = ScheduleEvent(
                    id=f"demo_{int(event_data['time'].timestamp())}",
                    name=event_data["name"],
                    event_type=event_data["type"],
                    scheduled_time=event_data["time"],
                    duration=event_data["duration"],
                    content=event_data["content"],
                    notes=event_data["notes"],
                    auto_execute=True,
                    priority=5
                )
                
                self.scheduler_tab.schedule_manager.add_event(event)
            
            self.statusBar().showMessage(f"Created {len(demo_events)} demo events")
            print(f"✅ Created {len(demo_events)} demo scheduler events")
            
        except Exception as e:
            print(f"❌ Failed to create demo events: {e}")
    
    def _sync_scheduler_to_playout(self):
        """Sync scheduler events to playout system"""
        if not TABS_AVAILABLE or not self.scheduler_tab or not self.playout_tab:
            return
        
        try:
            # Get upcoming events from scheduler
            upcoming_events = self.scheduler_tab.schedule_manager.get_upcoming_events(24)
            
            # Filter media events
            media_events = [event for event in upcoming_events 
                          if event.event_type in [EventType.MEDIA_PLAY, EventType.PLAYLIST]]
            
            # Send to playout system
            if media_events:
                # This would typically be handled by the playout system directly
                # For demo purposes, we'll show the integration
                result = self.playout_tab.execute_command("get_scheduler_playlist")
                if result["status"] == "success":
                    self.statusBar().showMessage(f"Synced {len(media_events)} media events to playout")
                    print(f"✅ Synced {len(media_events)} scheduler events to playout")
                else:
                    self.statusBar().showMessage("Failed to sync scheduler events")
                    print("❌ Failed to sync scheduler events")
            else:
                self.statusBar().showMessage("No media events to sync")
                print("⚠️ No media events found to sync")
                
        except Exception as e:
            print(f"❌ Sync failed: {e}")
    
    def _load_scheduler_playlist(self):
        """Load scheduler playlist in playout system"""
        if not TABS_AVAILABLE or not self.playout_tab:
            return
        
        try:
            # Request scheduler playlist for preview player
            if self.playout_tab.preview_player:
                self.playout_tab.preview_player.scheduler_playlist_requested.emit()
                self.statusBar().showMessage("Scheduler playlist loaded in preview player")
                print("✅ Scheduler playlist loaded in preview player")
            else:
                self.statusBar().showMessage("Preview player not available")
                print("⚠️ Preview player not available")
                
        except Exception as e:
            print(f"❌ Failed to load scheduler playlist: {e}")
    
    def _toggle_auto_sync(self, enabled):
        """Toggle auto-sync mode"""
        if enabled:
            self.integration_timer.start(10000)  # Check every 10 seconds
            self.statusBar().showMessage("Auto-sync mode enabled")
            print("✅ Auto-sync mode enabled")
        else:
            self.integration_timer.stop()
            self.statusBar().showMessage("Auto-sync mode disabled")
            print("🔄 Auto-sync mode disabled")
    
    def _check_integration(self):
        """Check integration status and sync if needed"""
        if not TABS_AVAILABLE or not self.scheduler_tab or not self.playout_tab:
            return
        
        try:
            # Check for upcoming events that need to be prepared
            upcoming_events = self.scheduler_tab.schedule_manager.get_upcoming_events(1)  # Next hour
            
            # Check if any events are due soon (within 5 minutes)
            now = datetime.now()
            due_soon = [event for event in upcoming_events 
                       if (event.scheduled_time - now).total_seconds() <= 300]
            
            if due_soon:
                # Prepare events in playout system
                media_events = [event for event in due_soon 
                              if event.event_type in [EventType.MEDIA_PLAY, EventType.PLAYLIST]]
                
                if media_events:
                    print(f"📅 {len(media_events)} media events due soon, preparing playout system")
                    self.statusBar().showMessage(f"Preparing {len(media_events)} upcoming media events")
                    
                    # Auto-load first event if preview is empty
                    playout_state = self.playout_tab.get_current_state()
                    if not playout_state.get('preview_state', {}).get('file'):
                        first_event = media_events[0]
                        if first_event.content:
                            self.playout_tab.load_preview_media(first_event.content)
                            print(f"🎬 Auto-loaded {first_event.name} in preview")
            
            # Update integration status
            self._update_integration_status()
            
        except Exception as e:
            print(f"❌ Integration check failed: {e}")
    
    def _update_integration_status(self):
        """Update integration status indicator"""
        if not TABS_AVAILABLE:
            self.integration_status.setText("🔴 Components Missing")
            self.integration_status.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            return
        
        if self.scheduler_tab and self.playout_tab:
            # Check if both systems are active
            scheduler_active = hasattr(self.scheduler_tab, 'schedule_manager')
            playout_active = self.playout_tab.get_current_state().get('audio_system_active', False)
            
            if scheduler_active and playout_active:
                self.integration_status.setText("🟢 Integration Active")
                self.integration_status.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
            else:
                self.integration_status.setText("🟡 Partial Integration")
                self.integration_status.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
    
    def _handle_scheduler_event(self, event):
        """Handle scheduler event trigger"""
        print(f"📅 Scheduler event triggered: {event.name}")
        
        # Route event to appropriate playout action
        if event.event_type == EventType.MEDIA_PLAY:
            if event.content:
                # Load media in preview first
                self.playout_tab.load_preview_media(event.content)
                # Then send to program
                self.playout_tab.execute_command("send_to_program")
                # Take to air if auto-execute is enabled
                if event.auto_execute:
                    self.playout_tab.execute_command("take_to_air")
        
        elif event.event_type == EventType.PLAYLIST:
            # Load playlist in preview
            if self.playout_tab.preview_player:
                self.playout_tab.preview_player.scheduler_playlist_requested.emit()
        
        elif event.event_type == EventType.STREAM_START:
            # Start streaming
            self.playout_tab.execute_command("stream_program")
        
        elif event.event_type == EventType.STREAM_STOP:
            # Stop streaming
            self.playout_tab.execute_command("stop_streaming")
        
        self.statusBar().showMessage(f"Executed scheduler event: {event.name}")
    
    def _handle_event_completed(self, event_id, success):
        """Handle scheduler event completion"""
        status = "completed" if success else "failed"
        print(f"📅 Scheduler event {event_id} {status}")
        
        if success:
            self.statusBar().showMessage(f"Event {event_id} completed successfully")
        else:
            self.statusBar().showMessage(f"Event {event_id} failed")
    
    def _handle_playout_status(self, message, timeout):
        """Handle playout status updates"""
        print(f"📺 Playout: {message}")
        
        # Update status bar briefly
        self.statusBar().showMessage(f"Playout: {message}", timeout)
    
    def _handle_media_on_air(self, media_path):
        """Handle media taken to air"""
        print(f"📺 Media ON AIR: {media_path}")
        
        # Update scheduler with on-air status
        if self.scheduler_tab:
            # This could update scheduler to show what's currently on air
            pass
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Stop timers
            if hasattr(self, 'integration_timer'):
                self.integration_timer.stop()
            
            # Cleanup tabs
            if self.playout_tab:
                self.playout_tab.cleanup()
            if self.scheduler_tab:
                self.scheduler_tab.cleanup()
            
            print("✅ Integrated broadcast system shutdown complete")
            
        except Exception as e:
            print(f"❌ Shutdown error: {e}")
        
        event.accept()


def main():
    """Main function to run the integration example"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Integrated Broadcast System")
    app.setApplicationVersion("1.0.0")
    
    # Create main window
    window = IntegratedBroadcastSystem()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
