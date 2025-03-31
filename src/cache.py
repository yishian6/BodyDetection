from typing import Dict, Optional, Any
import time
from src.config import get_logger

logger = get_logger()


class VideoCache:
    def __init__(self, max_size: int = 100, expiration: int = 3600):
        """
        初始化视频缓存系统

        Args:
            max_size (int): 最大缓存条目数
            expiration (int): 缓存过期时间(秒)
        """
        self.max_size = max_size
        self.expiration = expiration
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的视频处理结果

        Args:
            video_id (str): 视频ID

        Returns:
            Optional[Dict[str, Any]]: 缓存的结果或None
        """
        if video_id in self.cache:
            cache_data = self.cache[video_id]
            # 检查是否过期
            if time.time() - cache_data["timestamp"] <= self.expiration:
                logger.info(f"Cache hit for video: {video_id}")
                return cache_data["result"]
            else:
                # 删除过期缓存
                logger.info(f"Cache expired for video: {video_id}")
                del self.cache[video_id]
        return None

    def set(self, video_id: str, result: Dict[str, Any]) -> None:
        """
        缓存视频处理结果

        Args:
            video_id (str): 视频ID
            result (Dict[str, Any]): 处理结果
        """
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # 删除最旧的缓存
            oldest = min(self.cache.items(), key=lambda x: x[1]["timestamp"])
            del self.cache[oldest[0]]

        self.cache[video_id] = {"result": result, "timestamp": time.time()}
        logger.info(f"Cached result for video: {video_id}")

    def invalidate(self, video_id: str) -> None:
        """
        使指定视频的缓存失效

        Args:
            video_id (str): 视频ID
        """
        if video_id in self.cache:
            del self.cache[video_id]
            logger.info(f"Invalidated cache for video: {video_id}")

    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        logger.info("Cleared all cache")


# 创建全局缓存实例
video_cache = VideoCache()
