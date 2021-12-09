"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* Program for server's logic
* Linux OS support only
* args: Port number
"""

import os.path
import sys
from Data import Data
from socket import *


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


# start of server's program
if __name__ == '__main__':
    server = Server()
    while True:
        server.accept()
        # print("end...")  # for debugging, remove it later
