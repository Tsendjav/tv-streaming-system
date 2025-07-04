#!/usr/bin/env python3
"""
Enhanced Scheduler Tab - Complete Version
Advanced scheduling system for automated playout and streaming
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Fallback imports
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


# =============================================================================
# SCHEDULE EVENT MODELS
# =============================================================================

class EventType(Enum):
    """Types of scheduled events"""
    MEDIA_PLAY = "media_play"
    STREAM_START = "stream_start"
    STREAM_STOP = "stream_stop"
    AMCP_COMMAND = "amcp_command"
    PLAYLIST = "playlist"
    AUTOMATION = "automation"
    REMINDER = "reminder"


class EventStatus(Enum):
    """Status of scheduled events"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class ScheduleEvent:
    """Scheduled event data class"""
    id: str
    name: str
    event_type: EventType
    scheduled_time: datetime
    duration: Optional[timedelta] = None
    content: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: EventStatus = EventStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    repeat_pattern: Optional[str] = None  # daily, weekly, monthly
    repeat_until: Optional[datetime] = None
    priority: int = 5  # 1-10 scale
    auto_execute: bool = True
    notes: str = ""
    
    @property
    def end_time(self) -> Optional[datetime]:
        """Calculate end time if duration is set"""
        if self.duration:
            return self.scheduled_time + self.duration
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if event is currently active"""
        now = datetime.now()
        if self.end_time:
            return self.scheduled_time <= now <= self.end_time
        return False
    
    @property
    def is_overdue(self) -> bool:
        """Check if event is overdue"""
        return datetime.now() > self.scheduled_time and self.status == EventStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "event_type": self.event_type.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "duration": self.duration.total_seconds() if self.duration else None,
            "content": self.content,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "repeat_pattern": self.repeat_pattern,
            "repeat_until": self.repeat_until.isoformat() if self.repeat_until else None,
            "priority": self.priority,
            "auto_execute": self.auto_execute,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleEvent':
        """Create instance from dictionary"""
        # Handle datetime fields
        data["scheduled_time"] = datetime.fromisoformat(data["scheduled_time"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_modified"] = datetime.fromisoformat(data["last_modified"])
        
        if data.get("duration"):
            data["duration"] = timedelta(seconds=data["duration"])
        
        if data.get("repeat_until"):
            data["repeat_until"] = datetime.fromisoformat(data["repeat_until"])
        
        # Handle enums
        data["event_type"] = EventType(data["event_type"])
        data["status"] = EventStatus(data["status"])
        
        return cls(**data)


# =============================================================================
# SCHEDULE MANAGER
# =============================================================================

class ScheduleManager(QObject):
    """Manages schedule events and execution"""
    
    # Signals
    event_triggered = pyqtSignal(object)  # ScheduleEvent
    event_completed = pyqtSignal(str, bool)  # event_id, success
    schedule_updated = pyqtSignal()
    
    def __init__(self, schedule_file: str = "data/schedule.json"):
        super().__init__()
        self.schedule_file = Path(schedule_file)
        self.events: Dict[str, ScheduleEvent] = {}
        self.logger = get_logger(__name__)
        
        # Execution timer
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._check_events)
        self.execution_timer.start(1000)  # Check every second
        
        self._load_schedule()
    
    def add_event(self, event: ScheduleEvent) -> bool:
        """Add a new scheduled event"""
        try:
            event.last_modified = datetime.now()
            self.events[event.id] = event
            self._save_schedule()
            self.schedule_updated.emit()
            self.logger.info(f"Added scheduled event: {event.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add event: {e}")
            return False
    
    def update_event(self, event: ScheduleEvent) -> bool:
        """Update an existing event"""
        try:
            event.last_modified = datetime.now()
            self.events[event.id] = event
            self._save_schedule()
            self.schedule_updated.emit()
            self.logger.info(f"Updated scheduled event: {event.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update event: {e}")
            return False
    
    def remove_event(self, event_id: str) -> bool:
        """Remove a scheduled event"""
        try:
            if event_id in self.events:
                event_name = self.events[event_id].name
                del self.events[event_id]
                self._save_schedule()
                self.schedule_updated.emit()
                self.logger.info(f"Removed scheduled event: {event_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove event: {e}")
            return False
    
    def get_events_for_date(self, date: datetime) -> List[ScheduleEvent]:
        """Get events for a specific date"""
        events = []
        for event in self.events.values():
            if event.scheduled_time.date() == date.date():
                events.append(event)
        return sorted(events, key=lambda e: e.scheduled_time)
    
    def get_upcoming_events(self, hours: int = 24) -> List[ScheduleEvent]:
        """Get upcoming events within specified hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        upcoming = []
        for event in self.events.values():
            if (now <= event.scheduled_time <= cutoff and 
                event.status == EventStatus.PENDING):
                upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.scheduled_time)
    
    def _check_events(self):
        """Check for events that need to be executed"""
        now = datetime.now()
        
        for event in self.events.values():
            if (event.status == EventStatus.PENDING and 
                event.auto_execute and 
                event.scheduled_time <= now):
                
                self._execute_event(event)
    
    def _execute_event(self, event: ScheduleEvent):
        """Execute a scheduled event"""
        try:
            event.status = EventStatus.RUNNING
            self.event_triggered.emit(event)
            
            # Simulate execution (actual implementation would vary by event type)
            success = True  # This would be determined by actual execution
            
            if success:
                event.status = EventStatus.COMPLETED
            else:
                event.status = EventStatus.FAILED
            
            self.event_completed.emit(event.id, success)
            self._save_schedule()
            
        except Exception as e:
            self.logger.error(f"Failed to execute event {event.name}: {e}")
            event.status = EventStatus.FAILED
            self.event_completed.emit(event.id, False)
    
    def _load_schedule(self):
        """Load schedule from file"""
        try:
            if self.schedule_file.exists():
                with open(self.schedule_file, 'r') as f:
                    data = json.load(f)
                    
                    self.events = {}
                    for event_data in data.get('events', []):
                        event = ScheduleEvent.from_dict(event_data)
                        self.events[event.id] = event
                
                self.logger.info(f"Loaded {len(self.events)} scheduled events")
            else:
                self.logger.info("No existing schedule file found")
                
        except Exception as e:
            self.logger.error(f"Failed to load schedule: {e}")
    
    def _save_schedule(self):
        """Save schedule to file"""
        try:
            self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "events": [event.to_dict() for event in self.events.values()]
            }
            
            with open(self.schedule_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save schedule: {e}")


# =============================================================================
# EVENT CREATION DIALOG
# =============================================================================

class EventCreateDialog(QDialog):
    """Dialog for creating/editing scheduled events"""
    
    def __init__(self, event: Optional[ScheduleEvent] = None, parent=None):
        super().__init__(parent)
        self.event = event
        self.is_editing = event is not None
        
        self.setWindowTitle("Edit Event" if self.is_editing else "Create New Event")
        self.setModal(True)
        self.setFixedSize(500, 600)
        
        self._init_ui()
        
        if self.is_editing:
            self._populate_fields()
    
    def _init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Event name")
        basic_layout.addRow("Name:", self.name_edit)
        
        self.type_combo = QComboBox()
        for event_type in EventType:
            self.type_combo.addItem(event_type.value.replace('_', ' ').title(), event_type)
        basic_layout.addRow("Type:", self.type_combo)
        
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("Media file path, AMCP command, etc.")
        basic_layout.addRow("Content:", self.content_edit)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_content)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.content_edit)
        content_layout.addWidget(browse_btn)
        basic_layout.addRow("", content_layout)
        
        layout.addWidget(basic_group)
        
        # Timing
        timing_group = QGroupBox("Timing")
        timing_layout = QFormLayout(timing_group)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        timing_layout.addRow("Date:", self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        timing_layout.addRow("Time:", self.time_edit)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 24*60)  # 0 to 24 hours in minutes
        self.duration_spin.setSuffix(" minutes")
        self.duration_spin.setSpecialValueText("No duration")
        timing_layout.addRow("Duration:", self.duration_spin)
        
        layout.addWidget(timing_group)
        
        # Repeat settings
        repeat_group = QGroupBox("Repeat Settings")
        repeat_layout = QFormLayout(repeat_group)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["No Repeat", "Daily", "Weekly", "Monthly"])
        repeat_layout.addRow("Repeat:", self.repeat_combo)
        
        self.repeat_until_edit = QDateEdit()
        self.repeat_until_edit.setDate(QDate.currentDate().addDays(30))
        self.repeat_until_edit.setCalendarPopup(True)
        self.repeat_until_edit.setEnabled(False)
        repeat_layout.addRow("Repeat Until:", self.repeat_until_edit)
        
        self.repeat_combo.currentTextChanged.connect(
            lambda text: self.repeat_until_edit.setEnabled(text != "No Repeat")
        )
        
        layout.addWidget(repeat_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        options_layout.addRow("Priority:", self.priority_spin)
        
        self.auto_execute_cb = QCheckBox("Auto Execute")
        self.auto_execute_cb.setChecked(True)
        options_layout.addRow("", self.auto_execute_cb)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes...")
        options_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 Test")
        test_btn.clicked.connect(self._test_event)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save" if self.is_editing else "Create")
        save_btn.clicked.connect(self._save_event)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields when editing existing event"""
        if not self.event:
            return
        
        self.name_edit.setText(self.event.name)
        
        # Set event type
        type_index = self.type_combo.findData(self.event.event_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        if self.event.content:
            self.content_edit.setText(self.event.content)
        
        # Set date and time
        self.date_edit.setDate(QDate(self.event.scheduled_time.date()))
        self.time_edit.setTime(QTime(self.event.scheduled_time.time()))
        
        # Set duration
        if self.event.duration:
            self.duration_spin.setValue(int(self.event.duration.total_seconds() / 60))
        
        # Set repeat settings
        if self.event.repeat_pattern:
            repeat_text = self.event.repeat_pattern.title()
            index = self.repeat_combo.findText(repeat_text)
            if index >= 0:
                self.repeat_combo.setCurrentIndex(index)
        
        if self.event.repeat_until:
            self.repeat_until_edit.setDate(QDate(self.event.repeat_until.date()))
        
        # Set options
        self.priority_spin.setValue(self.event.priority)
        self.auto_execute_cb.setChecked(self.event.auto_execute)
        self.notes_edit.setPlainText(self.event.notes)
    
    def _browse_content(self):
        """Browse for content file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac);;All Files (*)"
        )
        
        if file_path:
            self.content_edit.setText(file_path)
    
    def _test_event(self):
        """Test the event configuration"""
        try:
            event = self._create_event_from_fields()
            if event:
                QMessageBox.information(
                    self,
                    "Test Event",
                    f"Event '{event.name}' is configured correctly.\n\n"
                    f"Scheduled for: {event.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Type: {event.event_type.value}\n"
                    f"Content: {event.content or 'None'}"
                )
        except Exception as e:
            QMessageBox.warning(self, "Test Failed", f"Event configuration error:\n{e}")
    
    def _save_event(self):
        """Save the event"""
        try:
            event = self._create_event_from_fields()
            if event:
                self.event = event
                self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save event:\n{e}")
    
    def _create_event_from_fields(self) -> Optional[ScheduleEvent]:
        """Create event from form fields - Alternative fix"""
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("Event name is required")
        
        # PyQt6 compatible date/time conversion
        qdate = self.date_edit.date()
        qtime = self.time_edit.time()
        
        # Convert QDate to Python date
        date = datetime.date(qdate.year(), qdate.month(), qdate.day())
        # Convert QTime to Python time  
        time_obj = datetime.time(qtime.hour(), qtime.minute(), qtime.second())
        
        scheduled_time = datetime.combine(date, time_obj)
        
        # Get duration
        duration = None
        if self.duration_spin.value() > 0:
            duration = timedelta(minutes=self.duration_spin.value())
        
        # Get repeat settings
        repeat_pattern = None
        repeat_until = None
        repeat_text = self.repeat_combo.currentText()
        if repeat_text != "No Repeat":
            repeat_pattern = repeat_text.lower()
            
            qdate_until = self.repeat_until_edit.date()
            date_until = datetime.date(qdate_until.year(), qdate_until.month(), qdate_until.day())
            repeat_until = datetime.combine(date_until, datetime.time(23, 59, 59))
        
        # Create event
        event_id = self.event.id if self.is_editing else f"event_{int(datetime.now().timestamp())}"
        
        return ScheduleEvent(
            id=event_id,
            name=name,
            event_type=self.type_combo.currentData(),
            scheduled_time=scheduled_time,
            duration=duration,
            content=self.content_edit.text().strip() or None,
            repeat_pattern=repeat_pattern,
            repeat_until=repeat_until,
            priority=self.priority_spin.value(),
            auto_execute=self.auto_execute_cb.isChecked(),
            notes=self.notes_edit.toPlainText().strip()
        )
    
    def get_event(self) -> Optional[ScheduleEvent]:
        """Get the created/edited event"""
        return self.event


