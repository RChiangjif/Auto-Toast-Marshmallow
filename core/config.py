"""
Configuration constants for the auto-toast marshmallow system.
"""
import os

# ─── Hardware Configuration ──────────────────────────────────────────────────
ROTATE_CHANNEL  = 0       # 360° continuous servo channel
SWING_CHANNEL   = 1       # 180° servo channel
HOME_ANGLE      = 70      # logical rest position  (marshmallow away from fire)
FIRE_ANGLE      = 0       # logical roasting position  (over fire)
SWING_REVERSED  = False   # keep physical direction aligned with logical angles
SWING_SPEED_DPS = 120      # 180° servo speed in degrees per second

# ─── Toasting Algorithm Parameters ───────────────────────────────────────────
BASE_SPEED      = 8       # rotation speed when raw        (1-100)
MAX_SPEED       = 40      # rotation speed when nearly done (1-100)
DONE_THRESHOLD  = 18.0    # toast score that means "done"  (0-100)
DONE_STREAK     = 5       # consecutive detections required before acting
CHECK_INTERVAL  = 0.40    # seconds between analysis frames
SCORE_SCALE     = 4.0     # sensitivity multiplier  (raise if not detecting)

# ─── YOLO Configuration ──────────────────────────────────────────────────────
MODEL_PATH      = os.getenv("YOLO_MODEL_PATH", "model_ncnn_model")
YOLO_CONFIDENCE = 0.1     # General detection confidence threshold
YOLO_MARSHMALLOW_CONFIDENCE = 0.85  # High confidence threshold for marshmallow detection
YOLO_INTERVAL   = 0.3     # Faster YOLO updates for better responsiveness 
USE_YOLO_ROI    = True    # use YOLO to focus toast analysis on detected regions

# ─── Camera Configuration ─────────────────────────────────────────────────────
CAMERA_SIZE     = (1280, 720)
CAMERA_FORMAT   = "RGB888"
CAMERA_SETTLE_TIME = 1.5  # seconds to let auto-exposure settle

# ─── UI Configuration ─────────────────────────────────────────────────────────
JPEG_QUALITY    = 80      # JPEG compression quality for video streams
UI_FPS          = 25      # target FPS for video streams
LOG_MAX_LINES   = 300     # maximum log lines to keep in memory
STATUS_POLL_INTERVAL = 500  # milliseconds between status updates

# ─── Server Configuration ─────────────────────────────────────────────────────
DEFAULT_PORT    = 8000