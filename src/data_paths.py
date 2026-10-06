"""RAW / WORK 폴더 구조 처리 — 원본(RAW)을 보호하고, 저장은 RAW 와 같은 구조의 WORK 에만 한다.

  RAW :  data/raw/이물검출_학습데이터2/images/validation/a.jpg      ← 읽기만
  WORK:  data/work/이물검출_학습데이터2/labels/validation/a.txt     ← 수정한 라벨 (여기에만 저장)

데이터셋 이름과 split(train/validation)이 경로에 그대로 남으므로 출처 정보를 잃지 않는다.
(경로는 호출할 때마다 settings 에서 읽는다 — 시험에서 다른 폴더로 바꿔 쓸 수 있도록)
"""
from pathlib import Path

from src import settings


def is_inside(child, parent):
    """child 경로가 parent 폴더 '안'에 있는가?  (RAW 안에 실수로 저장하는 것을 막는 데 사용)"""
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def locate_in_raw(image_path):
    """RAW 안의 이미지라면 (데이터셋 이름, split) 을 돌려준다.  RAW 밖이면 (None, None).

    예) data/raw/이물검출_학습데이터2/images/validation/a.jpg  →  ("이물검출_학습데이터2", "validation")
    이 두 값이 곧 Manifest 의 source_dataset / original_split 이다.
    """
    try:
        parts = Path(image_path).resolve().relative_to(settings.RAW_DIR.resolve()).parts
    except ValueError:
        return None, None
    if len(parts) >= 4 and parts[1] == "images":
        return parts[0], "/".join(parts[2:-1])
    return (parts[0], "") if parts else (None, None)


def work_label_path(image_path):
    """저장할 WORK TXT 경로.  RAW 와 '같은 폴더 구조'를 유지한다.

    RAW 밖의 이미지는 work/_RAW밖/a.txt 로 저장한다. (구조를 알 수 없으므로 따로 모아 둠)
    """
    stem = Path(image_path).stem
    dataset, split = locate_in_raw(image_path)
    if dataset is None:
        return settings.WORK_DIR / "_RAW밖" / f"{stem}.txt"
    return settings.WORK_DIR.joinpath(dataset, "labels", *([split] if split else []), f"{stem}.txt")


def find_raw_image(rel_path):
    """검증 결과의 상대 경로('데이터셋/split/파일이름' — 확장자 없음)로 RAW 안의 이미지를 정확히 찾는다. 없으면 None.

    예) 'DS2/validation/a'  →  data/raw/DS2/images/validation/a.jpg  (대문자 .JPG 도 찾는다)
    파일 이름만으로 찾으면 다른 데이터셋·split 에 같은 이름이 있을 때 엉뚱한 사진이 열릴 수 있어서 경로 전체를 쓴다.
    """
    parts = [p for p in str(rel_path).replace("\\", "/").split("/") if p]
    if len(parts) < 2:
        return None
    folder = Path(settings.RAW_DIR).joinpath(parts[0], "images", *parts[1:-1])
    if not folder.is_dir():
        return None
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.stem == parts[-1] and p.suffix.lower() in settings.IMAGE_EXTS:
            return p
    return None
