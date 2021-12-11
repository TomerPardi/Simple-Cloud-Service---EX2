# Simple Cloud Service Implementation
## General
- This Python project is an implementation of simple **cloud file backup service**.
- This implementation supports Linux OS **only**.
- The current project was written as part of an assignment we asked to make in _Introduction to Communication Networks_ 
course at Bar Ilan University.

## Logic
Cloud file backup services usually offer customers the option to download client program to
their computer that allows them:
- To select a folder on their computer and synchronize it automatically with a server in any change.
- Use the server to sync client's different computers.

That is, when the program is started, the client uploads to the server the files in the specified folder.
from now on the program monitors any changes that occur in the folder recursively - i.e., even changes
that occur in subfolders and files at any level inside the selected folder. When such a change is detected, 
the program updates the server about the change so that the server will be updated and synchronized accordingly.

The program also knows how to handle updates about changes that have occurred in other computers of
same user. i.e., if the user installed the program on another computer, he selected an empty folder on his computer - to
which the program downloads all the contents of the folder from the server,
Then, as before, the program monitors the folder for any changes and as a result updates the server.

The server can support and handle a lot of clients. i.e., the server can have a lot of registered customers
and each client has a different folder. When the client has finished the connection with the server - the server
moves on to the next connection.

Whenever a client software requests a server to update it on changes, the server must update the client in case of any
changes have been made to the client's folder on another computer.

## Implementation Info
In this program we implement a **TCP server**.
In order to keep track of folder changes, we use **WatchDog python library** that helps us
monitor any changes made in a given path (in our case, path to the folder we want to monitor).
