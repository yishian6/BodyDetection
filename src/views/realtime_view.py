import os
from flask import Response, Blueprint, request
from src.MultiModalVideoDetector import MultiModalVideoDetector
from src.config import ROOT

realtime_bp = Blueprint("realtime", __name__, url_prefix="/")


@realtime_bp.route("/realtime", methods=["GET"])
def video_feed():
    """实时双模态视频流接口"""

    # IR视频参数
    ir_params = {
        "video_path": os.path.join(ROOT, "data", "output_ir.mp4"),
        "start_frame": int(138.8 * 25),
        "crop_params": (100, 0, int(640 * 2.5), int(512 * 2.5)),
        "resolution": (640, 512),
    }

    # TR视频参数
    tr_params = {
        "video_path": os.path.join(ROOT, "data", "output_tr.mp4"),
        "start_frame": 170 * 25,
        "crop_params": (0, 60, int(640 * 0.95), int(512 * 0.95)),
        "resolution": (640, 512),
    }

    # 创建检测器
    detector = MultiModalVideoDetector(
        ir_params=ir_params,
        tr_params=tr_params,
        model_path=os.path.join(ROOT, "model", "yolo11n_merge_tr.pt"),  # YOLO模型路径
        output_path="output_detection.mp4",
        conf_thres=0.6,
        show_preview=True,
    )

    return Response(
        detector.gen(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )
