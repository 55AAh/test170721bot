from logging import log, INFO, ERROR
import socket
from time import time
from kiss_headers import parse_it
import json


class Server:
    LISTEN_CONN = 10
    BUFSIZE = 10
    TIMEOUT = 1

    def __init__(self, host, port):
        self.host, self.port = host, port
        self._stop = False

    def start(self):
        log(INFO, "\tSTARTING SERVER...")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen(self.LISTEN_CONN)
        log(INFO, f"\tSERVER IS LISTENING ON {self.host}:{self.port}, {self.LISTEN_CONN} CONN....")
        self.handle_webhooks(server_sock)

    def handle_webhooks(self, server_sock):
        while not self._stop:
            connection = server_sock.accept()
            updates = self.receive_http_json(connection)
            if updates is not None:
                log(INFO, f"HANDLED WEBHOOK FROM {connection[1]}, UPDATES:\n{updates}")

    def send(self, connection, data):
        sock, address = connection

        time_now = time()
        time_end = time_now + self.TIMEOUT

        try:
            while time_now < time_end:
                sock.settimeout(max(time_end - time_now, 0.1))
                try:
                    sent_count = sock.send(data[:self.BUFSIZE])
                except socket.timeout:
                    pass
                else:
                    data = data[sent_count:]
                    if len(data) == 0:
                        return True
                time_now = time()
            raise socket.error(f"Timeout ({self.TIMEOUT})s")
        except socket.error as e:
            log(ERROR, f"Error sending to {address}: {e}")
            try:
                sock.close()
            except socket.error:
                pass
            return None

    def recv_msg(self, connection, parse_header_callback):
        sock, address = connection

        data = b''
        message_size = None
        time_now = time()
        time_end = time_now + self.TIMEOUT

        try:
            while time_now < time_end:
                sock.settimeout(max(time_end - time_now, 0.1))
                try:
                    data += sock.recv(self.BUFSIZE)
                except socket.timeout:
                    pass
                else:
                    if message_size is None:
                        message_size = parse_header_callback(data)
                    if message_size is not None:
                        if len(data) >= message_size:
                            return data
                time_now = time()
            raise socket.error(f"Timeout ({self.TIMEOUT})s")
        except socket.error as e:
            log(ERROR, f"Error receiving message from {address}: {e}")
            try:
                sock.close()
            except socket.error:
                pass
            return None

    def recv_http_body(self, connection):
        content_length = [0]

        def parse_http_headers(data):
            try:
                header, _ = data.split(b"\r\n\r\n")
                content_length[0] = int(parse_it(header).content_length[0])
                return content_length[0] + len(header) + 4
            except (AttributeError, ValueError):
                return None

        msg = self.recv_msg(connection, parse_http_headers)
        if msg is None:
            return None
        _, body = msg.split(b"\r\n\r\n")
        body = body[:content_length[0]]

        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError as e:
            log(ERROR, f"{e}\nBODY:{body}")
            return None

        return body

    def respond_http_200(self, connection):
        self.send(connection,
                  "HTTP/1.0 200 OK\r\n"
                  "Server: BaseHTTP/0.6 Python/3.9.5\r\n"
                  "Date: Sat, 17 Jul 2021 13:18:48 GMT\r\n"
                  "Content-type: text/html\r\n"
                  "\r\n"
                  "OK".encode("utf-8"))
        connection[0].close()

    def receive_http_json(self, connection):
        data = self.recv_http_body(connection)
        if data is None:
            return None

        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            log(ERROR, f"{e}\nDATA:{data}")

        self.respond_http_200(connection)

        return data

