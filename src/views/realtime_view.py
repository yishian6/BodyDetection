from flask import Response, Blueprint
from ultralytics import YOLO
import cv2

realtime_bp = Blueprint("realtime", __name__)
model = YOLO(r"yolo11n.pt")
camera = cv2.VideoCapture(r"data\output_ir.mp4")


def gen():
    while True:
        ret, frame = camera.read()
        frame = cv2.imencode(".jpg", frame)[1].tobytes()
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@realtime_bp.route("/realtime", methods=["GET"])
def video_feed():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")
