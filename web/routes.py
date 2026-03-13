"""
Flask routes for the marshmallow toasting web interface.
"""
import time
import queue
import threading
from flask import Flask, Response, jsonify, stream_with_context

from core.state_manager import state_manager
from web.stream_manager import stream_manager
from web.templates import get_index_html


def create_routes(app: Flask, toasting_controller) -> None:
    """Register all routes with the Flask app."""
    
    @app.route("/")
    def index():
        return get_index_html()

    @app.route("/start", methods=["POST"])
    def route_start():
        current_state = state_manager.get_state()
        if current_state["phase"] not in ("idle", "done", "error"):
            return jsonify({"ok": False, "msg": "Already running"})
        
        # Clear stop event and start toasting
        state_manager.clear_stop()
        state_manager.update_state(
            phase="starting",
            message="Starting...",
            toast_score=0.0,
            speed=0,
            streak=0
        )
        
        # Start toasting in background thread
        threading.Thread(
            target=toasting_controller.run_toasting_process,
            daemon=True,
            name="ToastingController"
        ).start()
        
        return jsonify({"ok": True})
    
    @app.route("/stop", methods=["POST"])
    def route_stop():
        state_manager.set_stop()
        state_manager.update_state(
            phase="idle",
            message="Stopped by user."
        )
        return jsonify({"ok": True})
    
    @app.route("/status")
    def route_status():
        return jsonify(state_manager.get_state())
    
    @app.route("/stream.mjpg")
    def route_stream():
        return route_stream_view("raw")
    
    @app.route("/stream/<view_name>.mjpg")
    def route_stream_view(view_name):
        if view_name not in stream_manager.get_available_streams():
            return Response("Unknown view", status=404)
        
        def generate():
            while True:
                frame = stream_manager.get_stream_frame(view_name)
                if frame:
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
                time.sleep(0.04)  # ~25 FPS
        
        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )
    
    @app.route("/events")
    def route_events():
        """Server-sent events endpoint for real-time logs."""
        def generate():
            log_queue = state_manager.get_log_queue()
            while True:
                try:
                    line = log_queue.get(timeout=15)
                    yield f"data: {line}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    
    @app.route("/api/detection-stats")
    def route_detection_stats():
        """Get detection statistics from the toast detector."""
        if hasattr(toasting_controller, 'toast_detector'):
            stats = toasting_controller.toast_detector.get_detection_stats()
            return jsonify(stats)
        return jsonify({"error": "Detection system not available"})
