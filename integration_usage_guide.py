#!/usr/bin/env python3
"""
Integration Usage Guide - Tab Integration System хэрэглэх заавар
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Import integration system
try:
    from tab_integration_system import (
        setup_integration_system, 
        IntegrationConfig, 
        MongolianSystemMessages,
        EventType,
        SystemEvent
    )
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    print("⚠️ Integration system not available")

# =============================================================================
# MAIN WINDOW ENHANCEMENT FUNCTION
# =============================================================================

def integrate_with_existing_main_window(MainWindowClass):
    """
    Энэ функц нь одоо байгаа main window class-ыг integration system-тэй холбодог
    
    Хэрэглэх арга:
    ```python
    from ui.main_window import ProfessionalStreamingStudio
    from integration_usage_guide import integrate_with_existing_main_window
    
    # Enhanced version үүсгэх
    EnhancedStudio = integrate_with_existing_main_window(ProfessionalStreamingStudio)
    main_win = EnhancedStudio(config_manager, app)
    ```
    """
    
    if not INTEGRATION_AVAILABLE:
        print("Integration system не доступен, возвращаем оригинальный класс")
        return MainWindowClass
    
    class EnhancedMainWindow(MainWindowClass):
        def __init__(self, config_manager, app):
            # Эхлээд анхны class-ыг эхлүүлэх
            super().__init__(config_manager, app)
            
            # Integration system тохируулах
            self._setup_integration_system()
            
            # Integration menu items нэмэх
            self._add_integration_menu_items()
            
            # Integration signals холбох
            self._connect_integration_signals()
        
        def _setup_integration_system(self):
            """Integration system тохируулах"""
            try:
                # Configuration үүсгэх
                integration_config = IntegrationConfig()
                integration_config.monitoring_enabled = True
                integration_config.automation_enabled = True
                integration_config.use_localized_messages = True
                
                # Integration system тохируулах
                self.integration_system, self.system_monitor = setup_integration_system(
                    self, self.config_manager, integration_config
                )
                
                self.logger.info("Integration system setup successful")
                self._show_status_message(
                    MongolianSystemMessages.get_message("integration_ready"), 3000
                )
                
            except Exception as e:
                self.logger.error(f"Failed to add integration menu items: {e}")
        
        def _connect_integration_signals(self):
            """Integration signals холбох"""
            if not hasattr(self, 'integration_system'):
                return
            
            try:
                # Event bus signals холбох
                self.integration_system.event_bus.global_event.connect(self._on_integration_event)
                
                # Integration manager signals
                self.integration_system.integration_manager.global_status_update.connect(
                    self._on_status_update
                )
                self.integration_system.integration_manager.emergency_stop_triggered.connect(
                    self._on_emergency_stop_triggered
                )
                
                # Workflow engine signals
                self.integration_system.workflow_engine.workflow_started.connect(
                    self._on_workflow_started
                )
                self.integration_system.workflow_engine.workflow_completed.connect(
                    self._on_workflow_completed
                )
                
            except Exception as e:
                self.logger.error(f"Failed to connect integration signals: {e}")
        
        def _show_system_status(self):
            """System status харуулах"""
            if not hasattr(self, 'integration_system'):
                QMessageBox.warning(self, "Анхааруулга", "Integration system боломжгүй")
                return
            
            try:
                status = self.integration_system.get_system_status()
                
                dialog = SystemStatusDialog(status, self)
                dialog.exec()
                
            except Exception as e:
                QMessageBox.critical(self, "Алдаа", f"System status харуулахад алдаа: {e}")
        
        def _show_workflow_dialog(self):
            """Workflow ажиллуулах dialog"""
            if not hasattr(self, 'integration_system'):
                QMessageBox.warning(self, "Анхааруулга", "Integration system боломжгүй")
                return
            
            try:
                workflows = list(self.integration_system.workflow_engine.workflows.keys())
                
                if not workflows:
                    QMessageBox.information(self, "Мэдээлэл", "Боломжтой workflow алга")
                    return
                
                dialog = WorkflowDialog(workflows, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    workflow_name = dialog.get_selected_workflow()
                    params = dialog.get_parameters()
                    
                    execution_id = self.integration_system.execute_workflow(workflow_name, params)
                    self._show_status_message(
                        f"🔄 Workflow эхэллээ: {workflow_name} (ID: {execution_id})", 5000
                    )
                    
            except Exception as e:
                QMessageBox.critical(self, "Алдаа", f"Workflow dialog-д алдаа: {e}")
        
        def _emergency_stop(self):
            """Emergency stop гүйцэтгэх"""
            if not hasattr(self, 'integration_system'):
                QMessageBox.warning(self, "Анхааруулга", "Integration system боломжгүй")
                return
            
            reply = QMessageBox.question(
                self, "Emergency Stop - Яаралтай зогсоолт",
                "Та бүх үйл ажиллагааг яаралтай зогсоохдоо итгэлтэй байна уу?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.integration_system.trigger_emergency_stop(
                        "Manual emergency stop from main window"
                    )
                    self._show_status_message("🛑 Яаралтай зогсоолт идэвхжлээ", 5000)
                except Exception as e:
                    QMessageBox.critical(self, "Алдаа", f"Emergency stop алдаа: {e}")
        
        def _test_integration(self):
            """Integration тестлэх"""
            if not hasattr(self, 'integration_system'):
                QMessageBox.warning(self, "Анхааруулга", "Integration system боломжгүй")
                return
            
            try:
                # Test event илгээх
                test_event = SystemEvent(
                    event_type=EventType.SYSTEM_EVENT,
                    source_tab="main_window",
                    data={"test": True, "message": "Integration test event"}
                )
                
                self.integration_system.event_bus.emit_event(test_event)
                
                # Status авах
                status = self.integration_system.get_system_status()
                
                # Result харуулах
                result_text = f"""
