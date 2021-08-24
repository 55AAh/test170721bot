import argparse
from time import sleep
import requests


def do_request(address, timeout=None, wait_200=False):
    while True:
        try:
            response = requests.get(address, timeout=timeout)
            if not wait_200 or response.status_code == 200:
                return response
        except requests.ConnectionError or requests.Timeout:
            if timeout and not wait_200:
                return None
            sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["shutdown"])
    parser.add_argument("--host", default="http://127.0.0.1")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--wait_200", action="store_const", const=True)
    args = parser.parse_args()
    if args.command == "shutdown":
        print(do_request(args.host + "/api/shutdown", timeout=args.timeout, wait_200=args.wait_200))


if __name__ == '__main__':
    main()
