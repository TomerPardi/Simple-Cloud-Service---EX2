import os

chunk_size = 1_000_000


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


def send_folder(path, receiver):
    with receiver:
        for path, dirs, files in os.walk(path):
            for file in files:
                filename = os.path.join(path, file)
                relpath = os.path.relpath(filename, path)
                filesize = os.path.getsize(filename)

                with open(filename, 'rb') as f:
                    receiver.sendall(relpath.encode() + b'\n')
                    receiver.sendall(str(filesize).encode() + b'\n')

                    # Send the file in chunks so large files can be handled.
                    while True:
                        data = f.read(chunk_size)
                        if not data: break
                        receiver.sendall(data)
