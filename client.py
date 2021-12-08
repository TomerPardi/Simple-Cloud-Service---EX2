import os.path
import socket
import sys

import watchdog

import Utils
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
DELIM = "###endofmessage###"


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
        self.LAST_UPDATE_MADE = ""

    def handle_new_pc(self, ID):
        self.__sock.sendall(str.encode(ID) + b"\n")
        # string = b""
        # while string != b"got id":
        #    string += self.__sock.recv(64)

        self.__sock.sendall(b"null sub id" + b"\n")
        with self.__sock, self.__sock.makefile('rb') as server_file:
            self.__sub_id = server_file.readline().decode().strip()
        Utils.receive_folder(self.__sock, self.__path)

    def delete_dir(self, path):
        if not os.path.exists(path):
            return
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
                self.LAST_UPDATE_MADE = file_path
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.rmdir(dir_path)
                self.LAST_UPDATE_MADE = dir_path
        os.rmdir(path)
        self.LAST_UPDATE_MADE = path

    # handle new client situation - while ID isn't exist
    def handle_new_client(self):
        self.__sub_id = "1"  # new client with new pc - give it sub ID by chronological order
        self.__sock.sendall(b"no_id" + b"\n")

        self.__sock.sendall(b"1" + b"\n")
        with self.__sock, self.__sock.makefile('rb') as server_file:
            self.__id = server_file.readline().decode().strip()

            Utils.send_folder(self.__path, self.__sock)

    def handle_created_dir(self, rel_path, is_dir):
        update_msg = "created_dir" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(update_msg.encode() + b"\n")

    def handle_created_file(self, rel_path, is_dir, event, flag):
        update_msg = "created_file" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        print(update_msg)
        self.__sock.sendall(update_msg.encode() + b"\n")
        print(rel_path)
        if flag:
            Utils.send_file(self.__sock, rel_path,  event.dest_path)
        else:
            Utils.send_file(self.__sock, rel_path, event.src_path)

    def handle_deleted(self, rel_path, is_dir):
        update_msg = "deleted" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        print(update_msg)
        self.__sock.sendall(update_msg.encode() + b"\n")

    def on_any_event(self, event):
        if event.event_type == "modified" or event.src_path.split(".")[-1] == "swp":
            return
        if "goutputstream" in event.src_path and event.event_type == "created":
            return
        if event.src_path == self.LAST_UPDATE_MADE:
            self.LAST_UPDATE_MADE = ""
            return # the event was an update from server, ignore it
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((self.__ip_address, self.__server_port))
        rel_path = os.path.relpath(event.src_path, self.__path)
        is_dir = str(os.path.isdir(event.src_path))
        self.handle_event(event, event.event_type, rel_path, is_dir)
        self.__sock.close()

    def handle_event(self, event, event_type, rel_path, is_dir):
        if event_type == "created":
            if is_dir == "True":
                self.handle_created_dir(rel_path, is_dir)
            else:
                print("create file")
                self.handle_created_file(rel_path, is_dir, event, 0)

        if event_type == "deleted":
            print("deleted" + " " + is_dir)
            self.handle_deleted(rel_path, is_dir)

        if event_type == "moved":
            new_path = os.path.relpath(event.dest_path, self.__path)
            # modify file
            if "goutputstream" in event.src_path:
                print("now here")
                print(new_path)
                self.handle_deleted(new_path, is_dir)
                print("handled deleted move on to create again")
                self.__sock.close()
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.connect((self.__ip_address, self.__server_port))
                self.handle_created_file(new_path, is_dir, event, 1)
                return
            # happens only when we rename file/folder
            # first delete file/folder
            is_dir = str(os.path.isdir(new_path))
            self.handle_rename(rel_path, new_path, is_dir)

            ##############################################
            # self.handle_deleted(rel_path, is_dir)
            # now create the file/folder
            # self.__sock.close()
            # self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.__sock.connect((self.__ip_address, self.__server_port))
            # if is_dir == "True":
            #     self.handle_created_dir(new_path, is_dir)
            # else:
            #     self.handle_created_file(new_path, is_dir, event, 1)


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
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.connect((self.__ip_address, self.__server_port))
                self.update() # TODO - implement this function
                self.__sock.close()
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
        my_observer.stop()

    def update(self):
        # TODO - this function is for pulling the data from server
        message = "update" + "," + "null" + "," + "null" + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(message.encode() + b"\n")

        # from now on receive data from server
        with self.__sock, self.__sock.makefile('rb') as server_file:
            message = server_file.readline().decode().strip()
        if message == "no_updates":
            return
        message = message.split(",")
        command = message[0]
        is_dir = message[1]
        rel_path = message[2]
        if command == "deleted_file":
            path = os.path.join(self.__path, rel_path)
            if os.path.exists(path):
                os.remove(path)
            self.__LAST_UPDATE_MADE = path
        # TODO think of better way to handle this situation (import client in Utils)
        elif command == "deleted_folder":
            path = os.path.join(self.__path, rel_path)
            self.delete_dir(path)
        elif command == "created_dir":
            path = os.path.join(self.__path, rel_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.__LAST_UPDATE_MADE = path
        elif command == "created_file":
            path = os.path.join(self.__path, rel_path)
            dir_name = os.path.dirname(path)  # get the path without last component
            Utils.receive_folder(self.__sock, dir_name)
            self.__LAST_UPDATE_MADE = path


    def start(self):
        self.__sock.sendall(b"new_connection" + b"\n")
        if len(sys.argv) == 6:
            self.__id = sys.argv[5]
            self.handle_new_pc(self.__id)
        else: self.handle_new_client()

        print(self.__id)
        self.__sock.close()
        self.start_observe()

    def handle_rename(self, rel_path, new_path, is_dir):
        update_msg = "renamed" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id + "," + new_path
        # print(update_msg)
        self.__sock.sendall(update_msg.encode() + b"\n")
        pass


if __name__ == '__main__':
    client = Client()
    client.start()
