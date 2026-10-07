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
<meta name="color-scheme" content="light dark">
<title>결과 주고받기</title>
<style>
 :root{--bg:#f5f7fb;--card:#fff;--line:#e3e8f0;--text:#1c2433;--muted:#5d6b82;--accent:#3366ff;--accent-2:#2450d6;--accent-soft:#eaf0ff;
  --ok:#0f8a4b;--ok-soft:#e7f6ee;--bad:#d03b3b;--bad-soft:#fdeceb;--warn-soft:#fff6dd;--warn-line:#f0d58a;--code:#101827;--shadow:0 1px 2px rgba(16,24,40,.06),0 4px 14px rgba(16,24,40,.05)}
 @media (prefers-color-scheme:dark){:root{--bg:#0e1420;--card:#171f2e;--line:#2a3548;--text:#e8edf6;--muted:#9aa8bf;--accent:#6c8cff;--accent-2:#8aa4ff;--accent-soft:#1d2a4d;
  --ok:#4cc58a;--ok-soft:#123525;--bad:#ff7b7b;--bad-soft:#3b1a1a;--warn-soft:#3a3115;--warn-line:#6d5b21;--code:#0a0f19;--shadow:none}}
 *{box-sizing:border-box} html{scroll-behavior:smooth}
 body{margin:0;background:var(--bg);color:var(--text);font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',system-ui,sans-serif;line-height:1.65;-webkit-font-smoothing:antialiased}
 main{max-width:820px;margin:0 auto;padding:22px 16px 80px}
 header.top{display:flex;align-items:center;gap:14px;margin:4px 0 18px}
 .logo{flex:none;width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--accent),#7a5cff);display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:var(--shadow)}
 header h1{font-size:22px;margin:0;line-height:1.25} header p{margin:2px 0 0;color:var(--muted);font-size:13.5px}
 .pill{margin-left:auto;font-size:12px;padding:5px 11px;border-radius:999px;background:var(--ok-soft);color:var(--ok);font-weight:600;white-space:nowrap}
 nav.tabs{display:flex;gap:4px;padding:4px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);position:sticky;top:8px;z-index:5;margin-bottom:16px}
 nav.tabs button{flex:1;display:flex;align-items:center;justify-content:center;gap:7px;border:0;background:transparent;color:var(--muted);padding:10px 8px;border-radius:10px;font-size:14.5px;font-weight:600;cursor:pointer;font-family:inherit}
 nav.tabs button:hover{background:var(--accent-soft);color:var(--accent)} nav.tabs button.on{background:var(--accent);color:#fff}
 nav.tabs svg{width:17px;height:17px;flex:none}
 section.tab{display:none;animation:fade .18s ease} section.tab.on{display:block} @keyframes fade{from{opacity:.4;transform:translateY(3px)}to{opacity:1;transform:none}}
 .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:14px 0;box-shadow:var(--shadow)}
 h2{font-size:17px;margin:0 0 10px} h3{font-size:14.5px;margin:16px 0 6px;color:var(--muted)}
 .row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:8px 0}
 .muted{color:var(--muted);font-size:13px} .ok{color:var(--ok)} .bad{color:var(--bad)}
 select{font-size:15.5px;padding:9px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--text);font-family:inherit}
 label.pick{display:inline-flex;gap:6px;align-items:center;padding:7px 12px;border:1px solid var(--line);border-radius:10px;cursor:pointer;font-size:14px}
 label.pick:has(input:checked){border-color:var(--accent);background:var(--accent-soft);color:var(--accent);font-weight:600}
 .btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:0;border-radius:10px;padding:9px 16px;font-size:14.5px;font-weight:600;cursor:pointer;text-decoration:none;font-family:inherit;transition:transform .08s,background .15s}
 .btn:active{transform:scale(.97)} .btn svg{width:17px;height:17px}
 .btn.primary{background:var(--accent);color:#fff} .btn.primary:hover{background:var(--accent-2)}
 .btn.ghost{background:transparent;color:var(--muted);border:1px solid var(--line)} .btn.ghost:hover{color:var(--accent);border-color:var(--accent)}
 .btn.small{padding:6px 11px;font-size:13px}
 .progress{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:6px 0} .progress>i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--accent),#7a5cff);border-radius:99px;transition:width .2s}

 /* 가이드 단계 */
 .step{display:flex;gap:14px;align-items:flex-start;transition:opacity .2s}
 .step .num{flex:none;width:32px;height:32px;border-radius:50%;background:var(--accent);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:1px;font-size:14px}
 .step .body{flex:1;min-width:0} .step h2{margin-bottom:6px}
 .step.done{opacity:.55} .step.done .num{background:var(--ok)} .step.done .num span{display:none} .step.done .num::after{content:"✓"}
 .donebtn{margin-left:auto;flex:none}
 .stephead{display:flex;align-items:center;gap:8px}
 ul,ol{margin:6px 0 6px 20px;padding:0} li{margin:4px 0}
 pre{position:relative;background:var(--code);color:#e2e8f0;border-radius:11px;padding:12px 78px 12px 14px;margin:9px 0;overflow-x:auto;font-size:13.5px;line-height:1.55;white-space:pre-wrap;word-break:break-all;font-family:Consolas,'D2Coding',monospace}
 pre button{position:absolute;top:8px;right:8px;font-size:12px;padding:5px 10px;background:#33415c;color:#fff;border:0;border-radius:7px;cursor:pointer;font-family:inherit}
 pre button:hover{background:#46567a}
 code{background:var(--accent-soft);color:var(--accent);border-radius:5px;padding:1px 6px;font-size:13.2px;font-family:Consolas,'D2Coding',monospace}
 pre code{background:none;color:inherit;padding:0} kbd{background:var(--card);border:1px solid var(--line);border-bottom-width:2px;border-radius:6px;padding:1px 7px;font-size:12.5px;font-family:inherit}
 .note,.warn,.good{border-radius:11px;padding:10px 14px;margin:10px 0;font-size:14px;border:1px solid}
 .note{background:var(--warn-soft);border-color:var(--warn-line)} .warn{background:var(--bad-soft);border-color:var(--bad)} .good{background:var(--ok-soft);border-color:var(--ok)}
 table{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0;border:1px solid var(--line);border-radius:10px;overflow:hidden} td,th{border-bottom:1px solid var(--line);padding:8px 11px;text-align:left} th{background:var(--accent-soft)}
 tr:last-child td{border-bottom:0}
 .flow{font-family:Consolas,'D2Coding',monospace;font-size:12.8px;white-space:pre;overflow-x:auto;background:var(--accent-soft);border-radius:11px;padding:12px 14px}

 /* 파일 탭 */
 .lock{text-align:center;padding:30px 20px} .lock h2{font-size:19px}
 .pin{display:flex;gap:10px;justify-content:center;margin:16px 0 6px}
 .pin input{width:58px;height:68px;font-size:30px;text-align:center;border:2px solid var(--line);border-radius:14px;background:var(--bg);color:var(--text);font-family:inherit;outline:none;transition:border-color .15s,transform .1s}
 .pin input:focus{border-color:var(--accent);transform:translateY(-2px)} .pin.err input{border-color:var(--bad);animation:shake .3s}
 @keyframes shake{25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}
 .bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:2px 0 4px}
 .bar .status{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--ok);font-weight:600} .bar .status::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--ok)}
 .bar .sp{flex:1}
 ul.files{list-style:none;margin:0;padding:0}
 ul.files li{display:flex;align-items:center;gap:12px;padding:12px 4px;border-top:1px solid var(--line)} ul.files li:first-child{border-top:0}
 .ficon{flex:none;width:40px;height:40px;border-radius:10px;background:var(--accent-soft);color:var(--accent);display:flex;align-items:center;justify-content:center}
 .ficon svg{width:21px;height:21px} .ficon.recv{background:var(--ok-soft);color:var(--ok)}
 .finfo{flex:1;min-width:0} .fname{font-weight:600;word-break:break-all;font-size:14.5px} .fmeta{color:var(--muted);font-size:12.8px}
 .badge{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;background:var(--accent);color:#fff;margin-left:6px;vertical-align:1px}
 .empty{color:var(--muted);font-size:14px;padding:16px 4px;text-align:center}
 .drop{border:2px dashed var(--line);border-radius:16px;padding:30px 16px;text-align:center;cursor:pointer;transition:all .15s;background:var(--bg);display:block;width:100%;font-family:inherit;color:inherit}
 .drop:hover,.drop:focus-visible{border-color:var(--accent);outline:none} .drop.over{border-color:var(--accent);background:var(--accent-soft);transform:scale(1.01)}
 .drop *{pointer-events:none}
 .drop svg{width:44px;height:44px;color:var(--accent);margin-bottom:6px} .drop .big{font-size:16.5px;font-weight:700} .drop .small{color:var(--muted);font-size:13px;margin-top:3px}
 .qitem{padding:10px 4px;border-top:1px solid var(--line);font-size:14px} .qitem:first-child{border-top:0}
 .qhead{display:flex;justify-content:space-between;gap:10px} .qname{font-weight:600;word-break:break-all}
 .qstate{flex:none;font-size:13px;font-weight:600} .qmsg{font-size:13px;margin-top:2px}
 #toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,30px);background:#1c2433;color:#fff;padding:11px 18px;border-radius:12px;font-size:14px;opacity:0;pointer-events:none;transition:all .22s;z-index:50;max-width:92vw;box-shadow:0 8px 24px rgba(0,0,0,.25)}
 #toast.show{opacity:1;transform:translate(-50%,0)} #toast.bad{background:#b3261e}
 @media (max-width:560px){main{padding:14px 10px 70px}.card{padding:15px 14px}nav.tabs button{font-size:13px;padding:9px 4px}nav.tabs svg{display:none}.pin input{width:50px;height:60px}.pill{display:none}}
</style></head><body><main>

<header class="top">
 <div class="logo"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h11l-3-3M17 17H6l3 3"/></svg></div>
 <div><h1>결과 주고받기</h1><p>검수 결과를 같은 네트워크 안에서 주고받는 임시 페이지</p></div>
 <span class="pill">같은 와이파이 전용</span>
</header>

<nav class="tabs" role="tablist">
 <button data-tab="rv" class="on" role="tab"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>검수자 가이드</button>
 <button data-tab="pm" role="tab"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>PM 가이드 (전체 흐름)</button>
 <button data-tab="files" role="tab"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>파일 받기·올리기</button>
</nav>

<!-- ───────────────────────── 검수자 가이드 ───────────────────────── -->
<section class="tab on" id="tab-rv">
 <div class="card">
  <h2>먼저 내 이름을 고르세요 <span class="muted">(고른 값과 완료 표시는 이 브라우저에 기억됩니다)</span></h2>
  <div class="row"><select id="who"></select><span id="whoinfo" class="muted"></span></div>
  <div class="row"><b style="font-size:14px">VS Code 터미널 종류</b>
   <label class="pick"><input type="radio" name="term" value="wsl" checked> WSL (Ubuntu)</label>
   <label class="pick"><input type="radio" name="term" value="win"> Windows (PowerShell)</label></div>
  <div class="muted">터미널 왼쪽 위 이름이 <b>WSL 또는 Ubuntu</b>이면 위쪽, <b>powershell</b>이면 아래쪽을 고르세요. 아래 명령이 자동으로 바뀝니다.</div>
  <div style="margin-top:12px"><div class="muted" id="rvprog"></div><div class="progress"><i id="rvbar"></i></div></div>
 </div>

 <div class="card step" data-step="0"><div class="num"><span>0</span></div><div class="body">
  <div class="stephead"><h2>처음 한 번: 최신 도구 받기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  VS Code 에서 프로젝트 폴더를 열고, 터미널에 입력합니다.
  <pre>git pull origin main</pre>
  <div class="note">오류가 나면 화면의 문구를 PM 에게 알려 주세요. 작업 중이던 검수표(<code>manifests\dataset_manifest.csv</code>)가 있다면 먼저 다른 이름으로 복사해 두세요.</div>
 </div></div>

 <div class="card step" data-step="1"><div class="num"><span>1</span></div><div class="body">
  <div class="stephead"><h2>파일 받기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  <ol><li>아래 버튼으로 <b>파일 받기·올리기</b> 탭에 갑니다. <button class="btn primary small" onclick="showTab('files')" type="button">탭으로 이동</button></li>
  <li>PM 이 알려 준 <b>4자리 번호</b>를 입력합니다. (4칸을 다 채우면 자동으로 열립니다)</li>
  <li>목록의 <b>[내려받기]</b> 버튼을 누르면 zip 이 저장됩니다. 보통 <code>다운로드</code> 폴더에 들어갑니다.</li></ol>
 </div></div>

 <div class="card step" data-step="2"><div class="num"><span>2</span></div><div class="body">
  <div class="stephead"><h2>C 드라이브에 <code>받은결과</code> 폴더를 만들고 풀기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  <ol><li>탐색기에서 <b>C 드라이브</b>를 열고 새 폴더 <code>받은결과</code>를 만듭니다. (<code>C:\받은결과</code>) 이미 있으면 안의 내용을 모두 지웁니다.</li>
  <li>받은 zip 을 우클릭 ▸ <b>압축 풀기</b>(모두 압축 풀기)에서 위치를 <code>C:\받은결과</code>로 정합니다.</li></ol>
  <div class="good"><b>확인:</b> <code>C:\받은결과</code>를 열었을 때 바로 <code>검수표.csv</code>와 <code>이물검출_학습데이터1</code> 폴더가 보여야 합니다.</div>
  <div class="warn"><code>C:\받은결과\결과_2026…</code> 처럼 폴더가 <b>한 겹 더</b> 생겼다면 안쪽 내용을 위(<code>C:\받은결과</code>)로 꺼내 주세요. 그래야 아래 명령이 파일을 찾습니다.</div>
 </div></div>

 <div class="card step" data-step="3"><div class="num"><span>3</span></div><div class="body">
  <div class="stephead"><h2>내 검수표는 이름만 바꿔 치워 두기 (충돌 방지)</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  <ol><li>라벨링 프로그램을 <b>끕니다.</b></li>
  <li>VS Code 왼쪽 탐색기에서 <code>manifests</code> 폴더의 <code>dataset_manifest.csv</code>를 우클릭 ▸ <b>이름 바꾸기</b> ▸ <code>dataset_manifest.내것.csv</code></li></ol>
  <div class="note"><b>왜 하나요?</b> 받은 검수표에는 900장이 모두 들어 있습니다. 내 옛 파일과 합치면 같은 사진이 다르게 적혀 <b>충돌</b>이 날 수 있어서, 내 파일은 지우지 말고 이름만 바꿔 둡니다. 나중에 필요하면 이름을 되돌릴 수 있습니다. 파일이 없으면 건너뛰어도 됩니다.</div>
 </div></div>

 <div class="card step" data-step="4"><div class="num"><span>4</span></div><div class="body">
  <div class="stephead"><h2>명령 2개로 내 PC에 가져오기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  VS Code 터미널(프로젝트 폴더)에서 <b>한 줄씩</b> 실행합니다.
  <h3>① 라벨(txt) 가져오기</h3>
  <pre data-cmd="import"></pre>
  <div class="good">이렇게 나오면 정상: 마지막에 <code>…개를 복사했습니다.</code>가 나오고, 덮어쓴 파일이 있으면 <code>…에 백업해 두었습니다</code>도 나옵니다.</div>
  <div class="warn"><b><code>--overwrite</code>를 꼭 붙이세요.</b> 내 PC 에는 이전에 받은 <b>옛 라벨</b>이 남아 있을 수 있습니다. 붙이지 않으면 내용이 다른 라벨은 <b>복사하지 않고 건너뛰어서</b> 새 라벨이 하나도 안 들어옵니다. (검수표만 새것이 되고 라벨은 원본 그대로 보이는 증상)<br>
  덮어쓰기 전의 내 라벨은 <code>data/backup</code> 에 자동으로 백업됩니다. <b>검수를 시작하기 전에</b> 실행하세요. 이미 검수하며 저장했다면 <code>data/work</code> 를 먼저 복사해 두세요.</div>
  <h3>② 검수표 가져오기</h3>
  <pre data-cmd="merge"></pre>
  <div class="good">이렇게 나오면 정상: <code>합친 결과: 900줄</code> · <code>원본 사진 900장 중 검수표에 줄이 없는 사진: 0장</code> · 마지막에 <code>저장했습니다</code></div>
  <div class="warn"><b>"충돌"이라고 나오거나 줄 수가 900이 아니면</b> 3단계(내 검수표 이름 바꾸기)를 건너뛴 것입니다. 3단계를 하고 ②를 다시 실행하세요.</div>
 </div></div>

 <div class="card step" data-step="5"><div class="num"><span>5</span></div><div class="body">
  <div class="stephead"><h2>검수하기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  <ol><li>라벨링 프로그램을 켭니다.</li>
  <li><kbd>Ctrl</kbd>+<kbd>G</kbd>를 눌러 <b id="startno">내 시작 번호</b>로 이동합니다.</li>
  <li>검수자 칸에 <b>내 이름을 한 번</b> 씁니다. 다음 사진부터는 자동으로 채워집니다.</li>
  <li>한 장씩 보고: 맞으면 <kbd>Enter</kbd> · 틀리면 BBox 를 고치고 <kbd>Enter</kbd> · 애매하면 <kbd>R</kbd> 후 이유를 쓰고 <kbd>Enter</kbd></li>
  <li><b>이미지 유형도 꼭 고르세요.</b> 안 고르면 <kbd>Enter</kbd>가 넘어가지 않고 그 칸이 빨갛게 깜빡입니다. <kbd>Ctrl</kbd>+<kbd>1</kbd> 김치+대상 객체 · <kbd>Ctrl</kbd>+<kbd>2</kbd> 정상 김치 · <kbd>Ctrl</kbd>+<kbd>3</kbd> 대상 객체 단독 · <kbd>Ctrl</kbd>+<kbd>4</kbd> 판단 어려움</li>
  <li>BBox 를 지울 때는 선택(클릭 또는 <kbd>Tab</kbd>)한 뒤 <kbd>Delete</kbd> 를 누릅니다. 잘못 지웠으면 <kbd>Ctrl</kbd>+<kbd>Z</kbd></li></ol>
  <div class="warn"><b>내 번호 범위(<span class="rng">내 범위</span>)의 사진만 저장하세요.</b> 다른 사람 범위를 저장하면 합칠 때 서로 덮어씁니다.</div>
 </div></div>

 <div class="card step" data-step="6"><div class="num"><span>6</span></div><div class="body">
  <div class="stephead"><h2>검수가 끝나면 내 범위만 묶기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  프로그램을 끄고 터미널에서 실행합니다.
  <pre data-cmd="pack"></pre>
  <div class="good">끝에 <code>라벨(txt) 300개, 검수표 300줄</code>이 나오면 정상입니다. 파일은 프로젝트의 <code>data\share</code> 폴더에 <code>결과_<span class="nm">이름</span>_날짜_시각.zip</code>으로 만들어집니다.</div>
  <div id="packpath" class="muted"></div>
  <div class="warn"><b>라벨 개수가 내 장수와 다르거나 0개이면</b> 내가 저장한 라벨이 <code>data\work</code> 안의 다른 위치에 있을 수 있습니다. 사진 폴더 구조가 다른 PC 에서는 <code>work\data\labels\파일.txt</code> 처럼 저장되기도 합니다. 내 PC 에 txt 가 몇 개, 어느 폴더에 있는지 확인하세요.
   <pre>find data/work -name "*.txt" -printf "%h\n" | sort | uniq -c</pre>
   <div class="muted">Windows(PowerShell)는: <code>Get-ChildItem data\work -Recurse -Filter *.txt | Group-Object DirectoryName | Select-Object Count, Name</code></div>
   저장한 라벨이 어디에도 없으면 프로그램에서 해당 사진을 다시 열어 저장해야 합니다. PM 에게 알려 주세요.</div>
 </div></div>

 <div class="card step" data-step="7"><div class="num"><span>7</span></div><div class="body">
  <div class="stephead"><h2>이 페이지에 올리기</h2><button class="btn ghost small donebtn" type="button">완료</button></div>
  <ol><li><b>파일 받기·올리기</b> 탭으로 가서 6단계의 zip 을 <b>끌어다 놓거나</b> 눌러서 고릅니다. 놓으면 <b>바로 올라갑니다.</b> <button class="btn primary small" onclick="showTab('files')" type="button">탭으로 이동</button></li>
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

 <div class="card step"><div class="num"><span>①</span></div><div class="body">
  <h2>합친 결과 묶기 (처음 한 번)</h2>
  PM PC 의 WSL(프로젝트 폴더)에서:
  <pre>python tools/pack_results.py</pre>
  <div class="muted">라벨 900개와 검수표 900줄이 <code>data/share/결과_날짜_시각.zip</code>으로 만들어집니다. 검수표의 작성자 칸이 정리된 최신 상태여야 합니다.</div>
 </div></div>

 <div class="card step"><div class="num"><span>②</span></div><div class="body">
  <h2>서버 켜기</h2>
  <ol><li><b>방화벽 규칙</b>(PM PC 에서 한 번만, 관리자 PowerShell):
   <pre>New-NetFirewallRule -DisplayName "라벨공유 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private</pre></li>
  <li><code>공유시작.bat</code>을 더블클릭합니다. 방화벽 창이 뜨면 <b>개인 네트워크</b>만 허용합니다.</li>
  <li>검은 창에 나오는 <b>접속 주소</b>와 <b>4자리 번호</b>를 확인합니다.</li></ol>
 </div></div>

 <div class="card step"><div class="num"><span>③</span></div><div class="body">
  <h2>검수자에게 알려 주기</h2>
  <ul><li>접속 주소: <b id="myurl"></b></li><li>4자리 번호 (검은 창에 표시된 것)</li><li>"이 페이지의 <b>검수자 가이드</b>를 따라 하세요"</li></ul>
  <div class="note">검수자 PC 에도 최신 도구가 필요합니다. 먼저 <code>git pull origin main</code> 을 하라고 알려 주세요. (<code>tools/pack_results.py</code> 가 있어야 자기 범위를 묶을 수 있습니다.)</div>
 </div></div>

 <div class="card step"><div class="num"><span>④</span></div><div class="body">
  <h2>올라온 결과 확인</h2>
  <ul><li>이 페이지의 <b>파일 받기·올리기</b> 탭 ▸ <b>받은 파일</b>에 3개(김동훈·이후영·지혜성)가 보이는지 확인합니다.</li>
  <li>폴더로도 볼 수 있습니다: <code>C:\공유\받은결과</code> (zip) · <code>C:\공유\받은결과\풀림</code> (자동으로 풀린 라벨과 검수표)</li>
  <li>풀림 폴더에 <code>검수표_김동훈.csv</code>, <code>검수표_이후영.csv</code>, <code>검수표_지혜성.csv</code> 가 있어야 합니다.</li></ul>
 </div></div>

 <div class="card step"><div class="num"><span>⑤</span></div><div class="body">
  <h2>명령 2개로 합치기</h2>
  PM PC 의 WSL(프로젝트 폴더)에서 <b>한 줄씩</b>:
  <pre>python tools/import_labels.py /mnt/c/공유/받은결과/풀림 --apply --overwrite</pre>
  <pre>python tools/merge_manifests.py /mnt/c/공유/받은결과/풀림 --apply</pre>
  <ul><li>첫 줄: 검수하며 고친 라벨을 내 <code>data/work</code>에 반영합니다.</li>
  <li>둘째 줄: 검수표 3개와 내 검수표를 하나로 합칩니다. 내 기존 파일은 <code>manifests</code> 폴더에 <code>백업-날짜</code>로 자동 보관됩니다.</li>
  <li>같은 사진이 다르게 적히면(충돌) 검수일이 늦은 줄이 이기고 화면에 알려 줍니다.</li></ul>
 </div></div>

 <div class="card step"><div class="num"><span>⑥</span></div><div class="body">
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

 <div class="card step"><div class="num"><span>⑦</span></div><div class="body">
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
 <div class="card lock" id="pinbox">
  <h2>접속 번호를 입력하세요</h2>
  <div class="muted">서버를 켠 PM PC 의 검은 창에 표시된 4자리 번호입니다.</div>
  <div class="pin" id="pinrow">
   <input inputmode="numeric" pattern="[0-9]*" maxlength="1" autocomplete="off" aria-label="번호 1번째 자리">
   <input inputmode="numeric" pattern="[0-9]*" maxlength="1" autocomplete="off" aria-label="번호 2번째 자리">
   <input inputmode="numeric" pattern="[0-9]*" maxlength="1" autocomplete="off" aria-label="번호 3번째 자리">
   <input inputmode="numeric" pattern="[0-9]*" maxlength="1" autocomplete="off" aria-label="번호 4번째 자리">
  </div>
  <div id="pinmsg" class="bad" style="min-height:22px" role="alert"></div>
 </div>

 <div id="filesmain" hidden>
  <div class="bar"><span class="status">연결됨</span><span class="sp"></span>
   <button class="btn ghost small" id="refresh" type="button">새로고침</button>
   <button class="btn ghost small" id="relock" type="button">번호 다시 입력</button></div>

  <div class="card">
   <h2>내려받기 <span class="muted">PM 이 내놓은 파일</span></h2>
   <ul class="files" id="send"></ul>
  </div>

  <div class="card">
   <h2>올리기 <span class="muted">라벨(txt)과 검수표(csv)만 든 zip · 최대 __MAXMB__MB</span></h2>
   <div class="drop" id="drop" role="button" tabindex="0" aria-label="zip 파일을 끌어다 놓거나 눌러서 고르기">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 16.2A4.5 4.5 0 0 0 17.5 8h-1.8A7 7 0 1 0 4 14.9"/><path d="M12 12v9M8 16l4-4 4 4"/></svg>
    <div class="big">zip 파일을 여기로 끌어다 놓으세요</div>
    <div class="small">놓으면 <b>바로 올라갑니다.</b> 눌러서 파일을 고를 수도 있어요. 여러 개도 한 번에 됩니다.</div>
   </div>
   <input type="file" id="file" accept=".zip" multiple hidden>
   <div id="queue"></div>
   <h3>받은 파일</h3>
   <ul class="files" id="recv"></ul>
  </div>
 </div>
</section>

<div id="toast" role="status" aria-live="polite"></div>

<script>
const ASSIGN=__ASSIGN__;
const MAXMB=__MAXMB__;
let PIN="";
const $=id=>document.getElementById(id);
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
const sstore={get(k){try{return sessionStorage.getItem(k)}catch(e){return null}},set(k,v){try{v==null?sessionStorage.removeItem(k):sessionStorage.setItem(k,v)}catch(e){}}};
const names=Object.keys(ASSIGN);
const ICON={zip:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M10 12h2M10 16h2M12 14h2"/></svg>',
 down:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>'};

let toastTimer=null;
function toast(msg,bad){const t=$("toast");t.textContent=msg;t.className="show"+(bad?" bad":"");clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.className="",2600)}
function showTab(t){document.querySelectorAll("section.tab").forEach(s=>s.classList.toggle("on",s.id==="tab-"+t));
 document.querySelectorAll("nav.tabs button").forEach(b=>b.classList.toggle("on",b.dataset.tab===t));window.scrollTo({top:0});
 if(t==="files"&&!$("pinbox").hidden){const f=[...document.querySelectorAll("#pinrow input")].find(i=>!i.value);if(f)f.focus()}}
document.querySelectorAll("nav.tabs button").forEach(b=>b.onclick=()=>showTab(b.dataset.tab));

// ── 가이드: 이름·터미널 선택, 명령 자동 바뀜, 단계 완료 체크 ──
const sel=$("who");names.forEach(n=>sel.add(new Option(n,n)));
const savedWho=store.get("rv-who");if(savedWho&&names.includes(savedWho))sel.value=savedWho;
const savedTerm=store.get("rv-term");if(savedTerm){const r=document.querySelector("input[name=term][value="+savedTerm+"]");if(r)r.checked=true}
const tbl=$("assigntable");
names.forEach(n=>{const [a,b]=ASSIGN[n];const tr=tbl.insertRow();tr.insertCell().textContent=n;tr.insertCell().textContent=a+" ~ "+b;tr.insertCell().textContent=(b-a+1)+"장"});
$("myurl").textContent=location.origin;
const term=()=>document.querySelector("input[name=term]:checked").value;
function cmds(){const n=sel.value,[a,b]=ASSIGN[n]||[1,1],w=term()==="wsl";
 const dir=w?"/mnt/c/받은결과":"C:\\받은결과";
 return {import:`python tools/import_labels.py ${dir} --apply --overwrite`,
  merge:`python tools/merge_manifests.py ${dir}${w?"/":"\\"}검수표.csv --apply`,
  pack:`python tools/pack_results.py --name ${n} --from ${a} --to ${b}`}}
function addCopy(pre){const btn=document.createElement("button");btn.textContent="복사";btn.type="button";
 btn.onclick=()=>{const text=pre.dataset.text;const done=()=>{btn.textContent="복사됨";toast("명령을 복사했어요");setTimeout(()=>btn.textContent="복사",1500)};
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(done)}
  else{const t=document.createElement("textarea");t.value=text;document.body.append(t);t.select();try{document.execCommand("copy")}catch(e){}t.remove();done()}};
 pre.append(btn)}
