import base64
import getpass
import json
import os

from nacl import pwhash, secret, utils
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey

camera_private_key = PrivateKey.generate()
camera_public_key = camera_private_key.public_key
viewer_private_key = PrivateKey.generate()
viewer_public_key = viewer_private_key.public_key

server_config = {
    "max_recording_file_size": 20000000,
    "max_recording_files": 5,
    "records_directory": "records",
    "server_port": 8765
}

camera_config = {
    "video_height": 972,
    "video_width": 1296,
    "video_quality": 4,
    "server_address": "ws://192.168.0.2:8765"
}

camera_password_plain = base64.urlsafe_b64encode(os.urandom(32))
viewer_password_plain = getpass.getpass().encode()

camera_password_hash = pwhash.str(camera_password_plain)
viewer_password_hash = pwhash.str(viewer_password_plain)

server_config["camera_password_hash"] = camera_password_hash.decode()
server_config["viewer_password_hash"] = viewer_password_hash.decode()

camera_config["password"] = camera_password_plain.decode()
camera_config["viewer_public_key_hex"] = viewer_public_key.encode(HexEncoder).decode()
camera_config["camera_private_key_hex"] = camera_private_key.encode(HexEncoder).decode()

kdf = pwhash.argon2i.kdf
salt = utils.random(pwhash.argon2i.SALTBYTES)
ops = pwhash.argon2i.OPSLIMIT_SENSITIVE
mem = pwhash.argon2i.MEMLIMIT_INTERACTIVE

viewer_key_wrapping_key = kdf(secret.SecretBox.KEY_SIZE, viewer_password_plain, salt, opslimit=ops, memlimit=mem)
viewer_key_wrapper = secret.SecretBox(viewer_key_wrapping_key)

viewer_private_key_wrapped = viewer_key_wrapper.encrypt(viewer_private_key.encode())
camera_public_key_wrapped = viewer_key_wrapper.encrypt(camera_public_key.encode())

viewer_config = {
    "viewer_private_key_wrapped_b64": base64.urlsafe_b64encode(viewer_private_key_wrapped).decode(),
    "camera_public_key_wrapped_b64": base64.urlsafe_b64encode(camera_public_key_wrapped).decode(),
    "salt_b64": base64.urlsafe_b64encode(salt).decode(),
    "ops": ops,
    "mem": mem
}

with open("server_config.json", "w") as server_config_file:
    server_config_file.write(json.dumps(server_config, indent=4))

with open("camera_config.json", "w") as camera_config_file:
    camera_config_file.write(json.dumps(camera_config, indent=4))

with open("viewer_config.json", "w") as viewer_config_file:
    viewer_config_file.write(json.dumps(viewer_config, indent=4))
