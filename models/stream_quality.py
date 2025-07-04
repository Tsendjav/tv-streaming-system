# tv_streaming_system/models/stream_quality.py
"""
Data model for Stream Quality settings.
Defines the structure for video quality presets.
"""

from dataclasses import dataclass

@dataclass
class StreamQuality:
    """Represents a predefined streaming quality preset."""
    name: str
    resolution: str  # e.g., "1920x1080"
    bitrate: str     # e.g., "4500k"
    framerate: str   # e.g., "30" or "60"
    audio_bitrate: str = "192k" # Default audio bitrate for this quality

    def __str__(self):
        return f"{self.name} ({self.resolution} @ {self.framerate}fps, {self.bitrate})"

    def to_dict(self):
        return {
            'name': self.name,
            'resolution': self.resolution,
            'bitrate': self.bitrate,
            'framerate': self.framerate,
            'audio_bitrate': self.audio_bitrate
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            resolution=data['resolution'],
            bitrate=data['bitrate'],
            framerate=data['framerate'],
            audio_bitrate=data.get('audio_bitrate', '192k')
        )