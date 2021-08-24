import argparse
from time import sleep
import requests


def do_request(address, timeout=None, reconnect=False):
    while True:
        try:
            return requests.get(address, timeout=timeout)
        except requests.ConnectionError or requests.Timeout as e:
            if reconnect:
                sleep(1)
            else:
                return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["shutdown"])
    parser.add_argument("--host", default="http://127.0.0.1")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--reconnect", action="store_const", const=True)
    args = parser.parse_args()
    if args.command == "shutdown":
        print(do_request(args.host + "/api/shutdown", timeout=args.timeout, reconnect=args.reconnect))


if __name__ == '__main__':
    main()
