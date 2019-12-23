# NAME : MOHAMMED FURKHAN SHAIKH

# Took base code from below link and started working on it
###https://medium.com/swlh/lets-write-a-chat-app-in-python-f6783a9ac170

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import os
import errno
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import random

file_list = []  # files list of client
next_file = []  # next files to send to server
username = ['abcd']  # username of client. "abcd" is placeholder
sent_files = {}
received_files = {}
participants={}
addresses={}
deletedfile=['abcd']
deletebyotherclient = [0]


# http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
# the following class is from the above link
# this class uses Watchdog Package to monitor changes in files/directory
class MyHandler(PatternMatchingEventHandler):
    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """

    def on_created(self, event):
        print(f"{event.src_path} has been created!")
        createdfile = os.path.basename(event.src_path)
        if (createdfile in sent_files.keys() or createdfile in received_files.keys()):
            print(createdfile +" :Not new file")
            return
        arr = os.listdir(username[0])
        newfile = [x for x in arr if x not in file_list]
        if len(newfile) != 0:
            next_file.append(newfile[0])
            print("next_file", next_file[0])
            client_socket.send(bytes("{file}", "utf8"))
        # self.process(event)

    def on_deleted(self, event):
        print(f"Someone deleted {event.src_path}!")
        deletedfile[0] = os.path.basename(event.src_path)
        if(deletebyotherclient[0]):
            print(deletedfile[0]+" deleted by other client")
            deletebyotherclient[0] = 0
            return
        client_socket.send(bytes("{delete}", "utf8"))

# method always  on to check new files in client directory
def files_monitoring(folder): # folder argument is username (client directory)
    """Checks for new files in client's directory"""
    # https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    while True:
        arr = os.listdir(folder)
        newfile = [x for x in arr if x not in file_list]
        if len(newfile) != 0:
            next_file.append(newfile[0])
            print("next_file", next_file[0])
            client_socket.send(bytes("{file}", "utf8"))
        time.sleep(30)  # very important to allow file access. Can be less or more but should be there

# checks for new files on server and gets the list of files
def check_files():
    client_socket.send(bytes("LIST_OK", "utf8"))  # let server know client ready to recieve file list
    file_count = []  # to store indexes
    counter = 0  # counter to set index values
    while True:
        msg = client_socket.recv(BUFSIZ).decode("utf8")
        print(msg)
        if msg != "{EOL}":  # check if End of list reached
            if msg in file_list:
                counter += 1
            else:
                file_count.append(counter)
                counter += 1
            client_socket.send(bytes("OK", "utf8"))
        else:
            if len(file_count) == 0:
                client_socket.send((bytes("ALL_OK", "utf8")))  # all files on client
            else:
                client_socket.send(bytes("NUM", "utf8"))  # start sending index values
                client_socket.recv(BUFSIZ).decode("utf8")  # OK
                for i in range(len(file_count)):
                    client_socket.send(bytes(str(file_count[i]), "utf8"))
                    client_socket.recv(BUFSIZ).decode("utf8")
                client_socket.send(bytes("EOL", "utf8"))  # end of list
            break
    if len(file_count) > 0:
        client_socket.send(bytes("{DOWN}", "utf8"))  # ready to recieve new files from server
    return

# method to receive files from server
def receive_file():
    client_socket.send(bytes("OK", "utf8"))
    filename = client_socket.recv(BUFSIZ).decode("utf8")
    print("receiving file: ", filename)
    client_socket.send(bytes("FILENAME OK", "utf8"))
    received_files[filename] = time.time()
    f = open(username[0] + "/" + filename, 'wb+')
    while True:
        msg = client_socket.recv(BUFSIZ)
        if msg != bytes("{EOF}", "utf8"):  # continue loop until End of file received
            f.write(msg)
            client_socket.send(bytes("OK", "utf8"))
        else:
            f.close()
            print("Done Receiving")
            file_list.append(filename)  # add filename to client's list of files
            msg = "Received file from server: " + filename
            msg_list.insert(tkinter.END, msg)  # update on GUI
            break

