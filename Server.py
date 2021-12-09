"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* Program for server's logic
* Linux OS support only
* args: Port number
"""

import random
import string
import Utils
import os
import os.path
import sys
from socket import *
# global variable
chunk_size = 1_000_000


# server class, here we are going to manage all server's logic
class Server:
    # constructor
    def __init__(self):
        self.__sock = socket()
        self.__data = Data(self.__sock)
        self.__sock.bind(('', int(sys.argv[1])))
        self.__sock.listen()

    # handle new connections from server-client
    def id_manager(self,  id, sub_id, client):
        # in case the client didn't specify id number
        if id == "no_id":
            # generate id
            id = self.__data.add_client()
            print(id)
            client.sendall(id.encode() + b"\n")
            self.__data.identifies.add_pc(id, sub_id)
            self.__data.receive_folder(id, sub_id, client)
        # connection from new pc under known ID
        else:
            self.__data.add_pc(id, sub_id, client)
            self.__data.send_folder_to_new_pc(id, client)

    # function to handle folder creation
    def handle_dir_create(self, rel_path, is_dir, client_id, sub_id):
        self.__data.create_folder(rel_path, client_id, sub_id)

    # function to handle file creation
    def handle_file_create(self, rel_path, is_dir, client_id, sub_id, client):
        self.__data.create_file(rel_path, client_id, sub_id, client)

    # function to handle deletion of folder or file
    def handle_deleted(self, rel_path, is_dir, client_id, sub_id):
        if is_dir:
            self.__data.delete_folder(rel_path, client_id, sub_id)
        else:
            self.__data.delete_file(rel_path, client_id, sub_id)

    # handle update request from client
    def handle_update(self, client_id, sub_id, client):
        self.__data.update_client(client_id, sub_id, client)

    # accept clients and handle first connection
    def accept(self):
        client, address = self.__sock.accept()
        with client, client.makefile('rb') as client_file:
            message = client_file.readline().decode().strip()
            if message == "new_connection":
                id = client_file.readline().decode().strip()
                sub_id = client_file.readline().decode().strip()

                if sub_id == "null sub id":
                    # give sub_id in chronological order
                    sub_id = str(self.__data.identifies.get_size_of_sub_ids_dict(id) + 1)
                    client.sendall(str.encode(sub_id) + b"\n")

                self.id_manager(id, sub_id, client)
            elif message != "":
                message_parts = message.split(",")
                command = message_parts[0]  # get the command
                rel_path = message_parts[1]
                is_dir = message_parts[2]
                client_id = message_parts[3]
                sub_id = message_parts[4]

                if command == "created_dir":
                    self.handle_dir_create(rel_path, is_dir, client_id, sub_id)

                if command == "created_file":
                    self.handle_file_create(rel_path, is_dir, client_id, sub_id, client)

                if command == "deleted":
                    path = os.path.join(self.__data.paths[client_id], rel_path)
                    isdir = os.path.isdir(path)
                    self.handle_deleted(rel_path, isdir, client_id, sub_id)

                if command == "update":
                    self.handle_update(client_id, sub_id, client)

                if command == "renamed":
                    new_path = message_parts[5]
                    self.handle_rename(rel_path, new_path, is_dir, client_id, sub_id)

    # handle rename of file or folder
    def handle_rename(self, rel_path, new_path, is_dir, client_id, sub_id):
        src_path = os.path.join(self.__data.paths[client_id], rel_path)
        if os.path.exists(src_path):
            dest_path = os.path.join(self.__data.paths[client_id], new_path)
            os.rename(src_path, dest_path)
            command = "rename" + "," + "null" + "," + rel_path + "," + new_path
            self.__data.update_computers(client_id, sub_id, command)


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


class IDs:
    def __init__(self):
        self.__keys = dict()

    def add_client(self, id):
        self.__keys[id] = dict()

    def remove_id(self, id):
        if id in self.__keys.keys():
            self.__keys.pop(id)

    def get_size_of_sub_ids_dict(self, id):
        return len(self.__keys[id])

    def get_size_of_sub_id_set(self, id, sub_id):
        set = self.__keys[id][sub_id]
        return len(set)

    def get_id_dict(self, id):
        return self.__keys[id]

    def get_sub_id_set(self, id, sub_id):
        return self.__keys[id][sub_id]

    def add_pc(self,id, sub_id):
        paths = self.__keys[id]
        paths[sub_id] = []


# start of server's program
if __name__ == '__main__':
    server = Server()
    while True:
        server.accept()