from multiprocessing import Process
from signal import signal, SIGTERM
from time import sleep
import os
import socket


def rs(n):
	def sc():
		print(f"Caught SIGTERM in {n}")
	signal(SIGTERM, sc)


def bs():
	HOST = "0.0.0.0"
	PORT = int(os.getenv("PORT", 80))
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((HOST, PORT))
	print(f"LISTENING ON {HOST}:{PORT}")
	sock.listen(10)
	

def main():
	Process(target=bs).start()
	for i in range(5):
		Process(target=pt, args=("Process " + str(i + 1),)).start()
	rs("Main")
	i = 0
	while True:
		sleep(1)
		i += 1
		print(i)


def pt(i):
	rs(str(i))


if __name__ == '__main__':
	main()
