# server.py
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

class SPAHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/" and not os.path.exists(self.translate_path(self.path)):
            self.path = "/index.html"
        return super().do_GET()

if __name__ == "__main__":
    os.chdir("/opt/gate-web")
    server = HTTPServer(("0.0.0.0", 8080), SPAHandler)
    print("🚀 Serving on http://0.0.0.0:8080")
    server.serve_forever()
