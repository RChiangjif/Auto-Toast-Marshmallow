"""
PCA9685 PWM servo controller for Raspberry Pi.

Supports:
- 180° angle servos (0-180 degrees)
- 360° continuous rotation servos (-100 to +100 speed)
"""

import smbus2
import time


class PCA9685:
    """PWM controller for servo motors using PCA9685."""

    def __init__(self, address=0x40, bus=1, servo_mode=180):
        """
        Initialize PCA9685 controller.
        
        Args:
            address: I2C address of PCA9685 (default 0x40)
            bus: I2C bus number (default 1 for Raspberry Pi)
            servo_mode: 180 for angle servos, 360 for continuous rotation
        """
        self.bus = smbus2.SMBus(bus)
        self.address = address
        self.servo_mode = servo_mode
        self.stop_tick = 334  # 360-mode stop point (can be calibrated)
        
        self.reset()
        self.set_freq(50)  # Standard 50Hz for servos

    def reset(self):
        """Reset the PCA9685."""
        self.bus.write_byte_data(self.address, 0x00, 0x00)

    def set_freq(self, freq_hz):
        """Set PWM frequency."""
        prescale = int(25_000_000 / (4096 * freq_hz) - 1)
        old_mode = self.bus.read_byte_data(self.address, 0x00)
        self.bus.write_byte_data(self.address, 0x00, (old_mode & 0x7F) | 0x10)
        self.bus.write_byte_data(self.address, 0xFE, prescale)
        self.bus.write_byte_data(self.address, 0x00, old_mode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, 0x00, old_mode | 0xA0)

    def set_pwm(self, channel, on, off):
        """Set PWM on/off values for a channel."""
        base = 0x06 + channel * 4
        self.bus.write_byte_data(self.address, base, on & 0xFF)
        self.bus.write_byte_data(self.address, base + 1, on >> 8)
        self.bus.write_byte_data(self.address, base + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, base + 3, off >> 8)

    def set_servo(self, channel, value):
        """
        Set servo value.
        
        For 180° mode: value is angle (0-180)
        For 360° mode: value is speed (-100 to +100, 0=stop)
        """
        if self.servo_mode == 180:
            self._set_angle(channel, value)
        elif self.servo_mode == 360:
            self._set_speed(channel, value)
        else:
            raise ValueError("servo_mode must be 180 or 360")

    def _set_angle(self, channel, angle):
        """Set servo angle (0-180 degrees)."""
        angle = max(0, min(180, angle))
        # Standard servo: 1ms → 0°, 1.5ms → 90°, 2ms → 180°
        # At 50Hz (20ms period), 4096 steps per period
        tick = int(205 + angle * 2.0)  # Approximate calibration
        tick = max(150, min(600, tick))  # Safety bounds
        self.set_pwm(channel, 0, tick)

    def _set_speed(self, channel, speed):
        """Set continuous rotation speed (-100 to +100, 0=stop)."""
        speed = max(-100, min(100, speed))
        if speed == 0:
            tick = self.stop_tick
        else:
            # Speed control: positive = clockwise, negative = counter-clockwise
            tick = self.stop_tick + int(speed * 1.6)  # Approximate calibration
        tick = max(200, min(450, tick))  # Safety bounds
        self.set_pwm(channel, 0, tick)

    def close(self):
        """Close I2C connection."""
        self.bus.close()
