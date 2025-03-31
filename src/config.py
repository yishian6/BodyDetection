import logging
from os.path import dirname, abspath, join
from typing import Optional

ROOT = dirname(dirname(abspath(__file__)))
SRC_FOLDER = join(ROOT, "src")
MODEL_FOLDER = join(ROOT, "model")
UPLOAD_FOLDER = join(ROOT, "upload")
IMAGE_FOLDER = join(UPLOAD_FOLDER, "images")
VIDEO_FOLDER = join(UPLOAD_FOLDER, "videos")
DEHAZE_FOLDER = join(UPLOAD_FOLDER, "dehazed")
DETECT_FOLDER = join(UPLOAD_FOLDER, "detected")
MERGE_FOLDER = join(UPLOAD_FOLDER, "merged")

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
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