function render(){const n=sel.value,[a,b]=ASSIGN[n]||[1,1],c=cmds();
 document.querySelectorAll("pre[data-cmd]").forEach(p=>{p.dataset.text=c[p.dataset.cmd];p.textContent=c[p.dataset.cmd];addCopy(p)});
 document.querySelectorAll("pre:not([data-cmd])").forEach(p=>{if(!p.querySelector("button")){p.dataset.text=p.textContent;addCopy(p)}});
 $("startno").textContent=a+"번";document.querySelectorAll(".rng").forEach(e=>e.textContent=a+" ~ "+b+"번");
 document.querySelectorAll(".nm").forEach(e=>e.textContent=n);
 $("whoinfo").textContent="검수할 번호: "+a+" ~ "+b+" ("+(b-a+1)+"장)";
 $("packpath").textContent=term()==="wsl"?"탐색기 주소창에 \\\\wsl$\\Ubuntu\\home\\<사용자>\\group_3\\data\\share 를 붙여넣으면 파일이 보입니다. (WSL 에 프로젝트가 있는 경우)":"프로젝트 폴더 안의 data\\share 폴더에 만들어집니다.";
 store.set("rv-who",n);store.set("rv-term",term())}
sel.onchange=render;document.querySelectorAll("input[name=term]").forEach(r=>r.onchange=render);render();
const steps=[...document.querySelectorAll("#tab-rv .step")];
function progress(){const done=steps.filter(s=>s.classList.contains("done")).length;
 $("rvprog").textContent="내 진행: "+done+" / "+steps.length+" 단계 완료";$("rvbar").style.width=(done*100/steps.length)+"%"}
