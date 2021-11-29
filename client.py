import socket
import sys
import Utils


class Client:
    def __init__(self):
        self.__ip_address = sys.argv[1]
        self.__server_port = int(sys.argv[2])
        self.__path = sys.argv[3]
        self.__time = sys.argv[4]
        self.__id = ""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((self.__ip_address, self.__server_port))

    def handle_new_pc(self, ID):
        self.__sock.send(ID)
        string = b""
        while string != b"got id":
            string += self.__sock.recv(64)
        socket_name = str(self.__sock.getsockname()[0]) + "-" + str(self.__sock.getsockname()[1])  # "ip-port"
        self.__sock.send(str.encode(socket_name))
        string = ""
        while string != b"got socket name":
            string += self.__sock.recv(64)
        Utils.receive_folder(self.__sock, self.__path)

    # handle new client situation - while ID isn't exist
    def handle_new_client(self):
        self.__sock.send(b"no_id")
        string = b""
        while string != b"got id":
            string += self.__sock.recv(64)
        # TODO: change identification by socket and now by personal path
        # get socket name (getsockname() returns tuple name
        socket_name = str(self.__sock.getsockname()[0]) + "-" + str(self.__sock.getsockname()[1]) # "ip-port"
        self.__sock.send(str.encode(socket_name))
        string = b""
        while string != b"got socket name":
            string += self.__sock.recv(64)


        while len(self.__id) < 128:
            self.__id += self.__sock.recv(64).decode()
        # Utils.send_folder(self.__path, self.__sock)
        Utils.send_folder(self.__path, self.__sock)


    def start(self):
        try:
            id = sys.argv[5]
            self.handle_new_pc(id)
        except:
            self.handle_new_client()

if __name__ == '__main__':
    client = Client()
    client.start()