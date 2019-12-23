# NAME : MOHAMMED FURKHAN SHAIKH
# STUDENT ID: 1001722637

# Took base code from below link and started working on it
###https://medium.com/swlh/lets-write-a-chat-app-in-python-f6783a9ac170

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import os
import errno

clients = {}  # dictionary to save clients
addresses = {}  # save clients addresses
usernames = []  # current list of connected usernames
HOST = ''  # empty for localhost
PORT = 33000  # arbitrary port number between 1024 and 65000
BUFSIZ = 1024  # TCP window size
ADDR = (HOST, PORT)  # address tuple used by socket bind method
SERVER = socket(AF_INET, SOCK_STREAM)
"""AF_INET is the address family of the socket
here it is Internet family (IPv4).
SOCK_STREAM is the stream socket ie with continuous flow (TCP)."""
SERVER.bind(ADDR)  # Server socket is binded/linked to localhost and portnumber

FILES_ON_SERVER = []  # list of files currently on server
files_to_send={}  # dictionary files to send to each clients

# method to accept incoming connections. Always on
def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:  # keep running untill closed manually
        try:
            client, client_address = SERVER.accept()
            print("%s:%s has connected." % client_address)
            flag = True  # flag in case connection closed from client
            while True:  # retry for username conflict
                username = client.recv(BUFSIZ).decode("utf8")
                if username == "{quit}":  # check if username is recieved or quit message
                    client.send(bytes("ERROR1", "utf8"))
                    client.close()
                    flag = False
                    break
                elif username in clients.values():  # check username is existing or not
                    client.send(bytes("ERROR1", "utf8"))
                    continue
                else:
                    break
            if flag == False:
                continue
        except:
            continue
        msg_list.insert(tkinter.END, username+" has joined the server!")  # add message on GUI
        clients[client] = username  # save username
        addresses[client] = client_address  # save client ip and port
        Thread(target=handle_client, args=(client,)).start()  # start new thread for messages and files for each client

# method separate for each client to send and recieve messages/files
def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    name = clients[client]  # username as name
    welcome = 'Welcome %s! ' % name
    client.send(bytes(welcome, "utf8"))
    msg = "%s has joined the server!" % name
    print(msg)
    broadcast(bytes(msg, "utf8"))  # display to all clients
    msg = " Connected clients:"
    for cc in clients.keys():
        msg = msg + ' ' + clients[cc]
    broadcast(bytes(msg,"utf8"))
    msg_list.insert(tkinter.END, msg)  # add message on GUI
    while True:
        try:
            msg = client.recv(BUFSIZ).decode("utf8")
            print("in handle loop: ", msg)
            if msg == "{file}":  # if client wants to send file
                recieve_file(client)

            elif msg == "{chk_files}":  # if client wants to check files on server
                check_files(client)

            elif msg == "{DOWN}":  # to send files to client
                send_file(client)

            elif msg == "{quit}":  # if client wants to exit
                client.close()
                msg_list.insert(tkinter.END, "%s has left the server." % name)
                del clients[client]
                if (len(clients.keys()) != 0):
                    broadcast(bytes("%s has left the server." % name, "utf8"))
                    msg = "connected clients:"
                    for cc in clients.keys():
                        msg = msg + ' ' + clients[cc]
                    broadcast(bytes(msg, "utf8"))
                    msg_list.insert(tkinter.END, msg)  # add message on GUI
                break
        except:
            pass

# this method sends list of files on server to check which of them client has
def check_files(client):  # argument is client socket
    if len(FILES_ON_SERVER) > 0:  # check if server got any files # no client has send files
        client.send(bytes("SOL", "utf8"))  # start of List
        msg = client.recv(BUFSIZ).decode("utf8")
        if msg == "LIST_OK":  # see if client ready to recieve list of files
            for i in range(len(FILES_ON_SERVER)):
                client.send(bytes(FILES_ON_SERVER[i], "utf8"))  # send file names one by one
                msg = client.recv(BUFSIZ).decode("utf8")  # blocking recv function
            client.send(bytes("{EOL}", "utf8"))   # End of list
        msg = client.recv(BUFSIZ).decode("utf8")
        if msg == "ALL_OK":  # client has all files
            return
        elif msg == "NUM":  # client sends index of files
            files_to_send[client] = []
            client.send(bytes("OK", "utf8"))
            while True:
                msg = client.recv(BUFSIZ).decode("utf8")
                if msg != "EOL":  # end of list
                    files_to_send[client].append(FILES_ON_SERVER[int(msg)])  # dictionary to save file names
                    client.send(bytes("OK", "utf8"))
                else:
                    break