steps.forEach(s=>{const k="rv-step-"+s.dataset.step,b=s.querySelector(".donebtn");
 const apply=on=>{s.classList.toggle("done",on);b.textContent=on?"되돌리기":"완료"};
 apply(store.get(k)==="1");
 b.onclick=()=>{const on=!s.classList.contains("done");apply(on);store.set(k,on?"1":"0");progress();
  if(on){const nx=steps[steps.indexOf(s)+1];if(nx)nx.scrollIntoView({behavior:"smooth",block:"start"})}}});
progress();

// ── 파일 탭: 번호 4칸 ──
const pins=[...document.querySelectorAll("#pinrow input")];
pins.forEach((el,i)=>{
 el.addEventListener("input",()=>{el.value=el.value.replace(/\D/g,"").slice(0,1);$("pinrow").classList.remove("err");$("pinmsg").textContent="";
  if(el.value&&i<3)pins[i+1].focus();if(pins.every(p=>p.value))unlock(pins.map(p=>p.value).join(""))});
 el.addEventListener("keydown",e=>{if(e.key==="Backspace"&&!el.value&&i>0){pins[i-1].focus();pins[i-1].value=""}
  if(e.key==="ArrowLeft"&&i>0)pins[i-1].focus();if(e.key==="ArrowRight"&&i<3)pins[i+1].focus()});
 el.addEventListener("paste",e=>{const t=(e.clipboardData.getData("text")||"").replace(/\D/g,"").slice(0,4);if(!t)return;e.preventDefault();
  t.split("").forEach((c,j)=>pins[j].value=c);(pins[Math.min(t.length,3)]).focus();if(t.length===4)unlock(t)})});