🧪 Integration Test Results:

📊 Registered Tabs: {len(status['tabs'])}
📈 Event History: {status['event_bus']['event_history_count']}
🔄 Available Workflows: {len(status['workflows']['registered'])}
📡 Active Streams: {status['shared_data']['active_streams']}
🎬 Playout Live: {status['shared_data']['playout_live']}

✅ Integration system ажиллаж байна!
                """
                
                QMessageBox.information(self, "Integration Test", result_text)
                
            except Exception as e:
                QMessageBox.critical(self, "Test алдаа", f"Integration test failed: {e}")
        
        # Event handlers
        def _on_integration_event(self, event):
            """Integration event шийдэх"""
            try:
                # UI update хийх event-ын дагуу
                if event.event_type == EventType.STREAM_STARTED:
                    self.connection_status.setText("🔴 Streaming")
                    self._show_status_message(
                        MongolianSystemMessages.get_message(
                            "stream_started", 
                            stream_key=event.data.get("stream_key", "")
                        ), 3000
                    )
                
                elif event.event_type == EventType.STREAM_STOPPED:
                    self.connection_status.setText("🟡 Connected")
                    self._show_status_message(
                        MongolianSystemMessages.get_message(
                            "stream_stopped", 
                            stream_key=event.data.get("stream_key", "")
                        ), 3000
                    )
                
                elif event.event_type == EventType.PLAYOUT_TAKE:
                    self._show_status_message(
                        MongolianSystemMessages.get_message("playout_live"), 3000
                    )
                
                elif event.event_type == EventType.MEDIA_LOADED:
                    self._show_status_message(
                        MongolianSystemMessages.get_message(
                            "media_loaded", 
                            filename=event.data.get("title", "")
                        ), 3000
                    )
                
                # Log болгон event-ыг logs tab-д бичих
                if hasattr(self, 'log_display'):
                    timestamp = event.timestamp.strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {event.event_type.value}: {event.source_tab} -> {event.target_tab or 'ALL'}"
                    self.log_display.append(log_entry)
                    
                    # Auto-scroll
                    scrollbar = self.log_display.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                
            except Exception as e:
                self.logger.error(f"Error handling integration event: {e}")
        
        def _on_status_update(self, status):
            """Global status update шийдэх"""
            try:
                # UI elements шинэчлэх
                tab_count = len(status.get('tabs', {}))
                active_streams = status.get('active_streams', 0)
                
                # Status bar шинэчлэх
                status_text = f"Tabs: {tab_count} | Streams: {active_streams}"
                if hasattr(self, 'status_bar'):
                    # Permanent widget байхгүй бол нэмэх
                    if not hasattr(self, 'integration_status_label'):
                        self.integration_status_label = QLabel(status_text)
                        self.status_bar.addPermanentWidget(self.integration_status_label)
                    else:
                        self.integration_status_label.setText(status_text)
                
            except Exception as e:
                self.logger.error(f"Error updating status: {e}")
        
        def _on_emergency_stop_triggered(self):
            """Emergency stop triggered шийдэх"""
            self._show_status_message(
                MongolianSystemMessages.get_message("emergency_stop"), 10000
            )
            
            # UI-д emergency state харуулах
            if hasattr(self, 'connection_status'):
                self.connection_status.setText("🛑 Emergency Stop")
                self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        
        def _on_workflow_started(self, execution_id):
            """Workflow эхэлсэн үед"""
            self._show_status_message(f"🔄 Workflow эхэллээ: {execution_id}", 3000)
        
        def _on_workflow_completed(self, execution_id, success):
            """Workflow дууссан үед"""
            if success:
                self._show_status_message(f"✅ Workflow амжилттай дууслаа: {execution_id}", 5000)
            else:
                self._show_status_message(f"❌ Workflow амжилтгүй: {execution_id}", 5000)
        
        # Integration-specific methods нэмэх
        def execute_media_to_air_workflow(self, file_path: str):
            """Media to air workflow ажиллуулах"""
            if hasattr(self, 'integration_system'):
                return self.integration_system.execute_workflow("media_to_air", {"file_path": file_path})
            return None
        
        def broadcast_custom_event(self, event_type, data):
            """Custom event илгээх"""
            if hasattr(self, 'integration_system'):
                self.integration_system.integration_manager.broadcast_event(event_type, data, "main_window")
        
        def get_integration_status(self):
            """Integration status авах"""
            if hasattr(self, 'integration_system'):
                return self.integration_system.get_system_status()
            return None
    
    return EnhancedMainWindow

# =============================================================================
# DIALOGS FOR INTEGRATION
# =============================================================================

class SystemStatusDialog(QDialog):
    """System status харуулах dialog"""
    
    def __init__(self, status_data, parent=None):
        super().__init__(parent)
        self.status_data = status_data
        self.setWindowTitle("System Status - Системийн төлөв")
        self.setModal(True)
        self.resize(700, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📊 Professional Streaming Studio - System Status")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Tabs
        tab_widget = QTabWidget()
        
        # Overview tab
        overview_tab = self._create_overview_tab()
        tab_widget.addTab(overview_tab, "🏠 Overview")
        
        # Tabs status
        tabs_tab = self._create_tabs_tab()
        tab_widget.addTab(tabs_tab, "📑 Tabs")
        
        # Event history
        events_tab = self._create_events_tab()
        tab_widget.addTab(events_tab, "📋 Events")
        
        # Raw data
        raw_tab = self._create_raw_tab()
        tab_widget.addTab(raw_tab, "🔧 Raw Data")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("Хаах")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _create_overview_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary info
        summary = f"""
