"""Serve the presentation and photos on this PC's LAN (standard library only)."""
import argparse
import functools
import http.server
import http.client
import socket
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith('/demo/'):
            return self._proxy()
        self.send_error(405)

    def _proxy(self, head=False):
        # Fixed local upstream: never proxy a user-supplied host or URL.
        path = self.path[len('/demo'):]
        if not path.startswith('/') or path.startswith('//'):
            self.send_error(400)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > 41 * 1024 * 1024:
            self.send_error(413)
            return
        conn = http.client.HTTPConnection('127.0.0.1', self.server.demo_port, timeout=180)
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in ('host', 'connection', 'transfer-encoding', 'accept-encoding')}
        headers['Accept-Encoding'] = 'identity'
        try:
            conn.request('HEAD' if head else self.command, path,
                         body=self.rfile.read(length) if length else None, headers=headers)
            response = conn.getresponse()
            data = response.read()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in ('connection', 'transfer-encoding', 'content-length', 'cache-control'):
                    self.send_header(key, value)
            self.send_header('Content-Length', response.getheader('Content-Length', str(len(data))) if head else str(len(data)))
            self.end_headers()
            if not head:
                self.wfile.write(data)
        except (OSError, http.client.HTTPException):
            self.send_error(503, 'Demo server is offline. Start subject8/app/server.py on port 8010.')
        finally:
            conn.close()

    def do_GET(self):
        return self._serve(False)

    def do_HEAD(self):
        return self._serve(True)

    def _serve(self, head):
        if self.path == '/demo':
            self.send_response(302)
            self.send_header('Location', '/demo/')
            self.end_headers()
            return
        if self.path.startswith('/demo/'):
            return self._proxy(head)
        path = unquote(urlsplit(self.path).path)
        target = Path(self.translate_path(path)).resolve()
        allowed = target in (ROOT / 'index.html', ROOT / '발표대본.html') or any(
            (ROOT / folder) in target.parents for folder in ('assets', 'private')
        )
        if path == '/':
            self.path = '/index.html'
            allowed = True
        if not allowed or not target.is_relative_to(ROOT):
            self.send_error(404)
            return
        if head:
            super().do_HEAD()
        else:
            super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True

def lan_ips():
    addresses = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(('192.0.2.1', 9))
            addresses.append(sock.getsockname()[0])
        except OSError:
            pass
    try:
        addresses.extend(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return list(dict.fromkeys(ip for ip in addresses if not ip.startswith(('127.', '169.254.'))))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--demo-port', type=int, default=8010, help='Local Final GUI port')
    args = parser.parse_args()
    if not (ROOT / 'index.html').is_file():
        parser.error('index.html is missing next to serve_deck.py')
    try:
        server = Server(('0.0.0.0', args.port), functools.partial(Handler, directory=str(ROOT)))
    except OSError as exc:
        print(f'Cannot start port {args.port}: {exc}', flush=True)
        print('A server may already be running. Close it or use --port 8766.', flush=True)
        return 1
    server.demo_port = args.demo_port
    print('\n발표 서버가 열렸습니다. 팀원에게 아래 LAN 주소를 보내세요.', flush=True)
    for ip in lan_ips():
        print(f'  http://{ip}:{args.port}/index.html#1', flush=True)
    print(f'이 PC에서 보기: http://127.0.0.1:{args.port}/index.html#1', flush=True)
    print(f'폴더: {ROOT}', flush=True)
    print('같은 네트워크에서 접속하세요. 창을 닫거나 Ctrl+C를 누르면 종료됩니다.', flush=True)
    print('재부팅하면 다시 실행하세요. IP가 바뀌면 표시되는 새 주소를 사용하세요.\n', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())