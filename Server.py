import socket
import os


def send_file(path, sock):
    sock.send(path)
    sock.receive()
    file = open(path)
    line = file.read(1024)
    while line:
        sock.send(line)
        line = file.read(1024)
    sock.receive()


def send_dict(path, sock):
    sock.send(path)
    sock.receive()
    directory = open(path)
    for path in directory:
        if os.path.isfile(path):
            send_file(path, sock)
        elif os.path.isdir(path):
            send_dict(path, sock)


def init():
    directory_path = os.getcwd()
    # Directory
    directory = "ServerData"
    # Path
    path = os.path.join(directory_path, directory)

    os.mkdir(path)


if __name__ == '__main__':
    init()


