import socket

HOST = 'localhost'
PORT = 3000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print('Socket ready')

def send(msg):
    sock.sendto(msg, (HOST, PORT))