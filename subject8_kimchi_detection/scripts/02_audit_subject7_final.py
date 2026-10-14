import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.dataset_audit import DatasetAuditor
from src.constants import CLASS_NAMES

def main():
    data_root = PROJECT_ROOT / "data" / "subject7_final"
    report_dir = PROJECT_ROOT / "reports"

    print("=" * 65)
    print(" [Subject 08] Day 2: Dataset Audit (Subject 7 FINAL 900 Images)")
    print("=" * 65)
    print(f"Data Source: {data_root}")
    print(f"Report Dir : {report_dir}\n")

    auditor = DatasetAuditor(data_root=data_root, report_dir=report_dir)
    res = auditor.run_audit()

    print("-----------------------------------------------------------------")
    print(" [1] Data Overview")
    print("-----------------------------------------------------------------")
    print(f" - Total JPG Images  : {res['total_images']:>5} 장")
    print(f" - Total TXT Labels  : {res['total_labels']:>5} 개")
    print(f" - Empty Labels      : {res['empty_labels']:>5} 개 (BBox 없는 정상 김치/배경)")
    print(f" - Total BBoxes      : {res['total_bboxes']:>5} 개")
    print(f" - Total Issues Found: {res['issues_count']:>5} 건 (audit_issue.csv)")

    print("\n-----------------------------------------------------------------")
    print(" [2] Class Distribution (BBox Count)")
    print("-----------------------------------------------------------------")
    for cid, cnt in res['class_counts'].items():
        cname = CLASS_NAMES[cid]
        bar = "█" * int(cnt / max(1, max(res['class_counts'].values())) * 30)
        print(f" - Class {cid} ({cname:<20}): {cnt:>4} 개  {bar}")

    if res['scene_counts']:
        print("\n-----------------------------------------------------------------")
        print(" [3] Scene Type Distribution")
        print("-----------------------------------------------------------------")
        for sc, cnt in res['scene_counts'].items():
            print(f" - {sc:<25}: {cnt:>4} 장")

    if res['source_counts']:
        print("\n-----------------------------------------------------------------")
        print(" [4] Source Dataset & Split")
        print("-----------------------------------------------------------------")
        for src, cnt in res['source_counts'].items():
            print(f" - {src:<25}: {cnt:>4} 장")
        for splt, cnt in res['split_counts'].items():
            print(f" - (Original Split) {splt:<10}: {cnt:>4} 장")

    print("\n=================================================================")
    print(f" [Audit Complete] Reports saved successfully:")
    print(f"  -> {res['summary_csv']}")
    print(f"  -> {res['issue_csv']}")
    print("=================================================================")

if __name__ == "__main__":
    main()