"""
Servo motor controller for the marshmallow toasting system.
"""
import time
from typing import Optional

from servo import PCA9685
from core.config import (
    SWING_REVERSED, SWING_SPEED_DPS, HOME_ANGLE, FIRE_ANGLE,
    ROTATE_CHANNEL, SWING_CHANNEL
)
from core.state_manager import state_manager


class ServoController:
    """Controls both rotation and swing servos for the toasting system."""
    
    def __init__(self):
        self.pca: Optional[PCA9685] = None
        self._current_swing_angle = HOME_ANGLE
    
    def initialize(self) -> None:
        """Initialize the servo controller."""
        state_manager.log("Initializing servo controller...")
        self.pca = PCA9685(servo_mode=180)
        
        # Set initial positions
        self.set_swing_angle(HOME_ANGLE)
        self.set_rotation_speed(0)
        time.sleep(0.3)
        
        state_manager.log("Servo controller initialized")
    
    def _to_physical_angle(self, angle: float) -> float:
        """Convert logical angle to physical angle considering hardware direction."""
        angle = max(0, min(180, angle))
        if SWING_REVERSED:
            return 180 - angle
        return angle
    
    def set_swing_angle(self, angle: float) -> None:
        """Set the swing servo to a specific angle."""
        if self.pca is None:
            raise RuntimeError("Servo controller not initialized")
        
        physical_angle = self._to_physical_angle(angle)
        self.pca._set_angle(SWING_CHANNEL, physical_angle)
        self._current_swing_angle = angle
    
    def set_rotation_speed(self, speed: int) -> None:
        """Set the rotation servo speed (0-100)."""
        if self.pca is None:
            raise RuntimeError("Servo controller not initialized")
        
        self.pca._set_speed(ROTATE_CHANNEL, speed)
    
    def smooth_swing(self, start_angle: float, end_angle: float) -> None:
        """Move swing servo smoothly from start to end angle."""
        if self.pca is None:
            raise RuntimeError("Servo controller not initialized")
        
        start_angle = max(0, min(180, int(start_angle)))
        end_angle = max(0, min(180, int(end_angle)))
        delta = end_angle - start_angle
        
        if delta == 0:
            self.set_swing_angle(end_angle)
            return
        
        step_direction = 1 if delta > 0 else -1
        total_steps = abs(delta)
        step_delay = 1.0 / max(SWING_SPEED_DPS, 1)
        
        for offset in range(total_steps + 1):
            angle = start_angle + offset * step_direction
            self.set_swing_angle(angle)
            time.sleep(step_delay)
        
        self._current_swing_angle = end_angle
    
    def move_to_fire_position(self) -> None:
        """Move marshmallow to fire position."""
        state_manager.log(f"Moving swing servo: {HOME_ANGLE}° to {FIRE_ANGLE}°")
        self.smooth_swing(self._current_swing_angle, FIRE_ANGLE)
    
    def return_to_home(self) -> None:
        """Return marshmallow to home position."""
        state_manager.log(f"Returning swing servo: {FIRE_ANGLE}° to {HOME_ANGLE}°")
        self.smooth_swing(self._current_swing_angle, HOME_ANGLE)
    
    def stop_rotation(self) -> None:
        """Stop the rotation servo."""
        self.set_rotation_speed(0)
    
    def shutdown(self) -> None:
        """Safely shutdown servos."""
        if self.pca is None:
            return
        
        try:
            self.stop_rotation()
        except Exception:
            pass
        
        try:
            self.return_to_home()
        except Exception:
            pass