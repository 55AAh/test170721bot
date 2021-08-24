import argparse
from urllib.parse import urljoin
from time import sleep
import requests


def do_request(host, command, retry=False, wait_ok=False):
    retries = 0
    while True:
        try:
            response = requests.get(urljoin(host, f"/api/{command}"), timeout=5)
            if not wait_ok or response.json()['ok']:
                return response.status_code, response.json()
        except requests.ConnectionError or requests.Timeout as e:
            if not retry:
                print(f"CLI: ERROR:", e)
                return None
        sleep(1)
        retries += 1
        print(f"CLI: RETRYING: {retries}...")


def execute(args):
    if args.command == "finish":
        return do_request(args.host, "finish", retry=True)
    if args.command == "shutdown":
        return do_request(args.host, "shutdown")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["finish", "shutdown"])
    parser.add_argument("--host", default="http://127.0.0.1/")
    args = parser.parse_args()
    print(f"CLI: {args.command}: {execute(args)}")


if __name__ == '__main__':
    main()
