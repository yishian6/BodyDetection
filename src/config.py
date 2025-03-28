import logging
from os.path import dirname, abspath, join

ROOT = dirname(dirname(abspath(__file__)))
SRC_FOLDER = join(ROOT, "src")
MODEL_FOLDER = join(ROOT, "model")
UPLOAD_FOLDER = join(ROOT, "upload")
IMAGE_FOLDER = join(UPLOAD_FOLDER, "images")
VIDEO_FOLDER = join(UPLOAD_FOLDER, "videos")
DEHAZE_FOLDER = join(UPLOAD_FOLDER, "dehazed")
DETECT_FOLDER = join(UPLOAD_FOLDER, "detected")
MERGE_FOLDER = join(UPLOAD_FOLDER, "merged")



def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