# method to send files to client
def send_file(client): # argument is client socket
    if len(files_to_send.keys()) != 0:
        if len(files_to_send[client]) != 0:
            client.send(bytes("FILE", "utf8"))
            msg = client.recv(BUFSIZ).decode("utf8")  # OK
            filename = files_to_send[client][0]
            client.send(bytes(filename, "utf8"))
            msg = client.recv(BUFSIZ).decode("utf8")
            f = open("server_directory/" + filename, 'rb+')
            while True:
                l = f.read(BUFSIZ)
                # print(l)
                if l:
                    client.send(l)
                    msg = client.recv(BUFSIZ).decode("utf8")
                    # print(msg)
                else:
                    client.send(bytes("{EOF}", "utf8"))
                    f.close()
                    files_to_send[client].remove(filename)
                    msg_list.insert(tkinter.END, filename+" sent to "+ clients[client])
                    print("Done Sending")
                    break
        else:
            client.send(bytes("NO_FILE", "utf8"))
    else:
        client.send(bytes("NO_FILE", "utf8"))

# method to recieve files from clients
def recieve_file(client):  # argument is client socket
    client.send(bytes("FILE OK", "utf8"))
    filename = client.recv(BUFSIZ).decode("utf8")
    print("receiving file: ", filename)
    client.send(bytes("FILENAME OK", "utf8"))
    f = open("server_directory/" + filename, 'wb+')
    while True:
        msg = client.recv(BUFSIZ)
        if msg != bytes("{EOF}", "utf8"):
            f.write(msg)
            client.send(bytes("OK", "utf8"))
        else:
            f.close()
            print("Done Receiving")
            FILES_ON_SERVER.append(filename)  # update file list of server
            print(FILES_ON_SERVER)  # update file list of server
            msg_list.insert(tkinter.END, clients[client] + ": uploaded "+filename)  # display on GUI
            broadcast(bytes("uploaded file " + filename, "utf8"), clients[client] + ": ")  # notify everyone
            break

# method to send messages to all clients
def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    for sock in clients.keys():
        sock.send(bytes(prefix, "utf8") + msg)

# for closing window and program
def on_closing(event=None):
    """This function is to be called when the window is closed."""
    try:
        msg = "{quit}"
        client_socket.send(bytes(msg, "utf8"))
        client_socket.close()
        top.quit()
        os._exit(1)
    except:
        top.destroy()
        os._exit(1)

if __name__ == "__main__":
    top = tkinter.Tk()  # top is the main or root window
    top.title("Shared Box Server")

    messages_frame = tkinter.Frame(top)
    my_msg = tkinter.StringVar()  # For the messages to be sent.
    my_msg.set("")
    scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.

    msg_list = tkinter.Listbox(messages_frame, height=15, width=45, yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    msg_list.pack(side=tkinter.LEFT, fill=tkinter.X)
    msg_list.pack()
    messages_frame.pack()

    exit_button = tkinter.Button(top, text="EXIT", command=on_closing)
    exit_button.pack()

    top.protocol("WM_DELETE_WINDOW", on_closing)

    # check and create server directory to store files
    try:
        os.makedirs("server_directory")  # make client directory by username
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    SERVER.listen(5)  # Listens for 5 connections at max.
    print("Waiting for connection...")
    msg_list.insert(tkinter.END, "Waiting for clients to connect")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()  # Starts the infinite loop.
    tkinter.mainloop()  # Starts GUI execution.
    ACCEPT_THREAD.join()  # wait for thread to complete
    SERVER.close()
