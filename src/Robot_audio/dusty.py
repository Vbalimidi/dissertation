import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 12346))
while True:
    command = input()
    c = {"say": command}
    command = json.dumps(c)
    sock.sendall(command.encode(encoding="utf-8"))
