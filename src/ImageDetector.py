import cv2
from ultralytics import YOLO
from config import ROOT
from pathlib import Path


class ImageDetector:
    def __init__(self, image_path: str, model_path="yolo11n.pt"):
        self.image_path = image_path
        self.model = YOLO(model_path)

    def detect_and_draw(self):
        # 读取红外和可见光图像
        image = cv2.imread(self.image_path)

        if image is None:
            raise ValueError("无法读取图像文件")

        # 对两个图像进行目标检测
        results = self.model(image)[0]
        # 在红外图像上绘制检测框
        annotated = image.copy()
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # 绘制边界框
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # 添加标签
            label = f"Person {conf:.2f}"
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        output_dir = Path(ROOT) / "results"
        output_dir.mkdir(parents=True, exist_ok=True)  # 创建输出目录
        output_path = str(output_dir / "detection_result.jpg")
        cv2.imwrite(output_path, annotated)

        return output_path


if __name__ == "__main__":
    image_path = Path(ROOT) / "data" / "ir_align.png"
    tr_image_path = Path(ROOT) / "data" / "tr_align.png"

    detector = ImageDetector(image_path, "yolo11n.pt")
    print(detector.detect_and_draw())
