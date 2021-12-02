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
        self.__sub_id = ""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((self.__ip_address, self.__server_port))

    def handle_new_pc(self, ID):
        self.__sock.send(str.encode(ID))
        string = b""
        while string != b"got id":
            string += self.__sock.recv(64)

        self.__sock.send(b"null sub id")
        #string = b""
        #while string != b"got sub id":
        #    string += self.__sock.recv(128)

        self.__sub_id = self.__sock.recv(16).decode()  # receive sub id generated in server
        self.__sock.send(b"got sub id")
        Utils.receive_folder(self.__sock, self.__path)

    # handle new client situation - while ID isn't exist
    def handle_new_client(self):
        self.__sub_id = "1"  # new client with new pc - give it sub ID by chronological order
        self.__sock.send(b"no_id")
        string = b""
        while string != b"got id":
            string += self.__sock.recv(64)

        self.__sock.send(b"1")
        #string = b""
        #while string != b"got sub id":
        #    string += self.__sock.recv(64)

        while len(self.__id) < 128:
            self.__id += self.__sock.recv(128).decode()

        Utils.send_folder(self.__path, self.__sock)

    def start(self):
        if len(sys.argv) == 6:
            self.__id = sys.argv[5]
            self.handle_new_pc(self.__id)
        else: self.handle_new_client()

        print(self.__id)
        self.__sock.close()


if __name__ == '__main__':
    client = Client()
    client.start()