# =============================================================================
# SCHEDULE TABLE MODEL
# =============================================================================

class ScheduleTableModel(QAbstractTableModel):
    """Table model for schedule events"""
    
    def __init__(self, events: List[ScheduleEvent] = None):
        super().__init__()
        self.events = events or []
        self.headers = [
            "Time", "Name", "Type", "Content", "Duration", "Status", "Priority"
        ]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.events)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.events):
            return None
        
        event = self.events[index.row()]
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:  # Time
                return event.scheduled_time.strftime("%H:%M:%S")
            elif col == 1:  # Name
                return event.name
            elif col == 2:  # Type
                return event.event_type.value.replace('_', ' ').title()
            elif col == 3:  # Content
                if event.content:
                    return Path(event.content).name if len(event.content) > 30 else event.content
                return "-"
            elif col == 4:  # Duration
                if event.duration:
                    total_seconds = int(event.duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    if hours > 0:
                        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        return f"{minutes:02d}:{seconds:02d}"
                return "-"
            elif col == 5:  # Status
                return event.status.value.title()
            elif col == 6:  # Priority
                return str(event.priority)
        
        elif role == Qt.ItemDataRole.UserRole:
            return event.id
        
        elif role == Qt.ItemDataRole.ToolTipRole:
            tooltip = f"Event: {event.name}\n"
            tooltip += f"Scheduled: {event.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            tooltip += f"Type: {event.event_type.value}\n"
            if event.content:
                tooltip += f"Content: {event.content}\n"
            if event.notes:
                tooltip += f"Notes: {event.notes}\n"
            return tooltip
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color coding based on status
            if event.status == EventStatus.COMPLETED:
                return QColor(40, 167, 69)  # Green
            elif event.status == EventStatus.FAILED:
                return QColor(220, 53, 69)  # Red
            elif event.status == EventStatus.RUNNING:
                return QColor(255, 193, 7)  # Yellow
            elif event.is_overdue:
                return QColor(255, 108, 36)  # Orange
            return None
        
        return None
    
    def update_events(self, events: List[ScheduleEvent]):
        """Update events list"""
        self.beginResetModel()
        self.events = events
        self.endResetModel()
    
    def get_event(self, index: QModelIndex) -> Optional[ScheduleEvent]:
        """Get event at index"""
        if index.isValid() and index.row() < len(self.events):
            return self.events[index.row()]
        return None


# =============================================================================
# MAIN SCHEDULER TAB
# =============================================================================

class SchedulerTab(QWidget):
    """Enhanced scheduler tab with complete scheduling functionality"""
    
    # Signals
    status_message = pyqtSignal(str, int)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Schedule manager
        self.schedule_manager = ScheduleManager()
        
        # Current date
        self.current_date = QDate.currentDate()
        
        # UI components
        self.date_label = None
        self.schedule_table = None
        self.schedule_model = None
        self.upcoming_list = None
        
        self._init_ui()
        self._connect_signals()
        self._load_schedule_for_date()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_schedule)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
        self.logger.debug("Scheduler tab initialized")
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Top controls
        controls_section = self._create_controls_section()
        layout.addWidget(controls_section)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Schedule table
        left_panel = self._create_schedule_panel()
        content_splitter.addWidget(left_panel)
        
        # Right side - Upcoming events and controls
        right_panel = self._create_info_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([600, 300])
        layout.addWidget(content_splitter)
    
    def _create_controls_section(self) -> QWidget:
        """Create top controls section"""
        group = QGroupBox("⏰ Schedule Controls")
        layout = QGridLayout(group)
        
        # Date navigation
        layout.addWidget(QLabel("Date:"), 0, 0)
        
        prev_day_btn = QPushButton("◀ Previous")
        prev_day_btn.clicked.connect(self._previous_day)
        layout.addWidget(prev_day_btn, 0, 1)
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 4px;")
        layout.addWidget(self.date_label, 0, 2)
        
        next_day_btn = QPushButton("Next ▶")
        next_day_btn.clicked.connect(self._next_day)
        layout.addWidget(next_day_btn, 0, 3)
        
        today_btn = QPushButton("📅 Today")
        today_btn.clicked.connect(self._go_to_today)
        layout.addWidget(today_btn, 0, 4)
        
        # Action buttons
        create_btn = QPushButton("➕ Create Event")
        create_btn.clicked.connect(self._create_event)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(create_btn, 1, 0)
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self._import_schedule)
        layout.addWidget(import_btn, 1, 1)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self._export_schedule)
        layout.addWidget(export_btn, 1, 2)
        
        # Auto scheduler toggle
        self.auto_scheduler_cb = QCheckBox("🤖 Auto Scheduler")
        self.auto_scheduler_cb.setChecked(True)
        self.auto_scheduler_cb.toggled.connect(self._toggle_auto_scheduler)
        layout.addWidget(self.auto_scheduler_cb, 1, 3, 1, 2)
        
        self._update_date_label()
        return group
    
    def _create_schedule_panel(self) -> QWidget:
        """Create schedule table panel"""
        group = QGroupBox("📋 Schedule Timeline")
        layout = QVBoxLayout(group)
        
        # Schedule table
        self.schedule_table = QTableView()
        self.schedule_model = ScheduleTableModel()
        self.schedule_table.setModel(self.schedule_model)
        
        self.schedule_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setSortingEnabled(True)
        self.schedule_table.verticalHeader().setVisible(False)
        
        # Context menu
        self.schedule_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.schedule_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Double-click to edit
        self.schedule_table.doubleClicked.connect(self._edit_selected_event)
        
        layout.addWidget(self.schedule_table)
        
        # Quick action buttons
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self._edit_selected_event)
        button_layout.addWidget(edit_btn)
        
        duplicate_btn = QPushButton("📄 Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_selected_event)
        button_layout.addWidget(duplicate_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self._delete_selected_event)
        delete_btn.setStyleSheet("QPushButton { color: #dc3545; }")
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        execute_btn = QPushButton("▶️ Execute Now")
        execute_btn.clicked.connect(self._execute_selected_event)
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_layout.addWidget(execute_btn)
        
        layout.addLayout(button_layout)
        
        return group
    
    def _create_info_panel(self) -> QWidget:
        """Create information panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Upcoming events
        upcoming_group = QGroupBox("⏳ Upcoming Events")
        upcoming_layout = QVBoxLayout(upcoming_group)
        
        self.upcoming_list = QListWidget()
        self.upcoming_list.setMaximumHeight(200)
        upcoming_layout.addWidget(self.upcoming_list)
        
        layout.addWidget(upcoming_group)
        
        # Statistics
        stats_group = QGroupBox("📊 Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.total_events_label = QLabel("0")
        stats_layout.addRow("Total Events:", self.total_events_label)
        
        self.pending_events_label = QLabel("0")
        stats_layout.addRow("Pending:", self.pending_events_label)
        
        self.completed_events_label = QLabel("0")
        stats_layout.addRow("Completed:", self.completed_events_label)
        
        self.failed_events_label = QLabel("0")
        stats_layout.addRow("Failed:", self.failed_events_label)
        
        layout.addWidget(stats_group)
        
        # Quick templates
        templates_group = QGroupBox("📝 Quick Templates")
        templates_layout = QVBoxLayout(templates_group)
        
        templates = [
            ("🎵 Music Playlist", EventType.PLAYLIST),
            ("📺 Stream Start", EventType.STREAM_START),
            ("📹 Media Play", EventType.MEDIA_PLAY),
            ("🔄 AMCP Command", EventType.AMCP_COMMAND)
        ]
        
        for name, event_type in templates:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, et=event_type: self._create_template_event(et))
            templates_layout.addWidget(btn)
        
        layout.addWidget(templates_group)
        layout.addStretch()
        
        return widget
    
    def _connect_signals(self):
        """Connect signals"""
        self.schedule_manager.schedule_updated.connect(self._on_schedule_updated)
        self.schedule_manager.event_triggered.connect(self._on_event_triggered)
        self.schedule_manager.event_completed.connect(self._on_event_completed)
    
    def _update_date_label(self):
        """Update date label"""
        date_str = self.current_date.toString("dddd, MMMM d, yyyy")
        self.date_label.setText(date_str)
    
    def _load_schedule_for_date(self):
        """Load schedule for current date - Alternative fix"""
        # PyQt6 compatible date conversion
        qdate = self.current_date
        date = datetime(qdate.year(), qdate.month(), qdate.day())
        events = self.schedule_manager.get_events_for_date(date)
        
        self.schedule_model.update_events(events)
        self.schedule_table.resizeColumnsToContents()
        
        self._update_statistics()
        self._update_upcoming_events()
    
    def _update_statistics(self):
        """Update statistics display"""
        events = self.schedule_model.events
        
        total = len(events)
        pending = len([e for e in events if e.status == EventStatus.PENDING])
        completed = len([e for e in events if e.status == EventStatus.COMPLETED])
        failed = len([e for e in events if e.status == EventStatus.FAILED])
        
        self.total_events_label.setText(str(total))
        self.pending_events_label.setText(str(pending))
        self.completed_events_label.setText(str(completed))
        self.failed_events_label.setText(str(failed))
    
    def _update_upcoming_events(self):
        """Update upcoming events list"""
        self.upcoming_list.clear()
        
        upcoming = self.schedule_manager.get_upcoming_events(24)  # Next 24 hours
        
        for event in upcoming[:10]:  # Show only first 10
            time_str = event.scheduled_time.strftime("%m/%d %H:%M")
            item_text = f"{time_str} - {event.name}"
            
            item = QListWidgetItem(item_text)
            if event.is_overdue:
                item.setForeground(QColor(220, 53, 69))  # Red for overdue
            elif event.priority >= 8:
                item.setForeground(QColor(255, 193, 7))  # Yellow for high priority
            
            self.upcoming_list.addItem(item)
    
    def _previous_day(self):
        """Go to previous day"""
        self.current_date = self.current_date.addDays(-1)
        self._update_date_label()
        self._load_schedule_for_date()
    
    def _next_day(self):
        """Go to next day"""
        self.current_date = self.current_date.addDays(1)
        self._update_date_label()
        self._load_schedule_for_date()
    
    def _go_to_today(self):
        """Go to today"""
        self.current_date = QDate.currentDate()
        self._update_date_label()
        self._load_schedule_for_date()
    
    def _create_event(self):
        """Create new event"""
        dialog = EventCreateDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event = dialog.get_event()
            if event:
                if self.schedule_manager.add_event(event):
                    self.status_message.emit(f"Created event: {event.name}", 3000)
                else:
                    self.status_message.emit("Failed to create event", 5000)
    
    def _create_template_event(self, event_type: Enum):
        """Create event from template"""
        # Create basic event with current date and time + 1 hour
        current_datetime = datetime.combine(
            self.current_date.toPyDate(),  # toPython() оронд toPyDate() ашиглана
            datetime.now().time()
        ) + timedelta(hours=1)
        
        template_event = ScheduleEvent(
            id=f"event_{int(datetime.now().timestamp())}",
            name=f"New {event_type.value.replace('_', ' ').title()}",
            event_type=event_type,
            scheduled_time=current_datetime
        )
        
        dialog = EventCreateDialog(template_event, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event = dialog.get_event()
            if event:
                if self.schedule_manager.add_event(event):
                    self.status_message.emit(f"Created event: {event.name}", 3000)
                else:
                    self.status_message.emit("Failed to create event", 5000)
    
    def _edit_selected_event(self):
        """Edit selected event"""
        current = self.schedule_table.currentIndex()
        if current.isValid():
            event = self.schedule_model.get_event(current)
            if event:
                dialog = EventCreateDialog(event, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    updated_event = dialog.get_event()
                    if updated_event:
                        if self.schedule_manager.update_event(updated_event):
                            self.status_message.emit(f"Updated event: {updated_event.name}", 3000)
                        else:
                            self.status_message.emit("Failed to update event", 5000)
    
    def _duplicate_selected_event(self):
        """Duplicate selected event"""
        current = self.schedule_table.currentIndex()
        if current.isValid():
            event = self.schedule_model.get_event(current)
            if event:
                # Create duplicate with new ID and name
                duplicate = ScheduleEvent(
                    id=f"event_{int(datetime.now().timestamp())}",
                    name=f"{event.name} (Copy)",
                    event_type=event.event_type,
                    scheduled_time=event.scheduled_time + timedelta(hours=1),
                    duration=event.duration,
                    content=event.content,
                    parameters=event.parameters.copy(),
                    repeat_pattern=event.repeat_pattern,
                    repeat_until=event.repeat_until,
                    priority=event.priority,
                    auto_execute=event.auto_execute,
                    notes=event.notes
                )
                
                if self.schedule_manager.add_event(duplicate):
                    self.status_message.emit(f"Duplicated event: {duplicate.name}", 3000)
                else:
                    self.status_message.emit("Failed to duplicate event", 5000)
    
    def _delete_selected_event(self):
        """Delete selected event"""
        current = self.schedule_table.currentIndex()
        if current.isValid():
            event = self.schedule_model.get_event(current)
            if event:
                reply = QMessageBox.question(
                    self,
                    "Delete Event",
                    f"Are you sure you want to delete '{event.name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.schedule_manager.remove_event(event.id):
                        self.status_message.emit(f"Deleted event: {event.name}", 3000)
                    else:
                        self.status_message.emit("Failed to delete event", 5000)
    
    def _execute_selected_event(self):
        """Execute selected event immediately"""
        current = self.schedule_table.currentIndex()
        if current.isValid():
            event = self.schedule_model.get_event(current)
            if event:
                reply = QMessageBox.question(
                    self,
                    "Execute Event",
                    f"Execute '{event.name}' now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.schedule_manager._execute_event(event)
                    self.status_message.emit(f"Executing event: {event.name}", 3000)
    
    def _show_context_menu(self, position):
        """Show context menu for schedule table"""
        index = self.schedule_table.indexAt(position)
        if not index.isValid():
            return
        
        event = self.schedule_model.get_event(index)
        if not event:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("✏️ Edit", self)
        edit_action.triggered.connect(self._edit_selected_event)
        menu.addAction(edit_action)
        
        # Duplicate action
        duplicate_action = QAction("📄 Duplicate", self)
        duplicate_action.triggered.connect(self._duplicate_selected_event)
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        # Execute action
        execute_action = QAction("▶️ Execute Now", self)
        execute_action.triggered.connect(self._execute_selected_event)
        execute_action.setEnabled(event.status == EventStatus.PENDING)
        menu.addAction(execute_action)
        
        # Skip action
        if event.status == EventStatus.PENDING:
            skip_action = QAction("⏭️ Skip", self)
            skip_action.triggered.connect(lambda: self._set_event_status(event.id, EventStatus.SKIPPED))
            menu.addAction(skip_action)
        
        # Reset action
        if event.status in [EventStatus.COMPLETED, EventStatus.FAILED, EventStatus.SKIPPED]:
            reset_action = QAction("🔄 Reset", self)
            reset_action.triggered.connect(lambda: self._set_event_status(event.id, EventStatus.PENDING))
            menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self._delete_selected_event)
        menu.addAction(delete_action)
        
        menu.exec(self.schedule_table.mapToGlobal(position))
    
    def _set_event_status(self, event_id: str, status: EventStatus):
        """Set event status"""
        if event_id in self.schedule_manager.events:
            event = self.schedule_manager.events[event_id]
            event.status = status
            event.last_modified = datetime.now()
            self.schedule_manager._save_schedule()
            self.schedule_manager.schedule_updated.emit()
    
    def _toggle_auto_scheduler(self, enabled: bool):
        """Toggle auto scheduler"""
        if enabled:
            self.schedule_manager.execution_timer.start(1000)
            self.status_message.emit("Auto scheduler enabled", 3000)
        else:
            self.schedule_manager.execution_timer.stop()
            self.status_message.emit("Auto scheduler disabled", 3000)
    
    def _import_schedule(self):
        """Import schedule from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Schedule",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                imported_count = 0
                for event_data in data.get('events', []):
                    try:
                        event = ScheduleEvent.from_dict(event_data)
                        # Generate new ID to avoid conflicts
                        event.id = f"imported_{int(datetime.now().timestamp())}_{imported_count}"
                        
                        if self.schedule_manager.add_event(event):
                            imported_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to import event: {e}")
                
                self.status_message.emit(f"Imported {imported_count} events", 3000)
                
            except Exception as e:
                self.logger.error(f"Failed to import schedule: {e}")
                self.status_message.emit(f"Import failed: {e}", 5000)
    
    def _export_schedule(self):
        """Export schedule to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Schedule",
            f"schedule_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Export all events or just current date?
                reply = QMessageBox.question(
                    self,
                    "Export Options",
                    "Export all events or just current date?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Export all events
                    events_to_export = list(self.schedule_manager.events.values())
                else:
                    # Export current date only
                    events_to_export = self.schedule_model.events
                
                data = {
                    "version": "1.0",
                    "exported_at": datetime.now().isoformat(),
                    "export_type": "all" if reply == QMessageBox.StandardButton.Yes else "date",
                    "date": self.current_date.toString("yyyy-MM-dd") if reply == QMessageBox.StandardButton.No else None,
                    "events": [event.to_dict() for event in events_to_export]
                }
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.status_message.emit(f"Exported {len(events_to_export)} events", 3000)
                
            except Exception as e:
                self.logger.error(f"Failed to export schedule: {e}")
                self.status_message.emit(f"Export failed: {e}", 5000)
    
    def _refresh_schedule(self):
        """Refresh schedule display"""
        self._load_schedule_for_date()
    
    def _on_schedule_updated(self):
        """Handle schedule update"""
        self._load_schedule_for_date()
    
    def _on_event_triggered(self, event: ScheduleEvent):
        """Handle event trigger"""
        self.status_message.emit(f"Executing: {event.name}", 3000)
    
    def _on_event_completed(self, event_id: str, success: bool):
        """Handle event completion"""
        if event_id in self.schedule_manager.events:
            event = self.schedule_manager.events[event_id]
            status = "completed" if success else "failed"
            self.status_message.emit(f"Event {event.name} {status}", 3000)
    
    def refresh(self):
        """Refresh the scheduler tab"""
        self._refresh_schedule()
        self.status_message.emit("Scheduler refreshed", 2000)
    
    def cleanup(self):
        """Cleanup resources when tab is closed"""
        try:
            if hasattr(self, 'refresh_timer') and self.refresh_timer:
                self.refresh_timer.stop()
        except Exception as e:
            self.logger.error(f"Error during scheduler tab cleanup: {e}")


# =============================================================================
# EXPORT FOR INTEGRATION
# =============================================================================

__all__ = [
    'SchedulerTab',
    'ScheduleEvent',
    'ScheduleManager',
    'EventType',
    'EventStatus',
    'EventCreateDialog'
]


# =============================================================================
# TESTING AND STANDALONE USAGE
# =============================================================================

if __name__ == "__main__":
    """Test the scheduler tab standalone"""
    import sys
    
    class TestConfigManager:
        """Simple config manager for testing"""
        pass
    
    app = QApplication(sys.argv)
    
    # Create test config
    config = TestConfigManager()
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Scheduler Tab Test")
    window.setGeometry(100, 100, 1200, 800)
    
    # Create scheduler tab
    scheduler_tab = SchedulerTab(config)
    window.setCentralWidget(scheduler_tab)
    
    # Connect signals for testing
    scheduler_tab.status_message.connect(lambda msg, timeout: print(f"Status: {msg}"))
    
    window.show()
    sys.exit(app.exec())
        