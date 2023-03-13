import asyncio
from threading import Condition

import websockets as websockets
from nacl.public import PrivateKey, Box, PublicKey
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import Output

with open("receiver_public.key", "rb") as receiver_public_key_file:
    receiver_public_key = PublicKey(receiver_public_key_file.read())

with open("camera_private.key", "rb") as camera_private_key_file:
    camera_private_key = PrivateKey(camera_private_key_file.read())

encryptor = Box(camera_private_key, receiver_public_key)


class AsyncIterableOutput(Output):
    def __init__(self):
        super().__init__()
        self.latest_non_keyframe = None
        self.latest_keyframe = None
        self.new_frame_condition = Condition()

    def outputframe(self, frame, keyframe=True, timestamp=None):
        with self.new_frame_condition:
            encrypted_frame = encryptor.encrypt(frame)
            if keyframe:
                self.latest_keyframe = encrypted_frame
            else:
                self.latest_non_keyframe = encrypted_frame
            self.new_frame_condition.notify_all()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await asyncio.get_running_loop().run_in_executor(None, self.wait_for_new_frame)

    def wait_for_new_frame(self):
        with self.new_frame_condition:
            preferred_frame = self.get_preferred_frame()
            if preferred_frame:
                return preferred_frame
            self.new_frame_condition.wait()
            return self.get_preferred_frame()

    def get_preferred_frame(self):
        preferred_frame = None
        if self.latest_keyframe:
            preferred_frame = self.latest_keyframe
            self.latest_keyframe = None
        elif self.latest_non_keyframe:
            preferred_frame = self.latest_non_keyframe
            self.latest_non_keyframe = None
        return preferred_frame


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1296, 972)}))
camera_output = AsyncIterableOutput()
encoder = H264Encoder()
picam2.start_encoder(encoder, camera_output, quality=Quality.VERY_HIGH)
picam2.start()


async def send_frames():
    async with websockets.connect("ws://192.168.0.88:8765") as websocket:
        async for frame in camera_output:
            await websocket.send(frame)


asyncio.run(send_frames())
