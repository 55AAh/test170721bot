import os
import socket


def main():
    HOST = "127.0.0.1"
    PORT = int(os.getenv("PORT", 80))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    print("LISTENING")
    sock.listen(10)
    while True:
        (client_sock, address) = sock.accept()
        print(f"CONNECTION: {address}")
        data = client_sock.recv(10240)
        data = data.decode("utf-8")
        print(f"RECEIVED:\n{data}")
        print(f"CLIENT SERVED")


if __name__ == '__main__':
    main()
