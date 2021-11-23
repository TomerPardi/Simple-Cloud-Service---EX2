from Data import Data
from socket import *


class Server:
    def __init__(self):
        self.__data = Data()
        self.__sock = socket()
        self.__sock.bind(('', 12345))
        self.__sock.listen(1)
