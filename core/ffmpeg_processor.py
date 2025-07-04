# tv_streaming_system/core/ffmpeg_processor.py
"""
FFmpeg Processing Module
Handles all FFmpeg-related operations, including encoding, decoding, and processing.
"""

import subprocess
import threading
import time
import os
from typing import List, Optional, Dict, Union

class FFmpegProcessor:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        print(f"FFmpegProcessor initialized with path: {self.ffmpeg_path}")

    def _run_command(self, cmd: List[str], timeout: int = 60) -> Optional[str]:
        """Internal helper to run FFmpeg commands."""
        try:
            print(f"Executing FFmpeg command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode != 0:
                print(f"FFmpeg Error (return code {process.returncode}):\n{stderr}")
                return None
            return stdout
        except FileNotFoundError:
            print(f"Error: FFmpeg not found at '{self.ffmpeg_path}'. Please ensure it's in your PATH or specify the correct path.")
            return None
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print(f"FFmpeg command timed out after {timeout} seconds.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during FFmpeg execution: {e}")
            return None

    def transcode_media(self, input_file: str, output_file: str, codec: str = "libx264", bitrate: str = "2M") -> bool:
        """Transcodes a media file to a specified format/codec."""
        cmd = [
            self.ffmpeg_path,
            "-i", input_file,
            "-c:v", codec,
            "-b:v", bitrate,
            "-c:a", "aac",
            "-b:a", "128k",
            "-y", # Overwrite output file without asking
            output_file
        ]
        result = self._run_command(cmd)
        if result:
            print(f"Successfully transcoded {input_file} to {output_file}")
            return True
        return False

    def generate_thumbnail(self, video_file: str, output_thumbnail: str, time_pos: str = "00:00:05") -> bool:
        """Generates a thumbnail from a video file."""
        cmd = [
            self.ffmpeg_path,
            "-i", video_file,
            "-ss", time_pos,
            "-vframes", "1",
            "-y",  # Overwrite output file
            output_thumbnail
        ]
        result = self._run_command(cmd)
        if result:
            print(f"Successfully generated thumbnail for {video_file} at {time_pos} to {output_thumbnail}")
            return True
        return False
    
    def get_media_info(self, media_file: str) -> Optional[Dict]:
        """Get media file information using ffprobe"""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", media_file
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting media info: {e}")
        return None
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run([self.ffmpeg_path, "-version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False

# Export the class
__all__ = ['FFmpegProcessor']

# Example usage (requires ffmpeg installed and in PATH, or specify full path)
if __name__ == "__main__":
    processor = FFmpegProcessor()
    
    # Test FFmpeg availability
    if processor.is_ffmpeg_available():
        print("✅ FFmpeg is available")
    else:
        print("❌ FFmpeg is not available")
    
    # Create a dummy video file for testing
    dummy_video_path = "dummy_video.mp4"
    with open(dummy_video_path, "w") as f:
        f.write("This is a dummy video file content.") # Not a real video, but for path existence

    output_transcoded_path = "output_transcoded.mp4"
    output_thumbnail_path = "output_thumbnail.jpg"

    # Test transcoding (this will fail without a real video file/FFmpeg setup)
    print(f"Attempting to transcode {dummy_video_path}...")
    # success = processor.transcode_media(dummy_video_path, output_transcoded_path)
    # print(f"Transcode success: {success}")

    # Test thumbnail generation (this will fail without a real video file/FFmpeg setup)
    print(f"Attempting to generate thumbnail for {dummy_video_path}...")
    # success = processor.generate_thumbnail(dummy_video_path, output_thumbnail_path)
    # print(f"Thumbnail generation success: {success}")

    # Cleanup dummy file
    if os.path.exists(dummy_video_path):
        os.remove(dummy_video_path)
    if os.path.exists(output_transcoded_path):
        os.remove(output_transcoded_path)
    if os.path.exists(output_thumbnail_path):
        os.remove(output_thumbnail_path)
