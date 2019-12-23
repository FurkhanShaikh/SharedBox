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

file_list = []  # files list if client directory
new_files_list = []  # for monitoring purpose
sent_files = {}
received_files = {}
next_file = []  # next files to send to server
username = ['abcd']  # username of client. "abcd" is placeholder

# http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
# the following class is from the above link
# this class uses Watchdog Package to monitor changes in files/directory
class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.txt"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        print(os.path.basename(event.src_path), event.event_type,
              time.time() - os.path.getmtime(event.src_path))  # print now only for degug
        if event.event_type == "modified":
            modifiedfiles_send_port(os.path.basename(event.src_path), os.path.getmtime(event.src_path))

    def on_modified(self, event):
        self.process(event)

# To detect modified file and modification time to update
def modifiedfiles_send_port(modifiedfilename, modifiedtime):
    # current_time= time.time()
    # first check if it old file
    if ((modifiedfilename in sent_files.keys()) and (modifiedfilename in received_files.keys())):
        sent_time = sent_files[modifiedfilename]
        recvd_time = received_files[modifiedfilename]
        if (sent_time > recvd_time):  # check if it was sent by client recently
            if (modifiedtime - sent_time) > 10:  # check if it was modified after 10 sec of sending
                if modifiedfilename not in next_file:
                    next_file.append(modifiedfilename)
                print("modified in both...sent recent")
                print("next_file",next_file)
                client_socket.send(bytes("{update}", "utf8"))
                return
        else:
            if (modifiedtime - recvd_time) > 10:  # check if it was modifed after 10 sec of receiving
                if modifiedfilename not in next_file:
                    next_file.append(modifiedfilename)
                print("modified in both...recvd recent")
                print("next_file",next_file)
                client_socket.send(bytes("{update}", "utf8"))
                return
    if modifiedfilename in sent_files.keys():  # if it is this client's file
        sent_time = sent_files[modifiedfilename]  # last sent time
    else:
        sent_time = 0

    if modifiedfilename in received_files.keys():  # if it is received from other client
        recvd_time = received_files[modifiedfilename]  # last received time of file
    else:
        recvd_time = 0

    if (sent_time == 0 and recvd_time == 0):
        print(modifiedfilename + " is a new file")
        return  # files_monitoring function handles new files

    if (sent_time > recvd_time):  # check if it was sent by client recently
        if (modifiedtime - sent_time) > 10:  # check if it was modified after 10 sec of sending
            if modifiedfilename not in next_file:
                next_file.append(modifiedfilename)
            print("modified in recent sent")
            print("next_file",next_file)
            client_socket.send(bytes("{update}", "utf8"))
            return
    else:
        if (modifiedtime - recvd_time) > 10:  # check if it was modifed after 10 sec of receiving
            if modifiedfilename not in next_file:
                next_file.append(modifiedfilename)
            print("modified in recent recvd")
            print("next_file",next_file)
            client_socket.send(bytes("{update}", "utf8"))
            return



# method always  on to check new files in client directory
def files_monitoring(folder):  # folder argument is username (client directory)
    """Checks for new files in client's directory"""
    # https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    while True:
        arr = os.listdir(folder)
        newfile = [x for x in arr if x not in new_files_list]
        if len(newfile) != 0:
            if newfile[0] not in next_file:
                next_file.append(newfile[0])
            print("next_file", next_file[0])
            client_socket.send(bytes("{file}", "utf8"))
        time.sleep(30)  # very important to allow file access. Can be less or more but should be there


