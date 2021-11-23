import random
import string

from Data import Data
from socket import *


class Server:
    def __init__(self):
        self.__data = Data()
        self.__sock = socket()
        self.__sock.bind(('', 12345))
        self.__sock.listen()

    def id_manager(self, id):
        if id == "no_id":
            id = res = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
        self.__data._identifies.add_client(id)
        return id

    def accept(self):
        client, address = self.__sock.accept()
        id = self.__sock.recv(1024)
        self.__sock.send(id)
