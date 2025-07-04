"""
TV Stream - Server Management
Server configuration and management
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

# Safe imports
try:
    from .utils import LoggerManager, NetworkUtils, ErrorHandler
except ImportError:
    try:
        from utils import LoggerManager, NetworkUtils, ErrorHandler
    except ImportError:
        # Fallback implementations
        import logging
        import socket
        
        class LoggerManager:
            @classmethod
            def get_logger(cls, name): return logging.getLogger(name)
        
        class NetworkUtils:
            @staticmethod
            def test_connection(host, port, timeout=3):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    return result == 0
                except Exception:
                    return False
        
        class ErrorHandler:
            @staticmethod
            def safe_execute(func, error_msg="", logger=None):
                try:
                    return func()
                except Exception:
                    return None


@dataclass
class ServerConfig:
    """Server configuration"""
    name: str
    host: str
    port: int
    rtmp_port: int
    ssl_enabled: bool = False
    description: str = ""
    
    @property
    def rtmp_url(self) -> str:
        protocol = "rtmps" if self.ssl_enabled else "rtmp"
        return f"{protocol}://{self.host}:{self.rtmp_port}/live"
    
    @property
    def is_local(self) -> bool:
        return self.host.lower() in ['localhost', '127.0.0.1']
    
    @property
    def is_local_network(self) -> bool:
        return self.host.startswith('192.168.') or self.host.startswith('10.')
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        defaults = {
            'ssl_enabled': False,
            'description': ''
        }
        config_data = {**defaults, **data}
        return cls(**{k: v for k, v in config_data.items() if k in 
                     ['name', 'host', 'port', 'rtmp_port', 'ssl_enabled', 'description']})
    
    def validate(self) -> List[str]:
        """Validate server configuration"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Server name is required")
        
        if not self.host or not self.host.strip():
            errors.append("Host is required")
        
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            errors.append("Port must be between 1-65535")
        
        if not isinstance(self.rtmp_port, int) or not (1 <= self.rtmp_port <= 65535):
            errors.append("RTMP port must be between 1-65535")
        
        return errors
    
    def test_connection(self, timeout: int = 5) -> Dict[str, Any]:
        """Test server connection"""
        result = {
            'success': False,
            'rtmp_reachable': False,
            'error': None
        }
        
        try:
            result['rtmp_reachable'] = NetworkUtils.test_connection(self.host, self.rtmp_port, timeout)
            result['success'] = result['rtmp_reachable']
        except Exception as e:
            result['error'] = str(e)
        
        return result


class ServerManager:
    """Server management"""
    
    def __init__(self, config_file: str = "data/configs/servers.json"):
        self.config_file = Path(config_file)
        self.logger = LoggerManager.get_logger(__name__)
        self.servers: Dict[str, ServerConfig] = {}
        self.load_servers()
    
    def load_servers(self):
        """Load servers from configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for server_id, server_data in data.get('servers', {}).items():
                    try:
                        self.servers[server_id] = ServerConfig.from_dict(server_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to load server {server_id}: {e}")
            else:
                self.create_default_servers()
        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")
            self.create_default_servers()
    
    def create_default_servers(self):
        """Create default servers"""
        default_servers = {
            "localhost": ServerConfig(
                name="Localhost RTMP",
                host="localhost",
                port=8080,
                rtmp_port=1935,
                description="Local development server"
            )
        }
        self.servers.update(default_servers)
        self.save_servers()
    
    def save_servers(self) -> bool:
        """Save servers to configuration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                "version": "1.0",
                "servers": {k: v.to_dict() for k, v in self.servers.items()}
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save servers: {e}")
            return False
    
    def get_servers(self) -> Dict[str, ServerConfig]:
        """Get all servers"""
        return self.servers.copy()
