import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        filename = None
        if self.path == '/':
            filename = 'chess.html'
        elif self.path.startswith('/static/'):
            filename = self.path[8:]
        if filename:
            self.serve_static(filename)
        else:
            self.send_error(404)

    def serve_static(self, filename):
        content_type = self.get_file_mime_type(filename)
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        with open(f'static/{filename}', 'rb') as f:
            self.wfile.write(f.read())

    def get_file_mime_type(self, filename):
        if filename.endswith('.html'):
            content_type = 'text/html'
        elif filename.endswith('.css'):
            content_type = 'text/css'
        elif filename.endswith('.js'):
            content_type = 'application/javascript'
        elif filename.endswith('.png'):
            content_type = 'image/png'
        else:
            content_type = 'application/octet-stream'
        return content_type


parser = argparse.ArgumentParser(description="Start chess server.")
parser.add_argument('-l', '--listen', default="127.0.0.1")
parser.add_argument("-p", "--port", default=8000, type=int)


if __name__ == '__main__':
    args = parser.parse_args()
    server_address = (args.listen, args.port)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever() 