# checks for new files on server and gets the list of files
def check_files():
    client_socket.send(bytes("LIST_OK", "utf8"))  # let server know client ready to recieve file list
    file_count = []  # to store indexes
    counter = 0  # counter to set index values
    print("In check files, filelist:", file_list)
    while True:
        msg = client_socket.recv(BUFSIZ).decode("utf8")
        print(msg)
        if msg != "{EOL}":  # check if End of list reached
            if msg in file_list:  # filename check if exists on client
                counter += 1  # index value for server
            else:
                file_count.append(counter)
                counter += 1
            client_socket.send(bytes("OK", "utf8"))
        else:
            if len(file_count) == 0:
                client_socket.send((bytes("ALL_OK", "utf8")))  # all files on client
                print("send ALL_OK")
            else:
                client_socket.send(bytes("NUM", "utf8"))  # start sending index values
                print("Send NUM")
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
    f = open(username[0] + "/" + filename, 'wb+')
    while True:
        msg = client_socket.recv(BUFSIZ)
        if msg != bytes("{EOF}", "utf8"):  # continue loop until End of file received
            f.write(msg)
            client_socket.send(bytes("OK", "utf8"))
        else:
            f.close()
            print("Done Receiving")
            if filename not in file_list:
                file_list.append(filename)  # add filename to client's list of files
            if filename not in new_files_list:
                new_files_list.append(filename)
            received_files[filename] = time.time()  # set file receive time
            msg = "Received file from server: " + filename
            msg_list.insert(tkinter.END, msg)  # update on GUI
            break


# method to send files from client directory
def send_file():
    client_socket.send(bytes(next_file[0], "utf8"))
    msg = client_socket.recv(BUFSIZ).decode("utf8")  # receive FILENAME OK
    print(msg)
    f = open(str(username[0] + '/' + next_file[0]), 'rb')
    print('Sending:', next_file[0])
    while True:
        l = f.read(BUFSIZ)
        if (l):
            client_socket.send(l)
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            print(msg)
        else:
            client_socket.send(bytes("{EOF}", "utf8"))
            f.close()
            print("Done Sending")
            print("next_file", next_file)
            sent_files[next_file[0]] = time.time()  # set time of sending
            if next_file[0] not in file_list:
                file_list.append(next_file[0])  # add to client's list of files
            if next_file[0] not in new_files_list:
                new_files_list.append(next_file[0])
            next_file.remove(next_file[0])  # update next file to send if any
            print("next_file", next_file)
            break


def receive():  # always on method to receive incoming messages
    """Handles receiving of messages."""
    while True:
        msg = client_socket.recv(BUFSIZ).decode("utf8")
        print(msg)
        if msg == "FILE OK":  # server ready to recieve file
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
            continue
        elif msg == "INVALIDATE":  # invalidation notice from server
            client_socket.send(bytes("{invalidate}", "utf8"))
            invalid_file = client_socket.recv(BUFSIZ).decode("utf8")
            client_socket.send(bytes("whoupdated", "utf8"))
            fileupdater = client_socket.recv(BUFSIZ).decode("utf8")
            if fileupdater != username[0]:
                print("invalid file:", invalid_file)
                msg_list.insert(tkinter.END, invalid_file+" file invalidated by "+fileupdater+" ! Requesting update")
                file_list.remove(invalid_file)  # remove from client's filelist to receive update from server
                print(file_list)
                # now to receive the file ping server to check filelist
                client_socket.send(bytes("{chk_files}", "utf8"))
            else:
                continue

        else:  # update on GUI
            msg_list.insert(tkinter.END, msg)
            # now  check for new files on server
            if("has left the server" in msg):
                continue
            client_socket.send(bytes("{chk_files}", "utf8"))


# form connection by setting username before sending receiving files
def send(event=None):  # event is passed by binders.
    """Handles sending of username and setting up connection."""
    msg = my_msg.get()  # take username from client window
    username[0] = msg  # set username in global list for easy access
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
        files_monitoring_thread = Thread(target=files_monitoring, args=(username[0],)).start()
        # http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
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
BUFSIZ = 1024  # TCP window size
ADDR = (HOST, PORT)  # address tuple used by socket
client_socket = socket(AF_INET, SOCK_STREAM)  # creating tcp socket

client_socket.connect(ADDR)  # Connect to server

tkinter.mainloop()  # Starts GUI execution.
