"""
Camera controller for the marshmallow toasting system.
"""
import time
import threading
from typing import Optional, Callable
import numpy as np
from picamera2 import Picamera2

from core.config import CAMERA_SIZE, CAMERA_FORMAT, CAMERA_SETTLE_TIME, UI_FPS
from core.state_manager import state_manager


class CameraController:
    """Controls the camera and provides frame capture capabilities."""
    
    def __init__(self):
        self.camera: Optional[Picamera2] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._capture_stop_event = threading.Event()
        self._frame_callbacks = []
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
    
    def initialize(self) -> None:
        """Initialize the camera."""
        state_manager.log("Starting camera...")
        
        self.camera = Picamera2()
        self.camera.configure(
            self.camera.create_video_configuration(
                main={"size": CAMERA_SIZE, "format": CAMERA_FORMAT},
                raw=None
            )
        )
        self.camera.start()
        time.sleep(CAMERA_SETTLE_TIME)  # Let auto-exposure settle
        
        state_manager.log("Camera initialized")
    
    def start_capture_loop(self) -> None:
        """Start the background frame capture loop."""
        if self._capture_thread is not None and self._capture_thread.is_alive():
            return

        self._capture_stop_event.clear()
        
        self._capture_thread = threading.Thread(
            target=self._capture_loop, 
            daemon=True,
            name="CameraCapture"
        )
        self._capture_thread.start()
        state_manager.log("Camera capture loop started")
    
    def _capture_loop(self) -> None:
        """Background thread for continuous frame capture."""
        frame_interval = 1.0 / UI_FPS
        
        while not self._capture_stop_event.is_set():
            try:
                if self.camera is None:
                    time.sleep(0.1)
                    continue
                
                frame = self.camera.capture_array("main")
                
                # Convert BGR to RGB if needed (Picamera2 might output BGR)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Convert BGR to RGB
                    frame_rgb = frame[:, :, [2, 1, 0]]  # Swap B and R channels
                else:
                    frame_rgb = frame
                
                # Store latest frame in RGB format
                with self._frame_lock:
                    self._latest_frame = frame_rgb.copy()
                
                # Call all registered callbacks with RGB frame
                for callback in self._frame_callbacks:
                    try:
                        callback(frame_rgb)
                    except Exception as e:
                        state_manager.log(f"Frame callback error: {e}")
                
            except Exception as e:
                state_manager.log(f"Camera capture error: {e}")
            
            time.sleep(frame_interval)
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame directly."""
        if self.camera is None:
            return None
        
        try:
            frame = self.camera.capture_array("main")
            # Convert BGR to RGB if needed
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                # Convert BGR to RGB
                frame_rgb = frame[:, :, [2, 1, 0]]  # Swap B and R channels
                return frame_rgb
            return frame
        except Exception as e:
            state_manager.log(f"Frame capture error: {e}")
            return None
    
    def add_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Add a callback function to be called with each new frame."""
        self._frame_callbacks.append(callback)
    
    def remove_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Remove a frame callback."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)
    
    def shutdown(self) -> None:
        """Safely shutdown the camera."""
        self._capture_stop_event.set()

        if self._capture_thread is not None and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1.0)
        self._capture_thread = None

        if self.camera is None:
            return
        
        try:
            self.camera.stop()
        except Exception:
            pass
        
        try:
            self.camera.close()
        except Exception:
            pass
        
        self.camera = None
        state_manager.log("Camera shutdown complete")