"""폴더·사진을 창에 끌어다 놓기 (Drag & Drop).

Tkinter 에는 끌어다 놓기가 없어서 tkinterdnd2 (선택 설치) 를 쓴다.
설치되어 있지 않으면 끌어다 놓기만 꺼지고, 나머지 기능은 그대로 동작한다.  →  pip install tkinterdnd2
"""
import re
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from urllib.parse import unquote

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:                      # 설치 안 됨 → 끌어다 놓기 없이 실행
    DND_FILES = TkinterDnD = None

_WINDOWS_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def make_root():
    """끌어다 놓기가 가능하면 TkinterDnD.Tk(), 아니면 일반 tk.Tk()."""
    if TkinterDnD is not None:
        try:
            return TkinterDnD.Tk()
        except Exception:                # tkdnd 라이브러리를 읽지 못한 환경
            pass
    return tk.Tk()


def drop_available(widget):
    """이 창에서 끌어다 놓기를 쓸 수 있는가?"""
    return DND_FILES is not None and hasattr(widget, "drop_target_register")


def register_drop(widget, callback):
    """widget 위에 파일·폴더를 놓으면 callback(경로 문자열 목록) 을 부른다."""
    if not drop_available(widget):
        return False
    widget.drop_target_register(DND_FILES)

    def on_drop(event):
        callback([to_local_path(p) for p in widget.tk.splitlist(event.data)])
        return event.action
    widget.dnd_bind("<<Drop>>", on_drop)
    return True


def to_local_path(text):
    """놓은 항목의 경로를 이 프로그램이 읽을 수 있는 경로로 바꾼다.

    - file:///... 주소 → 보통 경로
    - WSL 에서 C:\\... 또는 \\\\wsl.localhost\\... (Windows 경로) → /mnt/c/... (wslpath)
    """
    text = text.strip()
    if text.startswith("file://"):
        text = unquote(text[len("file://"):])
        if text.startswith("localhost/"):
            text = text[len("localhost"):]
    if (_WINDOWS_PATH.match(text) or text.startswith("\\\\")) and shutil.which("wslpath"):
        try:
            out = subprocess.run(["wslpath", "-u", text], capture_output=True, text=True, check=True).stdout.strip()
            if out:
                return out
        except (OSError, subprocess.SubprocessError):
            pass
    return text


def pick_target(paths):
    """놓은 항목들 중 쓸 것 하나를 고른다 → ("folder" | "image", Path) 또는 None.

    폴더가 있으면 첫 폴더를, 없으면 첫 JPG 사진을 쓴다.
    """
    items = [Path(p) for p in paths if p]
    for p in items:
        if p.is_dir():
            return "folder", p
    for p in items:
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg"):
            return "image", p
    return None
