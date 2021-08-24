import json
import os
import socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread, Lock

from pipe_component import DuplexPipeComponent
from event_component import EventComponent
from worker_process import WorkerProcess, Worker
from logs import LoggingComponent

__all__ = ["Webserver", "BackendAPI"]


class Webserver(WorkerProcess):
    def __init__(self):
        super().__init__(w_class=_WebserverWorker, name="Webserver", daemon=True, ignore_sigterm=True)
        self.api_pipe = self.worker.pipe

    def start(self, host="0.0.0.0", port=int(os.getenv("PORT", 80))):
        super().start(host, port)

    def stop(self):
        self.worker.event.set()


class _WebserverWorker(DuplexPipeComponent, EventComponent, LoggingComponent, Worker):
    def run(self, host, port):
        log = self.get_logger("WEBSERVER")
        log.debug("Started")
        httpd = ThreadingHTTPServer((host, port), _HTTPRequestHandler)
        httpd.api_pipe = self.pipe
        httpd.api_pipe_lock = Lock()
        httpd.log = log

        def stopper_main():
            self.event.wait()
            httpd._BaseServer__shutdown_request = True
            _host = host if host != "0.0.0.0" else "127.0.0.1"
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((_host, port))
            httpd.shutdown()
        stopper = Thread(target=stopper_main)
        stopper.start()
        httpd.serve_forever(poll_interval=None)
        stopper.join()
        log.debug("Stopped")


class _HTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=os.path.abspath("web"), **kwargs)

    def handle_api_request(self, method):
        s_path = self.path.rstrip("/").split("/", 2)
        if len(s_path) >= 3 and s_path[1] == "api":
            function = s_path[2]
            parameters = s_path[3:]
            _FrontendAPI.handle(self, method, function, parameters,)
            return True

    def log_message(self, fmt, *args):
        self.server.log.debug(("%s:%s - - " % self.client_address) + fmt % args)

    def do_GET(self):
        if self.handle_api_request("GET") is not None:
            return
        return super().do_GET()

    def do_POST(self):
        if self.handle_api_request("POST") is not None:
            return
        self.send_response(501)
        self.end_headers()


class _FrontendAPI:
    @staticmethod
    def handle(handler, method: str, function: str, parameters: list[str]):
        if function == "ping":
            _FrontendAPI.handle_ping(handler, method, parameters)
        elif function == "finish":
            _FrontendAPI.handle_finish(handler, method, parameters)
        elif function == "shutdown":
            _FrontendAPI.handle_shutdown(handler, method, parameters)
        else:
            handler.send_error(404)

    @staticmethod
    def request(handler, request):
        with handler.server.api_pipe_lock:
            handler.server.api_pipe.send(request)
            return handler.server.api_pipe.recv()

    @staticmethod
    def handle_ping(handler, method, parameters):
        if method != "GET":
            return handler.send_error(405)
        if len(parameters) > 0:
            return handler.send_error(404, "Parameters not supported")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        body = {
            "pong": _FrontendAPI.request(handler, "ping"),
            "date": handler.date_time_string()
        }
        body = json.dumps(body).encode("utf-8")
        handler.wfile.write(body if body is not None else b'')

    @staticmethod
    def handle_finish(handler, method, parameters):
        if method != "GET":
            return handler.send_error(405)
        if len(parameters) > 0:
            return handler.send_error(404, "Parameters not supported")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        body = {
            "ok": _FrontendAPI.request(handler, "finish"),
        }
        body = json.dumps(body).encode("utf-8")
        handler.wfile.write(body if body is not None else b'')

    @staticmethod
    def handle_shutdown(handler, method, parameters):
        if method != "GET":
            return handler.send_error(405)
        if len(parameters) > 0:
            return handler.send_error(404, "Parameters not supported")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        body = {
            "ok": _FrontendAPI.request(handler, "shutdown"),
        }
        body = json.dumps(body).encode("utf-8")
        handler.wfile.write(body if body is not None else b'')


class BackendAPI:
    @staticmethod
    def handle(server, request):
        if request == "ping":
            return True
        elif request == "finish":
            return False
        elif request == "shutdown":
            server._remote_stop_event.send(None)
            return True
        else:
            return None
