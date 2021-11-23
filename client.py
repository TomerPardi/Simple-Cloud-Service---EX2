import socket
import sys

def receive_files():
    print("blabla")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('', 12345))

ip_address = sys.argv[1]
server_port = sys.argv[2]
path = sys.argv[3]
time = sys.argv[4]
id = ""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip_address, server_port))

try:
    id = sys.argv[5]
    receive_files() # a function to synchronise all the data from server
except:
    s.send(b"no_id")
    id = s.recv(128)




s.close()