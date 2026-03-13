"""
Image processing utilities for the toast detection system.
"""
import numpy as np
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw
from io import BytesIO

from core.config import JPEG_QUALITY


def encode_jpeg(image: Image.Image, quality: int = JPEG_QUALITY) -> bytes:
    """Encode PIL Image as JPEG bytes."""
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def create_heatmap(reference: np.ndarray, current: np.ndarray) -> Image.Image:
    """Create a heatmap visualization showing differences between frames."""
    if reference.shape != current.shape:
        raise ValueError("Reference and current frames must have the same shape")
    
    ref = reference.astype(np.int16)
    cur = current.astype(np.int16)
    delta = np.abs(cur - ref).mean(axis=2).astype(np.uint8)
    boosted = np.clip(delta * 4, 0, 255).astype(np.uint8)
    
    # Create heat colormap
    heat = np.zeros((boosted.shape[0], boosted.shape[1], 3), dtype=np.uint8)
    heat[:, :, 0] = np.clip(boosted * 2, 0, 255).astype(np.uint8)      # Red
    heat[:, :, 1] = np.clip(boosted * 0.8, 0, 255).astype(np.uint8)    # Green  
    heat[:, :, 2] = np.clip(255 - boosted, 0, 255).astype(np.uint8)    # Blue
    
    return Image.fromarray(heat)


def draw_overlay(image: Image.Image, 
                view_name: str = None,
                phase: str = "idle",
                toast_score: float = 0.0,
                speed: int = 0) -> None:
    """Draw overlay information on image."""
    draw = ImageDraw.Draw(image)
    W, H = image.size
    pct = min(toast_score / 100.0, 1.0)
    
    # Phase colors
    phase_colors = {
        "idle": (160, 160, 160),
        "starting": (120, 120, 255),
        "positioning": (100, 200, 255),
        "calibrating": (255, 220, 50),
        "toasting": (255, 140, 30),
        "done": (80, 255, 80),
        "error": (255, 60, 60),
    }
    phase_color = phase_colors.get(phase, (255, 255, 255))
    
    # Progress bar color
    if pct < 0.40:
        bar_color = (80, 220, 80)
    elif pct < 0.75:
        bar_color = (255, 200, 50)
    else:
        bar_color = (255, 80, 30)
    
    # View name (top-left)
    if view_name:
        draw.rectangle([6, 40, 126, 64], fill=(0, 0, 0, 160))
        draw.text((12, 46), view_name, fill=(180, 220, 255))
    
    # Phase label (top-left)
    draw.rectangle([6, 6, 200, 30], fill=(0, 0, 0, 160))
    draw.text((10, 9), f"PHASE: {phase.upper()}", fill=phase_color)
    
    # Score + speed (top-right)
    draw.rectangle([W - 210, 6, W - 6, 30], fill=(0, 0, 0, 160))
    draw.text((W - 206, 9), f"Score {toast_score:.1f}%  spd {speed}", fill=(255, 200, 100))
    
    # Bottom progress bar
    bx, by = 16, H - 38
    bw, bh = W - 32, 22
    fw = int(bw * pct)
    
    draw.rectangle([bx, by, bx + bw, by + bh], outline=(200, 200, 200), width=1)
    if fw > 0:
        draw.rectangle([bx, by, bx + fw, by + bh], fill=bar_color)
    
    label_color = (20, 20, 20) if pct > 0.08 else (200, 200, 200)
    draw.text((bx + 6, by + 3), f"Toast  {toast_score:.0f}%", fill=label_color)


def extract_roi_from_boxes(frame: np.ndarray, boxes: List[Tuple[int, int, int, int]], 
                          classes: List[str] = None, 
                          target_classes: List[str] = None,
                          confidences: List[float] = None) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Extract the HIGHEST CONFIDENCE region of interest from frame based on YOLO detection boxes.
    
    Args:
        frame: Input image frame
        boxes: List of bounding boxes as (x1, y1, x2, y2)
        classes: List of class names for each box
        target_classes: List of target class names to focus on (e.g., ["marshmallow"])
        confidences: List of confidence scores for each box
    
    Returns:
        Tuple of (ROI region as numpy array, (x1, y1, x2, y2) of selected box) or None
    """
    if not boxes:
        return None
    
    # Filter boxes by target classes if specified, carry confidence along
    valid_entries = []
    if target_classes and classes:
        for i, (box, cls) in enumerate(zip(boxes, classes)):
            if cls.lower() in [tc.lower() for tc in target_classes]:
                conf = confidences[i] if confidences else 0.0
                valid_entries.append((box, cls, conf))
    else:
        for i, box in enumerate(boxes):
            conf = confidences[i] if confidences else 0.0
            valid_entries.append((box, "unknown", conf))
    
    if not valid_entries:
        return None
    
    # Find the box with the highest confidence
    best_box = None
    best_conf = -1.0
    
    for box, cls, conf in valid_entries:
        if conf > best_conf:
            best_conf = conf
            best_box = box
    
    if best_box is None:
        return None
    
    # Extract ROI from the highest confidence box
    x1, y1, x2, y2 = best_box
    
    # Ensure coordinates are within frame bounds
    h, w = frame.shape[:2]
    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(w, int(x2))
    y2 = min(h, int(y2))
    
    # Extract ROI
    if x2 > x1 and y2 > y1:
        roi = frame[y1:y2, x1:x2]
        return roi, (x1, y1, x2, y2)
    
    return None