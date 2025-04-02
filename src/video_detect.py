import cv2
from ultralytics import YOLO
from config import ROOT, DETECT_FOLDER
from pathlib import Path
import time


def detect_video(
    video_path: str,
    model_path: str = "yolo11n.pt",
    save_folder: Path = Path(DETECT_FOLDER),
) -> tuple[str, float]:
    """检测视频中的目标

    Args:
        video_path (str): 输入视频路径
        model_path (str): 模型路径
        save_folder (Path): 输出目录

    Raises:
        ValueError: 无法读取视频文件

    Returns:
        str: 输出视频路径
        float: 检测总耗时
        list: 检测结果列表，包含每帧的检测信息
    """
    start_time = time.time()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("无法读取视频文件")

    # 获取视频基本信息
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 创建输出视频写入器
    filename = Path(video_path).name.replace(".mp4", "_detected.mp4")
    save_folder.mkdir(parents=True, exist_ok=True)
    output_path = str(save_folder / filename)

    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # 加载模型
    model = YOLO(model_path)

    # 存储检测结果
    detection_results = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 获取当前帧的时间戳
        timestamp = frame_count / fps

        # 对当前帧进行目标检测
        results = model(frame, conf=0.5, classes=[0], verbose=False)[0]

        # 在帧上绘制检测框
        annotated_frame = frame.copy()
        frame_detections = []

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # 存储检测结果
            frame_detections.append(
                {"bbox": [x1, y1, x2, y2], "confidence": conf, "label": "Person"}
            )

            # 绘制边界框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 添加标签
            label = f"Person {conf:.2f}"
            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        # 将检测结果添加到列表中
        if frame_detections:
            detection_results.append(
                {"timestamp": timestamp, "detections": frame_detections}
            )

        # 写入处理后的帧
        out.write(annotated_frame)
        frame_count += 1

    # 释放资源
    cap.release()
    out.release()

    end_time = time.time()
    process_time = end_time - start_time

    return output_path, process_time


if __name__ == "__main__":
    video_path = Path(ROOT) / "data" / "output_ir.mp4"

    try:
        output_path, process_time, detections = detect_video(
            str(video_path), model_path="yolo11n.pt", save_folder=Path(ROOT) / "results"
        )
        print(f"处理后的视频保存在: {output_path}")
        print(f"总处理时间: {process_time:.2f}秒")
        print(f"检测到的目标数量: {len(detections)}")
    except Exception as e:
        print(f"处理失败: {str(e)}")
