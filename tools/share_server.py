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
DEFAULT_ASSIGN = "김동훈:1-300,이후영:301-600,지혜성:601-900"      # 검수자별 번호 범위 (docs/team/검수_배정.md)


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


def parse_assign(text):
    """'김동훈:1-300,이후영:301-600' → {'김동훈': [1, 300], '이후영': [301, 600]}  (잘못되면 ValueError)"""
    out = {}
    for part in str(text).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            who, rng = part.split(":")
            lo, hi = (int(x) for x in rng.split("-"))
        except ValueError:
            raise ValueError(f"검수 범위 형식이 잘못되었습니다: '{part}' (예: 김동훈:1-300)")
        who = who.strip()
        if not who or lo < 1 or hi < lo:
            raise ValueError(f"검수 범위가 올바르지 않습니다: '{part}'")
        out[who] = [lo, hi]
    if not out:
        raise ValueError("검수 범위가 비어 있습니다.")
    return out


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
PAGE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>결과 주고받기</title>
<style>
 :root{--bg:#f4f6f8;--card:#fff;--line:#d9e2ec;--text:#1f2933;--muted:#52606d;--accent:#2f6fed;--ok:#0a7d33;--bad:#c62828;--code:#0f172a}
 *{box-sizing:border-box} body{font-family:'Malgun Gothic',system-ui,sans-serif;margin:0;background:var(--bg);color:var(--text);line-height:1.6}
 main{max-width:760px;margin:0 auto;padding:18px 16px 60px}
 h1{font-size:22px;margin:6px 0 2px} p.sub{margin:0 0 12px;color:var(--muted);font-size:14px}
 nav{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 14px}
 nav button{background:#e4e7eb;color:var(--text);border:0;border-radius:8px;padding:9px 14px;font-size:15px;cursor:pointer}
 nav button.on{background:var(--accent);color:#fff}
 section.tab{display:none} section.tab.on{display:block}
 .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
 h2{font-size:17px;margin:0 0 8px} h3{font-size:15px;margin:14px 0 6px}
 .step{display:flex;gap:12px;align-items:flex-start}
 .num{flex:none;width:30px;height:30px;border-radius:50%;background:var(--accent);color:#fff;font-weight:bold;display:flex;align-items:center;justify-content:center;margin-top:2px}
 .step .body{flex:1;min-width:0} .step h2{margin-bottom:4px}
 ul,ol{margin:6px 0 6px 20px;padding:0} li{margin:3px 0}
 pre{position:relative;background:var(--code);color:#e2e8f0;border-radius:8px;padding:10px 74px 10px 12px;margin:8px 0;overflow-x:auto;font-size:13.5px;line-height:1.5;white-space:pre-wrap;word-break:break-all}
 pre button{position:absolute;top:8px;right:8px;font-size:12px;padding:4px 9px;background:#334155;color:#fff;border:0;border-radius:6px;cursor:pointer}
 code{background:#eef1f4;border-radius:4px;padding:1px 5px;font-size:13.5px} pre code{background:none;padding:0}
 .note{background:#fff8e1;border:1px solid #f5d98b;border-radius:8px;padding:8px 12px;margin:8px 0;font-size:14px}
 .warn{background:#fdecea;border:1px solid #f1a9a0;border-radius:8px;padding:8px 12px;margin:8px 0;font-size:14px}
 .good{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:8px 12px;margin:8px 0;font-size:14px}
 .muted{color:var(--muted);font-size:13px} .ok{color:var(--ok)} .bad{color:var(--bad)}
 table{border-collapse:collapse;width:100%;font-size:14px;margin:6px 0} td,th{border:1px solid var(--line);padding:6px 9px;text-align:left} th{background:#f0f4f8}
 .row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:6px 0}
 select,input[type=password]{font-size:16px;padding:7px 10px} input[type=password]{width:110px;font-size:20px;letter-spacing:4px;text-align:center}
 button.main{font-size:15px;padding:9px 16px;border:0;border-radius:8px;background:var(--accent);color:#fff;cursor:pointer} button.main:disabled{opacity:.5}
 label.pick{display:inline-flex;gap:5px;align-items:center;margin-right:10px;font-size:14px}
 ul.files{list-style:none;margin:0;padding:0} ul.files li{display:flex;justify-content:space-between;gap:8px;padding:8px 0;border-top:1px solid #eef1f4;font-size:14px} ul.files li:first-child{border-top:0}
 progress{width:100%;height:10px;margin-top:10px} a{color:var(--accent);word-break:break-all}
 .flow{font-family:Consolas,monospace;font-size:13px;white-space:pre;overflow-x:auto;background:#f0f4f8;border-radius:8px;padding:10px 12px}
</style></head><body><main>
<h1>결과 주고받기</h1>
<p class="sub">검수 결과를 같은 와이파이 안에서 주고받는 임시 페이지입니다. 위쪽 탭에서 <b>가이드</b>를 보고 따라 하세요.</p>

<nav>
 <button data-tab="rv" class="on">검수자 가이드</button>
 <button data-tab="pm">PM 가이드 (전체 흐름)</button>
 <button data-tab="files">파일 받기·올리기</button>
</nav>

<!-- ───────────────────────── 검수자 가이드 ───────────────────────── -->
<section class="tab on" id="tab-rv">
 <div class="card">
  <h2>먼저 내 이름을 고르세요</h2>
  <div class="row"><select id="who"></select>
   <span id="whoinfo" class="muted"></span></div>
  <div class="row"><b>VS Code 터미널 종류</b>
   <label class="pick"><input type="radio" name="term" value="wsl" checked> WSL (Ubuntu)</label>
   <label class="pick"><input type="radio" name="term" value="win"> Windows (PowerShell)</label></div>
  <div class="muted">터미널 왼쪽 위 이름이 <b>WSL 또는 Ubuntu</b>이면 위쪽, <b>powershell</b>이면 아래쪽을 고르세요. 아래 명령이 자동으로 바뀝니다.</div>
 </div>

 <div class="card step"><div class="num">0</div><div class="body">
  <h2>처음 한 번: 최신 도구 받기</h2>
  VS Code 에서 프로젝트 폴더를 열고, 터미널에 입력합니다.
  <pre>git pull origin main</pre>
  <div class="note">오류가 나면 화면의 문구를 PM 에게 알려 주세요. 작업 중이던 검수표(<code>manifests\dataset_manifest.csv</code>)가 있다면 먼저 다른 이름으로 복사해 두세요.</div>
 </div></div>

 <div class="card step"><div class="num">1</div><div class="body">
  <h2>파일 받기</h2>
  <ol><li>위쪽 <b>파일 받기·올리기</b> 탭을 누릅니다. <button class="main" onclick="showTab('files')">탭으로 이동</button></li>
  <li>PM 이 알려 준 <b>4자리 번호</b>를 입력하고 확인을 누릅니다.</li>
  <li>목록의 zip 파일(<code>결과_날짜_시각.zip</code>)을 클릭하면 내려받아집니다. 보통 <code>다운로드</code> 폴더에 저장됩니다.</li></ol>
 </div></div>

 <div class="card step"><div class="num">2</div><div class="body">
  <h2>C 드라이브에 <code>받은결과</code> 폴더를 만들고 풀기</h2>
  <ol><li>탐색기에서 <b>C 드라이브</b>를 열고 새 폴더 <code>받은결과</code>를 만듭니다. (<code>C:\받은결과</code>) 이미 있으면 안의 내용을 모두 지웁니다.</li>
  <li>받은 zip 을 우클릭 ▸ <b>압축 풀기</b>(모두 압축 풀기)에서 위치를 <code>C:\받은결과</code>로 정합니다.</li></ol>
  <div class="good"><b>확인:</b> <code>C:\받은결과</code>를 열었을 때 바로 <code>검수표.csv</code>와 <code>이물검출_학습데이터1</code> 폴더가 보여야 합니다.</div>
  <div class="warn"><code>C:\받은결과\결과_2026…</code> 처럼 폴더가 <b>한 겹 더</b> 생겼다면 안쪽 내용을 위(<code>C:\받은결과</code>)로 꺼내 주세요. 그래야 아래 명령이 파일을 찾습니다.</div>
 </div></div>

 <div class="card step"><div class="num">3</div><div class="body">
  <h2>내 검수표는 이름만 바꿔 치워 두기 (충돌 방지)</h2>
  <ol><li>라벨링 프로그램을 <b>끕니다.</b></li>
  <li>VS Code 왼쪽 탐색기에서 <code>manifests</code> 폴더의 <code>dataset_manifest.csv</code>를 우클릭 ▸ <b>이름 바꾸기</b> ▸ <code>dataset_manifest.내것.csv</code></li></ol>
  <div class="note"><b>왜 하나요?</b> 받은 검수표에는 900장이 모두 들어 있습니다. 내 옛 파일과 합치면 같은 사진이 다르게 적혀 <b>충돌</b>이 날 수 있어서, 내 파일은 지우지 말고 이름만 바꿔 둡니다. 나중에 필요하면 이름을 되돌릴 수 있습니다. 파일이 없으면 건너뛰어도 됩니다.</div>
 </div></div>

 <div class="card step"><div class="num">4</div><div class="body">
  <h2>명령 2개로 내 PC에 가져오기</h2>
  VS Code 터미널(프로젝트 폴더)에서 <b>한 줄씩</b> 실행합니다.
  <h3>① 라벨(txt) 가져오기</h3>
  <pre data-cmd="import"></pre>
  <div class="good">이렇게 나오면 정상: <code>새 라벨 …개</code>가 보이고 마지막에 <code>…개를 복사했습니다.</code></div>
  <h3>② 검수표 가져오기</h3>
  <pre data-cmd="merge"></pre>
  <div class="good">이렇게 나오면 정상: <code>합친 결과: 900줄</code> · <code>원본 사진 900장 중 검수표에 줄이 없는 사진: 0장</code> · 마지막에 <code>저장했습니다</code></div>
  <div class="warn"><b>"충돌"이라고 나오거나 줄 수가 900이 아니면</b> 3단계(내 검수표 이름 바꾸기)를 건너뛴 것입니다. 3단계를 하고 ②를 다시 실행하세요.</div>
 </div></div>

 <div class="card step"><div class="num">5</div><div class="body">
  <h2>검수하기</h2>
  <ol><li>라벨링 프로그램을 켭니다.</li>
  <li><kbd>Ctrl</kbd>+<kbd>G</kbd>를 눌러 <b id="startno">내 시작 번호</b>로 이동합니다.</li>
  <li>검수자 칸에 <b>내 이름을 한 번</b> 씁니다. 다음 사진부터는 자동으로 채워집니다.</li>
  <li>한 장씩 보고: 맞으면 <kbd>Enter</kbd> · 틀리면 BBox 를 고치고 <kbd>Enter</kbd> · 애매하면 <kbd>R</kbd> 후 이유를 쓰고 <kbd>Enter</kbd></li></ol>
  <div class="warn"><b>내 번호 범위(<span class="rng">내 범위</span>)의 사진만 저장하세요.</b> 다른 사람 범위를 저장하면 합칠 때 서로 덮어씁니다.</div>
 </div></div>

 <div class="card step"><div class="num">6</div><div class="body">
  <h2>검수가 끝나면 내 범위만 묶기</h2>
  프로그램을 끄고 터미널에서 실행합니다.
  <pre data-cmd="pack"></pre>
  <div class="good">끝에 <code>라벨(txt) 300개, 검수표 300줄</code>이 나오면 정상입니다. 파일은 프로젝트의 <code>data\share</code> 폴더에 <code>결과_<span class="nm">이름</span>_날짜_시각.zip</code>으로 만들어집니다.</div>
  <div id="packpath" class="muted"></div>
  <div class="warn"><b>라벨 개수가 내 장수와 다르거나 0개이면</b> 내가 저장한 라벨이 <code>data\work</code> 안의 다른 위치에 있을 수 있습니다. 사진 폴더 구조가 다른 PC 에서는 <code>work\data\labels\파일.txt</code> 처럼 저장되기도 합니다. 내 PC 에 txt 가 몇 개, 어느 폴더에 있는지 확인하세요.
   <pre>find data/work -name "*.txt" -printf "%h\n" | sort | uniq -c</pre>
   <div class="muted">Windows(PowerShell)는: <code>Get-ChildItem data\work -Recurse -Filter *.txt | Group-Object DirectoryName | Select-Object Count, Name</code></div>
   저장한 라벨이 어디에도 없으면 프로그램에서 해당 사진을 다시 열어 저장해야 합니다. PM 에게 알려 주세요.</div>
 </div></div>

 <div class="card step"><div class="num">7</div><div class="body">
  <h2>이 페이지에 올리기</h2>
  <ol><li>위쪽 <b>파일 받기·올리기</b> 탭 ▸ <b>올리기</b>에서 6단계의 zip 을 고르고 <b>올리기</b>를 누릅니다.</li>
  <li><span class="ok">받았습니다: 결과_…zip (라벨 300개, 검수표 300줄)</span> 이 나오면 끝입니다. PM 에게 올렸다고 알려 주세요.</li></ol>
  <div class="note">거부되면 화면에 이유가 나옵니다. 사진(jpg)이나 다른 파일이 섞인 zip 은 올라가지 않습니다. 6단계의 명령으로 만든 zip 을 쓰세요.</div>
 </div></div>
</section>

<!-- ───────────────────────── PM 가이드 ───────────────────────── -->
<section class="tab" id="tab-pm">
 <div class="card">
  <h2>전체 흐름 한눈에</h2>
  <div class="flow">[PM]  ① 합친 결과 묶기 ─▶ ② 서버 켜기(공유시작.bat) ─▶ ③ 주소·번호 알려 주기
                                                       │
[검수자 3명]  내려받기 ─▶ 풀기 ─▶ 명령 2개로 가져오기 ─▶ 검수 ─▶ 내 범위 묶기 ─▶ 올리기
                                                       │
[PM]  ④ 올라온 결과 확인 ─▶ ⑤ 명령 2개로 합치기 ─▶ ⑥ 확인 ─▶ ⑦ 서버 끄기·마무리</div>
 </div>

 <div class="card">
  <h2>검수 범위 (3명, 각 300장)</h2>
  <table id="assigntable"><tr><th>검수자</th><th>번호</th><th>장수</th></tr></table>
  <div class="muted">번호는 프로그램 화면의 <b>N / 900</b>과 같습니다. 3명 모두 자기가 쓴 사진이 없는 범위입니다.</div>
 </div>

 <div class="card step"><div class="num">①</div><div class="body">
  <h2>합친 결과 묶기 (처음 한 번)</h2>
  PM PC 의 WSL(프로젝트 폴더)에서:
  <pre>python tools/pack_results.py</pre>
  <div class="muted">라벨 900개와 검수표 900줄이 <code>data/share/결과_날짜_시각.zip</code>으로 만들어집니다. 검수표의 작성자 칸이 정리된 최신 상태여야 합니다.</div>
 </div></div>

 <div class="card step"><div class="num">②</div><div class="body">
  <h2>서버 켜기</h2>
  <ol><li><b>방화벽 규칙</b>(PM PC 에서 한 번만, 관리자 PowerShell):
   <pre>New-NetFirewallRule -DisplayName "라벨공유 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private</pre></li>
  <li><code>공유시작.bat</code>을 더블클릭합니다. 방화벽 창이 뜨면 <b>개인 네트워크</b>만 허용합니다.</li>
  <li>검은 창에 나오는 <b>접속 주소</b>와 <b>4자리 번호</b>를 확인합니다.</li></ol>
 </div></div>

 <div class="card step"><div class="num">③</div><div class="body">
  <h2>검수자에게 알려 주기</h2>
  <ul><li>접속 주소: <b id="myurl"></b></li><li>4자리 번호 (검은 창에 표시된 것)</li><li>"이 페이지의 <b>검수자 가이드</b>를 따라 하세요"</li></ul>
  <div class="note">검수자 PC 에도 최신 도구가 필요합니다. 먼저 <code>git pull origin main</code> 을 하라고 알려 주세요. (<code>tools/pack_results.py</code> 가 있어야 자기 범위를 묶을 수 있습니다.)</div>
 </div></div>

 <div class="card step"><div class="num">④</div><div class="body">
  <h2>올라온 결과 확인</h2>
  <ul><li>이 페이지의 <b>파일 받기·올리기</b> 탭 ▸ <b>받은 파일</b>에 3개(김동훈·이후영·지혜성)가 보이는지 확인합니다.</li>
  <li>폴더로도 볼 수 있습니다: <code>C:\공유\받은결과</code> (zip) · <code>C:\공유\받은결과\풀림</code> (자동으로 풀린 라벨과 검수표)</li>
  <li>풀림 폴더에 <code>검수표_김동훈.csv</code>, <code>검수표_이후영.csv</code>, <code>검수표_지혜성.csv</code> 가 있어야 합니다.</li></ul>
 </div></div>

 <div class="card step"><div class="num">⑤</div><div class="body">
  <h2>명령 2개로 합치기</h2>
  PM PC 의 WSL(프로젝트 폴더)에서 <b>한 줄씩</b>:
  <pre>python tools/import_labels.py /mnt/c/공유/받은결과/풀림 --apply --overwrite</pre>
  <pre>python tools/merge_manifests.py /mnt/c/공유/받은결과/풀림 --apply</pre>
  <ul><li>첫 줄: 검수하며 고친 라벨을 내 <code>data/work</code>에 반영합니다.</li>
  <li>둘째 줄: 검수표 3개와 내 검수표를 하나로 합칩니다. 내 기존 파일은 <code>manifests</code> 폴더에 <code>백업-날짜</code>로 자동 보관됩니다.</li>
  <li>같은 사진이 다르게 적히면(충돌) 검수일이 늦은 줄이 이기고 화면에 알려 줍니다.</li></ul>
 </div></div>

 <div class="card step"><div class="num">⑥</div><div class="body">
  <h2>확인하기</h2>
  합치기 결과 요약에서 아래를 확인합니다.
  <table><tr><th>항목</th><th>기준</th></tr>
  <tr><td>합친 결과</td><td><b>900줄</b></td></tr>
  <tr><td>검수표에 줄이 없는 사진</td><td><b>0장</b></td></tr>
  <tr><td>작성자와 검수자가 같은 줄</td><td><b>0</b></td></tr>
  <tr><td>미처리 REVIEW</td><td><b>0</b> (남아 있으면 팀이 판단해 정리)</td></tr>
  <tr><td>내용이 달라 고른 줄(충돌)</td><td>있으면 화면에 나온 사진을 직접 확인</td></tr></table>
  라벨링 프로그램의 <b>[도구] ▸ Validation</b>도 실행해 <b>오류 0건</b>인지 확인합니다.
 </div></div>

 <div class="card step"><div class="num">⑦</div><div class="body">
  <h2>마무리</h2>
  <ul><li>검은 서버 창을 <b>닫습니다.</b> (공유가 바로 멈춥니다. 켠 지 120분이 지나도 저절로 꺼집니다)</li>
  <li>방화벽 규칙을 지웁니다. (관리자 PowerShell)
   <pre>Remove-NetFirewallRule -DisplayName "라벨공유 8000"</pre></li>
  <li>검수가 모두 끝나면 최종본(<code>data/final</code>)을 정리합니다.</li></ul>
  <div class="warn">라벨과 검수표는 사진 파일명이 들어 있는 <b>회사 데이터</b>입니다. 필요한 사람이 모두 받으면 바로 서버를 끄고, Git 에는 올리지 마세요.</div>
 </div></div>
</section>

<!-- ───────────────────────── 파일 받기·올리기 ───────────────────────── -->
<section class="tab" id="tab-files">
 <div class="card" id="pinbox"><h2>번호 입력</h2>
  <div class="row"><input id="pin" type="password" inputmode="numeric" maxlength="4" autocomplete="off" placeholder="0000">
   <button class="main" id="go">확인</button> <span id="pinmsg" class="bad"></span></div>
  <div class="muted">서버를 켠 PM PC 의 검은 창에 표시된 4자리 번호입니다.</div></div>
 <div id="filesmain" hidden>
  <div class="card"><h2>내려받기 <span class="muted">(PM 이 내놓은 파일)</span></h2><ul class="files" id="send"></ul></div>
  <div class="card"><h2>올리기 <span class="muted">(라벨 txt 와 검수표 csv 만 든 zip)</span></h2>
   <div class="row"><input id="file" type="file" accept=".zip"> <button class="main" id="up">올리기</button></div>
   <progress id="bar" value="0" max="100" hidden></progress>
   <p id="upmsg"></p>
   <div class="muted">받은 파일</div><ul class="files" id="recv"></ul></div>
 </div>
</section>

<script>
const ASSIGN=__ASSIGN__;
let PIN="";
const $=id=>document.getElementById(id);
const names=Object.keys(ASSIGN);
function showTab(t){document.querySelectorAll("section.tab").forEach(s=>s.classList.toggle("on",s.id==="tab-"+t));
 document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("on",b.dataset.tab===t));window.scrollTo(0,0)}
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>showTab(b.dataset.tab));

// 검수 범위 표 · 이름 선택
const sel=$("who");
names.forEach(n=>sel.add(new Option(n,n)));
const tbl=$("assigntable");
names.forEach(n=>{const [a,b]=ASSIGN[n];const tr=tbl.insertRow();tr.insertCell().textContent=n;tr.insertCell().textContent=a+" ~ "+b;tr.insertCell().textContent=(b-a+1)+"장"});
$("myurl").textContent=location.origin;
const term=()=>document.querySelector("input[name=term]:checked").value;
function cmds(){const n=sel.value,[a,b]=ASSIGN[n]||[1,1],w=term()==="wsl";
 const dir=w?"/mnt/c/받은결과":"C:\\받은결과";
 return {import:`python tools/import_labels.py ${dir} --apply`,
  merge:`python tools/merge_manifests.py ${dir}${w?"/":"\\"}검수표.csv --apply`,
  pack:`python tools/pack_results.py --name ${n} --from ${a} --to ${b}`}}
function addCopy(pre){const btn=document.createElement("button");btn.textContent="복사";btn.type="button";
 btn.onclick=()=>{const text=pre.dataset.text;const done=()=>{btn.textContent="복사됨";setTimeout(()=>btn.textContent="복사",1500)};
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(done)}
  else{const t=document.createElement("textarea");t.value=text;document.body.append(t);t.select();try{document.execCommand("copy")}catch(e){}t.remove();done()}};
 pre.append(btn)}
function render(){const n=sel.value,[a,b]=ASSIGN[n]||[1,1],c=cmds();
 document.querySelectorAll("pre[data-cmd]").forEach(p=>{p.dataset.text=c[p.dataset.cmd];p.textContent=c[p.dataset.cmd];addCopy(p)});
 document.querySelectorAll("pre:not([data-cmd])").forEach(p=>{if(!p.querySelector("button")){p.dataset.text=p.textContent;addCopy(p)}});
 $("startno").textContent=a+"번";document.querySelectorAll(".rng").forEach(e=>e.textContent=a+" ~ "+b+"번");
 document.querySelectorAll(".nm").forEach(e=>e.textContent=n);
 $("whoinfo").textContent="검수할 번호: "+a+" ~ "+b+" ("+(b-a+1)+"장)";
 $("packpath").textContent=term()==="wsl"?"탐색기 주소창에 \\\\wsl$\\Ubuntu\\home\\<사용자>\\group_3\\data\\share 를 붙여넣으면 파일이 보입니다. (WSL 에 프로젝트가 있는 경우)":"프로젝트 폴더 안의 data\\share 폴더에 만들어집니다."}
sel.onchange=render;document.querySelectorAll("input[name=term]").forEach(r=>r.onchange=render);render();

// 파일 받기·올리기
const kb=n=>n>1048576?(n/1048576).toFixed(1)+" MB":Math.max(1,Math.round(n/1024))+" KB";
function frow(f,link){const li=document.createElement("li");
 const a=document.createElement(link?"a":"span");a.textContent=f.name;if(link)a.href="/api/download?pin="+PIN+"&name="+encodeURIComponent(f.name);
 const s=document.createElement("span");s.className="muted";s.textContent=kb(f.size)+" · "+f.time;li.append(a,s);return li}
const empty=t=>Object.assign(document.createElement("li"),{textContent:t});
async function refresh(){
 const r=await fetch("/api/list?pin="+PIN);
 if(r.status==403){$("pinmsg").textContent="번호가 맞지 않습니다.";return false}
 if(r.status==429){$("pinmsg").textContent="너무 많이 틀렸습니다. 잠시 뒤에 다시 하세요.";return false}
 const d=await r.json();
 $("send").replaceChildren(...(d.send.length?d.send.map(f=>frow(f,true)):[empty("내려받을 파일이 없습니다.")]));
 $("recv").replaceChildren(...(d.received.length?d.received.map(f=>frow(f,false)):[empty("아직 없습니다.")]));
 return true}
$("go").onclick=async()=>{PIN=$("pin").value.trim();$("pinmsg").textContent="";
 if(await refresh()){$("pinbox").hidden=true;$("filesmain").hidden=false}};
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

    def __init__(self, address, base_dir, pin, max_mb=50, log=print, assign=None):
        super().__init__(address, Handler)
        self.page = PAGE.replace("__ASSIGN__", json.dumps(assign or parse_assign(DEFAULT_ASSIGN), ensure_ascii=False))
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
            return self._send(200, self.server.page.encode("utf-8"), "text/html; charset=utf-8")
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
    ap.add_argument("--host", default="0.0.0.0", help="접속을 받을 주소. 이 PC 안에서만 시험하려면 127.0.0.1 (기본: 같은 네트워크의 다른 PC 도 접속 가능)")
    ap.add_argument("--max-mb", type=float, default=50, help="올릴 수 있는 zip 의 최대 크기(MB)")
    ap.add_argument("--minutes", type=float, default=120, help="이 시간이 지나면 서버를 저절로 끈다")
    ap.add_argument("--assign", default=DEFAULT_ASSIGN, help="검수자별 번호 범위 (예: 김동훈:1-300,이후영:301-600,지혜성:601-900)")
    args = ap.parse_args(argv)
    pin = f"{secrets.randbelow(10000):04d}"
    try:
        assign = parse_assign(args.assign)
    except ValueError as e:
        print(e)
        return 2
    try:
        server = ShareServer((args.host, args.port), Path(args.dir).expanduser(), pin, args.max_mb,
                             log=lambda m: print(f"  {time.strftime('%H:%M:%S')} {m}", flush=True), assign=assign)
    except OSError as e:
        print(f"서버를 시작하지 못했습니다: {e}\n(이미 같은 포트로 실행 중인 서버가 있으면 그 창을 먼저 닫으세요.)")
        return 2
    print("=" * 62)
    print("  결과 주고받기 서버가 켜졌습니다.")
    print("  다른 PC 의 브라우저 주소창에 아래 중 하나를 입력하세요. (화면 위쪽 탭에 단계별 가이드가 있습니다)")
    addresses = local_addresses() if args.host in ("0.0.0.0", "") else [args.host]
    for ip in addresses:
        print(f"      http://{ip}:{args.port}")
    if args.host not in ("0.0.0.0", ""):
        print("      (시험용: 이 PC 안에서만 접속됩니다)")
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
