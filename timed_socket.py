from time import time
from socket import timeout


class TimedSocket:
    BUFFER_SIZE = 1024
    TIMEOUT = 1

    def __init__(self, socket):
        self.socket = socket
        self.time_after = time()
        self.time_end = self.time_after + self.TIMEOUT
        self.received_bytes = self.yield_received_bytes()

    def receive_part(self):
        try:
            if self.time_after > self.time_end:
                raise timeout
            self.socket.settimeout(max(self.time_end - self.time_after, 0.1))
            data = self.socket.recv(self.BUFFER_SIZE)
            self.time_after = time()
            return data
        except timeout:
            raise timeout(73, f"Socket operation timed out ({self.TIMEOUT}s)")

    def yield_received_bytes(self):
        while True:
            yield from self.receive_part()

    def receive_until(self, terminator):
        terminator = terminator[0]
        data = bytearray()
        for byte in self.received_bytes:
            if byte == terminator:
                return data
            data.append(byte)

    def receive_num(self, count):
        data = bytearray()
        while len(data) < count:
            data.append(next(self.received_bytes))
        return data

    def send(self, data):
        try:
            while self.time_after <= self.time_end:
                sent_count = self.socket.send(data[:self.BUFFER_SIZE])
                data = data[sent_count:]
                if len(data) == 0:
                    return
                self.time_after = time()
            raise timeout
        except timeout:
            raise timeout(self.TIMEOUT)
