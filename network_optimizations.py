#!/usr/bin/env python3
"""
Network Optimizations Module
VM сүлжээнд зориулсан сүлжээний оптимизаци модуль
"""

import socket
import time
import os
import platform
import re
from typing import Optional, Dict, Any
from pathlib import Path

# Fallback imports
try:
    from core.logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class NetworkOptimizer:
    """VM сүлжээнд зориулсан сүлжээний оптимизаци"""
    
    def __init__(self, logger):
        self.logger = logger
        self.connection_cache: Dict[str, Any] = {}
    
    def optimize_system_network(self):
        """Системийн сүлжээний настройкуудыг оптимизаци хийх"""
        try:
            if platform.system() == "Windows":
                # Windows TCP настройкууд
                commands = [
                    "netsh int tcp set global autotuninglevel=normal",
                    "netsh int tcp set global chimney=enabled", 
                    "netsh int tcp set global rss=enabled",
                    "netsh int tcp set global netdma=enabled"
                ]
                
                for cmd in commands:
                    try:
                        os.system(cmd)
                        self.logger.debug(f"Гүйцэтгэсэн: {cmd}")
                    except Exception as e:
                        self.logger.warning(f"Команд амжилтгүй: {cmd} - {e}")
                        
        except Exception as e:
            self.logger.warning(f"Сүлжээний оптимизаци амжилтгүй: {e}")
    
    def test_connection_quality(self, host: str, port: int) -> Dict[str, Any]:
        """Сүлжээний чанарыг шалгах"""
        results = {
            "latency_ms": 0,
            "packet_loss": 0.0,
            "bandwidth_mbps": 0.0,
            "jitter_ms": 0.0,
            "connection_stable": False
        }
        
        try:
            # Latency тест
            latencies = []
            for i in range(5):
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                
                try:
                    result = sock.connect_ex((host, port))
                    end_time = time.time()
                    
                    if result == 0:
                        latency_ms = (end_time - start_time) * 1000
                        latencies.append(latency_ms)
                    else:
                        results["packet_loss"] += 20  # 20% алдагдал
                        
                except Exception:
                    results["packet_loss"] += 20
                finally:
                    sock.close()
                
                time.sleep(0.1)  # Хэмжээний зай
            
            if latencies:
                results["latency_ms"] = sum(latencies) / len(latencies)
                results["jitter_ms"] = max(latencies) - min(latencies)
                results["connection_stable"] = results["latency_ms"] < 100 and results["jitter_ms"] < 50
                
                # Bandwidth тооцоолол (rough estimation)
                if results["latency_ms"] < 20:
                    results["bandwidth_mbps"] = 100  # Сайн
                elif results["latency_ms"] < 50:
                    results["bandwidth_mbps"] = 50   # Дунд зэрэг  
                elif results["latency_ms"] < 100:
                    results["bandwidth_mbps"] = 25   # Муу
                else:
                    results["bandwidth_mbps"] = 10   # Маш муу
            
            self.logger.info(f"Сүлжээний тест {host}:{port} - "
                           f"Latency: {results['latency_ms']:.1f}ms, "
                           f"Packet Loss: {results['packet_loss']:.1f}%, "
                           f"Jitter: {results['jitter_ms']:.1f}ms")
                           
        except Exception as e:
            self.logger.error(f"Сүлжээний тест амжилтгүй: {e}")
            
        return results
    
    def get_optimal_stream_settings(self, network_quality: Dict[str, Any]) -> Dict[str, Any]:
        """Сүлжээний чанарт тохируулсан оптимал настройка"""
        settings = {
            "preset": "superfast",
            "tune": "zerolatency", 
            "buffer_size_multiplier": 0.5,
            "keyframe_interval": 1.0,
            "max_bitrate_reduction": 1.0,
            "rtmp_buffer": 1000,
            "tcp_nodelay": True
        }
        
        latency = network_quality.get("latency_ms", 100)
        packet_loss = network_quality.get("packet_loss", 0)
        jitter = network_quality.get("jitter_ms", 0)
        
        # Latency дээр суурилсан оптимизаци
        if latency > 150:  # Маш удаан холболт
            settings.update({
                "preset": "ultrafast",
                "buffer_size_multiplier": 0.25,
                "keyframe_interval": 0.5,
                "max_bitrate_reduction": 0.7,
                "rtmp_buffer": 500
            })
            self.logger.warning(f"Удаан холболт илрүүлэгдлээ ({latency:.1f}ms) - Экстрем оптимизаци идэвхжүүлэгдлээ")
            
        elif latency > 100:  # Удаан холболт
            settings.update({
                "preset": "ultrafast",
                "buffer_size_multiplier": 0.3,
                "keyframe_interval": 0.75,
                "max_bitrate_reduction": 0.8,
                "rtmp_buffer": 750
            })
            self.logger.info(f"Удаан холболт ({latency:.1f}ms) - Оптимизаци идэвхжүүлэгдлээ")
            
        elif latency > 50:   # Дунд зэрэг холболт
            settings.update({
                "preset": "superfast",
                "buffer_size_multiplier": 0.4,
                "keyframe_interval": 1.0,
                "max_bitrate_reduction": 0.9,
                "rtmp_buffer": 1000
            })
            
        # Packet loss дээр суурилсан оптимизаци  
        if packet_loss > 5:
            settings.update({
                "keyframe_interval": 0.5,  # Илүү олон keyframe
                "max_bitrate_reduction": settings["max_bitrate_reduction"] * 0.8,
                "rtmp_buffer": settings["rtmp_buffer"] // 2
            })
            self.logger.warning(f"Пакет алдагдал өндөр ({packet_loss:.1f}%) - Тогтвортой байдлыг сайжруулж байна")
        
        # Jitter дээр суурилсан оптимизаци
        if jitter > 50:
            settings.update({
                "buffer_size_multiplier": settings["buffer_size_multiplier"] * 0.8,
                "rtmp_flush_interval": 5  # Илүү олон flush
            })
            
        return settings


