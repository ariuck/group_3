"""같은 와이파이/랜 안에서 결과 zip 을 내려받고 올리는 임시 공유 서버 (표준 라이브러리만 사용).

    py tools/share_server.py --dir C:\\공유            # Windows 에서
    python tools/share_server.py --dir ~/share         # 그 밖의 환경에서

폴더 구조 (--dir 아래)
    보내기/      여기에 있는 zip 을 다른 PC 가 내려받는다  (예: 합친 결과)
    받은결과/    다른 PC 가 올린 zip 이 저장된다
    받은결과/풀림/  올라온 zip 안의 라벨(txt)·검수표(csv)가 자동으로 풀린다  → tools/import_labels.py · merge_manifests.py 에 그대로 넣는다

다른 PC 는 브라우저로 http://<이 PC 주소>:8000 에 접속하고, 콘솔에 나온 4자리 번호를 입력하면 된다.

안전장치
  - 4자리 번호를 모르면 목록·내려받기·올리기가 모두 거부된다. (틀리면 잠시 잠긴다)
  - 같은 사설망(192.168.x.x, 10.x.x.x 등)의 PC 만 접속할 수 있다.
  - 올릴 수 있는 것은 '라벨(.txt)과 검수표(.csv)만 든 zip' 뿐이다. 사진·프로그램·폴더를 벗어나는 경로·너무 큰 파일은 거부한다.
  - 같은 이름의 파일은 덮어쓰지 않고 이름 뒤에 시각을 붙여 저장한다.
  - --minutes 가 지나면 서버가 저절로 꺼진다. (기본 120분)
라벨과 검수표는 사진 파일명이 들어 있는 회사 데이터다. 필요한 사람이 모두 받은 뒤에는 바로 끈다.
"""
import argparse
import csv
import ipaddress
import json
import os
import secrets
import shutil
import socket
import sys
import tempfile
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, quote, urlparse

SEND, RECEIVED, UNPACKED = "보내기", "받은결과", "풀림"
ALLOWED_SUFFIX = {".txt", ".csv"}
MAX_ENTRIES = 5000
NAME_BAD = set('\\/:*?"<>|\r\n\t\0')
MAX_FAILS, LOCK_SECONDS = 8, 60


# ── 파일 검사 ─────────────────────────────────────────────────────────────
def safe_name(name):
    """올라온 파일 이름에서 폴더 부분을 버리고 위험한 글자를 없앤다. 쓸 수 없으면 None."""
    name = PurePosixPath(str(name).replace("\\", "/")).name.strip()
    name = "".join(ch for ch in name if ch not in NAME_BAD).strip(". ")
    if not name or not name.lower().endswith(".zip") or len(name) > 120:
        return None
    return name


def unique_path(folder, name):
    """같은 이름이 있으면 덮어쓰지 않고 이름 뒤에 시각을 붙인다."""
    target = Path(folder) / name
    if target.exists():
        stem, suffix = target.stem, target.suffix
        target = target.with_name(f"{stem}_{time.strftime('%H%M%S')}{suffix}")
        n = 1
        while target.exists():
            n += 1
            target = target.with_name(f"{stem}_{time.strftime('%H%M%S')}_{n}{suffix}")
    return target


def inspect_zip(path, max_total_bytes):
    """zip 이 '라벨(.txt)·검수표(.csv)만 든 안전한 zip' 인지 검사한다.

    돌려주는 값: (라벨 수, 검수표 줄 수, [(zip 안 경로, 크기)]) — 문제가 있으면 ValueError(이유).
    """
    if not zipfile.is_zipfile(path):
        raise ValueError("zip 파일이 아닙니다.")
    entries, labels, rows, total = [], 0, 0, 0
    with zipfile.ZipFile(path) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        if not infos:
            raise ValueError("zip 안에 파일이 없습니다.")
        if len(infos) > MAX_ENTRIES:
            raise ValueError(f"파일이 너무 많습니다. (최대 {MAX_ENTRIES}개)")
        for info in infos:
            raw = info.filename
            parts = PurePosixPath(raw.replace("\\", "/")).parts
            if raw.startswith(("/", "\\")) or ":" in raw or ".." in parts or not parts:
                raise ValueError(f"안전하지 않은 경로가 있습니다: {raw}")
            suffix = PurePosixPath(parts[-1]).suffix.lower()
            if suffix not in ALLOWED_SUFFIX:
                raise ValueError(f"라벨(.txt)과 검수표(.csv)만 올릴 수 있습니다: {raw}")
            total += info.file_size
            if total > max_total_bytes:
                raise ValueError("압축을 풀면 너무 큽니다.")
            entries.append(("/".join(parts), info.file_size))
            if suffix == ".txt":
                labels += 1
            else:
                with z.open(info) as f:
                    rows += max(0, sum(1 for _ in csv.reader(line.decode("utf-8-sig", "replace") for line in f)) - 1)
    return labels, rows, entries