<h3>📊 System Overview</h3>
<table style="width:100%; border-collapse: collapse;">
<tr style="background-color: #f0f0f0;"><td><b>Registered Tabs:</b></td><td>{len(self.status_data.get('tabs', {}))}</td></tr>
<tr><td><b>Active Streams:</b></td><td>{self.status_data.get('active_streams', 0)}</td></tr>
<tr style="background-color: #f0f0f0;"><td><b>Current Media:</b></td><td>{'✅ Loaded' if self.status_data.get('current_media', False) else '❌ None'}</td></tr>
<tr><td><b>Playout Live:</b></td><td>{'🔴 Live' if self.status_data.get('playout_live', False) else '⚫ Offline'}</td></tr>
<tr style="background-color: #f0f0f0;"><td><b>Auto Scheduler:</b></td><td>{'✅ Enabled' if self.status_data.get('auto_scheduler', False) else '❌ Disabled'}</td></tr>
<tr><td><b>Emergency Stop:</b></td><td>{'🛑 Active' if self.status_data.get('emergency_stop', False) else '✅ Normal'}</td></tr>
<tr style="background-color: #f0f0f0;"><td><b>Event History:</b></td><td>{self.status_data.get('event_bus', {}).get('event_history_count', 0)} events</td></tr>
<tr><td><b>Running Workflows:</b></td><td>{self.status_data.get('workflows', {}).get('running', 0)}</td></tr>
</table>
        """
        
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        
        layout.addStretch()
        return widget
    
    def _create_tabs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        tabs_text = "<h3>📑 Tab Status</h3><br>"
        
        for tab_name, tab_status in self.status_data.get('tabs', {}).items():
            status_icon = "✅" if tab_status.get('initialized', False) else "❌"
            active_icon = "🟢" if tab_status.get('active', False) else "⚫"
            
            tabs_text += f"""