function pinError(msg){$("pinmsg").textContent=msg;$("pinrow").classList.add("err");pins.forEach(p=>p.value="");pins[0].focus();sstore.set("pin",null)}

// ── 파일 목록 ──
const kb=n=>n>1048576?(n/1048576).toFixed(1)+" MB":Math.max(1,Math.round(n/1024))+" KB";
function frow(f,kind,first){const li=document.createElement("li");
 const ic=document.createElement("div");ic.className="ficon"+(kind==="recv"?" recv":"");ic.innerHTML=ICON.zip;
 const info=document.createElement("div");info.className="finfo";
 const nm=document.createElement("div");nm.className="fname";nm.textContent=f.name;
 if(kind==="send"&&first){const b=document.createElement("span");b.className="badge";b.textContent="최신";nm.append(b)}
 const meta=document.createElement("div");meta.className="fmeta";meta.textContent=kb(f.size)+" · "+f.time+(kind==="recv"?" · 받음":"");
 info.append(nm,meta);li.append(ic,info);
 if(kind==="send"){const a=document.createElement("a");a.className="btn primary";a.href="/api/download?pin="+PIN+"&name="+encodeURIComponent(f.name);a.setAttribute("download",f.name);
  a.innerHTML=ICON.down+"<span>내려받기</span>";a.onclick=()=>toast("내려받기를 시작했어요 — 브라우저의 다운로드 폴더를 확인하세요");li.append(a)}
 return li}
