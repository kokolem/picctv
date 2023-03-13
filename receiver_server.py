import asyncio
import websockets


async def save_frame(websocket):
    with open("output.h264.enc", "wb") as output_file:
        async for frame in websocket:
            output_file.write(frame)
            output_file.write(b"--FRAME")
            output_file.flush()


async def run_server():
    async with websockets.serve(save_frame, "0.0.0.0", 8765):
        await asyncio.Future()


asyncio.run(run_server())
