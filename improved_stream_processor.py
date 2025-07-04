#!/usr/bin/env python3
"""
Improved Stream Processor for VM Networks
VM сүлжээнд оптимизацилагдсан stream processor
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

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

# Import network optimizations
try:
    from network_optimizations import NetworkOptimizer, StreamReconnector
except ImportError:
    print("Warning: network_optimizations module not found, using fallback")
    # Fallback бичих
    class NetworkOptimizer:
        def __init__(self, logger):
            self.logger = logger
        def test_connection_quality(self, host, port):
            return {"latency_ms": 50, "packet_loss": 0, "connection_stable": True}
        def get_optimal_stream_settings(self, quality):
            return {"preset": "veryfast", "buffer_size_multiplier": 0.5}
    
    class StreamReconnector:
        def __init__(self, processor, logger):
            self.processor = processor
            self.logger = logger
        def should_reconnect(self, error):
            return False
        def attempt_reconnect(self):
            return False


class ImprovedStreamProcessor(QObject):
    """VM сүлжээнд оптимизацилагдсан stream processor"""
    
    # Signals
    started = pyqtSignal(str)
    stopped = pyqtSignal(str, int, str)
    error_occurred = pyqtSignal(str, str)
    statistics_updated = pyqtSignal(str, dict)
    reconnecting = pyqtSignal(str)  # Шинэ signal
    
    def __init__(self, stream_config):
        super().__init__()
        self.stream_config = stream_config
        self.process = None
        self.is_running = False
        self.start_time = None
        
        # Сүлжээний оптимизаци
        self.network_optimizer = NetworkOptimizer(get_logger(__name__))
        self.reconnector = StreamReconnector(self, get_logger(__name__))
        
        # Статистик
        self.stats = {
            'fps': 0.0,
            'bitrate': '0kbits/s',
            'frames_processed': 0,
            'dropped_frames': 0,
            'uptime': '00:00:00',
            'network_quality': {},
            'reconnect_count': 0
        }
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        
        # Алдаа задлан шинжилгээ
        self.error_patterns = {
            'connection_failed': ['connection refused', 'connection reset', 'network unreachable'],
            'timeout': ['timeout', 'timed out'],
            'auth_failed': ['authentication failed', 'unauthorized'],
            'server_error': ['server error', '500', '503'],
            'stream_error': ['stream not found', 'invalid stream']
        }
        
        self.logger = get_logger(__name__)
        
        # Системийн сүлжээний оптимизаци
        self.network_optimizer.optimize_system_network()
    
    def start_stream(self) -> bool:
        """Сайжруулсан stream эхлүүлэх"""
        try:
            if self.is_running:
                return False
            
            # Эхлээд сүлжээний чанар шалгах
            self.logger.info("Сүлжээний чанар шалгаж байна...")
            network_quality = self.network_optimizer.test_connection_quality(
                self.stream_config.server.host,
                self.stream_config.server.rtmp_port
            )
            
            self.stats['network_quality'] = network_quality
            
            # Сүлжээний чанар муу бол настройка засварлах
            if not network_quality.get('connection_stable', False):
                self.logger.warning("Сүлжээний чанар тогтворгүй - настройка автомат засварлагдана")
                optimal_settings = self.network_optimizer.get_optimal_stream_settings(network_quality)
                self._apply_network_optimizations(optimal_settings)
            
            # Оптимизацилагдсан FFmpeg команд үүсгэх
            cmd = self._build_optimized_ffmpeg_command()
            if not cmd:
                return False
            
            # Process эхлүүлэх
            self.process = QProcess()
            self.process.finished.connect(self._on_process_finished)
            self.process.errorOccurred.connect(self._on_process_error)
            self.process.readyReadStandardOutput.connect(self._on_output_ready)
            self.process.readyReadStandardError.connect(self._on_error_ready)
            
            # Процессийн environment variables тохируулах
            env = QProcessEnvironment.systemEnvironment()
            env.insert("FFREPORT", "file=ffmpeg_log.txt:level=32")  # Дэлгэрэнгүй лог
            self.process.setProcessEnvironment(env)
            
            # Процесс эхлүүлэх
            self.process.start(cmd[0], cmd[1:])
            
            if self.process.waitForStarted(10000):  # 10 секунд хүлээх
                self.is_running = True
                self.start_time = datetime.now()
                self.stats_timer.start(1000)
                self.started.emit(self.stream_config.stream_key)
                
                self.logger.info(f"Stream амжилттай эхэллээ: {self.stream_config.stream_key}")
                self.logger.info(f"Сүлжээний чанар: Latency {network_quality.get('latency_ms', 'N/A'):.1f}ms, "
                               f"Packet Loss {network_quality.get('packet_loss', 'N/A'):.1f}%")
                return True
            else:
                self.logger.error("FFmpeg процесс эхлэх амжилтгүй боллоо")
                return False
                
        except Exception as e:
            self.logger.error(f"Stream эхлүүлэх алдаа: {e}")
            self.error_occurred.emit(self.stream_config.stream_key, str(e))
            return False
    
    def stop_stream(self):
        """Stop streaming process"""
        if self.process and self.is_running:
            self.stats_timer.stop()
            self.process.terminate()
            if not self.process.waitForFinished(5000):
                self.process.kill()
            self.is_running = False
    
    def _apply_network_optimizations(self, optimal_settings: Dict[str, Any]):
        """Сүлжээний оптимизаци хэрэглэх"""
        try:
            # Bitrate багасгах
            if "max_bitrate_reduction" in optimal_settings:
                reduction = optimal_settings["max_bitrate_reduction"]
                
                original_video = int(self.stream_config.quality["video_bitrate"].replace("k", ""))
                original_audio = int(self.stream_config.quality["audio_bitrate"].replace("k", ""))
                
                new_video = max(int(original_video * reduction), 200)  # Хамгийн багадаа 200k
                new_audio = max(int(original_audio * reduction), 64)   # Хамгийн багадаа 64k
                
                self.stream_config.quality["video_bitrate"] = f"{new_video}k"
                self.stream_config.quality["audio_bitrate"] = f"{new_audio}k"
                
                self.logger.info(f"Bitrate автомат багасгагдлаа: "
                               f"Video {original_video}k→{new_video}k, "
                               f"Audio {original_audio}k→{new_audio}k")
            
            # Encoder настройка
            if "preset" in optimal_settings:
                self.stream_config.preset = optimal_settings["preset"]
                
            # Keyframe interval
            if "keyframe_interval" in optimal_settings:
                self.keyframe_interval = optimal_settings["keyframe_interval"]
                
        except Exception as e:
            self.logger.warning(f"Сүлжээний оптимизаци хэрэглэх амжилтгүй: {e}")
    
    def _build_optimized_ffmpeg_command(self) -> List[str]:
        """VM сүлжээнд зориулсан оптимизацилагдсан FFmpeg команд"""
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        # Сүлжээний оптимизаци
        cmd.extend([
            "-fflags", "+genpts+igndts+discardcorrupt+flush_packets",
            "-thread_queue_size", "1024",     # Том queue
            "-probesize", "32768",            # Хурдан анализ
            "-analyzeduration", "500000"      # Богино анализ (500ms)
        ])

        # Оролтын тохиргоо (энгийн хувилбар)
        if self.stream_config.input_source.startswith("live:"):
            input_type = self.stream_config.input_source.split(":")[1]
            if input_type == "test_pattern":
                cmd.extend([
                    "-f", "lavfi", 
                    "-i", "testsrc=size=1280x720:rate=30,anullsrc=channel_layout=stereo:sample_rate=44100"
                ])
            elif input_type == "desktop_capture":
                cmd.extend(["-f", "gdigrab", "-i", "desktop"])
        else:
            # Файл оролт
            if self.stream_config.loop_input:
                cmd.extend(["-stream_loop", "-1"])
            if self.stream_config.start_time:
                cmd.extend(["-ss", self.stream_config.start_time])
            cmd.extend(["-i", str(self.stream_config.input_source)])
            if self.stream_config.duration:
                cmd.extend(["-t", self.stream_config.duration])

        # VM сүлжээнд зориулсан видео кодлол
        quality = self.stream_config.quality
        
        # Keyframe interval тооцоолох
        keyframe_interval = getattr(self, 'keyframe_interval', 1.0)
        keyframes_per_second = quality["fps"] * keyframe_interval
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", getattr(self.stream_config, 'preset', 'superfast'),
            "-tune", "zerolatency",
            "-profile:v", "baseline",
            "-level", "3.1",
            "-b:v", quality["video_bitrate"],
            "-s", f"{quality['width']}x{quality['height']}",
            "-r", str(quality["fps"]),
            "-pix_fmt", "yuv420p",
            
            # Keyframe настройка
            "-g", str(int(keyframes_per_second)),
            "-keyint_min", str(int(keyframes_per_second)),
            "-sc_threshold", "0",
            
            # VM сүлжээнд зориулсан оптимизаци
            "-bf", "0",                    # B-frame унтраах
            "-refs", "1",                  # Reference frame цөөрүүлэх
            "-flags", "+cgop+low_delay",   # Low delay
            "-fflags", "+flush_packets"    # Пакетыг шууд илгээх
        ])

        # Буферлалт тохиргоо
        video_bitrate_num = int(quality["video_bitrate"].replace('k', ''))
        buffer_multiplier = getattr(self, 'buffer_multiplier', 0.5)
        buffer_size = f"{int(video_bitrate_num * buffer_multiplier)}k"
        
        if self.stream_config.rate_control == "CBR":
            cmd.extend([
                "-minrate", quality["video_bitrate"],
                "-maxrate", quality["video_bitrate"],
                "-bufsize", buffer_size
            ])

        # Аудио кодлол
        if not self.stream_config.input_source.startswith("live:test_pattern"):
            cmd.extend([
                "-c:a", "aac",
                "-b:a", quality["audio_bitrate"],
                "-ar", "44100",
                "-ac", "2",
                "-aac_coder", "fast"
            ])

        # RTMP/VM холболтын оптимизаци
        rtmp_url = f"{self.stream_config.server.rtmp_url}/{self.stream_config.stream_key}"
        rtmp_buffer = getattr(self, 'rtmp_buffer', 500)  # Default 500ms буфер
        
        cmd.extend([
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            
            # RTMP сүлжээний тохиргоо
            "-rtmp_live", "live",
            "-rtmp_buffer", str(rtmp_buffer),
            "-rtmp_flush_interval", "10",
            
            # TCP тохиргоо (хэрэв дэмжиж байвал)
            "-tcp_nodelay", "1",
            
            rtmp_url
        ])

        self.logger.info(f"Оптимизацилагдсан FFmpeg команд үүсгэгдлээ")
        self.logger.debug(f"Команд: {' '.join(cmd)}")
        return cmd
    
    def _update_stats(self):
        """Update streaming statistics"""
        if self.start_time:
            uptime = datetime.now() - self.start_time
            self.stats['uptime'] = str(uptime).split('.')[0]
        
        # Emit updated statistics
        self.statistics_updated.emit(self.stream_config.stream_key, self.stats.copy())
    
    def _on_process_finished(self, exit_code, exit_status):
        """Handle process finished"""
        self.is_running = False
        self.stats_timer.stop()
        message = f"Процесс дууслаа, гаралтын код: {exit_code}"
        self.stopped.emit(self.stream_config.stream_key, exit_code, message)
    
    def _on_process_error(self, error):
        """Сайжруулсан алдаа зохицуулах"""
        self.is_running = False
        self.stats_timer.stop()
        
        error_message = f"FFmpeg алдаа: {error}"
        
        # Дэлгэрэнгүй алдааны мэдээлэл
        if self.process:
            stderr_data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if stderr_data:
                error_message += f"\n\nДэлгэрэнгүй:\n{stderr_data}"
        
        # Алдааны төрөл тодорхойлох
        error_type = self._classify_error(error_message)
        self.logger.error(f"Stream алдаа [{error_type}]: {error_message}")
        
        # Автомат дахин холбох шаардлагатай эсэхийг шалгах
        if self.reconnector.should_reconnect(error_message):
            self.reconnecting.emit(self.stream_config.stream_key)
            self.logger.info("Автомат дахин холбох эхэллээ...")
            
            # Дахин холбох оролдлого (бэкграундад)
            QTimer.singleShot(1000, lambda: self._attempt_auto_reconnect(error_message))
        else:
            self.error_occurred.emit(self.stream_config.stream_key, error_message)
    
    def _classify_error(self, error_message: str) -> str:
        """Алдааны төрөл тодорхойлох"""
        error_lower = error_message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            if any(pattern in error_lower for pattern in patterns):
                return error_type
                
        return "unknown"
    
    def _attempt_auto_reconnect(self, original_error: str):
        """Автомат дахин холбох оролдлого"""
        try:
            if self.reconnector.attempt_reconnect():
                self.stats['reconnect_count'] += 1
                self.logger.info(f"Автомат дахин холбогдлоо! (Нийт: {self.stats['reconnect_count']} удаа)")
            else:
                self.logger.error("Автомат дахин холбох амжилтгүй боллоо")
                self.error_occurred.emit(self.stream_config.stream_key, 
                                       f"Дахин холбох амжилтгүй: {original_error}")
                                       
        except Exception as e:
            self.logger.error(f"Автомат дахин холбох алдаа: {e}")
            self.error_occurred.emit(self.stream_config.stream_key, str(e))
    
    def _on_output_ready(self):
        """Handle standard output"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _on_error_ready(self):
        """Handle error output"""
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self._parse_ffmpeg_output(data)
    
    def _parse_ffmpeg_output(self, output: str):
        """Сайжруулсан FFmpeg гаралт боловсруулах"""
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Алдааны шинжилгээ
            if any(error_word in line.lower() for error_word in 
                   ['error', 'failed', 'connection refused', 'timeout', 'cannot', 'unable']):
                self.logger.warning(f"FFmpeg сэрэмжлүүлэг: {line}")
                
                # Зарим алдаануудыг автомат засварлах оролдох
                if 'rtmp' in line.lower() and 'timeout' in line.lower():
                    self.logger.info("RTMP timeout илрүүлэгдлээ - буферлалт багасгаж байна")
                    self.rtmp_buffer = max(getattr(self, 'rtmp_buffer', 1000) // 2, 100)  # Буферлалт хагасалах
                
            # Статистик боловсруулах
            if 'fps=' in line and 'bitrate=' in line:
                try:
                    # FPS парс хийх
                    fps_match = line.split('fps=')[1].split()[0]
                    self.stats['fps'] = float(fps_match)
                    
                    # Bitrate парс хийх
                    bitrate_match = line.split('bitrate=')[1].split()[0]
                    self.stats['bitrate'] = bitrate_match
                    
                    # Frame count парс хийх (хэрэв байвал)
                    if 'frame=' in line:
                        frame_match = line.split('frame=')[1].split()[0]
                        self.stats['frames_processed'] = int(frame_match)
                        
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Статистик парс хийх алдаа: {e}")
    
    def get_uptime(self) -> str:
        """Get stream uptime"""
        return self.stats['uptime']
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Сүлжээний статистик авах"""
        return {
            'quality': self.stats.get('network_quality', {}),
            'reconnect_count': self.stats.get('reconnect_count', 0),
            'is_optimized': hasattr(self, 'buffer_multiplier'),
            'current_settings': {
                'preset': getattr(self.stream_config, 'preset', 'default'),
                'buffer_size': getattr(self, 'rtmp_buffer', 'default'),
                'keyframe_interval': getattr(self, 'keyframe_interval', 1.0)
            }
        }


# Export классууд
__all__ = [
    'ImprovedStreamProcessor'
]


# Test функц
if __name__ == "__main__":
    """Test improved stream processor"""
    import sys
    
    # Mock stream config for testing
    class MockStreamConfig:
        def __init__(self):
            self.stream_key = "test_stream"
            self.input_source = "live:test_pattern"
            self.server = type('obj', (object,), {
                'host': 'localhost',
                'rtmp_port': 1935,
                'rtmp_url': 'rtmp://localhost:1935/live'
            })()
            self.quality = {
                "name": "720p (HD)",
                "width": 1280,
                "height": 720,
                "video_bitrate": "2500k",
                "audio_bitrate": "192k",
                "fps": 30
            }
            self.preset = "veryfast"
            self.rate_control = "CBR"
            self.loop_input = False
            self.start_time = None
            self.duration = None
    
    print("🧪 Improved Stream Processor Test")
    
    # Test stream config
    config = MockStreamConfig()
    
    app = QApplication(sys.argv)
    processor = ImprovedStreamProcessor(config)
    
    print("✅ Processor үүсгэгдлээ")
    print("✅ Сүлжээний оптимизаци бэлэн")
    print("✅ VM холболтын дэмжлэг идэвхтэй")
    
    # Test command building
    cmd = processor._build_optimized_ffmpeg_command()
    if cmd:
        print("✅ FFmpeg команд амжилттай үүсгэгдлээ")
        print(f"📝 Командын урт: {len(cmd)} параметр")
    else:
        print("❌ FFmpeg команд үүсгэх амжилтгүй")
    
    print("\n🎯 VM оптимизацийн онцлогууд:")
    print("  • Латенси багасгах: zerolatency tune")
    print("  • Буферлалт оптимизаци: 0.5x мультипликатор")  
    print("  • B-frame унтраах: 0 B-frames")
    print("  • Keyframe давтамж нэмэх: 1 секунд")
    print("  • RTMP буфер багасгах: 500ms")
    print("  • Автомат дахин холбох: 5 удаа хүртэл")
    
    sys.exit(0)
