import asyncio
import io
from threading import Condition

import websockets as websockets
from nacl.public import PrivateKey, Box, PublicKey
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FileOutput

with open("receiver_public.key", "rb") as receiver_public_key_file:
    receiver_public_key = PublicKey(receiver_public_key_file.read())

with open("camera_private.key", "rb") as camera_private_key_file:
    camera_private_key = PrivateKey(camera_private_key_file.read())

encryptor = Box(camera_private_key, receiver_public_key)


class CameraOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.new_frame_condition = Condition()

    def write(self, buf: bytes):
        with self.new_frame_condition:
            self.frame = encryptor.encrypt(buf)
            self.new_frame_condition.notify_all()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await asyncio.get_running_loop().run_in_executor(None, self.wait_for_new_frame)

    def wait_for_new_frame(self):
        with self.new_frame_condition:
            self.new_frame_condition.wait()
            frame = self.frame
        return frame


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1296, 972)}))
camera_output = CameraOutput()
encoder = H264Encoder()
picam2.start_recording(encoder, FileOutput(camera_output), Quality.VERY_HIGH)


async def send_frames():
    async with websockets.connect("ws://192.168.0.88:8765") as websocket:
        async for frame in camera_output:
            await websocket.send(frame)


asyncio.run(send_frames())
