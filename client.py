"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* Program for client
* Linux OS support only
* args: IP address of server, server's port, local path, sleep time and ID number (optional)
"""

import os.path
import socket
import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# global variable
chunk_size = 1_000_000


# Client's class
class Client:
    # constructor
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

    # logic for handling new pc connection
    def handle_new_pc(self, ID):
        self.__sock.sendall(str.encode(ID) + b"\n")
        self.__sock.sendall(b"null sub id" + b"\n")
        with self.__sock, self.__sock.makefile('rb') as server_file:
            self.__sub_id = server_file.readline().decode().strip()
            self.receive_folder(self.__sock, self.__path)

    # function for deleting folder recursively
    def delete_dir(self, path):
        if not os.path.exists(path):
            return
        for root, dirs, files in os.walk(path, topdown=False):
            # remove inner files
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
                self.LAST_UPDATE_MADE = file_path
            # remove inner folders
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.rmdir(dir_path)
                self.LAST_UPDATE_MADE = dir_path
        # now remove source folder
        os.rmdir(path)
        self.LAST_UPDATE_MADE = path

    # handle new client situation - while ID isn't exist
    def handle_new_client(self):
        # new client with new pc - give it sub ID by chronological order
        self.__sub_id = "1"
        self.__sock.sendall(b"no_id" + b"\n")
        self.__sock.sendall(b"1" + b"\n")
        # send local folder to sync with server
        with self.__sock, self.__sock.makefile('rb') as server_file:
            self.__id = server_file.readline().decode().strip()
            self.send_folder(self.__path, self.__sock)

    # handle creation of folder
    def handle_created_dir(self, rel_path, is_dir):
        update_msg = "created_dir" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(update_msg.encode() + b"\n")

    # handle creation of file
    def handle_created_file(self, rel_path, is_dir, event, flag):
        update_msg = "created_file" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(update_msg.encode() + b"\n")
        if flag:
            self.send_file(self.__sock, rel_path,  event.dest_path)
        else:
            self.send_file(self.__sock, rel_path, event.src_path)

    # handle deletion of file or folder
    def handle_deleted(self, rel_path, is_dir):
        update_msg = "deleted" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(update_msg.encode() + b"\n")

    # main function for watchdog observer, it's called every time watchdog notice event
    def on_any_event(self, event):
        # filter any redundant events we notice
        if event.event_type == "modified" or event.event_type == "closed" or event.src_path.split(".")[-1] == "swp":
            return
        if "goutputstream" in event.src_path and event.event_type == "created":
            return
        # in case the event was an update from server, ignore it
        if event.src_path == self.LAST_UPDATE_MADE:
            self.LAST_UPDATE_MADE = ""
            return
        # connect with socket
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((self.__ip_address, self.__server_port))
        rel_path = os.path.relpath(event.src_path, self.__path)
        is_dir = str(os.path.isdir(event.src_path))
        # handle any relevant event
        self.handle_event(event, event.event_type, rel_path, is_dir)
        # close socket
        self.__sock.close()

    # handle any relevant event that arose
    def handle_event(self, event, event_type, rel_path, is_dir):
        # handle creation
        if event_type == "created":
            # distinguish between file and folder creation
            if is_dir == "True":
                self.handle_created_dir(rel_path, is_dir)
            else:
                self.handle_created_file(rel_path, is_dir, event, 0)
        # handle deletion
        if event_type == "deleted":
            self.handle_deleted(rel_path, is_dir)
        # handle moving
        if event_type == "moved":
            new_path = os.path.relpath(event.dest_path, self.__path)
            # handle file modification
            if "goutputstream" in event.src_path:
                self.handle_deleted(new_path, is_dir)
                self.__sock.close()
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.connect((self.__ip_address, self.__server_port))
                self.handle_created_file(new_path, is_dir, event, 1)
                return
            # happens only when we rename file/folder
            is_dir = str(os.path.isdir(new_path))
            self.handle_rename(rel_path, new_path, is_dir)

    # setup watchdog - code we brought from the documentation of watchdog
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
                # handle update from server - pulling data from server
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.connect((self.__ip_address, self.__server_port))
                self.update()
                self.__sock.close()

        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
        my_observer.stop()

    # handle update sync from server
    def update(self):
        message = "update" + "," + "null" + "," + "null" + "," + self.__id + "," + self.__sub_id
        self.__sock.sendall(message.encode() + b"\n")

        # from now on receive data from server
        with self.__sock, self.__sock.makefile('rb') as server_file:
            while True:
                message = server_file.readline().decode().strip()
                if message == "no_updates" or message == "finished_updates" or not message:
                    return
                message = message.split(",")
                command = message[0]
                is_dir = message[1]
                rel_path = message[2]
                # handle deletion of file
                if command == "deleted_file":
                    path = os.path.join(self.__path, rel_path)
                    if os.path.exists(path):
                        self.LAST_UPDATE_MADE = path
                        os.remove(path)
                # handle deletion of folder
                elif command == "deleted_folder":
                    path = os.path.join(self.__path, rel_path)
                    self.delete_dir(path)
                # handle creation of folder
                elif command == "created_dir":
                    path = os.path.join(self.__path, rel_path)
                    os.makedirs(path, exist_ok=True)
                    self.LAST_UPDATE_MADE = path
                # handle creation of file
                elif command == "created_file":
                    path = os.path.join(self.__path, rel_path)
                    # get the path without last component
                    dir_name = os.path.dirname(path)
                    self.receive_file(self.__sock, dir_name)
                # handle rename of any directory
                elif command == "rename":
                    dest_path = os.path.join(self.__path, message[3])
                    src_path = os.path.join(self.__path, rel_path)
                    if os.path.exists(src_path):
                        os.rename(src_path, dest_path)
                        self.LAST_UPDATE_MADE = src_path

    # start client's logic
    def start(self):
        self.__sock.sendall(b"new_connection" + b"\n")
        if len(sys.argv) == 6:
            self.__id = sys.argv[5]
            self.handle_new_pc(self.__id)
        else: self.handle_new_client()
        self.__sock.close()
        # start watchdog observation
        self.start_observe()

    # handle rename of files and folders
    def handle_rename(self, rel_path, new_path, is_dir):
        update_msg = "renamed" + ',' + rel_path + ',' + is_dir + "," + self.__id + "," + self.__sub_id + "," + new_path
        self.__sock.sendall(update_msg.encode() + b"\n")

    # function for sending files through TCP socket
    def send_file(self, sock, relpath, filepath):
        filesize = os.path.getsize(filepath)
        with sock, sock.makefile('rb') as server_file:
            message = server_file.readline().decode().strip()
            with open(filepath, 'rb') as f:
                sock.sendall(relpath.encode() + b'\n')
                sock.sendall(str(filesize).encode() + b'\n')
                data = f.read(chunk_size)
                while data:
                    sock.sendall(data)
                    data = f.read(chunk_size)

    # function to receive data of servers folder while client has already ID
    def receive_folder(self, sock, local_path):
        with sock, sock.makefile('rb') as clientfile:
            while True:
                raw = clientfile.readline()
                # no more files, server closed connection.
                if not raw: break
                # TODO: change "empty dirs:"
                # handle receiving also the empty folders
                if raw.strip().decode() == "empty dirs:":
                    while True:
                        raw = clientfile.readline()
                        if not raw:
                            break
                        dir_name = raw.strip().decode()
                        dir_path = os.path.join(local_path, dir_name)
                        os.makedirs(dir_path, exist_ok=True)
                else:
                    filename = raw.strip().decode()
                    length = int(clientfile.readline())

                    path = os.path.join(local_path, filename)
                    os.makedirs(os.path.dirname(path), exist_ok=True)

                    # Read the data in chunks so it can handle large files.
                    with open(path, 'wb') as f:
                        while length:
                            chunk = min(length, chunk_size)
                            data = clientfile.read(chunk)
                            if not data: break
                            f.write(data)
                            length -= len(data)
                        else:  # only runs if while doesn't break and length==0
                            continue
                    # socket was closed early.
                    break

    # function to receive file from server over connection
    def receive_file(self, sock, local_path):
        with sock, sock.makefile('rb') as clientfile:
            sock.sendall(b"ready" + b"\n")
            raw = clientfile.readline()
            if not raw: return  # no more files, server closed connection.

            filename = raw.strip().decode()
            length = int(clientfile.readline())

            filename = os.path.basename(filename)
            path = os.path.join(local_path, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Read the data in chunks so it can handle large files.
            with open(path, 'wb') as f:
                self.LAST_UPDATE_MADE = path
                while length:
                    chunk = min(length, chunk_size)
                    data = clientfile.read(chunk)
                    if not data: break
                    f.write(data)
                    length -= len(data)

    # function to send folder recursively to server in new connection
    def send_folder(self, source_path, receiver):
        time.sleep(0.5)
        with receiver:
            for path, dirs, files in os.walk(source_path):
                for file in files:
                    filename = os.path.join(path, file)
                    relpath = os.path.relpath(filename, source_path)
                    filesize = os.path.getsize(filename)

                    with open(filename, 'rb') as f:
                        receiver.sendall(relpath.encode() + b'\n')
                        receiver.sendall(str(filesize).encode() + b'\n')

                        # Send the file in chunks so large files can be handled.
                        while True:
                            data = f.read(chunk_size)
                            if not data: break
                            receiver.sendall(data)
            # for empty folders
            receiver.sendall("empty dirs:".encode() + b'\n')
            for root, dirs, files in os.walk(source_path):
                for directory in dirs:
                    d = os.path.join(root, directory)
                    if not os.listdir(d):
                        d = os.path.relpath(d, source_path)
                        receiver.sendall(d.encode() + b'\n')


# start of program
if __name__ == '__main__':
    client = Client()
    client.start()