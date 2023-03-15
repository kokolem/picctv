import json
from pathlib import Path

from picamera2.encoders import Quality
from pydantic import BaseSettings


def load_config_json():
    return json.loads(Path("camera_config.json").read_text())


class Config(BaseSettings):
    receiver_public_key_hex: str
    camera_private_key_hex: str
    video_height: int
    video_width: int
    video_quality: Quality
    server_address: str


config = Config(**load_config_json())
