"""
Toast detection system that integrates YOLO object detection with color-based analysis.
"""
import os
import time
import threading
import importlib
from typing import Optional, List, Tuple
import numpy as np
from PIL import Image, ImageDraw

from core.config import (
    MODEL_PATH, YOLO_CONFIDENCE, YOLO_MARSHMALLOW_CONFIDENCE, USE_YOLO_ROI, SCORE_SCALE,
    DONE_THRESHOLD, DONE_STREAK, CHECK_INTERVAL
)
from core.state_manager import state_manager
from vision.image_processor import extract_roi_from_boxes


try:
    YOLO = importlib.import_module("ultralytics").YOLO
except Exception:
    YOLO = None


class ToastDetector:
    """
    Advanced toast detection system that uses YOLO for region detection
    and color analysis for doneness assessment.
    """
    
    def __init__(self):
        self.yolo_model = None
        self.yolo_error = None
        self.reference_frame = None
        self.last_yolo_time = 0.0
        self._detection_lock = threading.Lock()
        
        # Detection statistics
        self.total_detections = 0
        self.yolo_detections = 0
        self.roi_detections = 0
        
    def initialize(self) -> bool:
        """Initialize the YOLO model if available."""
        if self.yolo_model is not None or self.yolo_error is not None:
            return self.yolo_model is not None
        
        state_manager.log(f"Initializing YOLO model from: {MODEL_PATH}")
        
        if YOLO is None:
            self.yolo_error = "ultralytics not installed"
            state_manager.log("YOLO disabled: ultralytics not installed")
            return False
        
        if not os.path.exists(MODEL_PATH):
            self.yolo_error = f"model not found: {MODEL_PATH}"
            state_manager.log(f"YOLO disabled: {self.yolo_error}")
            # List available files for debugging
            try:
                import glob
                available_files = glob.glob("model*")
                state_manager.log(f"Available model files: {available_files}")
            except:
                pass
            return False
        
        try:
            self.yolo_model = YOLO(MODEL_PATH, task="detect")
            state_manager.log(f"✅ YOLO model loaded successfully from {MODEL_PATH}")
            
            # Test detection capability
            import numpy as np
            test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            test_results = self.yolo_model.predict(source=test_frame, conf=0.1, verbose=False)
            state_manager.log(f"YOLO test prediction completed: {len(test_results)} results")
            
            return True
        except Exception as exc:
            self.yolo_error = str(exc)
            state_manager.log(f"YOLO initialization failed: {exc}")
            return False
    
    def set_reference_frame(self, frame: np.ndarray) -> None:
        """Set the reference frame for toast comparison."""
        self.reference_frame = frame.copy()
        state_manager.log("Reference frame captured for toast detection")
    
    def detect_objects(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[str], List[float]]:
        """
        Run YOLO detection on frame.
        
        Returns:
            boxes: List of bounding boxes as (x1, y1, x2, y2)
            classes: List of class names
            confidences: List of confidence scores
        """
        if self.yolo_model is None:
            return [], [], []
        
        self.total_detections += 1
        
        try:
            with self._detection_lock:
                # Frame should already be in RGB format from camera controller
                state_manager.log(f"Running YOLO detection #{self.total_detections} on frame shape: {frame.shape}")
                                
                results = self.yolo_model.predict(
                    source=frame, 
                    imgsz=640, 
                    conf=0.1,  # Very low confidence to catch more objects
                    verbose=False,
                    device='cpu'  # Force CPU for stability
                )
            
            boxes = []
            classes = []
            confidences = []
            
            state_manager.log(f"YOLO prediction returned {len(results) if results else 0} results")
            
            if results:
                result = results[0]
                yolo_boxes = getattr(result, "boxes", None)
                names = result.names if hasattr(result, "names") else {}
                
                state_manager.log(f"YOLO result has boxes: {yolo_boxes is not None}, names: {len(names)}")
                
                if yolo_boxes is not None and len(yolo_boxes) > 0:
                    state_manager.log(f"Processing {len(yolo_boxes)} detected boxes")
                    
                    for i, box in enumerate(yolo_boxes):
                        try:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            class_name = names.get(class_id, f"class_{class_id}")
                            
                            # Apply different confidence thresholds for different objects
                            min_confidence = YOLO_CONFIDENCE
                            if class_name.lower() in ['marshmallow', 'food', 'cake', 'donut']:
                                min_confidence = YOLO_MARSHMALLOW_CONFIDENCE
                                state_manager.log(f"Food item detected: {class_name} with confidence {confidence:.3f} (required: {min_confidence:.2f})")
                            
                            # Only include detections that meet the confidence threshold
                            if confidence >= min_confidence:
                                state_manager.log(f"✅ Box {i}: {class_name}({confidence:.2f}) at ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) - ACCEPTED")
                                
                                boxes.append((int(x1), int(y1), int(x2), int(y2)))
                                classes.append(class_name)
                                confidences.append(confidence)
                            else:
                                state_manager.log(f"❌ Box {i}: {class_name}({confidence:.2f}) - REJECTED (below {min_confidence:.2f})")
                                
                        except Exception as box_error:
                            state_manager.log(f"Error processing box {i}: {box_error}")
                else:
                    state_manager.log("No boxes found in YOLO result")
            
            if boxes:
                self.yolo_detections += 1
                state_manager.log(f"✅ Successfully detected {len(boxes)} objects (after confidence filtering): {classes}")
                
                # Special logging for marshmallow detections
                marshmallow_items = [c for c in classes if c.lower() in ['marshmallow', 'food', 'cake', 'donut']]
                if marshmallow_items:
                    state_manager.log(f"🍡 HIGH-CONFIDENCE FOOD ITEMS: {marshmallow_items}")
            else:
                state_manager.log("❌ No objects detected this frame (after confidence filtering)")
            
            return boxes, classes, confidences
            
        except Exception as exc:
            state_manager.log(f"❌ YOLO detection error: {exc}")
            import traceback
            state_manager.log(f"Traceback: {traceback.format_exc()}")
            return [], [], []
    
    def compute_toast_score(self, current_frame: np.ndarray, 
                           use_yolo_roi: bool = USE_YOLO_ROI) -> Tuple[float, dict]:
        """
        Compute toast doneness score, using YOLO to focus on the largest detected region.
        
        Returns:
            score: Toast score (0-100)
            info: Detection info dictionary
        """
        if self.reference_frame is None:
            return 0.0, {"error": "No reference frame set"}
        
        self.total_detections += 1
        detection_info = {
            "method": "full_frame",
            "roi_used": False,
            "detections": 0,
            "roi_coverage": 0.0,
            "selected_box": None
        }
        
        # Default to full frame analysis
        analysis_region = current_frame
        reference_region = self.reference_frame
        
        # Try YOLO detection first if enabled
        if use_yolo_roi and self.yolo_model is not None:
            boxes, classes, confidences = self.detect_objects(current_frame)
            
            if boxes:
                detection_info["detections"] = len(boxes)
                detection_info["classes"] = classes
                
                # Extract the LARGEST ROI for analysis
                target_classes = ["marshmallow", "food", "person", "cake", "donut", "pizza", "sandwich"]
                roi_result = extract_roi_from_boxes(
                    current_frame, boxes, classes, target_classes, confidences
                )
                
                if roi_result is not None:
                    roi, selected_box = roi_result
                    x1, y1, x2, y2 = selected_box
                    
                    # Also extract corresponding region from reference frame
                    ref_roi = self.reference_frame[y1:y2, x1:x2]
                    
                    analysis_region = roi
                    reference_region = ref_roi
                    detection_info["method"] = "yolo_roi_highest_conf"
                    detection_info["roi_used"] = True
                    detection_info["roi_coverage"] = (roi.size / current_frame.size) * 100
                    detection_info["selected_box"] = selected_box
                    self.roi_detections += 1
                    
                    # Find the confidence of the selected box
                    sel_idx = boxes.index(list(selected_box)) if list(selected_box) in [list(b) for b in boxes] else -1
                    sel_conf = confidences[sel_idx] if sel_idx >= 0 else 0.0
                    state_manager.log(f"Using HIGHEST CONF box ({x1},{y1})-({x2},{y2}) conf={sel_conf:.2f} for analysis")
        
        # Compute toast score on the selected regions
        score = self._compute_color_score(reference_region, analysis_region)
        
        detection_info["score"] = score
        detection_info["total_detections"] = self.total_detections
        detection_info["yolo_success_rate"] = (self.yolo_detections / max(1, self.total_detections)) * 100
        detection_info["roi_usage_rate"] = (self.roi_detections / max(1, self.total_detections)) * 100
        
        return score, detection_info
    
    def _compute_color_score(self, reference: np.ndarray, current: np.ndarray) -> float:
        """
        Core color-based toast scoring algorithm.
        
        Analyzes two physics-based signals:
        1. Darkening - surface darkens as it caramelizes  
        2. Browning - red-minus-blue channel grows (white to golden hue shift)
        """
        # Ensure both regions have the same dimensions for comparison
        if reference.shape != current.shape:
            # Resize current region to match reference if needed
            from PIL import Image
            cur_pil = Image.fromarray(current.astype(np.uint8))
            cur_pil = cur_pil.resize((reference.shape[1], reference.shape[0]))
            current = np.array(cur_pil).astype(np.float32)
        
        # Down-sample for processing efficiency
        ref_sample = reference[::2, ::2].astype(np.float32)
        cur_sample = current[::2, ::2].astype(np.float32)
        
        # Luma (brightness) calculation
        ref_luma = 0.299 * ref_sample[:, :, 0] + 0.587 * ref_sample[:, :, 1] + 0.114 * ref_sample[:, :, 2]
        cur_luma = 0.299 * cur_sample[:, :, 0] + 0.587 * cur_sample[:, :, 1] + 0.114 * cur_sample[:, :, 2]
        darkening = float(np.clip(ref_luma - cur_luma, 0, None).mean()) / 255.0
        
        # Red-minus-blue delta (browning/caramelization)
        ref_rb = ref_sample[:, :, 0] - ref_sample[:, :, 2]
        cur_rb = cur_sample[:, :, 0] - cur_sample[:, :, 2]
        browning = float(np.clip(cur_rb - ref_rb, 0, None).mean()) / 255.0
        
        # Weighted combination
        raw_score = darkening * 0.65 + browning * 0.35
        final_score = float(np.clip(raw_score * SCORE_SCALE * 100, 0, 100))
        
        return final_score
    
    def render_detection_overlay(self, frame: np.ndarray) -> Image.Image:
        """Create visualization with YOLO detections overlay."""
        # Frame should already be in RGB format from camera controller
        image = Image.fromarray(frame.astype(np.uint8))
        draw = ImageDraw.Draw(image)
        
        if self.yolo_model is None:
            status = self.yolo_error or "YOLO loading"
            draw.rectangle([12, 42, 350, 68], fill=(0, 0, 0, 200))
            draw.text((18, 48), f"YOLO: {status}", fill=(255, 120, 120))
            state_manager.log(f"YOLO not available: {status}")
        else:
            # Run detection and draw results
            boxes, classes, confidences = self.detect_objects(frame)
            
            # Always log detection attempts for debug
            state_manager.log(f"YOLO detection attempt: found {len(boxes)} objects")
            
            # Determine which box has the highest confidence for highlighting
            best_box = None
            best_conf = -1.0
            
            if boxes:
                for i, (box, conf) in enumerate(zip(boxes, confidences)):
                    if conf > best_conf:
                        best_conf = conf
                        best_box = box
            
            if boxes:
                state_manager.log(f"✅ Drawing {len(boxes)} detection boxes: {list(zip(classes, confidences))}")
                
                for i, (box, class_name, confidence) in enumerate(zip(boxes, classes, confidences)):
                    x1, y1, x2, y2 = box
                    label = f"{class_name} {confidence:.2f}"
                    
                    is_best = (box == best_box)
                    
                    state_manager.log(f"Drawing box: {label} at ({x1},{y1})-({x2},{y2}) {'[BEST CONF]' if is_best else ''}")
                    
                    # Use different colors and styles for different categories
                    if class_name.lower() in ['marshmallow', 'food', 'cake', 'donut']:
                        if is_best:
                            box_color = (255, 0, 255)  # Bright magenta for highest-conf food item
                            bg_color = (255, 0, 255)
                            line_width = 6  # Extra thick for the analysis target
                        else:
                            box_color = (200, 0, 200)  # Darker magenta for other food items
                            bg_color = (200, 0, 200)
                            line_width = 3
                    else:
                        if is_best:
                            box_color = (255, 100, 0)  # Orange for highest-conf other object
                            bg_color = (255, 100, 0)
                            line_width = 5
                        else:
                            box_color = (255, 0, 0)    # Red for other objects
                            bg_color = (255, 255, 0)   # Yellow background
                            line_width = 3
                    
                    # Draw bounding box with category and confidence-specific styling
                    draw.rectangle((x1, y1, x2, y2), outline=box_color, width=line_width)
                    
                    # Add "ANALYSIS" label to the highest confidence box
                    if is_best:
                        label += " [ANALYSIS]"
                    label_width, label_height = 100, 20
                
                draw.rectangle(
                    (x1, max(0, y1 - label_height - 4), x1 + label_width + 8, y1),
                    fill=bg_color  # Color-coded background
                )
                draw.text((x1 + 4, max(0, y1 - label_height - 2)), label, fill=(0, 0, 0))  # Black text
            
            # Add detection statistics with best confidence info
            best_info = ""
            if best_box:
                best_info = f" | Best: {best_conf:.2f}"
                
            marshmallow_count = len([c for c in classes if c.lower() in ['marshmallow', 'food', 'cake', 'donut']])
            stats_text = (f"Objects: {len(boxes)} | Food: {marshmallow_count}{best_info} | "
                         f"Total: {self.total_detections} | YOLO: {self.yolo_success_rate:.1f}%")
            draw.rectangle([12, 12, 600, 36], fill=(0, 0, 0, 220))  # Wider for more info
            draw.text((18, 18), stats_text, fill=(0, 255, 255))
            
            # Add confidence threshold info
            conf_text = f"General: {YOLO_CONFIDENCE:.1f} | Marshmallow: {YOLO_MARSHMALLOW_CONFIDENCE:.2f}"
            draw.rectangle([12, 40, 350, 64], fill=(0, 100, 0, 200))
            draw.text((18, 46), conf_text, fill=(255, 255, 255))
        
        return image
    
    @property
    def yolo_success_rate(self) -> float:
        """Get YOLO detection success rate as percentage."""
        return (self.yolo_detections / max(1, self.total_detections)) * 100
    
    @property
    def roi_usage_rate(self) -> float:
        """Get ROI usage rate as percentage."""
        return (self.roi_detections / max(1, self.total_detections)) * 100
    
    def get_detection_stats(self) -> dict:
        """Get comprehensive detection statistics."""
        return {
            "total_detections": self.total_detections,
            "yolo_detections": self.yolo_detections, 
            "roi_detections": self.roi_detections,
            "yolo_success_rate": self.yolo_success_rate,
            "roi_usage_rate": self.roi_usage_rate,
            "yolo_available": self.yolo_model is not None,
            "yolo_error": self.yolo_error
        }