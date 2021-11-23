from IDs import IDs
import os


class Data:
    def __init__(self):
        self._identifies = IDs()
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

    def add_client(self, id):
        self._identifies.add_client(id)
        # Path
        path = os.path.join(self.__path, id)
        os.mkdir(path)

    def add_pc(self, id, personal_path):
        paths = self._identifies.get_id_value(id)
        paths[personal_path] = set()
        self.send_folder()

    def send_folder(self, path, sock):
        sock.send(path)
        sock.receive()
        directory = open(path)
        for path in directory:
            if os.path.isfile(path):
                self.send_file(path, sock)
            elif os.path.isdir(path):
                self.send_folder(path, sock)
