import sys
from pathlib import Path

import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.constants import CLASS_NAMES, SCENE_TYPES
from src.dataset_audit import DatasetAuditor
from src.leakage_check import run_leakage_check, NEAR_DUP_THRESHOLD
from src.split_builder import SplitBuilder


def section(title):
    print("\n-----------------------------------------------------------------")
    print(f" {title}")
    print("-----------------------------------------------------------------")


def main():
    data_root = PROJECT_ROOT / "data" / "subject7_final"
    report_dir = PROJECT_ROOT / "reports"

    print("=" * 65)
    print(" [Subject 08] Day 2: Dataset Audit (Subject 7 FINAL 900 Images)")
    print("=" * 65)
    print(f"Data Source: {data_root}")
    print(f"Report Dir : {report_dir}")

    auditor = DatasetAuditor(data_root=data_root, report_dir=report_dir)
    res = auditor.run_audit()

    section("[1] Data Overview")
    print(f" - Total JPG Images  : {res['total_images']:>5} 장")
    print(f" - Total TXT Labels  : {res['total_labels']:>5} 개")
    print(f" - Empty Labels      : {res['empty_labels']:>5} 개 (BBox 없는 TXT)")
    print(f" - Total BBoxes      : {res['total_bboxes']:>5} 개")
    print(f" - Total Issues Found: {res['issues_count']:>5} 건 (audit_issue.csv)")

    section("[2] Class Distribution (BBox Count)")
    for cid, cnt in res['class_counts'].items():
        cname = CLASS_NAMES[cid]
        bar = "█" * int(cnt / max(1, max(res['class_counts'].values())) * 30)
        print(f" - Class {cid} ({cname:<20}): {cnt:>4} 개  {bar}")

    if res['bbox_per_image']:
        section("[3] BBox per Image")
        s = res['bbox_per_image']
        print(f" - min {s['min']} / median {s['median']} / mean {s['mean']} / max {s['max']}")
        for n_boxes, n_images in res['bbox_distribution'].items():
            print(f" - {n_boxes:>2} boxes: {n_images:>4} 장")

    if res['scene_counts']:
        section("[4] Scene Type Distribution")
        for sc, cnt in res['scene_counts'].items():
            print(f" - {sc:<25}: {cnt:>4} 장")

        section("[5] Class x Scene Type (images containing the class)")
        scenes = list(res['scene_counts'])
        print(" " + " " * 26 + "".join(f"{SCENE_TYPES.get(sc, sc):>20}" for sc in scenes))
        for cid in range(7):
            per = res['class_scene'][cid]
            print(f" Class {cid} ({CLASS_NAMES[cid]:<17})" + "".join(f"{per.get(sc, 0):>20}" for sc in scenes))

    if res['source_counts']:
        section("[6] Source Dataset & Split")
        for src, cnt in res['source_counts'].items():
            print(f" - {src:<25}: {cnt:>4} 장")
        for splt, cnt in res['split_counts'].items():
            print(f" - (Original Split) {splt:<10}: {cnt:>4} 장")

    # [7] Data Leakage — 촬영 묶음(5분 간격)과 사진 지문(dHash) 대조
    section("[7] Data Leakage Check (capture_group x dHash)")
    builder = SplitBuilder(project_root=PROJECT_ROOT)
    df = builder.assign_capture_groups(pd.read_csv(builder.meta_csv, encoding="utf-8-sig"))
    leak = run_leakage_check(df, builder.images_dir, report_dir)
    print(f" - capture_group            : {leak['capture_groups']} 개 (촬영 간격 5분 초과에서 분리)")
    print(f" - 완전히 같은 사진 쌍       : {leak['exact_duplicate_pairs']} 쌍")
    print(f" - 거의 같은 사진 쌍 (<= {NEAR_DUP_THRESHOLD}) : {leak['near_duplicate_pairs']} 쌍"
          f"  (같은 묶음 {leak['near_duplicate_pairs_within_group']} / 다른 묶음 {leak['near_duplicate_pairs_across_group']})")
    print(f" - 평균 지문 거리            : 같은 묶음 {leak['mean_distance_within_group']} / 다른 묶음 {leak['mean_distance_across_group']}")
    mixed = [g['capture_group'] for g in leak['groups'] if g['original_train'] and g['original_validation']]
    print(f" - 원래 train/validation 이 섞인 묶음: {len(mixed)} / {leak['capture_groups']} 개")
    if leak['near_duplicate_pairs_across_group']:
        print(" [WARN] 서로 다른 묶음 사이에 거의 같은 사진이 있습니다. 묶음 기준을 다시 확인하세요.")

    print("\n=================================================================")
    print(" [Audit Complete] Reports saved successfully:")
    for key in ('summary_csv', 'issue_csv', 'class_scene_csv'):
        print(f"  -> {res[key]}")
    print(f"  -> {leak['leakage_csv']}")
    print(f"  -> {leak['group_csv']}")
    print("=================================================================")


if __name__ == "__main__":
    main()
