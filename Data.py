from IDs import IDs
import os


class Data:
    def __init__(self):
        self.__identifies = IDs()
        directory_path = os.getcwd()
        # Directory
        directory = "ServerData"
        # Path
        self.__path = os.path.join(directory_path, directory)
        os.mkdir(self.__path)

    def send_file(self, path, sock):
        sock.send(path)
        sock.receive()
        file = open(path)
        line = file.read(1024)
        while line:
            sock.send(line)
            line = file.read(1024)
        sock.receive()

    def send_directory(self, path, sock):
        sock.send(path)
        sock.receive()
        directory = open(path)
        for path in directory:
            if os.path.isfile(path):
                self.send_file(path, sock)
            elif os.path.isdir(path):
                self.send_directory(path, sock)
