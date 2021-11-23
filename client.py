import socket
import sys
import Utils


class Client:
    def __init__(self):
        self.__ip_address = sys.argv[1]
        self.__server_port = sys.argv[2]
        self.__path = sys.argv[3]
        self.__time = sys.argv[4]
        self.__id = ""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((self.__ip_address, self.__server_port))

    def handle_new_pc(self, id):
        self.__sock.send(id)
        str = ""
        while str is not b"got id":
            str += self.__sock.recv(64)
        self.__sock.send(bytes(self.__path))
        str = ""
        while str is not b"got personal path":
            str += self.__sock.recv(64)
        Utils.receive_folder(self.__sock, self.__path)

    def handle_new_client(self):
        s.send(b"no_id")
        str = ""
        while str is not b"got id":
            str += self.__sock.recv(64)

        self.__sock.send(bytes(self.__path))
        str = ""
        while str is not b"got personal path":
            str += self.__sock.recv(64)

        while len(self.__id) < 128:
            self.__id += self.__sock.recv(64).decode("UTF-8")

        Utils.send_folder(self.__path, self.__sock)

    def start(self):
        try:
            id = sys.argv[5]
            self.handle_new_pc(id)
        except:
            self.handle_new_client()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('', 12345))

if __name__ == '__main__':
