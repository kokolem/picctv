from nacl.encoding import HexEncoder
from nacl.public import PrivateKey

camera_private_key = PrivateKey.generate()
camera_public_key = camera_private_key.public_key
receiver_private_key = PrivateKey.generate()
receiver_public_key = receiver_private_key.public_key

with open("receiver_public.key", "wb") as receiver_public_key_file:
    receiver_public_key_file.write(receiver_public_key.encode(HexEncoder))

with open("receiver_private.key", "wb") as receiver_private_key_file:
    receiver_private_key_file.write(receiver_private_key.encode(HexEncoder))

with open("camera_public.key", "wb") as camera_public_key_file:
    camera_public_key_file.write(camera_public_key.encode(HexEncoder))

with open("camera_private.key", "wb") as camera_private_key_file:
    camera_private_key_file.write(camera_private_key.encode(HexEncoder))
