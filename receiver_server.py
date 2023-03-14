import asyncio
import datetime

import websockets

max_file_size = 20 * 1_000_000

VIEWERS = set()


async def handle_camera_client(websocket):
    global VIEWERS

    current_file_size = 0
    current_file = open(f"{datetime.datetime.now().isoformat(timespec='seconds')}.h264.enc", "wb")

    async for frame in websocket:
        if current_file_size + len(frame) > max_file_size:
            current_file.close()
            current_file = open(f"{datetime.datetime.now().isoformat(timespec='seconds')}.h264.enc", "wb")
            current_file_size = 0

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