<b>{status_icon} {tab_name}</b> {active_icon}<br>
&nbsp;&nbsp;Initialized: {tab_status.get('initialized', False)}<br>
&nbsp;&nbsp;Active: {tab_status.get('active', False)}<br>
&nbsp;&nbsp;Last Activity: {tab_status.get('last_activity', 'Unknown')}<br><br>
            """
        
        tabs_label = QLabel(tabs_text)
        tabs_label.setWordWrap(True)
        layout.addWidget(tabs_label)
        
        layout.addStretch()
        return widget
    
    def _create_events_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        events_label = QLabel("<h3>📋 Recent Events</h3>")
        layout.addWidget(events_label)
        
        # Events would be shown here if available
        events_text = QTextEdit()
        events_text.setReadOnly(True)
        events_text.setPlainText("Event history харалт дэмжигдээгүй.\nДэлгэрэнгүй мэдээлэл raw data tab-аас үзнэ үү.")
        layout.addWidget(events_text)
        
        return widget
    
    def _create_raw_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        raw_label = QLabel("<h3>🔧 Raw System Data</h3>")
        layout.addWidget(raw_label)
        
        raw_text = QTextEdit()
        raw_text.setReadOnly(True)
        raw_text.setFont(QFont("Consolas", 9))
        raw_text.setPlainText(json.dumps(self.status_data, indent=2, ensure_ascii=False))
        layout.addWidget(raw_text)
        
        return widget

class WorkflowDialog(QDialog):
    """Workflow сонгох ба ажиллуулах dialog"""
    
    def __init__(self, workflows, parent=None):
        super().__init__(parent)
        self.workflows = workflows
        self.setWindowTitle("Execute Workflow - Workflow ажиллуулах")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🔄 Select Workflow to Execute")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)
        
        # Workflow selection
        self.workflow_combo = QComboBox()
        self.workflow_combo.addItems(self.workflows)
        self.workflow_combo.currentTextChanged.connect(self._on_workflow_changed)
        layout.addWidget(QLabel("Workflow:"))
        layout.addWidget(self.workflow_combo)
        
        # Parameters
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QFormLayout(self.params_group)
        layout.addWidget(self.params_group)
        
        # Common parameters for workflows
        self.file_path_edit = QLineEdit()
        self.file_path_browse = QPushButton("📁 Browse")
        self.file_path_browse.clicked.connect(self._browse_file)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.file_path_browse)
        
        self.params_layout.addRow("File Path:", file_layout)
        
        # Additional params
        self.additional_params = QTextEdit()
        self.additional_params.setPlaceholderText('{"key": "value"}')
        self.additional_params.setMaximumHeight(100)
        self.params_layout.addRow("Additional Params (JSON):", self.additional_params)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        execute_btn = QPushButton("▶️ Execute")
        execute_btn.clicked.connect(self.accept)
        button_layout.addWidget(execute_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize
        self._on_workflow_changed(self.workflows[0] if self.workflows else "")
    
    def _on_workflow_changed(self, workflow_name):
        """Workflow өөрчлөгдөхөд parameters шинэчлэх"""
        # Show/hide parameters based on workflow
        if workflow_name == "media_to_air":
            self.file_path_edit.setVisible(True)
            self.file_path_browse.setVisible(True)
            self.params_group.setTitle("Media to Air Parameters")
        else:
            self.file_path_edit.setVisible(False)
            self.file_path_browse.setVisible(False)
            self.params_group.setTitle("Workflow Parameters")
    
    def _browse_file(self):
        """File сонгох"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def get_selected_workflow(self):
        """Сонгосон workflow буцаах"""
        return self.workflow_combo.currentText()
    
    def get_parameters(self):
        """Parameters авах"""
        params = {}
        
        # File path parameter
        if self.file_path_edit.text().strip():
            params["file_path"] = self.file_path_edit.text().strip()
        
        # Additional parameters
        additional_text = self.additional_params.toPlainText().strip()
        if additional_text:
            try:
                additional_params = json.loads(additional_text)
                params.update(additional_params)
            except json.JSONDecodeError:
                # Ignore invalid JSON
                pass
        
        return params

