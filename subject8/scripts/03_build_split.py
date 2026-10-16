import sys
import argparse
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.constants import BLOCK_RULES, DATASET_VERSIONS, DEFAULT_DATASET_VERSION
from src.split_builder import SplitBuilder

def main():
    parser = argparse.ArgumentParser(description="Build Dataset Split (Plan B: 18 Capture Groups + G00 Block Split)")
    parser.add_argument("--copy-files", action="store_true", help="Physically copy images and labels into data/yolo and data/bridge_holdout")
    parser.add_argument("--version", default=DEFAULT_DATASET_VERSION, choices=DATASET_VERSIONS,
                        help="Dataset Version (블록 분할 규칙: src/constants.py 의 BLOCK_RULES)")
    args = parser.parse_args()

    print("=" * 65)
    print(" [Subject 08] Day 2/3: Build Dataset Split (Plan B)")
    print("=" * 65)

    builder = SplitBuilder(project_root=PROJECT_ROOT, dataset_version=args.version)   # 공식이 아닌 Version 은 data/yolo_v4 등 꼬리표 폴더
    fix_dir = builder.label_fix_dir(args.version)   # kimchi_v3 인데 수정본이 없으면 Manifest 를 덮어쓰기 전에 멈춘다
    if fix_dir is not None:
        print(f" Label fixes: {len(list(fix_dir.glob('*.txt')))} TXT from {fix_dir.relative_to(PROJECT_ROOT)}")

    # 1. 메타데이터 로드
    df = pd.read_csv(builder.meta_csv, encoding="utf-8-sig")
    print(f" Loaded Subject 7 FINAL metadata: {len(df)} images")

    # 2. Capture Group 할당 (5분 간격 18개 묶음)
    df = builder.assign_capture_groups(df)
    n_groups = df["capture_group"].nunique()
    print(f" Assigned capture_groups: {n_groups} groups (G00 ~ G{n_groups-1:02d})")

    # 3. 방안 B 분할 할당
    df = builder.assign_splits(df, dataset_version=args.version)
    print(f" Applied Split Plan B ({args.version}: block split {sorted(BLOCK_RULES[args.version])} + G17 to train)")

    # 4. Manifests CSV 생성
    manifest_paths = builder.generate_manifests(df)
    print("\n-----------------------------------------------------------------")
    print(" [Generated Manifests]")
    print("-----------------------------------------------------------------")
    for role, path in manifest_paths.items():
        count = len(df[df["split"] == role]) if role in ["train", "val", "test", "bridge_holdout"] else len(df)
        print(f" - {role:<15}: {count:>4} 장  -> {path}")

    # 5. configs/dataset.yaml 생성
    yaml_path = builder.generate_dataset_yaml()
    print(f" - dataset yaml generated -> {yaml_path}")

    # 6. reports/01_data/dataset_summary.csv 생성 (산출물 1 표준 양식)
    summary_path = builder.generate_dataset_summary(df, dataset_version=args.version)
    print(f" - dataset summary generated -> {summary_path}")

    # 7. 분할 요약 통계 출력
    print("\n-----------------------------------------------------------------")
    print(" [Split Distribution Summary]")
    print("-----------------------------------------------------------------")
    crosstab_scene = pd.crosstab(df["split"], df["이미지 유형"], margins=True)
    print(crosstab_scene)

    # 8. 물리 파일 복사 (옵션)
    if args.copy_files:
        print(f"\n Copying physical files into {builder.yolo_dir.name} and {builder.bridge_dir.name}...")
        builder.build_physical_dataset(df, clean=True)
        print(" Physical dataset creation complete!")
    else:
        print("\n (Note: Physical file copy skipped. Run with --copy-files to generate data/yolo folders)")

    print("=" * 65)

if __name__ == "__main__":
    main()
