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
    def id_manager(self, id, sub_id, client):
        # in case the client didn't specify id number
        if id == "no_id":
            id = self.__data.add_client() # generate id
            client.send(id.encode()) # sent it to client
            self.__data.receive_folder(id, sub_id, client) # receive the folder from client
        else: # connection from new pc under known ID
            self.__data.send_folder_to_new_pc(id, client) # sent the folder to new pc
            self.__data.add_pc(id, sub_id, client) # add pc to dictionary

    # accept clients and handle first connection
    def accept(self):
        client, address = self.__sock.accept()
        id = ""
        while len(id) < 128 and id != "no_id":
            id += client.recv(64).decode()
        client.send(b"got id")
        # TODO: need to change to identify each pc by socket and not personal path
        # personal_path = self.__sock.recv(512)
        # self.__sock.send(b"got personal path")
        # self.id_manager(id, personal_path, client)
        # socket_name = client.recv(128).decode()
        # client.send(b"got socket name")
        # self.id_manager(id, socket_name, client)

        sub_id = client.recv(16).decode()
        client.send(b"got sub id")
        if sub_id == "":
            # give sub_id in chronological order
            sub_id = str(self.__data.identifies.get_size_of_sub_ids_dict(id) + 1)
            client.send(str.encode(sub_id))
        self.id_manager(id, sub_id, client)

if __name__ == '__main__':
    server = Server()
    server.accept()
    print("end main") # for debugging