# =============================================================================
# PRACTICAL USAGE EXAMPLES
# =============================================================================

class IntegrationExamples:
    """Integration system хэрэглэх жишээнүүд"""
    
    @staticmethod
    def example_media_to_air(main_window, file_path: str):
        """Media to air workflow жишээ"""
        if hasattr(main_window, 'integration_system'):
            execution_id = main_window.integration_system.execute_workflow(
                "media_to_air", {"file_path": file_path}
            )
            print(f"🎬 Media to air workflow started: {execution_id}")
            return execution_id
        else:
            print("❌ Integration system not available")
            return None
    
    @staticmethod
    def example_emergency_stop(main_window):
        """Emergency stop жишээ"""
        if hasattr(main_window, 'integration_system'):
            main_window.integration_system.trigger_emergency_stop("Example emergency stop")
            print("🛑 Emergency stop triggered")
        else:
            print("❌ Integration system not available")
    
    @staticmethod
    def example_custom_event(main_window):
        """Custom event илгээх жишээ"""
        if hasattr(main_window, 'integration_system'):
            main_window.broadcast_custom_event(
                EventType.SYSTEM_EVENT,
                {"message": "Custom event from example", "timestamp": datetime.now().isoformat()}
            )
            print("📡 Custom event broadcasted")
        else:
            print("❌ Integration system not available")
    
    @staticmethod
    def example_get_status(main_window):
        """System status авах жишээ"""
        if hasattr(main_window, 'integration_system'):
            status = main_window.get_integration_status()
            print("📊 System Status:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return status
        else:
            print("❌ Integration system not available")
            return None

# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================

def print_setup_instructions():
    """Setup заавар хэвлэх"""
    print("""
🎯 TAB INTEGRATION SYSTEM SETUP ЗААВАР

1️⃣ ФАЙЛУУД БАЙРЛУУЛАХ:
   📁 tab_integration_system.py - үндсэн системийн файл
   📁 integration_usage_guide.py - энэ заавар файл
   
2️⃣ MAIN.PY ФАЙЛД НЭМЭХ:
   ```python
   # main.py дотор imports хэсэгт:
   try:
       from integration_usage_guide import integrate_with_existing_main_window
       INTEGRATION_AVAILABLE = True
   except ImportError:
       INTEGRATION_AVAILABLE = False
   
   # main() функц дотор main window үүсгэх хэсэгт:
   if INTEGRATION_AVAILABLE:
       try:
           EnhancedStudio = integrate_with_existing_main_window(ProfessionalStreamingStudio)
           main_win = EnhancedStudio(config_manager, app)
           print("🎉 Integration system идэвхжлээ!")
       except Exception as e:
           print(f"Integration failed, using fallback: {e}")
           main_win = ProfessionalStreamingStudio(config_manager, app)
   else:
       main_win = ProfessionalStreamingStudio(config_manager, app)
   ```

3️⃣ ХЭРЭГЛЭХ:
   ▶️ Tools > System Status - системийн төлөв харах
   ▶️ Tools > Execute Workflow - workflow ажиллуулах  
   ▶️ Tools > Emergency Stop (Ctrl+Alt+E) - яаралтай зогсоолт
   ▶️ Tools > Test Integration - integration тестлэх

4️⃣ PROGRAMMATIC ХЭРЭГЛЭХ:
   ```python
   # Workflow ажиллуулах
   main_win.execute_media_to_air_workflow("/path/to/video.mp4")
   
   # Emergency stop
   main_win.trigger_emergency_stop("Manual stop")
   
   # Status авах
   status = main_win.get_integration_status()
   
   # Custom event илгээх
   main_win.broadcast_custom_event(EventType.MEDIA_SELECTED, {"file": "test.mp4"})
   ```

✅ INTEGRATION ИДЭВХЖСЭНИЙ ДАРАА:
   🔄 Табууд хоорондын автомат харилцаа холбоо
   📊 Бодит цагийн системийн мониторинг
   🎬 Media to air автомат workflow
   🛑 Emergency stop бүх табуудад
   📡 Event-driven архитектур
   🇲🇳 Монгол хэлний дэмжлэг

⚠️ АНХААР: Integration system нь optional - байхгүй байвал анхны функционал ажиллана.
    """)

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'integrate_with_existing_main_window',
    'SystemStatusDialog',
    'WorkflowDialog', 
    'IntegrationExamples',
    'print_setup_instructions'
]

