import asyncio
import datetime
import os.path
import pathlib

import websockets

max_file_size = 20 * 1_000_000
max_files = 5

VIEWERS = set()


def get_new_output_file():
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.h264.enc"
    output_file = pathlib.Path(f"records/{filename}")
    output_file.parent.mkdir(exist_ok=True, parents=True)
    return output_file.open("wb")


def delete_oldest_record_if_max_records_reached():
    records_dir = pathlib.Path("records")
    records = list(records_dir.iterdir())
    while len(records) > max_files:
        oldest_record = min(records, key=os.path.getmtime)
        oldest_record.unlink()
        records = list(records_dir.iterdir())


async def handle_camera_client(websocket):
    global VIEWERS

    current_file_size = 0
    current_file = get_new_output_file()
    delete_oldest_record_if_max_records_reached()

    async for frame in websocket:
        if current_file_size + len(frame) > max_file_size:
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
    client_type = await websocket.recv()
    if client_type == "camera":
        await handle_camera_client(websocket)
    elif client_type == "viewer":
        VIEWERS.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            VIEWERS.remove(websocket)


async def run_server():
    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        await asyncio.Future()


asyncio.run(run_server())
