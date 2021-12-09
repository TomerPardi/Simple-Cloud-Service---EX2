"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* utils class
* Linux OS support only
"""

import os
import time
chunk_size = 1_000_000


# function to handle file sending over connection
def send_file(sock, relpath, filepath):
    filesize = os.path.getsize(filepath)
    with sock, sock.makefile('rb') as server_file:
        message = server_file.readline().decode().strip()
        with open(filepath, 'rb') as f:
            sock.sendall(relpath.encode() + b'\n')
            sock.sendall(str(filesize).encode() + b'\n')
            # Send the file in chunks so large files can be handled.
            data = f.read(chunk_size)
            while data:
                sock.sendall(data)
                data = f.read(chunk_size)


# function to handle folder receiving over connection
def receive_folder(sock, local_path):
    with sock, sock.makefile('rb') as clientfile:
        while True:
            raw = clientfile.readline()
            if not raw: break  # no more files, server closed connection.
            # TODO: change "empty dirs:"
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


# function to handle file receiving over connection
def receive_file(sock, local_path):
    with sock, sock.makefile('rb') as clientfile:
        sock.sendall(b"ready" + b"\n")
        while True:
            raw = clientfile.readline()
            if not raw: break  # no more files, server closed connection.

            filename = raw.strip().decode()
            length = int(clientfile.readline())

            filename = os.path.basename(filename)
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


# function to handle send a folder over connection
def send_folder(source_path, receiver):
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
        # TODO: change name "empty dirs:"
        receiver.sendall("empty dirs:".encode() + b'\n')
        for root, dirs, files in os.walk(source_path):
            for directory in dirs:
                d = os.path.join(root, directory)
                if not os.listdir(d):
                    d = os.path.relpath(d, source_path)
                    receiver.sendall(d.encode() + b'\n')