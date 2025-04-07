import logging
from os.path import dirname, abspath, join
from typing import Optional


import os
from os.path import exists

ROOT = dirname(dirname(abspath(__file__)))
SRC_FOLDER = join(ROOT, "src")
MODEL_FOLDER = join(ROOT, "model")
UPLOAD_FOLDER = join(ROOT, "upload")
IMAGE_FOLDER = join(UPLOAD_FOLDER, "images")
VIDEO_FOLDER = join(UPLOAD_FOLDER, "videos")
DEHAZE_FOLDER = join(UPLOAD_FOLDER, "dehazed")
DETECT_FOLDER = join(UPLOAD_FOLDER, "detected")
MERGE_FOLDER = join(UPLOAD_FOLDER, "merged")
YOLO_FOLDER = join(UPLOAD_FOLDER, "yolo")  # yolo模型文件夹
DATASET_FOLDER = join(UPLOAD_FOLDER, "dataset")  # 数据集文件夹
VAL_FOLDER = join(UPLOAD_FOLDER, "val")  # 验证集文件夹

# 默认模型路径
DEFAULT_MODEL_PATH = join(MODEL_FOLDER, "yolo11n.pt")

# 确保文件夹存在
for folder in [
    IMAGE_FOLDER,
    VIDEO_FOLDER,
    DEHAZE_FOLDER,
    DETECT_FOLDER,
    MERGE_FOLDER,
    YOLO_FOLDER,
    DATASET_FOLDER,
    MODEL_FOLDER,
    VAL_FOLDER,
]:
    if not exists(folder):
        os.makedirs(folder)

# 全局logger实例
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    获取单例logger实例

    Returns:
        logging.Logger: 配置好的logger实例
    """
    global _logger

    if _logger is None:
        # 创建logger实例
        _logger = logging.getLogger("BodyDetection")
        _logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if not _logger.handlers:
            # 创建格式化器
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            )

            # 创建并配置控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            _logger.addHandler(console_handler)

            # 可选：添加文件处理器
            file_handler = logging.FileHandler(join(ROOT, "app.log"))
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)

    return _logger


def get_model_path(model_name: Optional[str] = "yolo11n.pt") -> str:
    """
    获取模型路径

    Args:
        model_name: 模型名称，如果为None则使用默认模型

    Returns:
        str: 模型完整路径
    """
    logger = get_logger()

    # 如果未指定模型名称，使用默认模型
    if model_name is None:
        logger.info(f"使用默认模型: {DEFAULT_MODEL_PATH}")
        return DEFAULT_MODEL_PATH

    # 检查模型是否在MODEL_FOLDER中
    model_path = join(MODEL_FOLDER, model_name)
    if exists(model_path):
        logger.info(f"找到模型: {model_path}")
        return model_path

    # 检查模型是否在YOLO_FOLDER中
    yolo_model_path = join(YOLO_FOLDER, model_name)
    if exists(yolo_model_path):
        logger.info(f"找到模型: {yolo_model_path}")
        return yolo_model_path

    # 检查是否是绝对路径
    if os.path.isabs(model_name) and exists(model_name):
        logger.info(f"使用绝对路径模型: {model_name}")
        return model_name

    # 如果模型不存在，返回默认模型
    logger.warning(f"模型 {model_name} 不存在，使用默认模型: {DEFAULT_MODEL_PATH}")
    return DEFAULT_MODEL_PATH
