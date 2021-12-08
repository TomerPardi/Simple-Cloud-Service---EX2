import os

chunk_size = 1_000_000

def send_file(sock, relpath, filepath):
    filesize = os.path.getsize(filepath)
    with open(filepath, 'rb') as f:
        sock.sendall(relpath.encode() + b'\n')
        sock.sendall(str(filesize).encode() + b'\n')
        # Send the file in chunks so large files can be handled.
        while True:
            data = f.read(chunk_size)
            if not data: break
            sock.sendall(data)

# TODO: look like this function can handle receiving file also. if yes, we need to give it client's path in server.
def receive_folder(sock, local_path):
    with sock, sock.makefile('rb') as clientfile:
        while True:
            raw = clientfile.readline()
            if not raw: break  # no more files, server closed connection.

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

# TODO: be aware its not like in data!!!!!!! its for receive files
def receive_file(sock, local_path):
    print("here2")
    with sock, sock.makefile('rb') as clientfile:
        sock.sendall(b"ready")
        while True:
            raw = clientfile.readline()
            print(raw)
            if not raw: break  # no more files, server closed connection.

            filename = raw.strip().decode()
            print(filename)
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
