import os.path
import socket
import sys

import watchdog

import Utils
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


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

        while len(self.__id) < 128:
            self.__id += self.__sock.recv(128).decode()

        Utils.send_folder(self.__path, self.__sock)

    def handle_created_dir(self, rel_path, is_dir):
        update_msg = "created_dir" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.send(update_msg.encode())
        string = self.__sock.recv(1024)
        while string != b"got_message":
            string += self.__sock.recv(64)

    def handle_created_file(self, rel_path, is_dir, event):
        update_msg = "created_file" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.send(update_msg.encode())
        string = self.__sock.recv(1024)
        while string != b"got_message":
            string += self.__sock.recv(64)
        Utils.send_file(self.__sock, rel_path, event.src_path)

    def handle_deleted(self, rel_path, is_dir):
        update_msg = "deleted" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.send(update_msg.encode())
        string = self.__sock.recv(1024)
        while string != b"got_message":
            string += self.__sock.recv(64)

    def on_any_event(self, event):
        self.__sock.connect((self.__ip_address, self.__server_port))
        rel_path = os.path.relpath(event.src_path, self.__path)
        is_dir = str(os.path.isdir(event.src_path))
        self.handle_event(event, event.event_type, rel_path, is_dir)
        self.__sock.close()

    def handle_event(self, event, event_type, rel_path, is_dir):
        if event_type == "created":
            if is_dir == "true":
                self.handle_created_dir(rel_path, is_dir)
            else:
                self.handle_created_file(rel_path, is_dir, event)
        if event_type == "deleted":
            self.handle_deleted(rel_path, is_dir)
        if event_type == "moved":
            # happens only when we rename file/folder
            # first delete file/folder
            self.handle_deleted(rel_path, is_dir)
            # now create the file/folder
            new_path = os.path.relpath(event.dest_path, self.__path)
            if is_dir == "true":
                self.handle_created_dir(new_path, is_dir)
            else:
                self.handle_created_file(new_path, is_dir, event)
        if event_type == "modified":
            if is_dir == "false":
                # just like creation of file
                self.handle_created_file(rel_path, is_dir, event)

    def start_observe(self):
        patterns = ["*"]
        ignore_patterns = None
        ignore_directories = False
        case_sensitive = True
        go_recursively = True
        my_observer = Observer()

        my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
        my_event_handler.on_any_event = self.on_any_event
        my_observer.schedule(my_event_handler, self.__path, recursive=go_recursively)
        my_observer.start()
        try:
            while True:
                time.sleep(int(self.__time))
                # here we need handle update from server/ pull info from server
                self.__sock.connect((self.__ip_address, self.__server_port))
                self.update() # TODO - implement this function
                self.__sock.close()
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
        my_observer.stop()

    def update(self):
        # TODO - this function is for pulling the data from server
        message = "update" + "," + self.__id + "," + self.__sub_id
        self.__sock.send(message.encode())
        string = self.__sock.recv(1024)
        while string != b"got_message":
            string += self.__sock.recv(64)
        # from now on receive data from server
        pass

    def start(self):
        self.__sock.send(b"new_connection")
        if len(sys.argv) == 6:
            self.__id = sys.argv[5]
            self.handle_new_pc(self.__id)
        else: self.handle_new_client()

        print(self.__id)
        self.__sock.close()
        self.start_observe()


if __name__ == '__main__':
    client = Client()
    client.start()
