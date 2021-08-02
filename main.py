import multiprocessing
from multiprocessing import Process, Event, Lock
from threading import Thread
from signal import signal, SIGTERM
from time import sleep
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler


ll = [0]
h = [0]
def log(*args, **kwargs):
	with ll[0]:
		print(*args, **kwargs)


def reg_signal(name, event):
	def callback(*args, **kwargs):
		log(f"Caught SIGTERM in {name}: {args}, {kwargs}")
		if event:
			event.set()
	signal(SIGTERM, callback)
	

def counter(_ll, name, event):
	print("LOOOOOOOOOOCK", _ll)
	ll[0] = _ll
	reg_signal(name, event)
	i = 0
	while True:
		sleep(1)
		i += 1
		log(name, ">", i)


def stopper(event):
	event.wait()
	log("GOT EVENT")
	h[0]._BaseServer__shutdown_request = True
	log("SET SHUTDOWN FLAG")


def main(_ll):
	ll[0] = _ll
	event=Event()
	processes = []
	for i in range(1):
		p = Process(target=counter, args=(ll[0], "Process " + str(i + 1), None), daemon=True)
		processes.append(p)
		p.start()
	reg_signal("main", event)
	HOST = "0.0.0.0"
	PORT = int(os.getenv("PORT", 80))
	httpd = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
	h[0] = httpd
	Thread(target=stopper, args=(event,)).start()
	httpd.serve_forever()
	log("EXITING")
	for p in processes:
		p.kill()
	log("EXITED")
	

if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")
	ll[0]=Lock()
	log(f"START METHOD = {multiprocessing.get_start_method()}")
	Process(target=main, args=(ll[0],)).start()
	sleep(90)
	log("ME")
