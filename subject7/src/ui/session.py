"""마지막으로 열었던 폴더와 사진을 기억해 두었다가, 프로그램을 다시 켜면 그 자리에서 이어서 작업한다.

기억하는 곳: data/work/_session.json  (WORK 안이라 Git 에 올라가지 않는다. 폴더·사진 경로 두 줄뿐이다)
저장 파일이 없거나 폴더·사진이 사라졌으면 조용히 건너뛴다. (라벨·검수표는 여기에 저장하지 않는다)
"""
import json
import os
import tempfile
from pathlib import Path

from src import settings


def session_path():
    return Path(settings.WORK_DIR) / "_session.json"


def save_session(folder, image):
    """열고 있는 폴더와 사진을 기록한다. 실패해도(쓰기 권한 등) 작업에는 영향이 없으므로 조용히 넘어간다."""
    if folder is None or image is None:
        return False
    path = session_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"folder": str(folder), "image": str(image)}, f, ensure_ascii=False)
        os.replace(tmp, path)                      # 쓰는 도중에 꺼져도 이전 기록이 깨지지 않는다
        return True
    except OSError:
        return False


def load_session():
    """(폴더, 사진) 경로. 기록이 없거나 깨졌거나 더 이상 없는 경로면 None."""
    try:
        data = json.loads(session_path().read_text(encoding="utf-8"))
        folder, image = Path(data["folder"]), Path(data["image"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not folder.is_dir() or not image.is_file():
        return None
    return folder, image
