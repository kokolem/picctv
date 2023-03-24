import base64
import getpass
import json
import sys

from nacl import pwhash, secret
from nacl.exceptions import CryptoError, ValueError
from nacl.public import PrivateKey, Box, PublicKey

with open(sys.argv[1]) as viewer_config_file:
    viewer_config = json.loads(viewer_config_file.read())

kdf = pwhash.argon2i.kdf
salt = base64.urlsafe_b64decode(viewer_config["salt_b64"])
ops = viewer_config["ops"]
mem = viewer_config["mem"]

viewer_password_plain = getpass.getpass().encode()

viewer_key_wrapping_key = kdf(secret.SecretBox.KEY_SIZE, viewer_password_plain, salt, opslimit=ops, memlimit=mem)
viewer_key_wrapper = secret.SecretBox(viewer_key_wrapping_key)

viewer_private_key_wrapped = base64.urlsafe_b64decode(viewer_config["viewer_private_key_wrapped_b64"])
camera_public_key_wrapped = base64.urlsafe_b64decode(viewer_config["camera_public_key_wrapped_b64"])

try:
    viewer_private_key = PrivateKey(viewer_key_wrapper.decrypt(viewer_private_key_wrapped))
    camera_public_key = PublicKey(viewer_key_wrapper.decrypt(camera_public_key_wrapped))
except CryptoError:
    print("Invalid password")
    exit()

decryptor = Box(viewer_private_key, camera_public_key)

with open(sys.argv[2], "rb") as encrypted_file, open(sys.argv[2][:-4], "wb") as decrypted_file:
    for encrypted_frame in encrypted_file.read().split(b"--FRAME"):
        try:
            decrypted_frame = decryptor.decrypt(encrypted_frame)
        except ValueError:
            continue
        else:
            decrypted_file.write(decrypted_frame)
            decrypted_file.flush()
