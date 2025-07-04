# tv_streaming_system/models/server_config.py
"""
Data model for Server Configuration.
Defines the structure for storing details about a streaming/CasparCG server.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict

@dataclass
class ServerConfig:
    """Represents a configuration for an external server (e.g., CasparCG, RTMP streaming server)."""
    name: str
    host: str
    port: int
    rtmp_port: int
    ssl_enabled: bool = False
    api_endpoint: str = "/api/v1"
    stream_endpoint: str = "/live"
    username: Optional[str] = None
    password: Optional[str] = None
    max_streams: int = 10
    description: str = ""
    auto_connect: bool = False  # Backward compatibility үүد хэрэгтэй

    @property
    def rtmp_url(self) -> str:
        """Get RTMP URL"""
        protocol = "rtmps" if self.ssl_enabled else "rtmp"
        return f"{protocol}://{self.host}:{self.rtmp_port}{self.stream_endpoint}"

    @property
    def api_url(self) -> str:
        """Get API URL"""
        protocol = "https" if self.ssl_enabled else "http"
        return f"{protocol}://{self.host}:{self.port}{self.api_endpoint}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "rtmp_port": self.rtmp_port,
            "ssl_enabled": self.ssl_enabled,
            "api_endpoint": self.api_endpoint,
            "stream_endpoint": self.stream_endpoint,
            "username": self.username,
            "password": self.password,
            "max_streams": self.max_streams,
            "description": self.description,
            "auto_connect": self.auto_connect
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary"""
        return cls(**data)

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"

    def __eq__(self, other):
        if not isinstance(other, ServerConfig):
            return NotImplemented
        return (self.name == other.name and 
                self.host == other.host and 
                self.port == other.port and
                self.rtmp_port == other.rtmp_port)

    def __hash__(self):
        return hash((self.name, self.host, self.port, self.rtmp_port))