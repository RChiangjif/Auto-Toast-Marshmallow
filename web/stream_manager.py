"""
Video stream management for the web interface.
"""
import time
import threading
from typing import Dict, Optional
from PIL import Image

from vision.image_processor import encode_jpeg
from core.state_manager import state_manager


class StreamManager:
    """Manages video streams for the web interface."""
    
    def __init__(self):
        self._streams: Dict[str, Optional[bytes]] = {
            "raw": None,
            "processed": None,
            "yolo": None
        }
        self._lock = threading.Lock()
    
    def update_stream(self, name: str, image: Image.Image) -> None:
        """Update a video stream with a new frame."""
        if name not in self._streams:
            return
        
        try:
            jpeg_data = encode_jpeg(image)
            with self._lock:
                self._streams[name] = jpeg_data
        except Exception as e:
            state_manager.log(f"Stream update error for {name}: {e}")
    
    def get_stream_frame(self, name: str) -> Optional[bytes]:
        """Get the latest frame for a stream."""
        with self._lock:
            return self._streams.get(name)
    
    def get_available_streams(self) -> list:
        """Get list of available stream names."""
        return list(self._streams.keys())


# Global stream manager instance
stream_manager = StreamManager()