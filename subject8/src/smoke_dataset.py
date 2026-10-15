"""Smoke Test 용 작은 Dataset 을 만든다 (가이드 16.5).

Train 에서 40장, Validation 에서 8장만 뽑아 data/smoke/ 에 YOLO 구조로 복사하고 configs/smoke_dataset.yaml 을 쓴다.
Frozen Test 와 Bridge Holdout 은 사용하지 않는다. 목적은 성능이 아니라 "학습 Pipeline 이 끝까지 도는가" 확인이다.
"""
import random
import shutil
from pathlib import Path
from typing import Dict

import yaml

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def build_smoke_dataset(project_root: Path, n_train: int = 40, n_val: int = 8, seed: int = 42) -> Dict:
    """data/yolo 의 train·val 에서 무작위(seed 고정)로 뽑아 data/smoke 를 새로 만든다. 반환: yaml 경로, 장수"""
    project_root = Path(project_root)
    src_root = project_root / "data" / "yolo"
    dst_root = project_root / "data" / "smoke"
    full_yaml = project_root / "configs" / "dataset.yaml"
    smoke_yaml = project_root / "configs" / "smoke_dataset.yaml"

    if not (src_root / "images" / "train").is_dir():
        raise FileNotFoundError(f"{src_root}/images/train 이 없습니다. 먼저 python scripts/03_build_split.py --copy-files")

    if dst_root.exists():
        shutil.rmtree(dst_root)  # 매번 같은 seed 로 새로 만들어 이전 파일이 섞이지 않게

    rng = random.Random(seed)
    counts = {}
    for split, n in (("train", n_train), ("val", n_val)):
        images = sorted(p for p in (src_root / "images" / split).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
        if len(images) < n:
            raise ValueError(f"{split} 이미지가 {len(images)}장뿐입니다 ({n}장 필요)")
        picked = sorted(rng.sample(images, n))
        (dst_root / "images" / split).mkdir(parents=True)
        (dst_root / "labels" / split).mkdir(parents=True)
        for img in picked:
            label = src_root / "labels" / split / f"{img.stem}.txt"
            if not label.is_file():
                raise FileNotFoundError(f"라벨 없음: {label}")
            shutil.copy2(img, dst_root / "images" / split / img.name)
            shutil.copy2(label, dst_root / "labels" / split / label.name)
        counts[split] = len(picked)

    # Class 이름은 본 dataset.yaml 에서 그대로 가져온다 (Class ID 0~6 유지)
    with full_yaml.open(encoding="utf-8") as f:
        names = yaml.safe_load(f)["names"]
    smoke_yaml.write_text(
        "# Smoke Test 전용 (진행용 보조파일) — scripts/05_smoke_train.py 가 자동 생성\n"
        "# Train 40장 / Val 8장. Frozen Test·Bridge Holdout 은 사용하지 않음\n"
        + yaml.safe_dump({"path": "data/smoke", "train": "images/train", "val": "images/val", "names": names},
                         allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return {"yaml": smoke_yaml, "root": dst_root, **counts}
