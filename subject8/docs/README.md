# 문서 목차 (교과 8)

```
docs/
├─ scripts/ · src/    코드 설명서 — 코드와 같은 경로 (src/inference.py → docs/src/inference.md)
└─ project/           그 밖의 프로젝트 문서 (분할 정책·과정 기록·시연 절차)
```

- **코드 파일이 궁금하면** 코드 경로 앞에 `docs/` 를 붙인다 → 아래 표
- **`project/`**: [split_policy](project/split_policy.md) 분할 정책 · [manual_split_guide](project/manual_split_guide.md) 6명 수동 분할 가이드(`kimchi_v5`) · [kimchi_v5_split](project/kimchi_v5_split.md) kimchi_v5 분할 기준(C안) · [experiment_handoff](project/experiment_handoff.md) 실험 인수인계·3대 분산 계획 · [process/dataset_audit_and_split](project/process/dataset_audit_and_split.md) 데이터 점검·분할 과정 · [demo_procedure](project/demo_procedure.md) 시연 절차
- 결과·보고서는 문서가 아니라 [`reports/`](../reports/README.md) 에 단계별(01_data ~ 05_acceptance)로 있다.
- 교과 7 문서는 [`subject7/docs/`](../../subject7/docs/README.md) 에 같은 규칙으로 있다 (기준서는 `subject7/docs/project/standards/`).
- 대응 점검 (이 폴더 `subject8/` 에서): `python ../subject7/tools/check_docs.py .`

## `scripts/` · `src/`

