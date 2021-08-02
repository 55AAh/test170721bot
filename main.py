import multiprocessing
from multiprocessing import Process, Event
from threading import Thread
from signal import signal, SIGTERM
from time import sleep
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler


def reg_signal(event, name):
	def callback(*args, **kwargs):
		print(f"Caught SIGTERM in {name}: {args}, {kwargs}")
		event.set()
	signal(SIGTERM, callback)
	

def counter(event, name):
	reg_signal(event, name)
	i = 0
	while True:
		sleep(1)
		i += 1
		print(name, ">", i)


def stopper(event, httpd):
	event.wait()
	httpd.shutdown()


def main():
	event=Event()
	for i in range(5):
		Process(target=counter, args=(event, "Process " + str(i + 1),), daemon=True).start()
	reg_signal(event, "main")
	HOST = "0.0.0.0"
	PORT = int(os.getenv("PORT", 80))
	httpd = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
	Thread(target=stopper, args=(event, httpd)).start()
	httpd.serve_forever()
	print("EXITED")
	

if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")
	print(f"START METHOD = {multiprocessing.get_start_method()}")
	main()
