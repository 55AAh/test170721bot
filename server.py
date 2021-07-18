from logging import log, INFO, ERROR
import socket
from http_handler import HttpHandler


class Server:
    LISTEN_CONN = 10

    def __init__(self, host, port):
        self.host, self.port = host, port
        self._stop = False

    def start(self):
        log(INFO, "\tSTARTING SERVER...")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen(self.LISTEN_CONN)
        log(INFO, f"\tSERVER IS LISTENING ON {self.host}:{self.port}, {self.LISTEN_CONN} CONN....")

        while True:
            client_sock, address = server_sock.accept()
            handler = HttpHandler(client_sock, address)
            try:
                request = handler.receive()
                handler.send_200()
                log(INFO, f"\tHANDLED REQUEST FROM {address}:\n"
                          f"{request.method} {request.url} {request.http_version}\n"
                          f"{request.headers}\n"
                          f"{request.payload}")
            except socket.timeout as e:
                log(ERROR, e)