| 코드 | 한 줄 설명 |
|---|---|
| [`scripts/00_setup.py`](scripts/00_setup.md) | **올인원 준비** — 어느 PC 든 명령 하나로 .venv → 교과 7 복원 → 점검 → v4·v5 학습 폴더 (된 단계는 건너뜀) |
| [`scripts/01_check_environment.py`](scripts/01_check_environment.md) | PyTorch·CUDA·YOLO11n 환경 점검 |
| [`scripts/02_audit_subject7_final.py`](scripts/02_audit_subject7_final.md) | 교과 7 최종본 900장 점검 + Data Leakage 확인 |
| [`scripts/03_build_split.py`](scripts/03_build_split.md) | 방안 B 분할 + Manifest·`dataset.yaml` |
| [`scripts/04_import_label_fixes.py`](scripts/04_import_label_fixes.md) | 라벨링 프로그램 수정본 → `kimchi_v3` 라벨 수정본 + 변경 기록 |
| [`scripts/05_smoke_train.py`](scripts/05_smoke_train.md) | Smoke Test (Train 40 / Val 8, 3 epoch → Prediction) |
| [`scripts/06_train_baseline.py`](scripts/06_train_baseline.md) | 공식 Baseline 학습 (`kimchi_v4` · YOLO11n · 640) + Weight 보관 + 학습 조건 기록 |
| [`scripts/07_evaluate_baseline.py`](scripts/07_evaluate_baseline.md) | Baseline Validation 평가 → `baseline_metrics.csv`·Class 별 성능·그래프 |
| [`scripts/08_predict_images.py`](scripts/08_predict_images.md) | 사진 예측 + 정답 비교 이미지 · TP/FP/FN 표 |
| [`scripts/11_train_v5.py`](scripts/11_train_v5.md) | `kimchi_v5`(C안) 학습: baseline_v5 (640) · exp001_v5 (1280) · exp002_v5 (1920) |
| [`scripts/14_train_tiles_v5.py`](scripts/14_train_tiles_v5.md) | 개선 실험 exp004_v5 타일링 (2×2 조각 학습 → 조각 예측 합쳐 원본 Val 채점) |
| [`scripts/15_eval_inference_options.py`](scripts/15_eval_inference_options.md) | 추론 설정 비교 (TTA · agnostic NMS) — 재학습 없이 Validation |
| [`scripts/16_evaluate_final_test.py`](scripts/16_evaluate_final_test.md) | Final Model Frozen Test 평가 (한 번만, Final 확정·선택 기록 후) |
| [`scripts/17_evaluate_bridge.py`](scripts/17_evaluate_bridge.md) | **교과 14 용** Bridge Holdout 156장 첫 평가 (`--subject14` 확인 필요 · 교과 8 에서는 실행하지 않음 · `--dry-run` 은 개수만 확인) |
| [`scripts/plot_v5_vs_v4.py`](scripts/plot_v5_vs_v4.md) | `kimchi_v4` → `v5` 달라진 점 그림·CSV (누수 · Class 박스 · Val 점수) |
| [`scripts/make_split_worksheet.py`](scripts/make_split_worksheet.md) | 수동 분할 준비: 담당자별 작업 시트(CSV) 6개 · 촬영 순서 사진판(JPG) |
| [`scripts/plot_runs.py`](scripts/plot_runs.md) | 모든 실행의 학습 곡선 · Version 별 비교 그래프 · `runs_summary.csv` (results.csv 만으로) |
| [`scripts/qa_acceptance_check.py`](scripts/qa_acceptance_check.md) | Acceptance Test 자동 점검 (Dataset·Model·Evaluation·환경·보안) → `reports/05_acceptance/acceptance_check.csv` |
| [`scripts/plot_improvement.py`](scripts/plot_improvement.md) | 개선 분석: Baseline vs exp001~003 비교 표(`improvement_summary.csv`)·2×2 그림(SVG) — 사진·GPU 없이 재생성 |
| [`scripts/09_collect_failures.py`](scripts/09_collect_failures.md) | 실패 사례 수집 → `failure_analysis.csv` · 요약 표 · 대표 사진 |
| [`scripts/10_train_v2.py`](scripts/10_train_v2.md) | 개선 실험 exp001 — Baseline 조건에서 imgsz 640 → 1280 (공식: `kimchi_v4`) |
| `manifests/kimchi_v5_draft/tools/*.py` (12개) | kimchi_v5 C안 결정 분석 기록: [features](manifests/kimchi_v5_draft/tools/features.md) → [crops](manifests/kimchi_v5_draft/tools/crops.md) → [match](manifests/kimchi_v5_draft/tools/match.md) → [anal_pairs](manifests/kimchi_v5_draft/tools/anal_pairs.md) · [batches](manifests/kimchi_v5_draft/tools/batches.md) · [groups](manifests/kimchi_v5_draft/tools/groups.md) · [seq](manifests/kimchi_v5_draft/tools/seq.md) · [sheet](manifests/kimchi_v5_draft/tools/sheet.md) · [search](manifests/kimchi_v5_draft/tools/search.md) → [split_v5](manifests/kimchi_v5_draft/tools/split_v5.md)·[b](manifests/kimchi_v5_draft/tools/split_v5b.md)·[c](manifests/kimchi_v5_draft/tools/split_v5c.md) |
| [`src/constants.py`](src/constants.md) | Class·장면·묶음 기준·Version 별 분할 규칙·역할 상수 (SSOT) |
| [`src/dataset_audit.py`](src/dataset_audit.md) | `DatasetAuditor` — 라벨 점검, 이미지별 BBox 수, Class×장면 |
| [`src/evaluate_detector.py`](src/evaluate_detector.md) | Weight 평가 (전체·Class 별 P·R·mAP), Frozen Test 보호 |
| [`src/failure_analyzer.py`](src/failure_analyzer.md) | 실패 유형 분류(FN·CLASS_ERROR·FP 3종) · 크기별 Recall · Train/Val 비교 사진 |
| [`src/inference.py`](src/inference.md) | 예측 ↔ 정답 짝짓기 (TP·CLASS_ERROR·FP·FN), 비교 이미지 |
| [`src/leakage_check.py`](src/leakage_check.md) | 사진 지문(dHash)으로 촬영 묶음 누수 확인 |
| [`src/smoke_dataset.py`](src/smoke_dataset.md) | Smoke Test 용 작은 Dataset 만들기 |
| [`src/split_builder.py`](src/split_builder.md) | `SplitBuilder` — 촬영 묶음 단위 분할 |
| [`src/registry.py`](src/registry.md) | 모델 등록부: 실행 이름 → Weight 위치 · Version · imgsz · 타일링, 공식 Baseline/Final 지정 |
| [`src/tiling.py`](src/tiling.md) | 타일링: 조각 만들기 · 조각 예측 합치기 · 원본 사진 단위 채점 |
| [`src/train_detector.py`](src/train_detector.md) | YOLO 학습 공통 함수 · 학습 점검 · 조건 기록 |