const emptyLi=t=>Object.assign(document.createElement("li"),{className:"empty",textContent:t});
let refreshTimer=null;
async function refresh(quiet){
 let r;try{r=await fetch("/api/list?pin="+PIN)}catch(e){if(!quiet)toast("서버에 연결할 수 없어요. PM PC 의 서버가 켜져 있나요?",true);return false}
 if(r.status===403){pinError("번호가 맞지 않습니다.");return false}
 if(r.status===429){pinError("너무 많이 틀렸습니다. 잠시 뒤에 다시 하세요.");return false}
 const d=await r.json();
 $("send").replaceChildren(...(d.send.length?d.send.map((f,i)=>frow(f,"send",i===0)):[emptyLi("내려받을 파일이 없습니다. (PM 이 아직 올리지 않았어요)")]));
 $("recv").replaceChildren(...(d.received.length?d.received.map(f=>frow(f,"recv")):[emptyLi("아직 받은 파일이 없습니다.")]));
 return true}
async function unlock(pin){PIN=pin;$("pinmsg").textContent="";
 if(await refresh()){sstore.set("pin",pin);$("pinbox").hidden=true;$("filesmain").hidden=false;
  clearInterval(refreshTimer);refreshTimer=setInterval(()=>{if(!document.hidden&&$("tab-files").classList.contains("on"))refresh(true)},8000)}}
