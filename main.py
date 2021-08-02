from multiprocessing import Process
from signal import signal, SIGTERM
from time import sleep
import os
import socket


def rs(n):
	def sc():
		print(f"Caught SIGTERM in {n}")
	signal(SIGTERM, sc)
	

def ctr():
	i = 0
	while True:
		sleep(1)
		i += 1
		print(i)
	
	
def main():
	for i in range(5):
		Process(target=pt, args=("Process " + str(i + 1),)).start()
	rs("Main")
	HOST = "0.0.0.0"
	PORT = int(os.getenv("PORT", 80))
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((HOST, PORT))
	Process(target=ctr).start()
	sock.listen()
	print(f"LISTENING ON {HOST}:{PORT}")


def pt(i):
	rs(str(i))


if __name__ == '__main__':
	main()
