import random
import string

import Utils
from IDs import IDs
import os

# this variable is for sending folder
chunk_size = 1_000_000


# class that holds all data dictionary for server side.
class Data:
    # constructor, we are declaring dictionary for IDs, for each ID we have more dictionary for each pc that connects
    def __init__(self, sock):
        self.__paths = dict()  # dict to map between ID and its path in server's side
        self.__sock = sock  # server's socket
        self.identifies = IDs()  # ID dict
        directory_path = os.getcwd()  # get current main's path (current folder)
        # Directory
        directory = "ServerData"
        # Path
        self.__mypath = os.path.join(directory_path, directory)  # generate path name
        os.mkdir(self.__mypath)  # make the directory

    # this function is for getting data from new computer that connects with known ID
    def receive_folder(self, id, sub_id, client):
        # an function to add new pc under known ID
        self.identifies.add_pc(id, sub_id)
        # the process that copies the files from new pc to IDs folder in server side
        with client, client.makefile('rb') as clientfile:
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

    # TODO: why is this function here?
    def send_file(self, path):
        self.__sock.send(path)
        self.__sock.receive()
        file = open(path)
        line = file.read(1024)
        while line:
            self.__sock.send(line)
            line = file.read(1024)
        self.__sock.receive()

    # function to add new client to our dictionary, in case he didn't has ID
    def add_client(self):
        # create random ID number
        id = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
        # add it to the identifies dict
        self.identifies.add_client(id)
        # create a path to this ID; there we are going to add all files this client uploads
        path = os.path.join(self.__mypath, id)
        os.mkdir(path)
        # add the path to map between id and path easily
        self.__paths[id] = path
        return id

    # TODO: make a signal that the directory is added and other users need to download it
    def create_folder(self, rel_path, client_id, sub_id):
        os.makedirs(os.path.dirname(os.path.join(self.__mypath, rel_path)), exist_ok=True)

    # TODO: make a signal that the file is added and other users need to download it
    def create_file(self, rel_path, client_id, sub_id):
        open(os.path.join(self.__mypath, rel_path))

    # this function is for saving for each ID the computers that connects under this ID
    # we want to identify each computer by its path TODO: change it to identify by socket
    def add_pc(self, id, sub_id, client):
        id_dict = self.identifies.get_id_value(id)
        # TODO: identify each pc by its socket
        id_dict[sub_id] = set()  # this dictionary will hold for each key set of updates.
        # send the ID folder to new pc we just registered
        # self.send_folder(self.__paths[id], client)

    # function that call send folder function
    def send_folder_to_new_pc(self, id, client):
        Utils.send_folder(self.__paths[id], client)

    # function that sends folder to receiver TODO: we have the same function at Utils - check it
    def send_folder(self, source_path, client):
        with client:
            for path, dirs, files in os.walk(source_path):
                for file in files:
                    filename = os.path.join(path, file)
                    relpath = os.path.relpath(filename, source_path)
                    filesize = os.path.getsize(filename)

                    with open(filename, 'rb') as f:
                        client.sendall(relpath.encode() + b'\n')
                        client.sendall(str(filesize).encode() + b'\n')

                        # Send the file in chunks so large files can be handled.
                        while True:
                            data = f.read(chunk_size)
                            if not data: break
                            client.sendall(data)