$("refresh").onclick=async()=>{if(await refresh())toast("목록을 새로 불러왔어요")};
$("relock").onclick=()=>{PIN="";sstore.set("pin",null);clearInterval(refreshTimer);$("filesmain").hidden=true;$("pinbox").hidden=false;pins.forEach(p=>p.value="");pins[0].focus()};

// ── 올리기: 끌어다 놓기 · 자동 업로드 · 진행 막대 ──
const MAXB=MAXMB*1048576;
function qitem(name){const d=document.createElement("div");d.className="qitem";
 d.innerHTML='<div class="qhead"><span class="qname"></span><span class="qstate muted">대기</span></div><div class="progress"><i></i></div><div class="qmsg muted"></div>';
 d.querySelector(".qname").textContent=name;$("queue").prepend(d);return {el:d,bar:d.querySelector("i"),state:d.querySelector(".qstate"),msg:d.querySelector(".qmsg")}}
function setQ(q,cls,state,msg){q.state.className="qstate "+cls;q.state.textContent=state;q.msg.className="qmsg "+cls;q.msg.textContent=msg||""}
function sendOne(f,q){return new Promise(res=>{
 const x=new XMLHttpRequest();x.open("PUT","/api/upload?pin="+PIN+"&name="+encodeURIComponent(f.name));
 setQ(q,"muted","올리는 중…","");
 x.upload.onprogress=e=>{if(e.lengthComputable){q.bar.style.width=(e.loaded*100/e.total)+"%";q.state.textContent=Math.round(e.loaded*100/e.total)+"%"}};
 x.onload=()=>{let d={};try{d=JSON.parse(x.responseText)}catch(e){}
  if(x.status===200){q.bar.style.width="100%";setQ(q,"ok","완료 ✓","받았습니다: "+d.saved+" (라벨 "+d.labels+"개, 검수표 "+d.rows+"줄)");res(true)}
  else{setQ(q,"bad","실패",d.error||("올리지 못했습니다 ("+x.status+")"));res(false)}};
 x.onerror=()=>{setQ(q,"bad","실패","연결이 끊겼습니다. 서버 PC 가 켜져 있는지 확인하세요.");res(false)};
 x.send(f)})}
