# tv_streaming_system/audio/audio_profiles.py

import json
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AudioProfile:
    """
    Нэг аудио профайлыг тодорхойлно.
    Үүнд энэ профайлд багтах LV2 plugin-ууд болон тэдгээрийн тохиргоо орно.
    """
    def __init__(self, name: str, description: str, plugins: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.plugins = plugins # List of dicts, each with 'uri', 'enabled', 'parameters'
        logger.debug(f"AudioProfile '{self.name}' created.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "plugins": self.plugins
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioProfile':
        return cls(data["name"], data.get("description", ""), data.get("plugins", []))


class AudioProfileManager:
    """
    Аудио профайлуудыг удирдах менежер.
    Профайлуудыг файл болон санах ойд хадгална.
    """
    def __init__(self, config_file: str = "data/audio_profiles.json"):
        self.config_file = Path(config_file)
        self.profiles: Dict[str, AudioProfile] = {}
        self._load_profiles()
        logger.info(f"AudioProfileManager initialized. Config file: {self.config_file}")

    def _load_profiles(self):
        """
        Тохиргооны файлаас профайлуудыг ачаалах.
        Хэрэв файл байхгүй бол өгөгдмөл профайлуудыг үүсгэнэ.
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for profile_data in data.get("profiles", []):
                        profile = AudioProfile.from_dict(profile_data)
                        self.profiles[profile.name] = profile
                logger.info(f"Loaded {len(self.profiles)} audio profiles from {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding audio profiles JSON from {self.config_file}: {e}")
                self._create_default_profiles() # Fallback to defaults
            except Exception as e:
                logger.error(f"Error loading audio profiles from {self.config_file}: {e}")
                self._create_default_profiles() # Fallback to defaults
        else:
            self._create_default_profiles()
            self._save_profiles() # Save defaults to file
            logger.info("Created default audio profiles.")

    def _create_default_profiles(self):
        """Өгөгдмөл аудио профайлуудыг үүсгэх."""
        self.profiles.clear() # Clear existing profiles

        # Default profile (no specific effects, just base EQ if needed)
        self.add_profile(AudioProfile(
            name="default",
            description="General purpose audio profile.",
            plugins=[
                {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": 0.0, "mid_gain": 0.0, "high_gain": 0.0, "freq1": 1000.0}},
            ]
        ))

        # Movie mode: Dialogue enhancement, subtle bass boost, light compression
        self.add_profile(AudioProfile(
            name="movie_mode",
            description="Optimized for movie watching with clear dialogue and cinematic bass.",
            plugins=[
                {"uri": "urn:lv2:voice_clarity", "enabled": True, "parameters": {"enhancement": 0.4}},
                {"uri": "urn:lv2:bass_boost", "enabled": True, "parameters": {"boost": 3.0}},
                {"uri": "http://ardour.org/lv2/ardour_compressor", "enabled": True, "parameters": {"threshold": -15.0, "ratio": 2.5, "attack": 0.05, "release": 0.2}},
                {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": 1.0, "mid_gain": 0.5, "high_gain": 0.0, "freq1": 1000.0}},
            ]
        ))

        # Music mode: Flat EQ or slight loudness, no dialogue enhancement
        self.add_profile(AudioProfile(
            name="music_mode",
            description="Designed for music listening with balanced sound.",
            plugins=[
                {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": 2.0, "mid_gain": 0.0, "high_gain": 1.0, "freq1": 1000.0}},
                {"uri": "urn:lv2:voice_clarity", "enabled": False}, # Explicitly disable
                {"uri": "urn:lv2:bass_boost", "enabled": False},
            ]
        ))

        # News mode: Strong dialogue enhancement, minimal bass
        self.add_profile(AudioProfile(
            name="news_mode",
            description="Focuses on vocal clarity for news and talk shows.",
            plugins=[
                {"uri": "urn:lv2:voice_clarity", "enabled": True, "parameters": {"enhancement": 0.8}},
                {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": -3.0, "mid_gain": 2.0, "high_gain": 0.0, "freq1": 1000.0}},
                {"uri": "urn:lv2:bass_boost", "enabled": False},
            ]
        ))

        # Sports mode: Emphasize crowd noise and commentary
        self.add_profile(AudioProfile(
            name="sports_mode",
            description="Enhanced atmosphere for sports broadcasts.",
            plugins=[
                {"uri": "urn:lv2:voice_clarity", "enabled": True, "parameters": {"enhancement": 0.2}}, # Slight clarity for commentary
                {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": 3.0, "mid_gain": 1.0, "high_gain": 2.0, "freq1": 1000.0}}, # Boost lows and highs
                {"uri": "http://ardour.org/lv2/ardour_compressor", "enabled": True, "parameters": {"threshold": -10.0, "ratio": 1.5, "attack": 0.01, "release": 0.1}}, # Gentle compression for overall sound
            ]
        ))

        # Night mode: Reduce dynamic range, pull down loud sounds
        self.add_profile(AudioProfile(
            name="night_mode_profile", # This profile could be activated/deactivated separately or override others
            description="Reduces loud sounds for late-night viewing.",
            plugins=[
                {"uri": "urn:lv2:night_mode", "enabled": True, "parameters": {"reduction": 0.6}},
                {"uri": "http://ardour.org/lv2/ardour_compressor", "enabled": True, "parameters": {"threshold": -20.0, "ratio": 5.0, "attack": 0.1, "release": 0.5}},
            ]
        ))


    def _save_profiles(self):
        """Одоогийн профайлуудыг файлд хадгалах."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({"profiles": [p.to_dict() for p in self.profiles.values()]}, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved {len(self.profiles)} audio profiles to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving audio profiles to {self.config_file}: {e}")

    def add_profile(self, profile: AudioProfile):
        """Шинэ аудио профайл нэмэх."""
        if profile.name in self.profiles:
            logger.warning(f"Audio profile '{profile.name}' already exists. Overwriting.")
        self.profiles[profile.name] = profile
        self._save_profiles()
        logger.info(f"Added/updated audio profile: {profile.name}")

    def get_profile(self, name: str) -> Optional[AudioProfile]:
        """Нэрээр профайлыг авах."""
        return self.profiles.get(name)

    def delete_profile(self, name: str) -> bool:
        """Нэрээр профайлыг устгах."""
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            logger.info(f"Deleted audio profile: {name}")
            return True
        logger.warning(f"Audio profile '{name}' not found for deletion.")
        return False

    def get_all_profile_names(self) -> List[str]:
        """Бүх профайлын нэрийг авах."""
        return list(self.profiles.keys())

# Global instance
audio_profile_manager = AudioProfileManager()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("--- Audio Profile Manager Demo ---")

    # Initialize manager (will load from file or create defaults)
    manager = AudioProfileManager(config_file="test_audio_profiles.json")

    # List available profiles
    print("\nAvailable Profiles:")
    for name in manager.get_all_profile_names():
        print(f"- {name}")

    # Get a specific profile
    movie_profile = manager.get_profile("movie_mode")
    if movie_profile:
        print(f"\nDetails for 'movie_mode' profile:")
        print(f"  Description: {movie_profile.description}")
        for plugin in movie_profile.plugins:
            print(f"    Plugin URI: {plugin['uri']}, Enabled: {plugin.get('enabled', True)}, Parameters: {plugin.get('parameters', {})}")

    # Add a new custom profile
    custom_profile_data = AudioProfile(
        name="podcast_clarity",
        description="Profile optimized for podcast listening, high vocal clarity.",
        plugins=[
            {"uri": "urn:lv2:voice_clarity", "enabled": True, "parameters": {"enhancement": 0.9}},
            {"uri": "http://ardour.org/lv2/ardour_eq", "enabled": True, "parameters": {"low_gain": -5.0, "mid_gain": 3.0, "high_gain": 1.0, "freq1": 1000.0}},
        ]
    )
    manager.add_profile(custom_profile_data)
    print("\nAdded 'podcast_clarity' profile.")

    # List profiles again to confirm new addition
    print("\nAvailable Profiles (After adding custom):")
    for name in manager.get_all_profile_names():
        print(f"- {name}")

    # Delete a profile
    print("\nDeleting 'podcast_clarity' profile.")
    manager.delete_profile("podcast_clarity")

    # List profiles after deletion
    print("\nAvailable Profiles (After deleting custom):")
    for name in manager.get_all_profile_names():
        print(f"- {name}")

    # Clean up test file
    if Path("test_audio_profiles.json").exists():
        Path("test_audio_profiles.json").unlink()
        print("\nCleaned up test_audio_profiles.json")

    print("\n--- Demo End ---")