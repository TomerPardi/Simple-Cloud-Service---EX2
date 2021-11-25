import random
import string

from IDs import IDs
import os

chunk_size = 1_000_000


class Data:
    def __init__(self, sock):
        self.__paths = dict()
        self.__sock = sock
        self.identifies = IDs()
        directory_path = os.getcwd()
        # Directory
        directory = "ServerData"
        # Path
        self.__path = os.path.join(directory_path, directory)
        if not os.path.isdir(self.__path):
            os.mkdir(self.__path)

    def receive_folder(self, id, personal_path):
        self.identifies.add_pc(id, personal_path)
        with self.__sock, self.__sock.makefile('rb') as clientfile:
            while True:
                raw = clientfile.readline()
                if not raw: break  # no more files, server closed connection.

                filename = raw.strip().decode()
                length = int(clientfile.readline())

                path = os.path.join(self.__paths[id], filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # Read the data in chunks so it can handle large files.
                with open(path, 'wb') as f:
                    while length:
                        chunk = min(length, chunk_size)
                        data = clientfile.read(chunk)
                        if not data: break
                        f.write(data)
                        length -= len(data)
                    else:  # only runs if while doesn't break and length==0
                        continue

                # socket was closed early.
                break

    def send_file(self, path):
        self.__sock.send(path)
        self.__sock.receive()
        file = open(path)
        line = file.read(1024)
        while line:
            self.__sock.send(line)
            line = file.read(1024)
        self.__sock.receive()

    def add_client(self):
        id = res = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
        self.identifies.add_client(id)
        # Path
        path = os.path.join(self.__path, id)
        os.mkdir(path)
        self.__paths[id] = path
        return id

    def add_pc(self, id, personal_path, client):
        paths = self.identifies.get_id_value(id)
        paths[personal_path] = set()
        self.send_folder(self.__paths[id], client)

    def send_folder_to_new_pc(self, id, client):
        self.send_folder(self.__paths[id], client)

    def send_folder(self, path, client):
        with client:
            for path, dirs, files in os.walk(path):
                for file in files:
                    filename = os.path.join(path, file)
                    relpath = os.path.relpath(filename, path)
                    filesize = os.path.getsize(filename)

                    with open(filename, 'rb') as f:
                        client.sendall(relpath.encode() + b'\n')
                        client.sendall(str(filesize).encode() + b'\n')

                        # Send the file in chunks so large files can be handled.
                        while True:
                            data = f.read(chunk_size)
                            if not data: break
                            client.sendall(data)
