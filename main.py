from threading import Thread
from time import sleep
import requests
import os
from logging import log, ERROR
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
from logger import Logger

h=[None]
s=[False]

def t():
    def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
        server_address = ('0.0.0.0', int(os.getenv("PORT", 80)))
        httpd = server_class(server_address, handler_class)
        h[0]=httpd
        httpd.serve_forever()
    run()

def main():
    Logger("log.txt")
    log(ERROR, "\tSTARTING")
    th=Thread(target=t,args=())
    th.start()
    def sss(signum, frame):
        print(signum, frame)
        h[0].shutdown()
        s[0]=True
    signal.signal(signal.SIGTERM, sss)
    log(ERROR, "\tSTART")
    # sleep(20 * 60)
    log(ERROR, "\tNTF1")
    requests.get("https://test170721.herokuapp.com/notify")
    # sleep(20 * 60)
    log(ERROR, "\tNTF2")
    requests.get("https://test170721.herokuapp.com/notify")
    i=0
    while not s[0]:
        if i % 1 == 0:
            log(ERROR, i)
        i+=1
        sleep(1)
    th.join()
    log(ERROR, "\tSAVING DATA")
    i=0
    while i < 3:
        log(ERROR, i)
        i += 1
        sleep(1)
    log(ERROR, "DATA SAVED, EXITING")
    return

if __name__ == '__main__':
    main()
