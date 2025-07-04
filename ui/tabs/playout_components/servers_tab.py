from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton, 
                             QTableWidget, QFormLayout, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
import asyncio

class ServersTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout(self)
        
        # Server list
        servers_group = QGroupBox("ðŸ–¥ï¸� Streaming Servers")
        servers_layout = QVBoxLayout(servers_group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_server_btn = QPushButton("âž• Add Server")
        add_server_btn.clicked.connect(self._add_server_dialog)
        toolbar.addWidget(add_server_btn)
        
        edit_server_btn = QPushButton("âœ�ï¸� Edit Server")
        edit_server_btn.clicked.connect(self._edit_server_dialog)
        toolbar.addWidget(edit_server_btn)
        
        remove_server_btn = QPushButton("ðŸ—‘ï¸� Remove Server")
        remove_server_btn.clicked.connect(self._remove_server)
        toolbar.addWidget(remove_server_btn)
        
        toolbar.addStretch()
        
        test_connection_btn = QPushButton("ðŸ”— Test Connection")
        test_connection_btn.clicked.connect(self._test_server_connection)
        toolbar.addWidget(test_connection_btn)
        
        servers_layout.addLayout(toolbar)
        
        # Servers table
        self.servers_table = QTableWidget()
        self.servers_table.setColumnCount(6)
        self.servers_table.setHorizontalHeaderLabels([
            "Name", "Host", "Port", "RTMP Port", "Status", "SSL"
        ])
        self.servers_table.horizontalHeader().setStretchLastSection(True)
        self.servers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        servers_layout.addWidget(self.servers_table)
        
        self.layout.addWidget(servers_group)
        
        # Server details and monitoring
        details_group = QGroupBox("ðŸ“Š Server Details")
        details_layout = QFormLayout(details_group)
        
        self.server_name_label = QLabel("N/A")
        self.server_url_label = QLabel("N/A")
        self.server_status_label = QLabel("N/A")
        self.server_uptime_label = QLabel("N/A")
        self.server_streams_label = QLabel("N/A")
        
        details_layout.addRow("Name:", self.server_name_label)
        details_layout.addRow("URL:", self.server_url_label)
        details_layout.addRow("Status:", self.server_status_label)
        details_layout.addRow("Uptime:", self.server_uptime_label)
        details_layout.addRow("Active Streams:", self.server_streams_label)
        
        self.layout.addWidget(details_group)
        
        self._update_servers_table()
    
    def _update_servers_table(self):
        self.servers_table.setRowCount(len(self.parent.config_manager.servers))
        
        for row, (server_id, config) in enumerate(self.parent.config_manager.servers.items()):
            self.servers_table.setItem(row, 0, QTableWidgetItem(config.name))
            self.servers_table.setItem(row, 1, QTableWidgetItem(config.host))
            self.servers_table.setItem(row, 2, QTableWidgetItem(str(config.port)))
            self.servers_table.setItem(row, 3, QTableWidgetItem(str(config.rtmp_port)))
            
            server = self.parent.stream_servers.get(config.name)
            status = "Connected" if server and server.connected else "Disconnected"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor("#28a745") if server and server.connected else QColor("#dc3545"))
            self.servers_table.setItem(row, 4, status_item)
            
            ssl_text = "Yes" if config.ssl_enabled else "No"
            self.servers_table.setItem(row, 5, QTableWidgetItem(ssl_text))
    
    def _add_server_dialog(self):
        dialog = ServerConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            server_id = config.name.lower().replace(" ", "_")
            
            self.parent.config_manager.add_server(server_id, config)
            self.parent.stream_servers[config.name] = StreamServer(config)
            
            self._update_servers_table()
            self.parent._update_server_combo()
            
            self.parent._log_message(f"Added server: {config.name}", "info")
    
    def _edit_server_dialog(self):
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a server to edit.")
            return
        
        QMessageBox.information(self, "Not Implemented", "Server editing will be implemented in a future version.")
    
    def _remove_server(self):
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a server to remove.")
            return
        
        server_name = self.servers_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove server '{server_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent._log_message(f"Removed server: {server_name}", "info")
    
    def _test_server_connection(self):
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a server to test.")
            return
        
        server_name = self.servers_table.item(current_row, 0).text()
        server = self.parent.stream_servers.get(server_name)
        
        if server:
            QTimer.singleShot(0, lambda: self._test_server_connection_sync(server))
    
    def _test_server_connection_sync(self, server: StreamServer):
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            connected = loop.run_until_complete(server.connect())
            
            if connected:
                self.parent._log_message(f"Server '{server.config.name}' connection successful", "info")
                QMessageBox.information(self, "Connection Test", f"Successfully connected to '{server.config.name}'")
            else:
                self.parent._log_message(f"Server '{server.config.name}' connection failed", "error")
                QMessageBox.warning(self, "Connection Test", f"Failed to connect to '{server.config.name}'")
                
        except Exception as e:
            self.parent._log_message(f"Server connection test error: {e}", "error")
            QMessageBox.critical(self, "Connection Error", f"Connection test failed: {e}")
        finally:
            self._update_servers_table()