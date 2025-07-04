# tv_streaming_system/core/config_manager.py
#!/usr/bin/env python3
"""
Core Configuration Manager
Handles application configuration, server settings, and persistent data
"""

import configparser
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# models.server_config-г импортлох
try:
    from models.server_config import ServerConfig
except ImportError:
    # Fallback for development if models not yet structured
    from dataclasses import dataclass
    
    @dataclass
    class ServerConfig:
        def __init__(self, name: str, host: str, port: int, rtmp_port: int = 1935, 
                     ssl_enabled: bool = False, api_endpoint: str = "/api/v1",
                     stream_endpoint: str = "/live", username: Optional[str] = None,
                     password: Optional[str] = None, max_streams: int = 10,
                     description: str = "", auto_connect: bool = False):
            self.name = name
            self.host = host
            self.port = port
            self.rtmp_port = rtmp_port
            self.ssl_enabled = ssl_enabled
            self.api_endpoint = api_endpoint
            self.stream_endpoint = stream_endpoint
            self.username = username
            self.password = password
            self.max_streams = max_streams
            self.description = description
            self.auto_connect = auto_connect
            
        def to_dict(self):
            return {
                'name': self.name, 'host': self.host, 'port': self.port,
                'rtmp_port': self.rtmp_port, 'ssl_enabled': self.ssl_enabled,
                'api_endpoint': self.api_endpoint, 'stream_endpoint': self.stream_endpoint,
                'username': self.username, 'password': self.password,
                'max_streams': self.max_streams, 'description': self.description,
                'auto_connect': self.auto_connect
            }
        
        @classmethod
        def from_dict(cls, data: Dict[str, Any]):
            return cls(**data)


