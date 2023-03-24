import _sodium from 'libsodium-wrappers-sumo'
import JMuxer from "jmuxer";
import {Base64} from 'js-base64';

let sodium = null

function startLivestream(camera_public_key, viewer_private_key, address, password) {
    const jmuxer = new JMuxer({
        node: "player",
        mode: "video",
        flushingTime: 0,
        debug: import.meta.env.DEV,
        maxDelay: 500
    })

    const websocket = new WebSocket(address);
    websocket.binaryType = "arraybuffer"

    websocket.onopen = () => {
        websocket.send(`viewer:${password}`)
    }

    websocket.onmessage = ({data}) => {
        const encrypted_frame = new Uint8Array(data)

        const nonce = encrypted_frame.slice(0, sodium.crypto_box_NONCEBYTES)
        const ciphertext = encrypted_frame.slice(sodium.crypto_box_NONCEBYTES)

        const decrypted_frame = sodium.crypto_box_open_easy(ciphertext, nonce, camera_public_key, viewer_private_key)

        jmuxer.feed({video: decrypted_frame})
    }
}

function unwrapKey(wrapped_key_b64, wrapping_key) {
    const uint8array_wrapped = Base64.toUint8Array(wrapped_key_b64.replace(/_/g, '/').replace(/-/g, '+'))
    const nonce = uint8array_wrapped.slice(0, sodium.crypto_secretbox_NONCEBYTES)
    const ciphertext = uint8array_wrapped.slice(sodium.crypto_secretbox_NONCEBYTES)
    return sodium.crypto_secretbox_open_easy(ciphertext, nonce, wrapping_key)
}

function getInputValuesAndStartStream() {
    const viewer_config_file = document.getElementById("viewer_config_file").files[0]
    const password = document.getElementById("viewer_password").value
    const address = document.getElementById("address").value

    const reader = new FileReader()
    reader.onload = e => {
        const viewer_config = JSON.parse(e.target.result)

        const salt = Base64.toUint8Array(viewer_config.salt_b64.replace(/_/g, '/').replace(/-/g, '+'))
        const ops = viewer_config.ops
        const mem = viewer_config.mem

        const wrapping_key = sodium.crypto_pwhash(
            sodium.crypto_secretbox_KEYBYTES,
            password,
            salt,
            ops,
            mem,
            sodium.crypto_pwhash_ALG_ARGON2I13
        )

        const viewer_private_key = unwrapKey(viewer_config.viewer_private_key_wrapped_b64, wrapping_key)
        const camera_public_key = unwrapKey(viewer_config.camera_public_key_wrapped_b64, wrapping_key)

        document.getElementById("input").style.display = "none"

        startLivestream(camera_public_key, viewer_private_key, address, password)
    }
    reader.readAsText(viewer_config_file)
}

_sodium.ready.then(() => {
    sodium = _sodium
    document.getElementById("input").addEventListener("submit", getInputValuesAndStartStream, false)
})
