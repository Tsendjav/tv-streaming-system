# tv_streaming_system/core/media_library.py
"""
Media Library Management
Handles scanning, indexing, and organizing media assets.
"""

from pathlib import Path
from typing import List, Dict, Any
import time

class MediaLibrary:
    def __init__(self, media_path: Path):
        self.media_path = media_path
        self.media_files: List[Dict[str, Any]] = []
        print(f"MediaLibrary initialized with path: {media_path}")

    def scan_media(self) -> int:
        """Scans the media directory for supported files and updates the library."""
        print(f"Scanning media in {self.media_path}...")
        start_time = time.time()
        self.media_files = [] # Clear existing
        supported_extensions = {".mp4", ".mov", ".mp3", ".wav"} # Example extensions

        count = 0
        if self.media_path.exists() and self.media_path.is_dir():
            for f in self.media_path.iterdir():
                if f.is_file() and f.suffix.lower() in supported_extensions:
                    self.media_files.append({
                        "name": f.name,
                        "path": str(f),
                        "size": f.stat().st_size,
                        "last_modified": f.stat().st_mtime,
                        "type": "video" if f.suffix.lower() in {".mp4", ".mov"} else "audio"
                    })
                    count += 1
        else:
            print(f"Media path {self.media_path} does not exist or is not a directory.")

        end_time = time.time()
        print(f"Scan complete. Found {count} media files in {end_time - start_time:.2f} seconds.")
        return count

    def get_all_media(self) -> List[Dict[str, Any]]:
        """Returns all indexed media files."""
        return self.media_files

    def search_media(self, query: str) -> List[Dict[str, Any]]:
        """Searches for media files by name."""
        return [
            media for media in self.media_files
            if query.lower() in media["name"].lower()
        ]

# Example usage
if __name__ == "__main__":
    # Create a dummy media directory for testing
    dummy_media_path = Path("temp_media_library_test")
    dummy_media_path.mkdir(exist_ok=True)
    (dummy_media_path / "video1.mp4").touch()
    (dummy_media_path / "audio1.mp3").touch()
    (dummy_media_path / "image1.jpg").touch()

    library = MediaLibrary(dummy_media_path)
    library.scan_media()
    print("All media:", library.get_all_media())
    print("Search 'video':", library.search_media("video"))

    import shutil
    shutil.rmtree(dummy_media_path)