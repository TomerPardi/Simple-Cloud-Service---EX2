from Data import Data
from socket import *


# server class, here we are going to manage all server's logic
class Server:
    # constructor
    def __init__(self):
        self.__sock = socket() # create socket for server
        self.__data = Data(self.__sock) # here we have ID dictionary
        self.__sock.bind(('', 12345)) # bind to port as usual
        self.__sock.listen() # be ready to get clients

    # handle new connections from server-client
    def id_manager(self, id, personal_path, client):
        # in case the client didn't specify id number
        if id == "no_id":
            id = self.__data.add_client() # generate id
            self.__sock.send(id) # sent it to client
            self.__data.receive_folder(id, personal_path) # receive the folder from client
        else: # connection from new pc under known ID
            self.__data.send_folder_to_new_pc(id, client) # sent the folder to new pc
            self.__data.add_pc(id, personal_path, client) # add pc to dictionary

    # accept clients and handle first connection
    def accept(self):
        client, address = self.__sock.accept()
        id = ""
        while len(id) < 128 and id != "no_id":
            id += self.__sock.recv(64).decode()
        self.__sock.send(b"got id")
        # TODO: need to change to identify each pc by socket and not personal path
        # personal_path = self.__sock.recv(512)
        # self.__sock.send(b"got personal path")
        # self.id_manager(id, personal_path, client)
        socket_name = self.__sock.recv(128).decode()
        self.__sock.send(b"got socket name")
        self.id_manager(id, socket_name, client)
