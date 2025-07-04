#!/usr/bin/env python3
"""
AMCP Command Module
Enhanced AMCP command handling with validation and execution
"""

import re
from datetime import datetime
from typing import Dict, Any


class AMCPCommand:
    """AMCP command representation with enhanced validation"""
    
    VALID_COMMANDS = {"LOAD", "PLAY", "STOP", "CLEAR", "INFO"}
    
    def __init__(self, command: str, channel: int = 1, layer: int = 1, 
                 parameters: Dict[str, Any] = None):
        self.amcp_server_control = amcp_server_control
        self.command = command.upper()
        self.channel = max(1, min(channel, 16))
        self.layer = max(1, min(layer, 20))
        self.parameters = parameters or {}
        self.timestamp = self._format_timestamp()
        
        if self.command not in self.VALID_COMMANDS:
            raise ValueError(f"Invalid AMCP command: {command}")
        
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate command parameters"""
        if "media" in self.parameters and self.parameters["media"]:
            media = str(self.parameters["media"])
            if not re.match(r'^[\w\-./\\]+$', media):
                raise ValueError(f"Invalid media name: {media}")
        
        if "transition" in self.parameters:
            valid_transitions = {"CUT", "MIX", "PUSH", "SLIDE", "WIPE"}
            transition = self.parameters["transition"].split()[0]
            if transition not in valid_transitions:
                raise ValueError(f"Invalid transition type: {transition}")
    
    def _format_timestamp(self):
        """Format timestamp"""
        return datetime.now().strftime("%H:%M:%S")
    
    def execute(self):
        if self.amcp_server_control:
            self.amcp_server_control.send_custom_command(self.command_string)
    
    def to_string(self) -> str:
        """Convert to AMCP command string"""
        cmd_str = f"{self.command} {self.channel}-{self.layer}"
        
        if self.parameters:
            if "media" in self.parameters and self.parameters["media"]:
                cmd_str += f" \"{self.parameters['media']}\""
            
            if "transition" in self.parameters:
                cmd_str += f" {self.parameters['transition']}"
            
            if "loop" in self.parameters and self.parameters["loop"]:
                cmd_str += " LOOP"
            
            if "auto" in self.parameters and self.parameters["auto"]:
                cmd_str += " AUTO"
        
        return cmd_str
