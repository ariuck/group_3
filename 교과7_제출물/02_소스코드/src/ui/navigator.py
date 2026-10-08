"""사진 목록 · 이전/다음 · 진행률 · 보기 필터.  (화면 코드 없음 — main_window.py 에서 import 해서 사용)

all_files = 폴더에서 찾은 사진 전체,  files = 지금 보이는 사진(필터를 건 경우 걸러진 것).
이전/다음·번호·진행률은 모두 files(보이는 목록) 기준이다.
"""
import re
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg"}


def _natural_key(p):
    """img2.jpg 가 img10.jpg 보다 앞에 오도록 숫자를 숫자로 비교한다."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


class ImageNavigator:
    def __init__(self):
        self.folder = None     # 지금 목록을 만든 폴더
        self.all_files = []    # 찾은 사진 전체 (정렬됨)
        self.files = []        # 지금 보이는 사진 (필터가 없으면 all_files 와 같음)
        self.index = -1        # 현재 사진 번호 (files 안에서, 0부터)
        self.predicate = None  # 보기 필터: 사진 경로 → True/False (None 이면 전체)
        self.current = None    # 현재 사진 경로

    # ── 목록 만들기 ──────────────────────────────────────────────────────
    def _set_all(self, files, keep_filter=False):
        self.all_files = list(files)
        if not keep_filter:
            self.predicate = None
        self._refilter()

    def _refilter(self):
        self.files = [p for p in self.all_files if self.predicate(p)] if self.predicate else list(self.all_files)

    def set_current(self, path):
        """현재 사진을 지정한다. 목록에 없는 파일이면 그 사진이 있는 폴더를 스캔한다.
        필터에 걸러진 사진을 열면 필터를 풀어 전체 목록으로 돌아간다."""
        path = Path(path)
        if path not in self.files:
            if path in self.all_files:                       # 필터 때문에 안 보이던 사진 → 필터를 푼다
                self.predicate = None
                self._refilter()
            else:
                self.folder = path.parent
                self._set_all(sorted((p for p in self.folder.iterdir()
                                      if p.is_file() and p.suffix.lower() in IMAGE_EXTS), key=_natural_key))
        try:
            self.index = self.files.index(path)
        except ValueError:                      # 목록에 없으면 이 사진 1장만 있는 것으로 처리
            self._set_all([path])
            self.index = 0
        self.current = path

    def load_folder(self, folder):
        """폴더를 선택했을 때 하위의 모든 JPG 이미지를 찾아 목록을 만든다. 첫 사진 경로를 돌려준다 (없으면 None).

        폴더 바로 아래에 사진이 있으면 그것만, 없으면 하위 폴더(images/train, images/val 등)까지 찾는다.
        이 목록은 그 안의 사진을 열어도 유지된다. (새 폴더를 열면 필터는 풀린다)
        """
        folder = Path(folder)
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        if not files:
            files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        if not files:
            return None
        self.folder = folder
        self._set_all(sorted(files, key=lambda p: (str(p.parent).lower(), _natural_key(p))))   # 폴더별로 묶고 이름순 (train → val)
        self.index = 0
        self.current = self.files[0]
        return self.files[0]

    # ── 보기 필터 ────────────────────────────────────────────────────────
    def set_filter(self, predicate):
        """보기 필터를 건다 (None = 전체). 걸러진 사진 수를 돌려준다.
        현재 사진이 필터를 통과하면 그 위치를 유지하고, 아니면 index 는 -1 (보이는 목록에 없음)."""
        self.predicate = predicate
        self._refilter()
        self.index = self.files.index(self.current) if self.current in self.files else -1
        return len(self.files)

    @property
    def filtered(self):
        return self.predicate is not None

    # ── 이동 ────────────────────────────────────────────────────────────
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

    def jump_to_index(self, index):
        """0부터 세는 번호의 사진 경로 (범위 밖이면 None)."""
        if 0 <= index < self.total:
            return self.files[index]
        return None

    def progress_text(self):
        if self.index < 0:
            return "0 / 0"
        return f"{self.index + 1} / {self.total}"
