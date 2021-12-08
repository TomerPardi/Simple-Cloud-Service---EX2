import sys
import time

from Data import Data
from socket import *


# server class, here we are going to manage all server's logic
class Server:
    # constructor
    def __init__(self):
        self.__sock = socket()  # create socket for server
        self.__data = Data(self.__sock)  # here we have ID dictionary
        self.__sock.bind(('', int(sys.argv[1])))  # bind to port as usual
        self.__sock.listen()  # be ready to get clients

    # handle new connections from server-client
    def id_manager(self,  id, sub_id, client):
        # in case the client didn't specify id number
        if id == "no_id":
            id = self.__data.add_client()  # generate id
            client.sendall(id.encode() + b"\n")  # sent it to client
            self.__data.receive_folder(id, sub_id, client)  # receive the folder from client
        else:  # connection from new pc under known ID
            self.__data.send_folder_to_new_pc(id, client)  # sent the folder to new pc
            self.__data.add_pc(id, sub_id, client)  # add pc to dictionary

    def handle_dir_create(self, rel_path, is_dir, client_id, sub_id):
        self.__data.create_folder(rel_path, client_id, sub_id)

    def handle_file_create(self, rel_path, is_dir, client_id, sub_id, client):
        print("file creation")
        self.__data.create_file(rel_path, client_id, sub_id, client)

    def handle_deleted(self, rel_path, is_dir, client_id, sub_id):
        if is_dir == "true":
            self.__data.delete_folder(rel_path, client_id, sub_id)
        else:
            self.__data.delete_file(rel_path, client_id, sub_id)

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
                print(message_parts)
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
                    self.handle_deleted(rel_path, is_dir, client_id, sub_id)
                if command == "update":
                    self.handle_update(client_id, sub_id, client)


if __name__ == '__main__':
    server = Server()
    while True:
        server.accept()
        print("end...")  # for debugging, remove it later
