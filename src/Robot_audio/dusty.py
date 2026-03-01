# import socket
# import json

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect(('192.168.1.53', 12346))
# while True:
#     command = input()
#     c = {"say": command}
#     command = json.dumps(c)
#     sock.sendall(command.encode(encoding="utf-8"))


import socket
import json
# from naoqi import ALProxy

# tts = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 12346))
server.listen(1)

print("[Pepper] Waiting for speech commands...")

conn, addr = server.accept()
print("[Pepper] Connected to:", addr)

while True:
    data = conn.recv(4096)
    if not data:
        break

    msg = json.loads(data.decode("utf-8"))
    text = msg.get("say", "")

    print("[Pepper] Saying:", text)
    # tts.say(text)