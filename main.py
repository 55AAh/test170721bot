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
        print(f"\n\tCONNECTION: {address}")
        data = client_sock.recv(10000)
        #data = data.decode("utf-8")
        print(f"\tRECEIVED:\n{data}")
        s = data.decode("utf-8").split("\r\n\r\n")
        if len(s) == 2 and len(s[1]) == 0:
            print("\tNOT FOUND DATA")
            from time import sleep
            sleep(1)
            data = client_sock.recv(10000)
            # data = data.decode("utf-8")
            print(f"\tRECEIVED ADDITIONAL:\n{data}")
        print("\tFOUND DATA")
        response = "HTTP/1.0 200 OK\r\nServer: BaseHTTP/0.6 Python/3.9.5\r\nDate: Sat, 17 Jul 2021 13:18:48 GMT\r\nContent-type: text/html\r\n\r\nPOST request for /"
        response = response.encode("utf-8")
        client_sock.send(response)
        client_sock.close()
        print(f"\tCLIENT SERVED")


if __name__ == '__main__':
    main()