# method to send files from client directory
def send_file():
    client_socket.send(bytes(next_file[0], "utf8"))
    msg = client_socket.recv(BUFSIZ).decode("utf8")  # receive FILENAME OK
    sent_files[next_file[0]] = time.time()
    f = open(str(username[0] + '/' + next_file[0]), 'rb')
    print('Sending: ', next_file[0])
    while True:
        l = f.read(BUFSIZ)
        if (l):
            client_socket.send(l)
            msg = client_socket.recv(BUFSIZ).decode("utf8")
        else:
            client_socket.send(bytes("{EOF}", "utf8"))
            f.close()
            print("Done Sending")
            file_list.append(next_file[0])  # add to client's list of files
            next_file.remove(next_file[0])  # update next file to send if any
            break

def participant_receive(participantsocket1,participantsocket2):
    countyes=0
    msg = participantsocket1.recv(BUFSIZ).decode("utf8")
    if(msg == 'YES'):
        countyes+=1;
    msg = participantsocket2.recv(BUFSIZ).decode("utf8")
    if (msg == 'YES'):
        countyes += 1;
    if(countyes==2):
        participantsocket1.send(bytes("Commit", "utf8"))
        participantsocket2.send(bytes("Commit", "utf8"))
    else:
        participantsocket1.send(bytes("Abort", "utf8"))
        participantsocket2.send(bytes("Abort", "utf8"))

def handle_participant(partcipant):

    if(file_deleted_flag):
        msg = "{vote_request}"
        broadcast(bytes(msg, "utf8"))

def broadcast(msg):
    for sock in clients.keys():
        sock.send(bytes(prefix, "utf8") + msg)


def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    COORDIPORT = 34000
    CORDIADRR = (HOST, COORDIPORT)
    coordisocket = socket(AF_INET, SOCK_STREAM)
    coordisocket.bind(CORDIADRR)
    coordisocket.listen(5)
    for i in range(2):
        try:
            participant, partcipant_addr = coordisocket.accept()
            print("%s:%s has connected." % partcipant_addr)
            participants[participant] = i
            addresses[participant] = partcipant_addr
            Thread(target=handle_participant, args=(participant,)).start()
        except:
            print("Error in connecting with participants")



def receive():  # always on method to receive incoming messages
    """Handles receiving of messages."""
    while True:
        msg = client_socket.recv(BUFSIZ).decode("utf8")
        print(msg)
        if msg == "DELETE OK":
            client_socket.send(bytes(deletedfile[0],"utf8"))
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            if " has deleted: " in msg:
                msgli=msg.split(" ")
                if(msgli[0] == username[0]):
                    decision1 = random.randint(0,1)
                    decision2 = random.randint(0, 1)
                    time.sleep(3)
                    if(decision1):
                        msg_list.insert(tkinter.END, "First vote: YES")
                    else:
                        msg_list.insert(tkinter.END, "First vote: NO")
                    if (decision2):
                        msg_list.insert(tkinter.END, "Second vote: YES")
                    else:
                        msg_list.insert(tkinter.END, "Second vote: NO")
                    if(decision1 and decision2):
                        client_socket.send(bytes("{DELETE FILE}","utf8"))
                    else:
                        msg_list.insert(tkinter.END, "[ABORTED] File Delete: " + msgli[2])
                        client_socket.send(bytes("{aborted}", "utf8"))
            else:
                msg_list.insert(tkinter.END,msg)
        elif "deletefile" in msg:
            msgli = msg.split(' ')
            if(msgli[0] == username[0]):
                msg_list.insert(tkinter.END, "[COMMITTED] File Delete: "+msgli[2])
            else:
                deletebyotherclient[0] = 1
                os.remove(username[0]+'/'+msgli[2])
                msg_list.insert(tkinter.END, "File Deleted: " + msgli[2])
        elif msg == "FILE OK":  # server ready to recieve file
            send_file_thread = Thread(target=send_file)
            send_file_thread.start()
            send_file_thread.join()

        elif msg == "SOL":  # server sends List of files on server
            check_files_thread = Thread(target=check_files)
            check_files_thread.start()
            check_files_thread.join()

        elif msg == "FILE":  # receive new files from server
            receive_file_thread = Thread(target=receive_file)
            receive_file_thread.start()
            receive_file_thread.join()

        elif msg == "NO_FILE":  # no new files on server
            pass
        else:  # update on GUI
            msg_list.insert(tkinter.END, msg)
            # now  check for new files on server
            client_socket.send(bytes("{chk_files}", "utf8"))

