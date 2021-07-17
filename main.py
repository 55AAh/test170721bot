import os
import socket


def main():
    print(os.environ)
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 80))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    print(f"LISTENING ON {HOST}:{PORT}")
    sock.listen(10)
    while True:
        (client_sock, address) = sock.accept()
        print(f"CONNECTION: {address}")
        data = client_sock.recv(10240)
        data = data.decode("utf-8")
        response = "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n"
        response = response.encode("utf-8")
        client_sock.send(response)
        client_sock.close()
        print(f"RECEIVED:\n{data}")
        print(f"CLIENT SERVED")


if __name__ == '__main__':
    main()