class StreamReconnector:
    """Автомат дахин холбогч"""
    
    def __init__(self, stream_processor, logger):
        self.stream_processor = stream_processor
        self.logger = logger
        self.reconnect_attempts = 0
        self.max_attempts = 5
        self.reconnect_delay = 2  # секунд
        
    def should_reconnect(self, error_message: str) -> bool:
        """Дахин холбох шаардлагатай эсэхийг тодорхойлох"""
        reconnect_triggers = [
            "connection refused",
            "connection reset",
            "network unreachable", 
            "timeout",
            "broken pipe",
            "rtmp",
            "io error"
        ]
        
        error_lower = error_message.lower()
        return any(trigger in error_lower for trigger in reconnect_triggers)
    
    def attempt_reconnect(self) -> bool:
        """Дахин холбох оролдлого"""
        if self.reconnect_attempts >= self.max_attempts:
            self.logger.error(f"Дахин холбох оролдлого дууслаа ({self.max_attempts} удаа)")
            return False
            
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Exponential backoff
        
        self.logger.info(f"Дахин холбох оролдлого {self.reconnect_attempts}/{self.max_attempts} "
                        f"({delay} секундын дараа)")
        
        time.sleep(delay)
        
        try:
            # Stream дахин эхлүүлэх
            config = self.stream_processor.stream_config
            
            # Сүлжээний чанар дахин шалгах
            network_opt = NetworkOptimizer(self.logger)
            quality = network_opt.test_connection_quality(
                config.server.host, 
                config.server.rtmp_port
            )
            
            # Настройка автомат засварлах
            if not quality["connection_stable"]:
                optimal_settings = network_opt.get_optimal_stream_settings(quality)
                self._apply_optimal_settings(config, optimal_settings)
            
            # Дахин эхлүүлэх
            if self.stream_processor.start_stream():
                self.logger.info("Дахин холбогдлоо амжилттай!")
                self.reconnect_attempts = 0  # Reset counter
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Дахин холбох оролдлого амжилтгүй: {e}")
            return False
    
    def _apply_optimal_settings(self, config, optimal_settings):
        """Оптимал настройкуудыг хэрэглэх"""
        try:
            # Bitrate багасгах
            if "max_bitrate_reduction" in optimal_settings:
                reduction = optimal_settings["max_bitrate_reduction"]
                
                # Video bitrate багасгах
                current_video = int(config.quality["video_bitrate"].replace("k", ""))
                new_video = int(current_video * reduction)
                config.quality["video_bitrate"] = f"{new_video}k"
                
                # Audio bitrate багасгах
                current_audio = int(config.quality["audio_bitrate"].replace("k", ""))
                new_audio = int(current_audio * reduction)
                config.quality["audio_bitrate"] = f"{new_audio}k"
                
                self.logger.info(f"Bitrate багасгагдлаа: Video {current_video}k→{new_video}k, "
                               f"Audio {current_audio}k→{new_audio}k")
            
            # Encoder preset өөрчлөх
            if "preset" in optimal_settings:
                config.preset = optimal_settings["preset"]
                self.logger.info(f"Encoder preset өөрчлөгдлөө: {config.preset}")
                
        except Exception as e:
            self.logger.warning(f"Настройка хэрэглэх амжилтгүй: {e}")


# Export классууд
__all__ = [
    'NetworkOptimizer',
    'StreamReconnector'
]


# Test функц
if __name__ == "__main__":
    """Test network optimization"""
    import sys
    
    logger = get_logger(__name__)
    network_opt = NetworkOptimizer(logger)
    
    # Test connection quality
    print("🧪 Сүлжээний чанар шалгаж байна...")
    quality = network_opt.test_connection_quality("localhost", 1935)
    
    print(f"📊 Үр дүн:")
    print(f"  Latency: {quality['latency_ms']:.1f}ms")
    print(f"  Packet Loss: {quality['packet_loss']:.1f}%") 
    print(f"  Jitter: {quality['jitter_ms']:.1f}ms")
    print(f"  Stable: {quality['connection_stable']}")
    
    # Test optimal settings
    print("\n⚙️ Оптимал настройка:")
    settings = network_opt.get_optimal_stream_settings(quality)
    for key, value in settings.items():
        print(f"  {key}: {value}")