if __name__ == "__main__":
    print_setup_instructions()
                self.logger.error(f"Integration setup failed: {e}")
                self._show_status_message(f"Integration system алдаа: {e}", 5000)
        
        def _add_integration_menu_items(self):
            """Integration-ын menu items нэмэх"""
            if not hasattr(self, 'integration_system'):
                return
            
            try:
                # Tools menu олох
                tools_menu = None
                for action in self.menuBar().actions():
                    if action.text() == "&Tools":
                        tools_menu = action.menu()
                        break
                
                if tools_menu:
                    tools_menu.addSeparator()
                    
                    # System Status
                    status_action = QAction("📊 System Status", self)
                    status_action.triggered.connect(self._show_system_status)
                    tools_menu.addAction(status_action)
                    
                    # Execute Workflow
                    workflow_action = QAction("🔄 Execute Workflow", self)
                    workflow_action.triggered.connect(self._show_workflow_dialog)
                    tools_menu.addAction(workflow_action)
                    
                    # Emergency Stop
                    emergency_action = QAction("🛑 Emergency Stop", self)
                    emergency_action.setShortcut(QKeySequence("Ctrl+Alt+E"))
                    emergency_action.triggered.connect(self._emergency_stop)
                    tools_menu.addAction(emergency_action)
                    
                    # Test Integration
                    test_action = QAction("🧪 Test Integration", self)
                    test_action.triggered.connect(self._test_integration)
                    tools_menu.addAction(test_action)
            
            except Exception as e:
                