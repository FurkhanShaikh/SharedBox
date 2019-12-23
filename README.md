# SharedBox

A prototype project for sharing files between clients. The clients connect to server and have their own directory. The user at client adds a file to the client's directory. The file get uploaded to the server and then is shared with the connected clients. File is added by the native file manager of the client. This project relies on Multithreading and uses sockets for data transfer.

NB: This project was developed and tested on windows OS only.

# Branch Update
When a file is updated in a client directory, it is detected by that client's program. The client sends updated filename to server and from server to other clients. The program then uploads(pushes) the updated file to remaining clients.

The program uses [WatchDog](https://github.com/gorakhargosh/watchdog) package for detection of updated file.

## Getting Started

The GUI is created using tkinter library and other libraries include os, thread and time.

### Prerequisites

Python 3

## Deployment

Server:
```
Python server.py
```

Clients:
Run following command on different shells for more client instances (tested for 3).
```
Python client.py
```
In the GUI window set username. This username will be the client's directory name.

## Output

![alt text](Sample_OUTPUT.jpg)

## Authors

* **Furkhan Shaikh** - *Initial work* - [FurkhanShaikh](https://github.com/FurkhanShaikh)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to anyone whose code was used
* My professor Chance Eary at UTA

