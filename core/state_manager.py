"""
Centralized state management for the toast control system.
"""
import queue
import threading
import time
from typing import Dict, Any, Optional


class StateManager:
    """Thread-safe state manager for the toasting process."""
    
    def __init__(self):
        self._state = {
            "phase": "idle",
            "toast_score": 0.0,
            "speed": 0,
            "streak": 0,
            "message": "Ready. Press Start to begin.",
        }
        self._lock = threading.Lock()
        self._log_queue = queue.Queue(maxsize=300)
        self._stop_event = threading.Event()
    
    def get_state(self) -> Dict[str, Any]:
        """Get a copy of the current state."""
        with self._lock:
            return self._state.copy()
    
    def update_state(self, **kwargs) -> None:
        """Update state with the given key-value pairs."""
        with self._lock:
            self._state.update(kwargs)
    
    def get_stop_event(self) -> threading.Event:
        """Get the stop event for coordinating shutdown."""
        return self._stop_event
    
    def set_stop(self) -> None:
        """Signal all threads to stop."""
        self._stop_event.set()
    
    def clear_stop(self) -> None:
        """Clear the stop signal."""
        self._stop_event.clear()
    
    def log(self, message: str) -> None:
        """Add a timestamped log message."""
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        
        try:
            self._log_queue.put_nowait(line)
        except queue.Full:
            # Remove oldest log if queue is full
            try:
                self._log_queue.get_nowait()
            except queue.Empty:
                pass
            self._log_queue.put_nowait(line)
    
    def get_log_queue(self) -> queue.Queue:
        """Get the log queue for streaming to frontend."""
        return self._log_queue


# Global state manager instance
state_manager = StateManager()