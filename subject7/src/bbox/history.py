"""BBox 편집 되돌리기(Undo) / 다시 실행(Redo).

'변경하기 직전의 BBox 목록 전체'를 사본으로 쌓아 두는 단순한 스냅샷 방식이다.
이미지 1장의 BBox 는 많아야 수십 개라서 이 방식이 가장 안전하고 이해하기 쉽다.

사용법 (main_window 쪽):
    self.history.push(self.boxes)        # 추가·삭제·이동·Class 변경 '직전'에 호출
    self.boxes.append(new_box)

    prev = self.history.undo(self.boxes) # Ctrl+Z
    if prev is not None:
        self.boxes = prev

    nxt = self.history.redo(self.boxes)  # Ctrl+Y / Ctrl+Shift+Z
    if nxt is not None:
        self.boxes = nxt

    self.history.clear()                 # 다른 이미지를 열 때
"""

MAX_HISTORY = 100


def _snapshot(boxes):
    """BBox 목록의 독립 사본 (원본을 나중에 고쳐도 기록이 바뀌지 않게)."""
    return [dict(b) for b in boxes]


class History:
    def __init__(self, limit=MAX_HISTORY):
        self.limit = max(1, int(limit))
        self._undo = []
        self._redo = []

    def push(self, boxes):
        """변경 직전 상태를 기록한다. 직전 기록과 똑같으면 쌓지 않는다."""
        snap = _snapshot(boxes)
        if self._undo and self._undo[-1] == snap:
            return False
        self._undo.append(snap)
        if len(self._undo) > self.limit:
            del self._undo[0]
        self._redo.clear()           # 새 편집을 하면 Redo 기록은 무효
        return True

    def undo(self, current):
        """한 단계 이전 상태(사본)를 돌려준다. 되돌릴 것이 없으면 None."""
        if not self._undo:
            return None
        self._redo.append(_snapshot(current))
        return _snapshot(self._undo.pop())

    def redo(self, current):
        """Undo 한 것을 다시 적용한 상태(사본)를 돌려준다. 없으면 None."""
        if not self._redo:
            return None
        self._undo.append(_snapshot(current))
        return _snapshot(self._redo.pop())

    def clear(self):
        self._undo.clear()
        self._redo.clear()

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def can_redo(self):
        return bool(self._redo)

    def __len__(self):
        return len(self._undo)