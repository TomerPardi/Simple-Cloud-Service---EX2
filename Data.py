"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* Util class for server.
* Linux OS support only
"""

import random
import string
import Utils
from IDs import IDs
import os

# global variable
chunk_size = 1_000_000


# class that holds all data dictionary for server side.
class Data:
    # constructor, we are declaring dictionary for IDs, for each ID we have more dictionary for each pc
    def __init__(self, sock):
        self.paths = dict()
        self.__sock = sock
        self.identifies = IDs()
        # program's path
        directory_path = os.getcwd()
        directory = "ServerData"
        # generate path name
        self.__mypath = os.path.join(directory_path, directory)
        os.mkdir(self.__mypath)  # make the directory

    # this function is for getting data from new computer that connects with known ID
    def receive_folder(self, id, sub_id, client):
        # the process that copies the files from new pc to IDs folder in server side
        with client, client.makefile('rb') as clientfile:
            while True:
                raw = clientfile.readline()
                if not raw: break  # no more files, server closed connection.
                # TODO: change "empty dirs:"
                if raw.strip().decode() == "empty dirs:":
                    while True:
                        raw = clientfile.readline()
                        if not raw:
                            break
                        dir_name = raw.strip().decode()
                        dir_path = os.path.join(self.paths[id], dir_name)
                        os.makedirs(dir_path, exist_ok=True)
                else:
                    filename = raw.strip().decode()
                    length = int(clientfile.readline())

                    path = os.path.join(self.paths[id], filename)
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
        self.paths[id] = path
        return id

    # add new command  for each computer of specified client
    def update_computers(self, id, pc_id, command):
        for sub_id in self.identifies.get_id_dict(id).keys():
            if sub_id != pc_id:
                self.identifies.get_sub_id_set(id, sub_id).append(command)

    # function to handle folder creation
    def create_folder(self, rel_path, client_id, sub_id):
        path = os.path.join(self.paths[client_id], rel_path)
        os.makedirs(path, exist_ok=True)
        command = "created_dir" + "," + "true" + "," + rel_path
        self.update_computers(client_id, sub_id, command)

    # function to handle file creation
    def create_file(self, rel_path, client_id, sub_id, client):
        path = os.path.join(self.paths[client_id], rel_path)
        dir_name = os.path.dirname(path) # get the path without last component
        Utils.receive_file(client, dir_name)
        command = "created_file" + "," + "false" + "," + rel_path
        self.update_computers(client_id, sub_id, command)

    # function to handle file deletion
    def delete_file(self, rel_path, client_id, sub_id):
        path = os.path.join(self.paths[client_id], rel_path)
        if os.path.exists(path):
            os.remove(path)
            command = "deleted_file" + "," + "false" + "," + rel_path
            self.update_computers(client_id, sub_id, command)

    # function to handle folder deletion
    def delete_folder(self, rel_path, client_id, sub_id):
        path = os.path.join(self.paths[client_id], rel_path)
        self.delete_dir(path)
        command = "deleted_folder" + "," + "true" + "," + rel_path
        self.update_computers(client_id, sub_id, command)

    # this function is for saving for each ID the computers that connects under this ID
    # we want to identify each computer by its path
    def add_pc(self, id, sub_id, client):
        self.identifies.add_pc(id, sub_id)

    # function that call send folder function
    def send_folder_to_new_pc(self, id, client):
        Utils.send_folder(self.paths[id], client)

    # update client for each data we need to sync
    def update_client(self, client_id, sub_id, client):
        if self.identifies.get_size_of_sub_id_set(client_id, sub_id) == 0:
            client.sendall(b"no_updates" + b"\n")
        else:
            for command in self.identifies.get_sub_id_set(client_id, sub_id):
                client.sendall(command.encode() + b"\n")

                # in case of our logic we now need to send file
                command = command.split(",")
                if command[0] == "created_file":
                    rel_path = command[2]
                    src_path = os.path.join(self.paths[client_id], rel_path)
                    Utils.send_file(client, rel_path, src_path)

            client.sendall(b"finished_updates" + b"\n")
        # now we want to clear the set - after update done
        self.identifies.get_sub_id_set(client_id, sub_id).clear()

    # function to delete folder recursively
    def delete_dir(self, path):
        if not os.path.exists(path):
            return
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.rmdir(dir_path)
        os.rmdir(path)
