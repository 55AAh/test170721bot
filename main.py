import multiprocessing
from multiprocessing import Process, Event, Lock
from threading import Thread
from signal import signal, SIGTERM
from time import sleep
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import selectors
if hasattr(selectors, 'PollSelector'):
	_ServerSelector = selectors.PollSelector
else:
	_ServerSelector = selectors.SelectSelector
print(_ServerSelector)


ll = [0]
h = [0]
def log(*args, **kwargs):
	with ll[0]:
		print(*args, **kwargs)


def reg_signal(name, event):
	def callback(*args, **kwargs):
		log(f"Caught SIGTERM in {name}: {args}, {kwargs}")
		if event:
			log(f"Setting event in {name}...")
			event.set()
			log(f"Event was set in {name}...")
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
	h[0].shutdown()
	log("KILLED WEB")


def serve_forever(self, poll_interval=0.5):
	"""Handle one request at a time until shutdown.

	Polls for shutdown every poll_interval seconds. Ignores
	self.timeout. If you need to do periodic tasks, do them in
	another thread.
	"""
	self._BaseServer__is_shut_down.clear()
	try:
		# XXX: Consider using another file descriptor or connecting to the
		# socket to wake this up instead of polling. Polling reduces our
		# responsiveness to a shutdown request and wastes cpu at all other
		# times.
		log("1111111111111111")
		with _ServerSelector() as selector:
			selector.register(self, selectors.EVENT_READ)
			log("22222222222222222")
			while not self._BaseServer__shutdown_request:
				log("3333333333333333")
				ready = selector.select(poll_interval)
				log("444444444444444")
				# bpo-35017: shutdown() called during select(), exit immediately.
				if self._BaseServer__shutdown_request:
					break
				if ready:
					self._handle_request_noblock()

				self.service_actions()
			log("555555555555555")
	finally:
		self._BaseServer__shutdown_request = False
		self._BaseServer__is_shut_down.set()
	log("66666666666666")


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
	httpd.serve_forever = serve_forever
	Thread(target=stopper, args=(event,)).start()
	httpd.serve_forever(httpd)
	log("EXITING")
	for p in processes:
		p.kill()
	log("EXITED")
	

if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")
	ll[0]=Lock()
	log(f"START METHOD = {multiprocessing.get_start_method()}")
	p = Process(target=main, args=(ll[0],))
	p.start()
	sleep(10)
	log("SD HTTPD")
	p.terminate()
	p.join()
	log("ME")
