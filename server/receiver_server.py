import asyncio
import datetime
import os.path
import pathlib

import websockets
from nacl import pwhash
from nacl.exceptions import InvalidkeyError

from config_parser import config


VIEWERS = set()


def get_new_output_file():
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.h264.enc"
    output_file = pathlib.Path(f"{config.records_directory}/{filename}")
    output_file.parent.mkdir(exist_ok=True, parents=True)
    return output_file.open("wb")


def delete_oldest_record_if_max_records_reached():
    records_dir = pathlib.Path(config.records_directory)
    records = list(records_dir.iterdir())
    while len(records) > config.max_recording_files:
        oldest_record = min(records, key=os.path.getmtime)
        oldest_record.unlink()
        records = list(records_dir.iterdir())


async def handle_camera_client(websocket):
    global VIEWERS

    current_file_size = 0
    current_file = get_new_output_file()
    delete_oldest_record_if_max_records_reached()

    async for frame in websocket:
        if current_file_size + len(frame) > config.max_recording_file_size:
            current_file.close()
            current_file = get_new_output_file()
            current_file_size = 0

            delete_oldest_record_if_max_records_reached()

        current_file.write(frame)
        current_file.write(b"--FRAME")
        current_file.flush()

        current_file_size += len(frame)

        websockets.broadcast(VIEWERS, frame)

    current_file.close()


async def handle_connection(websocket):
    client_auth = await websocket.recv()
    client_type, _, password = client_auth.partition(":")
    password = password.encode()

    if not password:
        await websocket.close()
        print("No password received")
        return

    if client_type == "camera":
        try:
            pwhash.verify(config.camera_password_hash, password)
        except InvalidkeyError:
            await websocket.close()
            print("Invalid camera password")
            return

        print("Camera connected")

        await handle_camera_client(websocket)

    elif client_type == "viewer":
        try:
            pwhash.verify(config.viewer_password_hash, password)
        except InvalidkeyError:
            await websocket.close()
            print("Invalid viewer password")
            return

        print("Viewer connected")

        VIEWERS.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            VIEWERS.remove(websocket)


async def run_server():
    async with websockets.serve(handle_connection, "0.0.0.0", config.server_port):
        await asyncio.Future()


asyncio.run(run_server())
