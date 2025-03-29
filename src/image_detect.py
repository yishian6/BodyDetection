import cv2
from ultralytics import YOLO
from config import ROOT, DETECT_FOLDER
from pathlib import Path
import time


def detect_and_draw(
        image_path: str,
        model_path: str = "yolo11n.pt",
        save_folder: Path = Path(DETECT_FOLDER),
) -> tuple[str, float]:
    """检测并绘制边界框

    Args:
        image_path (str): 输入图像路径
        model_path (str): 模型路径
        save_folder (Path): 输出目录

    Raises:
        ValueError: 无法读取图像文件

    Returns:
        str: 输出图像路径
        float: 检测耗时
    """
    start = time.time()
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("无法读取图像文件")

    model = YOLO(model_path)
    # 对两个图像进行目标检测
    results = model(image, conf=0.5, classes=[0])[0]
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
    filename = Path(image_path).name
    save_folder.mkdir(parents=True, exist_ok=True)  # 创建输出目录
    output_path = str(save_folder / filename)
    cv2.imwrite(output_path, annotated)

    end = time.time()

    return output_path, end - start


if __name__ == "__main__":
    image_path = Path(ROOT) / "data" / "ir_align.png"
    tr_image_path = Path(ROOT) / "data" / "tr_align.png"

    detector = detect_and_draw(
        str(image_path), model_path="yolo11n.pt", save_folder=Path(ROOT) / "results"
    )
    print(f"检测结果保存在 {detector[0]}")
    print(f"检测耗时: {detector[1]}")
