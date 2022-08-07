import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote as urldecode

from ..db import JsonDatabase
from ..types import Position
from ..utils import b64encode


class Handler(BaseHTTPRequestHandler):

    @property
    def db(self):
        return self.server.db

    def do_GET(self):
        if self.path == '/':
            self.serve_static('chess.html')
        elif self.path.startswith('/static/'):
            self.serve_static(self.path[8:])
        elif self.path.startswith('/api/'):
            self.serve_api(self.path[5:])
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.serve_api(self.path[5:])
        else:
            self.send_error(404)

    def serve_api(self, endpoint):
        endpoint = urldecode(endpoint)
        response = None
        if m := re.match('^position/fen/(.*)$', endpoint):
            position = Position.load_fen(m[1])
            position_id = b64encode(position)
            response = {
                'id': position_id,
                'moves': self.db.get(position_id),
            }
        elif m := re.match('^position/save/([A-Za-z0-9_-]+)$', endpoint):
            position_id = m[1]
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode())
            if 'moves' in data:
                data = data['moves']
            self.db.set(position_id, data)
            self.db.save()
            response = {
                'id': position_id,
                'moves': self.db.get(position_id),
            }
        if response is not None:
            self.render_json(response)
        else:
            self.send_error(404)

    def render_json(self, response):
        self.send_response(200)
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

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
    httpd.db = JsonDatabase('data/db.json')
    httpd.serve_forever()
