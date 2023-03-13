import asyncio
import datetime

import websockets

max_file_size = 50 * 1_000_000


async def save_frame(websocket):
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


async def run_server():
    async with websockets.serve(save_frame, "0.0.0.0", 8765):
        await asyncio.Future()


asyncio.run(run_server())
