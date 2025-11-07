from functools import lru_cache
from typing import List


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 允许哪些前端地址访问
    cors_origins: List[str] = ["*"]

    # 厂商中间件的 HTTP 基地址
    vendor_base_url: str = "http://127.0.0.1:27101"

    # 视频流配置文件路径
    video_streams_file: str = "../video-service/video_service.yaml"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> "Settings":
    """Return singleton settings instance."""
    return Settings()


# 供其它模块直接使用的全局实例
settings = get_settings()