def unpack_zip(zip_path, dest):
    """검사를 통과한 zip 을 dest 아래에 푼다. (경로가 dest 밖으로 나가지 않는지 한 번 더 확인)"""
    dest = Path(dest).resolve()
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            parts = PurePosixPath(info.filename.replace("\\", "/")).parts
            target = dest.joinpath(*parts).resolve()
            if dest not in target.parents:
                raise ValueError("안전하지 않은 경로입니다.")
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


def is_local_client(ip):
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return False
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_private or addr.is_loopback or addr.is_link_local


def list_files(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    out = []
    for p in sorted(folder.glob("*.zip"), key=lambda q: q.stat().st_mtime, reverse=True):
        st = p.stat()
        out.append({"name": p.name, "size": st.st_size, "time": time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime))})
    return out


# ── 화면 ──────────────────────────────────────────────────────────────────
PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>결과 주고받기</title>
<style>
 body{font-family:'Malgun Gothic',system-ui,sans-serif;margin:0;background:#f4f6f8;color:#1f2933}
 main{max-width:640px;margin:0 auto;padding:20px 16px 40px}
 h1{font-size:22px;margin:8px 0 4px} p.sub{margin:0 0 16px;color:#52606d;font-size:14px}
 section{background:#fff;border:1px solid #d9e2ec;border-radius:10px;padding:16px;margin:12px 0}
 h2{font-size:16px;margin:0 0 10px} input[type=text],input[type=password]{font-size:20px;padding:8px 10px;width:120px;letter-spacing:4px;text-align:center}
 button{font-size:15px;padding:9px 16px;border:0;border-radius:8px;background:#2f6fed;color:#fff;cursor:pointer}
 button.sub{background:#e4e7eb;color:#1f2933} button:disabled{opacity:.5;cursor:default}
 ul{list-style:none;padding:0;margin:0} li{display:flex;justify-content:space-between;gap:8px;padding:8px 0;border-top:1px solid #eef1f4;font-size:14px}
 li:first-child{border-top:0} .muted{color:#7b8794;font-size:13px} .ok{color:#0a7d33} .bad{color:#c62828}
 progress{width:100%;height:10px;margin-top:10px} a{color:#2f6fed;word-break:break-all}
</style></head><body><main>
<h1>결과 주고받기</h1>
<p class="sub">같은 와이파이 안에서만 쓸 수 있고, 서버를 켠 PC 에 표시된 4자리 번호가 필요합니다.</p>

<section id="pinbox"><h2>1. 번호 입력</h2>
 <input id="pin" type="password" inputmode="numeric" maxlength="4" autocomplete="off" placeholder="0000">
 <button id="go">확인</button> <span id="pinmsg" class="bad"></span></section>

<div id="main" hidden>
<section><h2>2. 내려받기 <span class="muted">(서버 PC 가 내놓은 파일)</span></h2><ul id="send"></ul></section>
<section><h2>3. 올리기 <span class="muted">(라벨 txt 와 검수표 csv 만 든 zip)</span></h2>
 <input id="file" type="file" accept=".zip"> <button id="up">올리기</button>
 <progress id="bar" value="0" max="100" hidden></progress>
 <p id="upmsg"></p>
 <div class="muted">받은 파일</div><ul id="recv"></ul></section>
</div>
<script>
let PIN="";
const $=id=>document.getElementById(id);
const kb=n=>n>1048576?(n/1048576).toFixed(1)+" MB":Math.max(1,Math.round(n/1024))+" KB";
function row(f,link){const li=document.createElement("li");
 const a=document.createElement(link?"a":"span");a.textContent=f.name;if(link)a.href="/api/download?pin="+PIN+"&name="+encodeURIComponent(f.name);
 const s=document.createElement("span");s.className="muted";s.textContent=kb(f.size)+" · "+f.time;li.append(a,s);return li}
async function refresh(){
 const r=await fetch("/api/list?pin="+PIN);
 if(r.status==403){$("pinmsg").textContent="번호가 맞지 않습니다.";return false}
 if(r.status==429){$("pinmsg").textContent="너무 많이 틀렸습니다. 잠시 뒤에 다시 하세요.";return false}
 const d=await r.json();
 $("send").replaceChildren(...(d.send.length?d.send.map(f=>row(f,true)):[Object.assign(document.createElement("li"),{textContent:"내려받을 파일이 없습니다."})]));
 $("recv").replaceChildren(...(d.received.length?d.received.map(f=>row(f,false)):[Object.assign(document.createElement("li"),{textContent:"아직 없습니다."})]));
 return true}
$("go").onclick=async()=>{PIN=$("pin").value.trim();$("pinmsg").textContent="";
 if(await refresh()){$("pinbox").hidden=true;$("main").hidden=false}};
$("pin").addEventListener("keydown",e=>{if(e.key==="Enter")$("go").click()});
$("up").onclick=()=>{const f=$("file").files[0];const m=$("upmsg");m.className="";
 if(!f){m.textContent="올릴 zip 파일을 먼저 고르세요.";m.className="bad";return}
 if(!f.name.toLowerCase().endsWith(".zip")){m.textContent="zip 파일만 올릴 수 있습니다.";m.className="bad";return}
 const x=new XMLHttpRequest();x.open("PUT","/api/upload?pin="+PIN+"&name="+encodeURIComponent(f.name));
 $("bar").hidden=false;$("bar").value=0;$("up").disabled=true;m.textContent="올리는 중...";
 x.upload.onprogress=e=>{if(e.lengthComputable)$("bar").value=e.loaded*100/e.total};
 x.onload=async()=>{$("up").disabled=false;let d={};try{d=JSON.parse(x.responseText)}catch(e){}
  if(x.status==200){m.textContent="받았습니다: "+d.saved+" (라벨 "+d.labels+"개, 검수표 "+d.rows+"줄)";m.className="ok";await refresh()}
  else{m.textContent=d.error||("올리지 못했습니다 ("+x.status+")");m.className="bad"}};
 x.onerror=()=>{$("up").disabled=false;m.textContent="연결이 끊겼습니다. 서버 PC 가 켜져 있는지 확인하세요.";m.className="bad"};
 x.send(f)};
</script></main></body></html>
"""


# ── 서버 ──────────────────────────────────────────────────────────────────
class ShareServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, base_dir, pin, max_mb=50, log=print):
        super().__init__(address, Handler)
        self.base = Path(base_dir)
        self.send_dir = self.base / SEND
        self.recv_dir = self.base / RECEIVED
        self.unpacked_dir = self.recv_dir / UNPACKED
        for d in (self.send_dir, self.recv_dir, self.unpacked_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.pin = pin
        self.max_bytes = int(max_mb * 1024 * 1024)
        self.log = log
        self.fails = {}                       # IP → (틀린 횟수, 잠금이 풀리는 시각)
        self._lock = threading.Lock()

    def check_pin(self, ip, given):
        """(허용 여부, 상태코드) — 번호가 틀리면 403, 너무 많이 틀리면 429"""
        with self._lock:
            count, until = self.fails.get(ip, (0, 0.0))
            if until > time.monotonic():
                return False, 429
            if given and secrets.compare_digest(str(given), self.pin):
                self.fails.pop(ip, None)
                return True, 200
            count += 1
            self.fails[ip] = (0, time.monotonic() + LOCK_SECONDS) if count >= MAX_FAILS else (count, 0.0)
            return False, 403


class Handler(BaseHTTPRequestHandler):
    server_version = "ResultShare"

    def log_message(self, fmt, *args):            # 기본 로그는 끄고, 필요한 것만 server.log 로 남긴다
        pass

    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, data):
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _guard(self, query):
        ip = self.client_address[0]
        if not is_local_client(ip):
            self._json(403, {"error": "같은 네트워크의 PC 만 접속할 수 있습니다."})
            return False
        ok, code = self.server.check_pin(ip, (query.get("pin") or [""])[0])
        if not ok:
            self.server.log(f"[거부] {ip} 번호 불일치 또는 잠김")
            self._json(code, {"error": "번호가 맞지 않습니다." if code == 403 else "너무 많이 틀렸습니다. 잠시 뒤에 다시 하세요."})
        return ok

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/":
            if not is_local_client(self.client_address[0]):
                return self._json(403, {"error": "같은 네트워크의 PC 만 접속할 수 있습니다."})
            return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if url.path == "/api/list":
            if not self._guard(query):
                return
            return self._json(200, {"send": list_files(self.server.send_dir), "received": list_files(self.server.recv_dir)})
        if url.path == "/api/download":
            if not self._guard(query):
                return
            name = safe_name((query.get("name") or [""])[0])
            target = (self.server.send_dir / name) if name else None
            if not target or not target.is_file():
                return self._json(404, {"error": "파일을 찾을 수 없습니다."})
            data = target.read_bytes()
            self.server.log(f"[내려받기] {self.client_address[0]} ← {name} ({len(data) // 1024} KB)")
            return self._send(200, data, "application/zip",
                              {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})
        self._json(404, {"error": "없는 주소입니다."})

    def do_PUT(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path != "/api/upload":
            return self._json(404, {"error": "없는 주소입니다."})
        if not self._guard(query):
            self.close_connection = True
            return
        name = safe_name((query.get("name") or [""])[0])
        if not name:
            self.close_connection = True
            return self._json(400, {"error": "zip 파일만 올릴 수 있습니다."})
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.close_connection = True
            return self._json(411, {"error": "파일 크기를 알 수 없습니다."})
        if length <= 0 or length > self.server.max_bytes:
            self.close_connection = True
            return self._json(413, {"error": f"파일이 너무 큽니다. (최대 {self.server.max_bytes // 1048576}MB)"})
        fd, tmp_name = tempfile.mkstemp(suffix=".part", dir=self.server.recv_dir)
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            remaining = length
            with open(tmp, "wb") as f:
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            if remaining:
                raise ValueError("파일이 중간에 끊겼습니다. 다시 올려 주세요.")
            labels, rows, _entries = inspect_zip(tmp, self.server.max_bytes * 4)
            final = unique_path(self.server.recv_dir, name)
            tmp.replace(final)
            unpack_zip(final, self.server.unpacked_dir)
            self.server.log(f"[받음] {self.client_address[0]} → {final.name} (라벨 {labels}개, 검수표 {rows}줄)")
            self._json(200, {"saved": final.name, "labels": labels, "rows": rows})
        except (ValueError, zipfile.BadZipFile, OSError) as e:
            self.server.log(f"[거부] {self.client_address[0]} 올린 파일: {e}")
            self.close_connection = True
            self._json(400, {"error": str(e)})
        finally:
            tmp.unlink(missing_ok=True)


def local_addresses():
    """이 PC 의 사설 IPv4 주소 후보 (다른 PC 가 접속할 주소)"""
    found = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))                  # 실제로 보내지는 않고 어느 어댑터를 쓸지만 정한다
        found.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        found += [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
    except OSError:
        pass
    out = []
    for ip in found:
        if ip not in out and ipaddress.ip_address(ip).is_private and not ip.startswith(("127.", "169.254.")):
            out.append(ip)
    return out


def default_dir():
    return Path("C:/공유") if sys.platform.startswith("win") else Path.home() / "share"


def main(argv=None):
    ap = argparse.ArgumentParser(description="결과 zip 을 같은 네트워크에서 주고받는 임시 서버")
    ap.add_argument("--dir", default=str(default_dir()), help="공유 폴더 (그 안에 보내기/·받은결과/ 를 만든다)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--max-mb", type=float, default=50, help="올릴 수 있는 zip 의 최대 크기(MB)")
    ap.add_argument("--minutes", type=float, default=120, help="이 시간이 지나면 서버를 저절로 끈다")
    args = ap.parse_args(argv)
    pin = f"{secrets.randbelow(10000):04d}"
    try:
        server = ShareServer(("0.0.0.0", args.port), Path(args.dir).expanduser(), pin, args.max_mb,
                             log=lambda m: print(f"  {time.strftime('%H:%M:%S')} {m}", flush=True))
    except OSError as e:
        print(f"서버를 시작하지 못했습니다: {e}\n(이미 같은 포트로 실행 중인 서버가 있으면 그 창을 먼저 닫으세요.)")
        return 2
    print("=" * 62)
    print("  결과 주고받기 서버가 켜졌습니다.")
    print("  다른 PC 의 브라우저 주소창에 아래 중 하나를 입력하세요:")
    for ip in local_addresses():
        print(f"      http://{ip}:{args.port}")
    print(f"\n  접속 번호:  {pin}      (이 번호를 알려 준 사람만 쓸 수 있습니다)")
    print(f"  보낼 파일 폴더:   {server.send_dir}")
    print(f"  받은 파일 폴더:   {server.recv_dir}   (자동으로 풀린 것: {server.unpacked_dir})")
    print(f"  {args.minutes:g}분 뒤 저절로 꺼지고, 끝나면 이 창을 닫거나 Ctrl+C 를 누르세요.")
    print("=" * 62, flush=True)
    timer = threading.Timer(args.minutes * 60, server.shutdown)
    timer.daemon = True
    timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("서버를 껐습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
