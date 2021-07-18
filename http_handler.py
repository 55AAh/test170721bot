from timed_socket import TimedSocket


class HttpRequest:
    def __init__(self, method, url, http_version, headers, payload):
        self.method = method
        self.url = url
        self.http_version = http_version
        self.headers = headers
        self.payload = payload


class HttpHandler:
    def __init__(self, socket, address=None):
        self.socket = socket
        self.address = address

    @staticmethod
    def receive_header_lines(timed):
        while True:
            line = timed.receive_until(b'\n').decode("ascii").rstrip('\r')
            if len(line) == 0:
                return
            yield line

    @staticmethod
    def receive_payload(timed, content_length):
        return timed.receive_num(content_length)

    def receive(self):
        timed_socket = TimedSocket(self.socket)

        lines = self.receive_header_lines(timed_socket)
        method, url, http_version = next(lines).split(" ")

        headers = dict()
        for line in lines:
            name, value = line.split(":", 1)
            value = value.lstrip().rstrip('\r')
            headers.setdefault(name, []). append(value)

        content_length = int((headers.get("Content-Length") or [0])[0])
        payload = self.receive_payload(timed_socket, content_length)

        return HttpRequest(method, url, http_version, headers, payload)

    def send_200(self):
        timed_socket = TimedSocket(self.socket)

        timed_socket.send(
            "HTTP/1.0 200 OK\r\n"
            "Server: BaseHTTP/0.6 Python/3.9.5\r\n"
            "Date: Sat, 17 Jul 2021 13:18:48 GMT\r\n"
            "Content-type: text/html\r\n"
            "Content-Length: 2\r\n"
            "\r\n"
            "OK".encode("utf-8"))