# form connection by setting username before sending receiving files
def send(event=None):  # event is passed by binders.
    """Handles sending of username and setting up connection."""
    msg = my_msg.get()  # take username from client window
    username[0] = msg   # set username in global list for easy access
    client_socket.send(bytes(msg, "utf8"))
    initial_res = client_socket.recv(BUFSIZ).decode("utf8")  # check username available or not
    if initial_res == "ERROR1":
        msg_list.insert(tkinter.END, 'Username not available. Enter new username')  # display to user on client window
    else:
        # https://stackoverflow.com/questions/3842155/is-there-a-way-to-make-the-tkinter-text-widget-read-only
        entry_field.config(state='readonly')  # no more able to change username
        # https://stackoverflow.com/questions/55326738/how-do-you-disable-a-button-when-it-is-clicked?noredirect=1&lq=1
        send_button.config(state=tkinter.DISABLED)  # no more call to send method
        print(initial_res)  # response from server
        msg_list.insert(tkinter.END, "Succesfully connected to Server!")
        # https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
        try:
            os.makedirs(username[0])  # make client directory by username
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        receive_thread = Thread(target=receive).start()  # Thread always on to recieve incoming message
        # thread to check client directory for new files
        # files_monitoring_thread = Thread(target=files_monitoring, args=(username[0],)).start()
        observer = Observer()
        observer.schedule(MyHandler(), path=username[0])
        observer.start()

# method to close window and socket
def on_closing(event=None):
    """This function is to be called when the window is closed."""
    try:
        msg = "{quit}"
        client_socket.send(bytes(msg, "utf8"))
        client_socket.close()  # close socket before exit
        top.quit()  # remove main window
        os._exit(1)
    except:
        top.destroy()  # remove main window
        os._exit(1)  # exit program


top = tkinter.Tk()  # top is the main or root window
top.title("Shared Box")  # title for GUI window

messages_frame = tkinter.Frame(top)  # Separate frame to sit on top of main frame
my_msg = tkinter.StringVar()  # For the messages to be sent. #String variable to insert text
my_msg.set("Type your username here")
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.

# listbox will contain all text messages
msg_list = tkinter.Listbox(messages_frame, height=15, width=65, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.X)
msg_list.pack()  # pack function from tkinter used to display on the window
messages_frame.pack()

user_label = tkinter.Label(top, text="username")
entry_field = tkinter.Entry(top, textvariable=my_msg)
# https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
entry_field.bind("<FocusIn>", lambda args: entry_field.delete('0', 'end'))

user_label.pack(side=tkinter.TOP)
entry_field.bind("<Return>", send)
entry_field.pack(side=tkinter.TOP)  # Entry field to take username input

send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack(side=tkinter.TOP)  # send button to initiate

exit_button = tkinter.Button(top, text="EXIT", command=on_closing)
exit_button.pack(side=tkinter.RIGHT)  # exit button on window

top.protocol("WM_DELETE_WINDOW", on_closing)  # if someone press X on window

HOST = '127.0.0.1'  # local host
PORT = 33000  # Default value set by us
BUFSIZ = 1024   # TCP window size
ADDR = (HOST, PORT)  # address tuple used by socket
client_socket = socket(AF_INET, SOCK_STREAM)  # creating tcp socket

client_socket.connect(ADDR)  # Connect to server

tkinter.mainloop()  # Starts GUI execution.