let uploading=false;
async function uploadFiles(list){
 if($("filesmain").hidden){toast("먼저 접속 번호를 입력하세요",true);showTab("files");return}
 const files=[...list];if(!files.length)return;
 showTab("files");if(uploading){toast("올리는 중인 파일이 끝나면 다시 올려 주세요",true);return}
 uploading=true;let okN=0;
 for(const f of files){const q=qitem(f.name);
  if(!f.name.toLowerCase().endsWith(".zip")){setQ(q,"bad","거부","zip 파일만 올릴 수 있습니다. (pack_results.py 로 만든 zip)");continue}
  if(f.size>MAXB){setQ(q,"bad","거부","파일이 너무 큽니다. (최대 "+MAXMB+"MB)");continue}
  if(await sendOne(f,q))okN++}
 uploading=false;await refresh(true);
 toast(okN===files.length?(okN+"개 올렸어요 ✓"):(okN+"개 올림, "+(files.length-okN)+"개는 실패했어요"),okN!==files.length)}
$("drop").onclick=()=>$("file").click();
$("drop").addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();$("file").click()}});
$("file").onchange=e=>{uploadFiles(e.target.files);e.target.value=""};
const drop=$("drop");
["dragenter","dragover"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add("over")}));
["dragleave","drop"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove("over")}));
drop.addEventListener("drop",e=>{e.stopPropagation();uploadFiles(e.dataTransfer.files)});
// 점선 영역 밖에 놓으면 브라우저가 파일을 열어 버려서 이 페이지를 벗어나므로, 그것만 막고 영역을 알려 준다
const hasFiles=e=>e.dataTransfer&&[...e.dataTransfer.types].includes("Files");
window.addEventListener("dragover",e=>{if(hasFiles(e))e.preventDefault()});
window.addEventListener("drop",e=>{if(!hasFiles(e))return;e.preventDefault();
 if(!$("filesmain").hidden){showTab("files");toast("점선 영역 안에 놓아 주세요",true)}else toast("먼저 접속 번호를 입력하세요",true)});

// 새로고침해도 번호를 다시 묻지 않게 (이 탭을 닫으면 지워진다)
const savedPin=sstore.get("pin");if(savedPin&&/^\d{4}$/.test(savedPin)){unlock(savedPin).then(()=>{if(!$("pinbox").hidden){$("pinmsg").textContent="서버가 다시 켜져서 번호가 바뀌었을 수 있어요. 새 번호를 입력하세요."}})}
</script></main></body></html>
"""


# ── 서버 ──────────────────────────────────────────────────────────────────
class ShareServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, base_dir, pin, max_mb=50, log=print, assign=None):
        super().__init__(address, Handler)
        self.page = (PAGE.replace("__ASSIGN__", json.dumps(assign or parse_assign(DEFAULT_ASSIGN), ensure_ascii=False))
                     .replace("__MAXMB__", f"{max_mb:g}"))
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
