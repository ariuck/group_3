"""촬영 묶음(capture_group)이 실제로 '비슷한 사진 묶음'인지 사진 지문(dHash)으로 확인한다 (가이드 15.3 Data Leakage).

- 사진을 17×16 흑백으로 줄여 옆 픽셀과의 밝기 차이로 256bit 지문을 만든다.
- 두 지문의 다른 bit 수(해밍 거리, 0~256)가 작을수록 비슷한 사진이다. 0 = 사실상 같은 사진.
- 거의 같은 사진 쌍이 서로 다른 묶음에 있으면, 묶음 단위로 나눠도 누수가 생긴다는 뜻이다.
"""
import re
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict

import pandas as pd
from PIL import Image

HASH_W, HASH_H = 17, 16          # 16×16 = 256bit
NEAR_DUP_THRESHOLD = 10          # 이 거리 이하면 '거의 같은 사진'
TIME_RE = re.compile(r"^\d{6}_(\d{2})(\d{2})(\d{2})")


def dhash(path) -> int:
    """사진 1장 → 256bit 지문(int)"""
    with Image.open(path) as im:
        im.draft("L", (320, 180))  # JPEG 를 작게 디코딩 (4K 원본 전체를 읽지 않아 빠름)
        px = list(im.convert("L").resize((HASH_W, HASH_H), Image.BILINEAR).getdata())
    bits = 0
    for y in range(HASH_H):
        for x in range(HASH_W - 1):
            bits = (bits << 1) | (px[y * HASH_W + x] > px[y * HASH_W + x + 1])
    return bits


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def _clock(name: str) -> str:
    m = TIME_RE.match(name)
    return f"{m.group(1)}:{m.group(2)}:{m.group(3)}" if m else ""


def run_leakage_check(df: pd.DataFrame, images_dir: Path, report_dir: Path, workers: int = None) -> Dict:
    """df 에는 `이미지 파일명`, `capture_group` 이 있어야 한다. (`원래 split`, `이미지 유형` 이 있으면 요약에 넣는다)

    출력: reports/audit/leakage_check.csv (지표), reports/audit/capture_group_summary.csv (묶음별 표)
    """
    images_dir, report_dir = Path(images_dir), Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    paths = {p.name: p for p in images_dir.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
    df = df.sort_values("이미지 파일명").reset_index(drop=True)
    missing = [n for n in df["이미지 파일명"] if n not in paths]
    if missing:
        raise FileNotFoundError(f"이미지를 찾을 수 없습니다 ({len(missing)}장): {missing[:3]} ...")

    with ProcessPoolExecutor(max_workers=workers) as pool:
        hashes = list(pool.map(dhash, [paths[n] for n in df["이미지 파일명"]], chunksize=16))

    groups = df["capture_group"].tolist()
    n = len(hashes)
    nearest = [257] * n
    nearest_same_group = [False] * n
    within, across = [], []
    within_by_group = defaultdict(list)
    exact = near_within = near_across = 0
    for i in range(n):
        hi, gi = hashes[i], groups[i]
        for j in range(i + 1, n):
            d = hamming(hi, hashes[j])
            same = gi == groups[j]
            if same:
                within.append(d)
                within_by_group[gi].append(d)
            else:
                across.append(d)
            exact += d == 0
            if d <= NEAR_DUP_THRESHOLD:
                if same:
                    near_within += 1
                else:
                    near_across += 1
            if d < nearest[i]:
                nearest[i], nearest_same_group[i] = d, same
            if d < nearest[j]:
                nearest[j], nearest_same_group[j] = d, same

    metrics = {
        "images": n,
        "capture_groups": len(set(groups)),
        "hash_bits": (HASH_W - 1) * HASH_H,
        "near_dup_threshold": NEAR_DUP_THRESHOLD,
        "exact_duplicate_pairs": exact,
        "near_duplicate_pairs": near_within + near_across,
        "near_duplicate_pairs_within_group": near_within,
        "near_duplicate_pairs_across_group": near_across,
        "mean_distance_within_group": round(statistics.mean(within), 1) if within else None,
        "mean_distance_across_group": round(statistics.mean(across), 1) if across else None,
        "nearest_neighbor_min": min(nearest),
        "nearest_neighbor_median": statistics.median(nearest),
    }
    leakage_csv = report_dir / "leakage_check.csv"
    # dtype=object: 정수 지표가 900.0 처럼 소수로 바뀌지 않게
    pd.DataFrame({"metric": list(metrics), "value": list(metrics.values())}, dtype=object).to_csv(
        leakage_csv, index=False, encoding="utf-8-sig")

    rows = []
    for gid, part in df.groupby("capture_group", sort=True):
        names = sorted(part["이미지 파일명"])
        d = within_by_group.get(gid, [])
        split_counts = Counter(part["원래 split"]) if "원래 split" in part else Counter()
        rows.append({
            "capture_group": gid,
            "images": len(part),
            "date": names[0][:6],
            "start": _clock(names[0]),
            "end": _clock(names[-1]),
            "scene": Counter(part["이미지 유형"]).most_common(1)[0][0] if "이미지 유형" in part else "",
            "original_train": split_counts.get("train", 0),
            "original_validation": split_counts.get("validation", 0),
            "near_dup_pairs": sum(1 for x in d if x <= NEAR_DUP_THRESHOLD),
            "internal_median_distance": statistics.median(d) if d else None,
        })
    group_csv = report_dir / "capture_group_summary.csv"
    pd.DataFrame(rows).to_csv(group_csv, index=False, encoding="utf-8-sig")

    return {**metrics, "leakage_csv": str(leakage_csv), "group_csv": str(group_csv), "groups": rows}
