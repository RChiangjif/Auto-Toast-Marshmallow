"""
Main toasting controller that orchestrates the entire marshmallow toasting process.
"""
import time
import threading
from typing import Optional
import numpy as np
from PIL import Image

from core.config import (
    BASE_SPEED, MAX_SPEED, DONE_THRESHOLD, DONE_STREAK, CHECK_INTERVAL
)
from core.state_manager import state_manager
from hardware.servo_controller import ServoController
from hardware.camera_controller import CameraController
from vision.toast_detector import ToastDetector
from vision.image_processor import draw_overlay, create_heatmap
from web.stream_manager import stream_manager


class ToastingController:
    """Main controller that coordinates the toasting process."""
    
    def __init__(self):
        self.servo_controller = ServoController()
        self.camera_controller = CameraController()
        self.toast_detector = ToastDetector()
        
        # Runtime state
        self._current_speed = 0
        self._streak_count = 0
        self._systems_ready = False
        
        # Initialize systems immediately for live preview
        self.initialize_preview_systems()
        
    def initialize_servo_for_toasting(self) -> bool:
        """Initialize servo system for toasting process."""
        try:
            # Initialize servo controller
            self.servo_controller.initialize()
            state_manager.log("Servo system ready for toasting")
            return True
            
        except Exception as exc:
            state_manager.log(f"Servo initialization failed: {exc}")
            state_manager.update_state(phase="error", message=str(exc))
            return False
    
    def run_toasting_process(self) -> None:
        """Run the complete toasting process."""
        try:
            # Ensure preview systems are ready
            self.initialize_preview_systems()
            
            # Initialize servo for toasting
            if not self.initialize_servo_for_toasting():
                return
            
            # Step 1: Move to fire position
            self._move_to_fire_position()
            if state_manager.get_stop_event().is_set():
                return
            
            # Step 2: Capture reference frame
            self._capture_reference_frame()
            if state_manager.get_stop_event().is_set():
                return
            
            # Step 3: Start rotation
            self._start_rotation()
            if state_manager.get_stop_event().is_set():
                return
            
            # Step 4-5: Monitor and adjust until done
            self._monitor_toasting_process()
            if state_manager.get_stop_event().is_set():
                state_manager.log("Stopped by user")
                return
            
            # Finish: Return to home
            self._finish_toasting()
            
        except Exception as exc:
            state_manager.log(f"Toasting process error: {exc}")
            state_manager.update_state(phase="error", message=str(exc))
        finally:
            self._shutdown_toasting_only()
    
    def _move_to_fire_position(self) -> None:
        """Step 1: Move marshmallow over fire."""
        state_manager.update_state(
            phase="positioning",
            message="Step 1 — Moving marshmallow over fire..."
        )
        
        self.servo_controller.move_to_fire_position()
        time.sleep(0.5)
    
    def _capture_reference_frame(self) -> None:
        """Step 2: Capture reference image for comparison."""
        state_manager.update_state(
            phase="calibrating", 
            message="Step 2 — Capturing reference image..."
        )
        
        time.sleep(0.5)  # Let position settle
        reference_frame = self.camera_controller.capture_frame()
        
        if reference_frame is not None:
            self.toast_detector.set_reference_frame(reference_frame)
            state_manager.log("Reference frame captured successfully")
        else:
            raise RuntimeError("Failed to capture reference frame")
    
    def _start_rotation(self) -> None:
        """Step 3: Start rotation at base speed."""
        state_manager.update_state(
            phase="toasting",
            message=f"Step 3 — Starting rotation at speed {BASE_SPEED}...",
            speed=BASE_SPEED
        )
        
        self.servo_controller.set_rotation_speed(BASE_SPEED)
        self._current_speed = BASE_SPEED
        state_manager.log(f"Rotation started at speed {BASE_SPEED}")
    
    def _monitor_toasting_process(self) -> None:
        """Steps 4-5: Monitor toast level and adjust speed dynamically."""
        self._streak_count = 0
        last_check_time = 0.0
        
        while not state_manager.get_stop_event().is_set():
            current_time = time.time()
            if current_time - last_check_time < CHECK_INTERVAL:
                time.sleep(0.03)
                continue
            
            last_check_time = current_time
            
            # Capture current frame and analyze
            current_frame = self.camera_controller.capture_frame()
            if current_frame is None:
                continue
            
            # Get toast score using integrated YOLO + color analysis
            toast_score, detection_info = self.toast_detector.compute_toast_score(current_frame)
            
            # Auto mode: update speed based on toast score
            self._update_rotation_speed(toast_score)
            
            # Check doneness (always, regardless of mode)
            done_label = self._update_streak_count(toast_score)
            
            # Update status
            message = (f"Analyzing — score {toast_score:.1f}  "
                      f"speed {self._current_speed}  {done_label}  "
                      f"(streak {self._streak_count}/{DONE_STREAK})")
            
            if detection_info.get("roi_used", False):
                message += f" [{detection_info['method'].upper()}]"
            
            state_manager.update_state(
                toast_score=round(toast_score, 1),
                speed=self._current_speed,
                streak=self._streak_count,
                message=message
            )
            
            state_manager.log(message)
            
            # Check if done
            if self._streak_count >= DONE_STREAK:
                state_manager.log(f"Toasting complete! Final score: {toast_score:.1f}")
                break
    
    def _update_rotation_speed(self, toast_score: float) -> None:
        """Update rotation speed based on toast progress."""
        progress = min(toast_score / DONE_THRESHOLD, 1.0)
        new_speed = int(BASE_SPEED + (MAX_SPEED - BASE_SPEED) * progress)
        
        if new_speed != self._current_speed:
            self._current_speed = new_speed
            self.servo_controller.set_rotation_speed(self._current_speed)
    
    def _update_streak_count(self, toast_score: float) -> str:
        """Update streak count and return doneness label."""
        if toast_score >= DONE_THRESHOLD:
            self._streak_count += 1
            return "DONE"
        elif toast_score >= DONE_THRESHOLD * 0.70:
            self._streak_count = 0
            return "almost there"
        elif toast_score >= DONE_THRESHOLD * 0.40:
            self._streak_count = 0
            return "warming up"
        else:
            self._streak_count = 0
            return "raw"
    
    def _finish_toasting(self) -> None:
        """Finish toasting process and return home."""
        state_manager.update_state(
            phase="done",
            message="Done! Pulling marshmallow from fire...",
            speed=0
        )
        
        # Stop rotation
        self.servo_controller.stop_rotation()
        time.sleep(0.3)
        
        # Return to home position
        self.servo_controller.return_to_home()
        time.sleep(0.4)
        
        state_manager.update_state(
            phase="done",
            message="Your marshmallow is ready! Enjoy~"
        )
        state_manager.log("Toasting process completed successfully!")
    
    def _process_frame_for_display(self, frame: np.ndarray) -> None:
        """Process frames for web display streams."""
        try:
            current_state = state_manager.get_state()
            
            # Ensure frame is in RGB format (picamera2 gives us RGB)
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            # Raw view with overlay
            raw_image = Image.fromarray(frame)
            draw_overlay(
                raw_image,
                view_name="RAW",
                phase=current_state["phase"],
                toast_score=current_state["toast_score"],
                speed=current_state["speed"]
            )
            stream_manager.update_stream("raw", raw_image)
            
            # Processed view (heatmap) with overlay
            if self.toast_detector.reference_frame is not None:
                heatmap = create_heatmap(self.toast_detector.reference_frame, frame)
                draw_overlay(
                    heatmap,
                    view_name="PROCESSED",
                    phase=current_state["phase"],
                    toast_score=current_state["toast_score"],
                    speed=current_state["speed"]
                )
                stream_manager.update_stream("processed", heatmap)
            else:
                # No reference yet, show raw with different label
                processed_image = Image.fromarray(frame)
                draw_overlay(
                    processed_image,
                    view_name="PROCESSED",
                    phase=current_state["phase"],
                    toast_score=current_state["toast_score"],
                    speed=current_state["speed"]
                )
                stream_manager.update_stream("processed", processed_image)
            
            # YOLO view with detections (this should show the boxes)
            yolo_image = self.toast_detector.render_detection_overlay(frame)
            draw_overlay(
                yolo_image,
                view_name="YOLO",
                phase=current_state["phase"],
                toast_score=current_state["toast_score"],
                speed=current_state["speed"]
            )
            stream_manager.update_stream("yolo", yolo_image)
            
        except Exception as e:
            state_manager.log(f"Display processing error: {e}")
    
    def initialize_preview_systems(self) -> None:
        """Initialize camera and YOLO for live preview without servo control."""
        if self._systems_ready:
            return
            
        try:
            # Initialize camera for preview
            self.camera_controller.initialize()
            
            # Initialize YOLO detection
            yolo_available = self.toast_detector.initialize()
            if yolo_available:
                state_manager.log("YOLO detection ready for live preview")
            else:
                state_manager.log("YOLO detection disabled, using full-frame preview")
            
            # Start camera capture and live streaming
            self.camera_controller.add_frame_callback(self._process_frame_for_display)
            self.camera_controller.start_capture_loop()
            
            self._systems_ready = True
            state_manager.log("Preview systems ready - live video and YOLO detection active")
            
        except Exception as exc:
            state_manager.log(f"Preview system initialization failed: {exc}")
    
    def _shutdown_toasting_only(self) -> None:
        """Shutdown only toasting-related resources, keep preview active."""
        try:
            if hasattr(self.servo_controller, 'pca') and self.servo_controller.pca:
                self.servo_controller.shutdown()
        except Exception:
            pass
        
        # Keep camera and YOLO running for preview
        state_manager.log("Toasting systems shutdown, preview remains active")
    
    def _shutdown(self) -> None:
        """Clean up all resources completely."""
        state_manager.log("Shutting down all systems...")
        
        try:
            self.servo_controller.shutdown()
        except Exception:
            pass
        
        try:
            self.camera_controller.shutdown()
        except Exception:
            pass
        
        self._systems_ready = False
        state_manager.log("Complete shutdown finished")