class ConfigManager:
    """Configuration manager for the application"""

    def __init__(self, config_file: str = "config.ini"):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.servers: Dict[str, ServerConfig] = {}
        self.load_config()

    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                self.config.read(self.config_file)
                self._load_servers()
                logging.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                self._create_default_config()
                logging.info("Created default configuration")
                return True
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return False

    def _create_default_config(self):
        """Create default configuration"""
        self.config['DEFAULT'] = {
            'log_level': 'INFO',
            'media_library_path': 'data/media',
            'plugin_directory': 'plugins',
            'backup_directory': 'data/backups',
            'auto_backup_interval': '24', # hours
            'theme': 'Dark',
            'default_video_quality': '1080p',
            'default_encoder': 'libx264',
            'default_audio_bitrate': '192k',
            'auto_scan_on_startup': 'True'
        }
        self.config['amcp'] = {
            'host': 'localhost',
            'port': '5250',
            'timeout': '5',
            'auto_connect': 'False'
        }
        self.config['ui'] = {
            'window_x': '-1',
            'window_y': '-1',
            'window_width': '1280',
            'window_height': '720'
        }
        # Үндсэн сервер нэмэх
        self._create_default_servers()
        self.save_config()

    def _create_default_servers(self):
        """Create default server configurations"""
        default_server = ServerConfig(
            name="Орон нутгийн NGINX+RTMP",
            host="localhost",
            port=8080,
            rtmp_port=1935,
            ssl_enabled=False,
            description="Үндсэн орон нутгийн RTMP сервер"
        )
        self.servers["local"] = default_server

    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            self._save_servers()
            logging.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False

    def get(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value"""
        return self.config.get(section, key, fallback=default)

    def getint(self, section: str, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer configuration value"""
        try:
            return self.config.getint(section, key, fallback=default)
        except ValueError:
            logging.warning(f"Invalid integer value for {section}.{key}. Using default: {default}")
            return default

    def getboolean(self, section: str, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get a boolean configuration value"""
        try:
            return self.config.getboolean(section, key, fallback=default)
        except ValueError:
            logging.warning(f"Invalid boolean value for {section}.{key}. Using default: {default}")
            return default

    def set(self, section: str, key: str, value: str):
        """Set a configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def get_server_configs(self) -> Dict[str, ServerConfig]:
        """Get all server configurations - Dialog-той нийцэхийн тулд"""
        return self.servers

    def save_server_configs(self, servers: Dict[str, Any]):
        """Save server configurations from dialog"""
        self.servers.clear()
        for key, server_data in servers.items():
            if isinstance(server_data, dict):
                self.servers[key] = ServerConfig.from_dict(server_data)
            else:
                self.servers[key] = server_data
        self.save_config()

    def _load_servers(self):
        """Load server configurations from config file - Enhanced version"""
        self.servers.clear()
        for section in self.config.sections():
            if section.startswith('server:'):
                name = section[len('server:'):]
                try:
                    # Шинэ форматыг уншихыг оролдох
                    server_data = {
                        'name': self.config.get(section, 'name', name),
                        'host': self.config.get(section, 'host', 'localhost'),
                        'port': self.config.getint(section, 'port', 8080),
                        'rtmp_port': self.config.getint(section, 'rtmp_port', 1935),
                        'ssl_enabled': self.config.getboolean(section, 'ssl_enabled', False),
                        'api_endpoint': self.config.get(section, 'api_endpoint', '/api/v1'),
                        'stream_endpoint': self.config.get(section, 'stream_endpoint', '/live'),
                        'username': self.config.get(section, 'username', None),
                        'password': self.config.get(section, 'password', None),
                        'max_streams': self.config.getint(section, 'max_streams', 10),
                        'description': self.config.get(section, 'description', ''),
                        'auto_connect': self.config.getboolean(section, 'auto_connect', False)
                    }
                    # None утгуудыг цэвэрлэх
                    clean_data = {k: v for k, v in server_data.items() if v is not None or k in ['username', 'password', 'description']}
                    self.servers[name] = ServerConfig.from_dict(clean_data)
                    
                except Exception as e:
                    # Хуучин форматыг backward compatibility-ийн тулд
                    logging.warning(f"Using legacy format for server {name}: {e}")
                    host = self.config.get(section, 'host', 'localhost')
                    port = self.config.getint(section, 'port', 5250)
                    auto_connect = self.config.getboolean(section, 'auto_connect', False)
                    
                    # Legacy ServerConfig-г шинэ форматад хөрвүүлэх
                    self.servers[name] = ServerConfig(
                        name=name,
                        host=host,
                        port=port,
                        rtmp_port=1935,  # default
                        auto_connect=auto_connect
                    )
                    
        # Хэрэв сервер байхгүй бол үндсэн сервер үүсгэх
        if not self.servers:
            self._create_default_servers()
            
        logging.debug(f"Loaded servers: {list(self.servers.keys())}")

    def _save_servers(self):
        """Save server configurations to config file - Enhanced version"""
        # Remove old server sections before saving
        for section in list(self.config.sections()):
            if section.startswith('server:'):
                self.config.remove_section(section)

        for name, server in self.servers.items():
            section_name = f'server:{name}'
            server_dict = server.to_dict()
            
            self.config[section_name] = {}
            for key, value in server_dict.items():
                if value is not None:
                    self.config[section_name][key] = str(value)
                    
        logging.debug(f"Saved servers: {list(self.servers.keys())}")

    def add_server(self, server: ServerConfig):
        """Add a new server configuration"""
        self.servers[server.name] = server
        self.save_config()
        logging.info(f"Server added: {server.name}")

    def get_server(self, name: str) -> Optional[ServerConfig]:
        """Get a server configuration by name"""
        return self.servers.get(name)

    def get_all_servers(self) -> Dict[str, ServerConfig]:
        """Get all configured servers"""
        return self.servers

    def delete_server(self, name: str):
        """Delete a server configuration by name"""
        if name in self.servers:
            del self.servers[name]
            section_name = f'server:{name}'
            if self.config.has_section(section_name):
                self.config.remove_section(section_name)
            self.save_config()
            logging.info(f"Server deleted: {name}")

    def get_media_library_path(self) -> Path:
        """Get the media library path"""
        path_str = self.get('DEFAULT', 'media_library_path', 'data/media')
        return Path(path_str)

    def set_media_library_path(self, path: str):
        """Set the media library path"""
        self.set('DEFAULT', 'media_library_path', path)

    def get_log_level(self) -> str:
        """Get the log level"""
        return self.get('DEFAULT', 'log_level', 'INFO')

    def set_log_level(self, level: str):
        """Set the log level"""
        self.set('DEFAULT', 'log_level', level)

    def get_plugin_directory(self) -> Path:
        """Get the plugin directory path"""
        path_str = self.get('DEFAULT', 'plugin_directory', 'plugins')
        return Path(path_str)

    def get_backup_directory(self) -> Path:
        """Get the backup directory path"""
        path_str = self.get('DEFAULT', 'backup_directory', 'data/backups')
        return Path(path_str)

    def get_auto_backup_interval(self) -> int:
        """Get the auto backup interval in hours"""
        return self.getint('DEFAULT', 'auto_backup_interval', 24)

    def get_theme(self) -> str:
        """Get the UI theme"""
        return self.get('DEFAULT', 'theme', 'Dark')

    def set_theme(self, theme: str):
        """Set the UI theme"""
        self.set('DEFAULT', 'theme', theme)

    def get_default_video_quality(self) -> str:
        """Get the default video quality setting"""
        return self.get('DEFAULT', 'default_video_quality', '1080p')

    def set_default_video_quality(self, quality: str):
        """Set the default video quality setting"""
        self.set('DEFAULT', 'default_video_quality', quality)

    def get_default_encoder(self) -> str:
        """Get the default video encoder setting"""
        return self.get('DEFAULT', 'default_encoder', 'libx264')

    def set_default_encoder(self, encoder: str):
        """Set the default video encoder setting"""
        self.set('DEFAULT', 'default_encoder', encoder)

    def get_default_audio_bitrate(self) -> str:
        """Get the default audio bitrate setting"""
        return self.get('DEFAULT', 'default_audio_bitrate', '192k')

    def set_default_audio_bitrate(self, bitrate: str):
        """Set the default audio bitrate setting"""
        self.set('DEFAULT', 'default_audio_bitrate', bitrate)

    def get_auto_scan_on_startup(self) -> bool:
        """Get the auto scan on startup setting"""
        return self.getboolean('DEFAULT', 'auto_scan_on_startup', True)

    def set_auto_scan_on_startup(self, value: bool):
        """Set the auto scan on startup setting"""
        self.set('DEFAULT', 'auto_scan_on_startup', str(value))

    def get_window_position(self) -> tuple[int, int]:
        """Get the main window position"""
        x = self.getint('ui', 'window_x', -1)
        y = self.getint('ui', 'window_y', -1)
        return x, y

    def set_window_position(self, x: int, y: int):
        """Set the main window position"""
        self.set('ui', 'window_x', str(x))
        self.set('ui', 'window_y', str(y))

    def get_window_size(self) -> tuple[int, int]:
        """Get the main window size"""
        width = self.getint('ui', 'window_width', 1280)
        height = self.getint('ui', 'window_height', 720)
        return width, height

    def set_window_size(self, width: int, height: int):
        """Set the main window size"""
        self.set('ui', 'window_width', str(width))
        self.set('ui', 'window_height', str(height))

    @property
    def amcp_settings(self) -> dict:
        """Get AMCP connection settings"""
        return {
            'host': self.get('amcp', 'host', 'localhost'),
            'port': self.getint('amcp', 'port', 5250),
            'timeout': self.getint('amcp', 'timeout', 5),
            'auto_connect': self.getboolean('amcp', 'auto_connect', False)
        }

    def get_all_settings(self) -> dict:
        """Get all configuration settings as dictionary"""
        result = {}
        for section_name in self.config.sections():
            result[section_name] = dict(self.config[section_name])
        return result

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            # Backup current config
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix('.bak')
                self.config_file.rename(backup_path)
                logging.info(f"Backed up current config to {backup_path}")

            # Clear current config
            self.config.clear()
            self.servers.clear()

            # Create new default config
            self._create_default_config()

            logging.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logging.error(f"Failed to reset configuration: {e}")
            return False