import random
import string

from Data import Data
from socket import *


class Server:
    def __init__(self):
        self.__sock = socket()
        self.__sock.bind(('', 12345))
        self.__data = Data(self.__sock)
        self.__sock.listen()

    def start(self):
        while True:
            self.accept()

    def id_manager(self, id, personal_path, client):
        if id == "no_id":
            id = self.__data.add_client()
            self.__sock.send(id)
            self.__data.receive_folder(id, personal_path)
        else:
            self.__data.send_folder_to_new_pc(id, client)
            self.__data.add_pc(id, personal_path, client)

    def accept(self):
        client, address = self.__sock.accept()
        id = ""
        while len(id) < 128 and id != "no_id":
            id += self.__sock.recv(64).decode("UTF-8")
        self.__sock.send(b"got id")
        personal_path = self.__sock.recv(512)
        self.__sock.send(b"got personal path")
        self.id_manager(id, personal_path, client)


if __name__ == '__main__':
    server = Server()
    server.start()
