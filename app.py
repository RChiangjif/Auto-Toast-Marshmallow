"""
Auto-Toast Marshmallow — Modular Flask Application

Refactored version with:
- Hardware control modules (servo, camera)
- Vision processing with integrated YOLO + color analysis  
- Centralized state management
- Clean web interface separation
"""

import os
from flask import Flask

from core.config import DEFAULT_PORT
from core.state_manager import state_manager
from toasting_controller import ToastingController
from web.routes import create_routes

app = Flask(__name__)

# Initialize the main toasting controller
toasting_controller = ToastingController()

# Register all routes
create_routes(app, toasting_controller)
if __name__ == "__main__":
    port = int(os.getenv("PORT", DEFAULT_PORT))
    state_manager.log(f"Starting Auto-Toast Marshmallow server on port {port}")
    
    # Initialize preview systems immediately
    state_manager.log("Initializing camera and YOLO for live preview...")
    toasting_controller.initialize_preview_systems()
    
    try:
        app.run(host="0.0.0.0", port=port, threaded=True)
    except KeyboardInterrupt:
        state_manager.log("Server stopped by user")
    except Exception as e:
        state_manager.log(f"Server error: {e}")
    finally:
        # Cleanup on exit
        state_manager.set_stop()
        toasting_controller._shutdown()
