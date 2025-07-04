# tv_streaming_system/audio/tv_audio_engine.py

import logging
from typing import Dict, Any, List, Optional
import time

# Импортын хийх модулиуд
from audio.jack_backend import JACKServer, JACKClient
from audio.lv2_plugins import LV2PluginManager
from audio.carla_host import CarlaPluginHost
from audio.audio_profiles import AudioProfileManager, AudioProfile

logger = logging.getLogger(__name__)

class TVAudioSystem(JACKClient):
    """
    ТВ-ийн стриминг системийн аудио удирдлага.
    JACK, LV2, Carla-г нэгтгэн аудио боловсруулалт хийнэ.
    """
    def __init__(self, name="tv_audio_engine_client"):
        super().__init__(name)
        self.jack_server = JACKServer()
        self.lv2_plugin_manager = LV2PluginManager()
        self.carla_host = CarlaPluginHost()  # LV2PluginManager-г параметр болгон дамжуулахгүй
        self.audio_profile_manager = AudioProfileManager()
        self.master_volume = 1.0  # Initialize master volume

        # Input/Output портуудыг бүртгэх
        self.input_main = self.register_port("main_input", "audio")
        self.output_main = self.register_port("main_output", "audio", is_input=False)

        # Одоогийн аудио профайлыг ачаална
        self.current_profile: Optional[AudioProfile] = None
        self.load_profile("default")

        logger.info("TVAudioSystem initialized.")

    def register_port(self, port_name: str, port_type: str, is_input: bool = True):
        """
        Register an audio port for JACK connections.
        
        Args:
            port_name (str): Name of the port
            port_type (str): Type of port ('audio', etc.)
            is_input (bool, optional): Whether the port is input (True) or output (False). Defaults to True.
        
        Returns:
            Port object if successful, None otherwise
        """
        try:
            if self.jack_server and hasattr(self.jack_server, 'register_port'):
                return self.jack_server.register_port(self, port_name, port_type, is_input)
            else:
                logger.warning(f"Cannot register port {port_name}: JACK server not available")
                return None
        except Exception as e:
            logger.error(f"Failed to register port {port_name}: {e}")
            return None

    def load_profile(self, profile_name: str):
        """
        Аудио профайлыг ачаалж, холбогдох plugin-уудыг тохируулна.
        """
        profile = self.audio_profile_manager.get_profile(profile_name)
        if profile:
            self.current_profile = profile
            logger.info(f"Loaded audio profile: {profile.name}")

            # Одоо ачаалагдсан бүх плагиныг хасна
            for plugin_id in list(self.carla_host.plugins.keys()):  # loaded_plugins-ийн оронд plugins ашиглана
                self.carla_host.remove_plugin(plugin_id)

            # Профайлд заасан плагинуудыг ачаална, тохиргоо хийнэ
            new_plugin_chain = []
            for plugin_config in profile.plugins:
                plugin_uri = plugin_config["uri"]
                plugin_instance = self.carla_host.add_plugin(plugin_uri)
                if plugin_instance is not None:  # plugin_instance нь plugin_id буцаана
                    for param_name, value in plugin_config.get("parameters", {}).items():
                        self.carla_host.set_parameter(plugin_instance, param_name, value)
                    if not plugin_config.get("enabled", True):
                        self.carla_host.plugins[plugin_instance]["active"] = False
                    new_plugin_chain.append(plugin_instance)
                else:
                    logger.warning(f"Plugin '{plugin_uri}' from profile '{profile_name}' could not be loaded.")
            self.carla_host.reorder_plugins(new_plugin_chain)
            logger.info(f"Applied plugins from profile '{profile_name}'. New chain: {new_plugin_chain}")

        else:
            logger.warning(f"Audio profile '{profile_name}' not found.")

    def set_content_type(self, content_type: str):
        """
        Контентын төрлөөс хамаарч аудио профайлыг автоматаар сонгоно.
        """
        if content_type == "movie":
            self.load_profile("movie_mode")
        elif content_type == "music":
            self.load_profile("music_mode")
        elif content_type == "news":
            self.load_profile("news_mode")
        elif content_type == "sports":
            self.load_profile("sports_mode")
        else:
            self.load_profile("default")
        logger.info(f"Set content type to '{content_type}', loaded corresponding audio profile.")

    def enable_night_mode(self, enable: bool = True):
        """Шөнийн горимыг идэвхжүүлэх/идэвхгүй болгох."""
        night_mode_id = None
        for plugin_id, plugin in self.carla_host.plugins.items():
            if plugin["uri"] == "urn:lv2:night_mode":
                night_mode_id = plugin_id
                break
        if night_mode_id is not None:
            self.carla_host.plugins[night_mode_id]["active"] = enable
            logger.info(f"Night Mode {'enabled' if enable else 'disabled'}.")
        else:
            logger.warning("Night Mode plugin not loaded.")

    def enhance_dialogue(self, enable: bool = True):
        """Яриаг сайжруулах горимыг идэвхжүүлэх/идэвхгүй болгох."""
        voice_clarity_id = None
        for plugin_id, plugin in self.carla_host.plugins.items():
            if plugin["uri"] == "urn:lv2:voice_clarity":
                voice_clarity_id = plugin_id
                break
        if voice_clarity_id is not None:
            self.carla_host.plugins[voice_clarity_id]["active"] = enable
            logger.info(f"Voice Clarity {'enabled' if enable else 'disabled'}.")
        else:
            logger.warning("Voice Clarity plugin not loaded.")

    def set_bass_boost(self, boost_db: float):
        """Бассыг өсгөх түвшинг тохируулах."""
        bass_boost_id = None
        for plugin_id, plugin in self.carla_host.plugins.items():
            if plugin["uri"] == "urn:lv2:bass_boost":
                bass_boost_id = plugin_id
                break
        if bass_boost_id is not None:
            self.carla_host.set_parameter(bass_boost_id, "boost", boost_db)
            self.carla_host.plugins[bass_boost_id]["active"] = (boost_db > 0)
            logger.info(f"Bass Boost set to {boost_db} dB.")
        else:
            logger.warning("Bass Boost plugin not loaded.")

    def process(self):
        """
        JACK-ийн аудио боловсруулалтын callback.
        Эндээс үндсэн аудио оролтоос авсан өгөгдлийг Carla хостоор дамжуулж,
        гаралтын порт руу илгээнэ.
        """
        input_audio = self.input_main.read_buffer()

        if input_audio:
            processed_audio = self.carla_host.process_audio_buffer(input_audio)
            processed_audio = [sample * self.master_volume for sample in processed_audio]  # Apply master volume
            self.output_main.write_buffer(processed_audio)
            logger.debug(f"Processed and routed {len(input_audio)} samples through TVAudioSystem.")
        else:
            logger.debug("TVAudioSystem: No input audio to process.")

    def unregister_port(self, port):
        """Unregister audio port"""
        try:
            if self.jack_server and hasattr(self.jack_server, 'unregister_port'):
                return self.jack_server.unregister_port(port)
            else:
                logger.warning("Cannot unregister port: JACK server not available")
                return False
        except Exception as e:
            logger.error(f"Failed to unregister port: {e}")
            return False

    def connect_ports(self, source_port, dest_port):
        """Connect two audio ports"""
        try:
            if self.jack_server and hasattr(self.jack_server, 'connect_ports'):
                return self.jack_server.connect_ports(source_port, dest_port)
            else:
                logger.warning("Cannot connect ports: JACK server not available")
                return False
        except Exception as e:
            logger.error(f"Failed to connect ports: {e}")
            return False

    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        try:
            self.master_volume = max(0.0, min(1.0, volume))
            logger.info(f"Master volume set to {self.master_volume:.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to set master volume: {e}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("--- TV Audio System Demo ---")

    # Create an instance of the TVAudioSystem
    audio_system = TVAudioSystem()

    # Register the audio system client with the global JACK server
    audio_system.jack_server.register_client(audio_system)
    audio_system.activate()

    # Simulate creating buffers for I/O ports
    buffer_size = 1024
    audio_system.input_main.create_buffer(10)
    audio_system.output_main.create_buffer(10)

    # --- Simulate an external audio source writing to TVAudioSystem's input ---
    class MockAudioSource(JACKClient):
        def __init__(self, name="mock_source", output_port_name="output"):
            super().__init__(name)
            self.output_port = self.register_port(output_port_name, "audio", is_input=False)
            self.output_port.create_buffer(10)
            self.counter = 0

        def process(self):
            dummy_audio = [i * 0.01 for i in range(buffer_size)]
            self.output_port.write_buffer(dummy_audio)
            self.counter += 1
            if self.counter % 50 == 0:
                logger.info(f"MockAudioSource: Generated and wrote {len(dummy_audio)} samples.")
            time.sleep(0.01)

    mock_source = MockAudioSource()
    audio_system.jack_server.register_client(mock_source)
    mock_source.activate()

    # Connect mock source to TVAudioSystem's input
    audio_system.jack_server.connect_ports(f"{mock_source.name}:{mock_source.output_port.name}", f"{audio_system.name}:{audio_system.input_main.name}")

    # --- Demo various features ---
    print("\n--- Applying 'Movie' profile ---")
    audio_system.set_content_type("movie")
    time.sleep(2)

    print("\n--- Enabling Night Mode ---")
    audio_system.enable_night_mode(True)
    time.sleep(2)

    print("\n--- Disabling Night Mode and Enabling Voice Clarity ---")
    audio_system.enable_night_mode(False)
    audio_system.enhance_dialogue(True)
    time.sleep(2)

    print("\n--- Setting Bass Boost to 8dB ---")
    audio_system.set_bass_boost(8.0)
    time.sleep(2)

    print("\n--- Applying 'Music' profile ---")
    audio_system.set_content_type("music")
    time.sleep(2)

    print("\n--- Deactivating audio system and mock source ---")
    audio_system.jack_server.disconnect_ports(f"{mock_source.name}:{mock_source.output_port.name}", f"{audio_system.name}:{audio_system.input_main.name}")
    mock_source.deactivate()
    audio_system.deactivate()

    audio_system.jack_server.unregister_client(mock_source.name)
    audio_system.jack_server.unregister_client(audio_system.name)

    print("\n--- TV Audio System Demo End ---")