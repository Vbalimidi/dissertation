import socket
import json

HOST = "127.0.0.1" 
PORT = 12346

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"Listening on {HOST}:{PORT} ...")

        conn, addr = server.accept()
        with conn:
            print(f"Connected by {addr}")

            buffer = b""
            decoder_errors = "replace"

            while True:
                data = conn.recv(4096)
                if not data:
                    print("Client disconnected.")
                    break

                buffer += data

                # Try to parse complete JSON objects from the stream.
                # Your sender sends JSON like {"say": "..."} but without a delimiter,
                # so we use JSONDecoder to peel objects off the front of the buffer.
                while buffer:
                    try:
                        text = buffer.decode("utf-8", errors=decoder_errors)
                        obj, idx = json.JSONDecoder().raw_decode(text)
                        print("RECEIVED:", obj)
                        buffer = text[idx:].lstrip().encode("utf-8")
                    except json.JSONDecodeError:
                        # Not enough data yet for a full JSON object
                        break

if __name__ == "__main__":
    main()
