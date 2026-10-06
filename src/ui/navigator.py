"""사진 목록 · 이전/다음 · 진행률.  (화면 코드 없음 — main_window.py 에서 import 해서 사용)"""
import re
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg"}


def _natural_key(p):
    """img2.jpg 가 img10.jpg 보다 앞에 오도록 숫자를 숫자로 비교한다."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


class ImageNavigator:
    def __init__(self):
        self.folder = None     # 지금 목록을 만든 폴더
        self.files = []        # 같은 폴더의 사진 목록 (정렬됨)
        self.index = -1        # 현재 사진 번호 (0부터)
        self.fixed = False     # True = 폴더째 연 목록 (set_folder)

    def set_folder(self, folder):
        """폴더 하나를 통째로 목록으로 쓴다 (끌어다 놓기·폴더 열기). 사진 수를 돌려준다.

        폴더 바로 아래에 사진이 있으면 그것만, 없으면 하위 폴더(images/train 등)까지 찾는다.
        이 목록은 그 안의 사진을 열어도 유지된다.
        """
        folder = Path(folder)
        direct = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        found = direct or [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        self.folder = folder
        self.files = sorted(found, key=lambda p: (str(p.parent).lower(), _natural_key(p)))
        self.index = -1
        self.fixed = True
        return len(self.files)

    def set_current(self, path):
        """현재 사진을 지정한다. 폴더가 바뀌었으면 목록을 다시 만든다."""
        path = Path(path)
        if self.fixed and path in self.files:        # 폴더째 연 목록 안의 사진이면 목록을 그대로 둔다
            self.index = self.files.index(path)
            return
        self.fixed = False
        if self.folder != path.parent or path not in self.files:
            self.folder = path.parent
            self.files = sorted((p for p in self.folder.iterdir()
                                 if p.is_file() and p.suffix.lower() in IMAGE_EXTS), key=_natural_key)
        try:
            self.index = self.files.index(path)
        except ValueError:                      # 목록에 없으면 이 사진 1장만 있는 것으로 처리
            self.files, self.index = [path], 0

    @property
    def total(self):
        return len(self.files)

    def has_prev(self):
        return self.index > 0

    def has_next(self):
        return 0 <= self.index < self.total - 1

    def prev_path(self):
        """이전 사진 경로 (없으면 None). 번호는 set_current 가 불릴 때 바뀐다."""
        return self.files[self.index - 1] if self.has_prev() else None

    def next_path(self):
        return self.files[self.index + 1] if self.has_next() else None

    def progress_text(self):
        if self.index < 0:
            return "0 / 0"
        return f"{self.index + 1} / {self.total}"