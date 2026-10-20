"""Serve the presentation and photos on this PC's LAN (standard library only)."""
import argparse
import functools
import http.server
import socket
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        return self._serve(False)

    def do_HEAD(self):
        return self._serve(True)

    def _serve(self, head):
        path = unquote(urlsplit(self.path).path)
        target = Path(self.translate_path(path)).resolve()
        allowed = target == ROOT / 'index.html' or any(
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
    args = parser.parse_args()
    if not (ROOT / 'index.html').is_file():
        parser.error('index.html is missing next to serve_deck.py')
    try:
        server = Server(('0.0.0.0', args.port), functools.partial(Handler, directory=str(ROOT)))
    except OSError as exc:
        print(f'Cannot start port {args.port}: {exc}', flush=True)
        print('A server may already be running. Close it or use --port 8766.', flush=True)
        return 1
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