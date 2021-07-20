from threading import Thread
from time import sleep
import requests
import os
from logging import log, ERROR, INFO
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
from logger import Logger
import psycopg2

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
    log(INFO, "\tACQUIRING LOCK")
    DATABASE_URL = os.environ['DATABASE_URL']
    db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    db_curr = db_conn.cursor()
    while True:
        db_curr.execute("SELECT * FROM lock")
        if len(db_curr.fetchall()) == 0:
            break
        sleep(1)
    db_curr.execute("INSERT INTO lock VALUES (CURRENT_DATE)")
    db_conn.commit()
    log(INFO, "\tLOCK ACQUIRED, STARTING")
    th=Thread(target=t,args=())
    th.start()
    def sss(signum, frame):
        print(signum, frame)
        requests.get("https://test170721.herokuapp.com/notify")
        i = 0
        while i < 10:
            log(INFO, "\tSELF_NOTIFY "+str(i))
            sleep(1)
        h[0].shutdown()
        s[0]=True
    signal.signal(signal.SIGTERM, sss)
    log(INFO, "\tSTART")
    # sleep(20 * 60)
    # log(INFO, "\tNTF1")
    # requests.get("https://test170721.herokuapp.com/notify")
    # sleep(20 * 60)
    # log(INFO, "\tNTF2")
    # requests.get("https://test170721.herokuapp.com/notify")
    i=0
    while not s[0]:
        if i % 1 == 0:
            log(INFO, i)
        i+=1
        sleep(1)
    th.join()
    log(INFO, "\tSAVING DATA")
    i=0
    while i < 10:
        log(INFO, "\tSAVING DATA "+str(i))
        i += 1
        sleep(1)
    log(INFO, "DATA SAVED, EXITING")
    db_curr.execute("DELETE FROM lock")
    db_conn.commit()
    return

if __name__ == '__main__':
    main()
