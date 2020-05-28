# All-In-One Network Utility
AIONet was built as a multipurpose tool to replace netcat. Written in Python3, AIONet offers features like reverse shell spawning, file upload and file download.
This tool was written as a replacement for (netutil)[https://github.com/aarole/netutil]. A detailed explanation of the differences between the two can be found at the end of this document.

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
