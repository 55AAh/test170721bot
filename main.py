import multiprocessing
from multiprocessing import Process
from signal import signal, SIGTERM
from time import sleep
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler


h=[0]


def rs(n):
	def sc(*args, **kwargs):
		print(f"Caught SIGTERM in {n}: {args}, {kwargs}")
		h=[0].shutdown()
	signal(SIGTERM, sc)
	

def ctr():
	i = 0
	while True:
		sleep(1)
		i += 1
		print(i)
	
	
def main():
	for i in range(5):
		Process(target=pt, args=("Process " + str(i + 1),), daemon=True).start()
	rs("Main")
	HOST = "0.0.0.0"
	PORT = int(os.getenv("PORT", 80))
	httpd = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
	h[0]=httpd
	Process(target=ctr, daemon=True).start()
	httpd.serve_forever()
	print("EXITED")
	

def pt(n):
	i = 0
	while True:
		sleep(1)
		i += 1
		print(n, ">", i)

if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")
	print(f"START METHOD = {multiprocessing.get_start_method()}")
	main()
