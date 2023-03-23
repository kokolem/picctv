import json
from pathlib import Path

from pydantic import BaseSettings


def load_config_json():
    return json.loads(Path("server_config.json").read_text())


class Config(BaseSettings):
    max_recording_file_size: int
    max_recording_files: int
    records_directory: str
    server_port: int
    camera_password_hash: bytes
    viewer_password_hash: bytes


config = Config(**load_config_json())
