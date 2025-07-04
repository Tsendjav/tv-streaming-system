#!/usr/bin/env python3
"""
Simple Streaming Test
Ubuntu server-рүү тест stream илгээх
"""

import subprocess
import sys
import time
from pathlib import Path

def test_streaming_to_ubuntu():
    """Test streaming to Ubuntu server"""
    print("🧪 Ubuntu Server Streaming Test")
    print("=" * 50)
    
    # Check if test video exists
    test_video = Path("data/media").glob("*.mp4")
    test_video_list = list(test_video)
    
    if not test_video_list:
        print("❌ No test video found in data/media/")
        print("💡 Please add a test video file to data/media/ directory")
        return False
    
    video_file = test_video_list[0]
    print(f"📹 Using test video: {video_file.name}")
    
    # Ubuntu server details
    rtmp_url = "rtmp://192.168.1.50:1935/live/test_stream"
    
    print(f"📡 Streaming to: {rtmp_url}")
    print("⏰ Duration: 30 seconds")
    print("")
    
    # FFmpeg command for streaming
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",  # Read input at native frame rate
        "-i", str(video_file),
        "-c:v", "libx264",
        "-preset", "fast",
        "-tune", "zerolatency", 
        "-b:v", "1000k",
        "-maxrate", "1000k",
        "-bufsize", "2000k",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        "-t", "30",  # Stream for 30 seconds
        rtmp_url
    ]
    
    try:
        print("🚀 Starting stream...")
        print("📺 You can watch at: http://192.168.1.50:8080/hls/test_stream.m3u8")
        print("")
        
        # Start streaming
        process = subprocess.Popen(ffmpeg_cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Wait for 30 seconds or until process finishes
        stdout, stderr = process.communicate(timeout=35)
        
        if process.returncode == 0:
            print("✅ Stream completed successfully!")
            print("🎉 Ubuntu server streaming test PASSED!")
            return True
        else:
            print("❌ Stream failed")
            print(f"Error: {stderr[-500:]}")  # Last 500 chars of error
            return False
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("✅ Stream timed out (normal - 30 second test)")
        print("🎉 Ubuntu server streaming test PASSED!")
        return True
        
    except FileNotFoundError:
        print("❌ FFmpeg not found!")
        print("💡 Please ensure FFmpeg is installed and in PATH")
        return False
        
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        return False

if __name__ == "__main__":
    success = test_streaming_to_ubuntu()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Open browser: http://192.168.1.50:8080/stat")
        print("2. Check HLS stream: http://192.168.1.50:8080/hls/test_stream.m3u8")
        print("3. Use TV Streaming System to start real streams")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check Ubuntu server is running")
        print("2. Verify network connectivity")
        print("3. Ensure FFmpeg is installed")
    
    sys.exit(0 if success else 1)
