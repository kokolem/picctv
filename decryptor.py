from nacl.public import PrivateKey, Box, PublicKey

with open("camera_public.key", "rb") as camera_public_key_file:
    camera_public_key = PublicKey(camera_public_key_file.read())

with open("receiver_private.key", "rb") as receiver_private_key_file:
    receiver_private_key = PrivateKey(receiver_private_key_file.read())

decryptor = Box(receiver_private_key, camera_public_key)

with open("output.h264.enc", "rb") as encrypted_file:
    with open("output.h264", "wb") as decrypted_file:
        for encrypted_frame in encrypted_file.read().split(b"--FRAME"):
            decrypted_frame = decryptor.decrypt(encrypted_frame)
            decrypted_file.write(decrypted_frame)
            decrypted_file.flush()
