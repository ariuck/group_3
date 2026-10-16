"""Git 에 올린 최종본 라벨·검수표로 다른 PC 의 작업 폴더를 되살린다. (사진은 data/raw 의 회사 원본을 쓴다)

    python tools/restore_from_final.py            # 미리보기: 무엇을 만들지만 보여 준다
    python tools/restore_from_final.py --apply    # 실제로 만든다

Git 에 있는 것 (이 PC 에서 만든 결과)
  data/final/labels/<split>/*.txt     검수가 끝난 최종 라벨 900개
  data/final/검수표.csv                 검수 기록 900줄 (출처 데이터셋 · 원래 split 포함)
  data/final/classes.txt              Class 0~6 이름

각 PC 에 넣을 것
  data/raw/<데이터셋>/images|labels/<split>/   회사 원본 그대로 (예: 이물검출_학습데이터1/images/train/a.jpg)

--apply 가 만드는 것 (이미 있는 파일은 내용이 같으면 건너뛰고, 다르면 덮어쓰지 않고 알려 준다)
  data/work/<데이터셋>/labels/<split>/*.txt     최종 라벨 → 작업본 (라벨링 프로그램이 이어서 열 수 있게)
  manifests/dataset_manifest.csv              data/final/검수표.csv 와 같은 내용 (라벨링 프로그램의 검수표)
  data/final/images/<split>/*.jpg             RAW 사진 (같은 디스크면 하드 링크 — 용량을 더 쓰지 않음)

끝나면 tools/build_final.py 의 조건 검사(check)를 돌려, 지금 RAW·work·검수표로 다시 만들어도
Git 의 최종 라벨과 똑같이 나오는지 확인한다.  RAW 는 읽기만 한다.
"""
import argparse
import csv
import filecmp
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings                                   # noqa: E402
from tools import build_final                              # noqa: E402


def read_rows(final_dir):
    with open(Path(final_dir) / build_final.MANIFEST_NAME, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def plan(raw_dir=None, work_dir=None, final_dir=None, manifest_path=None):
    """할 일 목록 {'copy': [(원본, 대상, 종류)], 'same': 개수, 'conflict': [대상], 'missing': [설명]}"""
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    work_dir = Path(work_dir or settings.WORK_DIR)
    final_dir = Path(final_dir or settings.FINAL_DIR)
    manifest_path = Path(manifest_path or settings.MANIFEST_PATH)
    todo = {"copy": [], "same": 0, "conflict": [], "missing": []}

    def want(src, dst, kind):
        if not dst.exists():
            todo["copy"].append((src, dst, kind))
        elif filecmp.cmp(src, dst, shallow=False):
            todo["same"] += 1
        else:
            todo["conflict"].append(str(dst))

    for r in read_rows(final_dir):
        ds, split, img, lbl = r["출처 데이터셋"], r["원래 split"], r["이미지 파일명"], r["라벨(TXT) 파일명"]
        final_lbl = final_dir / "labels" / split / lbl
        raw_img = raw_dir / ds / "images" / split / img
        if not final_lbl.is_file():
            todo["missing"].append(f"최종 라벨 없음: {final_lbl}")
            continue
        if not raw_img.is_file():
            todo["missing"].append(f"RAW 사진 없음: {raw_img}")
            continue
        want(final_lbl, work_dir / ds / "labels" / split / lbl, "work 라벨")
        want(raw_img, final_dir / "images" / split / img, "final 사진")
    want(final_dir / build_final.MANIFEST_NAME, manifest_path, "검수표")
    return todo


def link_or_copy(src, dst):
    """같은 디스크면 하드 링크(용량 0), 안 되면 복사"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def verify(raw_dir=None, work_dir=None, final_dir=None, manifest_path=None):
    """build_final.check 로 다시 만들면 Git 의 최종 라벨과 같은지 — (문제 목록) 비어 있으면 통과"""
    final_dir = Path(final_dir or settings.FINAL_DIR)
    result = build_final.check(raw_dir=raw_dir, work_dir=work_dir, manifest_path=manifest_path)
    problems = [f"{reason}: {len(names)}장" for reason, names in result["blocked"].items()]
    for it in result["items"]:
        dst = final_dir / "labels" / it["split"] / f"{it['image'].stem}.txt"
        if not dst.is_file() or not filecmp.cmp(it["label"], dst, shallow=False):
            problems.append(f"다시 만들면 라벨이 달라짐: {it['name']}")
    if len(result["items"]) != len(read_rows(final_dir)):
        problems.append(f"사진 수가 다름: 다시 만들면 {len(result['items'])}장, 검수표 {len(read_rows(final_dir))}줄")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Git 의 최종본 라벨·검수표 + data/raw 사진으로 work·검수표·final 을 되살린다")
    ap.add_argument("--apply", action="store_true", help="실제로 만든다 (없으면 미리보기만)")
    args = ap.parse_args(argv)

    todo = plan()
    kinds = {}
    for _, _, kind in todo["copy"]:
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f"만들 파일: {kinds or '없음'}   이미 같은 파일: {todo['same']}개")
    for title, items in (("⚠ 없음", todo["missing"]), ("⚠ 이미 있는데 내용이 다름 (덮어쓰지 않음)", todo["conflict"])):
        if items:
            print(f"\n{title}: {len(items)}개")
            for x in items[:5]:
                print(f"  {x}")
    if todo["missing"]:
        print("\ndata/raw 에 회사 원본(이물검출_학습데이터1·2)을 그대로 넣었는지 확인하세요.")
        return 1
    if not args.apply:
        print("\n미리보기입니다. 만들려면 --apply 를 붙이세요.")
        return 0
    for src, dst, kind in todo["copy"]:
        if kind == "final 사진":
            link_or_copy(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    problems = verify()
    if problems:
        print("\n⚠ 확인 실패:")
        for p in problems[:10]:
            print(f"  {p}")
        return 1
    print(f"\n완료: build_final 조건 통과, 다시 만들어도 Git 의 최종 라벨과 같음 ({settings.FINAL_DIR})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
