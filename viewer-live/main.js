import _sodium from 'libsodium-wrappers'
import JMuxer from "jmuxer";

let sodium = null

function startLivestream(camera_public_key, viewer_private_key, address) {
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
        websocket.send("viewer")
    }

    websocket.onmessage = ({data}) => {
        const encrypted_frame = new Uint8Array(data)

        const nonce = encrypted_frame.slice(0, sodium.crypto_box_NONCEBYTES)
        const ciphertext = encrypted_frame.slice(sodium.crypto_box_NONCEBYTES)

        const decrypted_frame = sodium.crypto_box_open_easy(ciphertext, nonce, camera_public_key, viewer_private_key)

        jmuxer.feed({video: decrypted_frame})
    }
}

function getInputValuesAndStartStream() {
    const camera_public_key = sodium.from_hex(document.getElementById("camera_public_key").value)
    const viewer_private_key = sodium.from_hex(document.getElementById("viewer_private_key").value)
    const address = document.getElementById("address").value

    startLivestream(camera_public_key, viewer_private_key, address)
}

_sodium.ready.then(() => {
    sodium = _sodium
    document.getElementById("input").addEventListener("submit", getInputValuesAndStartStream, false)
})
