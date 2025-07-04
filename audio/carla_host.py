#!/usr/bin/env python3
"""
Carla Host - Complete fallback version with all required classes (Final Fix)
"""

import logging
from typing import Dict, List, Optional, Any

class CarlaPluginHost:
    """Mock Carla Plugin Host implementation"""
    
    def __init__(self, sample_rate=48000, buffer_size=512):
        # Handle cases where sample_rate might be an object instead of int
        if hasattr(sample_rate, '__class__') and 'LV2PluginManager' in str(sample_rate.__class__):
            self.sample_rate = 48000  # Default fallback
            print("⚠️ Received LV2PluginManager object as sample_rate, using default 48000")
        else:
            self.sample_rate = sample_rate
            
        self.buffer_size = buffer_size
        self.plugins = {}
        self.plugin_count = 0
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        print(f"🎛️ Carla Plugin Host initialized (fallback mode) - SR: {self.sample_rate}, Buffer: {buffer_size}")
    
    def start(self):
        """Start the Carla host"""
        self.is_running = True
        print("🟢 Carla Host started (emulation mode)")
        return True
    
    def stop(self):
        """Stop the Carla host"""
        self.is_running = False
        print("🔴 Carla Host stopped")
        return True
    
    def add_plugin(self, plugin_uri: str, plugin_name: str = None):
        """Add a plugin to the host"""
        plugin_id = self.plugin_count
        self.plugins[plugin_id] = {
            "uri": plugin_uri,
            "name": plugin_name or f"Plugin_{plugin_id}",
            "active": True,
            "parameters": {}
        }
        self.plugin_count += 1
        print(f"📦 Carla: Added plugin '{plugin_name or plugin_uri}' (ID: {plugin_id})")
        return plugin_id
    
    def remove_plugin(self, plugin_id: int):
        """Remove a plugin from the host"""
        if plugin_id in self.plugins:
            plugin_name = self.plugins[plugin_id]["name"]
            del self.plugins[plugin_id]
            print(f"🗑️ Carla: Removed plugin '{plugin_name}' (ID: {plugin_id})")
            return True
        return False
    
    def set_parameter(self, plugin_id: int, parameter_id: int, value: float):
        """Set plugin parameter"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["parameters"][parameter_id] = value
            print(f"🎚️ Carla: Set parameter {parameter_id} = {value} for plugin {plugin_id}")
            return True
        return False
    
    def get_parameter(self, plugin_id: int, parameter_id: int):
        """Get plugin parameter"""
        if plugin_id in self.plugins:
            return self.plugins[plugin_id]["parameters"].get(parameter_id, 0.0)
        return 0.0
    
    def reorder_plugins(self, plugin_order: List[int]):
        """Reorder plugins in the chain"""
        print(f"🔄 Carla: Plugin chain reordered to: {plugin_order}")
        return True
    
    def get_plugin_count(self):
        """Get number of plugins"""
        return len(self.plugins)
    
    def get_plugin_info(self, plugin_id: int):
        """Get plugin information"""
        return self.plugins.get(plugin_id, {})


class CarlaHost:
    """Main Carla Host class - backwards compatibility"""
    
    def __init__(self, sample_rate=48000, buffer_size=512):
        # Handle parameter validation
        if hasattr(sample_rate, '__class__') and 'LV2PluginManager' in str(sample_rate.__class__):
            sample_rate = 48000  # Default fallback
            print("⚠️ Fixed sample_rate parameter to default value")
            
        self.plugin_host = CarlaPluginHost(sample_rate, buffer_size)
        self.logger = logging.getLogger(__name__)
        print(f"🎛️ Carla Host initialized - SR: {sample_rate}, Buffer: {buffer_size}")
    
    def start(self):
        """Start Carla host"""
        return self.plugin_host.start()
    
    def stop(self):
        """Stop Carla host"""
        return self.plugin_host.stop()
    
    def add_plugin(self, plugin_uri: str, plugin_name: str = None):
        """Add plugin"""
        return self.plugin_host.add_plugin(plugin_uri, plugin_name)
    
    def remove_plugin(self, plugin_id: int):
        """Remove plugin"""
        return self.plugin_host.remove_plugin(plugin_id)
    
    def set_parameter(self, plugin_id: int, parameter_id: int, value: float):
        """Set parameter"""
        return self.plugin_host.set_parameter(plugin_id, parameter_id, value)
    
    def get_parameter(self, plugin_id: int, parameter_id: int):
        """Get parameter"""
        return self.plugin_host.get_parameter(plugin_id, parameter_id)
    
    def reorder_plugins(self, plugin_order: List[int]):
        """Reorder plugins"""
        return self.plugin_host.reorder_plugins(plugin_order)
    
    def get_plugin_count(self):
        """Get plugin count"""
        return self.plugin_host.get_plugin_count()
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()


# Export all classes
__all__ = [
    'CarlaPluginHost',
    'CarlaHost'
]

print("✅ Carla Host module loaded with all required classes (final fix)")
