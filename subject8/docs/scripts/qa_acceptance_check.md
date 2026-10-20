# `subject8/scripts/qa_acceptance_check.py`

> 가이드 22.7 Acceptance Test 체크리스트 중 **사진·GPU 없이 확인할 수 있는 항목**을 자동으로 점검하고 `PASS / FAIL / TODO / MANUAL` 로 나눠 보여 준다. 결과는 `reports/05_acceptance/acceptance_test.md` 의 근거다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/qa_acceptance_check.py)

## 사용법

```bash
cd subject8
python scripts/qa_acceptance_check.py       # FAIL 이 있으면 종료 코드 1
```

| 입력 | 출력 (Git 에 올림) |
|---|---|
| `manifests/*.csv`, `configs/dataset.yaml`, `docs/project/split_policy.md`, `models/**/*.pt`, `reports/*`, `runs/*/args.yaml`, `git ls-files` | 화면 표, `reports/05_acceptance/acceptance_check.csv` (`area, item, status, detail`) |

## 상태

| 상태 | 뜻 |
|---|---|
| `PASS` | 확인 완료 |
| `FAIL` | 기준에 어긋남 — 고치고 다시 실행 (재시험 결과를 `acceptance_test.md` 에 기록) |
| `TODO` | 아직 만들어지지 않은 산출물 (`final_best.pt`, `final_metrics.csv`, Auto Label, `demo/` 자료 등) |
| `MANUAL` | 사진·GPU 가 있는 PC 에서 사람이 확인 (Detection 실행, Auto Label, 다른 팀원 재현 등) |

## 점검 영역

| 함수 | 점검 내용 |
|---|---|
| `check_dataset()` | 출처·Version 추적, 네 역할 합 900장, `dataset_summary` 일치, 역할 간 중복 이미지 0, FROZEN 문구, Class 0~6, Bridge 가 `dataset.yaml` 에 없음, Frozen Test 사용 흔적(휴리스틱), **Bridge 사용 흔적(휴리스틱 — `runs/`·`runs/eval`·`reports/06_subject14`)**, 학습에 쓴 Manifest 해시 일치 |
| `check_model()` | `models/` 에 보관된 모든 Weight(Baseline·exp001~050)의 SHA-256 앞 12자리가 `*_training_condition.md` 기록과 일치, 학습조건 항목, `final_best.pt`·선택 이유, **`final_best.pt` = 공식 Final 실행의 Weight = 선택 문서의 해시** |
| `check_evaluation()` | Baseline 지표 4종, Class 별 성능, 실패분석, 가설·비교 문서, `experiment_log.csv` 15개 필드, **`models/` 의 모든 실행이 `experiment_log.csv` 에 있는지**, **Frozen Test 결과(1행 · 82장 · 공식 Final)와 Class 별 파일** |
| `check_use()` | 예측·Auto Label 코드 존재, 시연 백업자료(`demo/`) |
| `check_env()` | `src/`·`scripts/` 문법 컴파일, 패키지(`ultralytics`·`torch`·`cv2` 등) import, Git 에 사진·모델 밖 `.pt` 없음, **`docs/handoff_subject14.md` 존재와 필수 내용(Final · Bridge · Dataset Version · 한계)** |

## 주의사항

- **Frozen Test·Bridge 미사용은 휴리스틱이다.** `runs/` 이름·`args.yaml` 의 `split: test`·`data:` 경로·`evaluate_detector.py` 의 `allow_test` 보호만 본다. 남은 기록이 없는 열람은 잡지 못한다 — 실제로 2026-10-16 에 Final 확정 전 Test 점수를 한 번 본 적이 있다는 팀 기록이 있어도 이 점검은 PASS 였다 (`reports/04_improvement/baseline_vs_improved.md` 3장). 학습 로그와 팀 기록은 사람이 본다.
- Bridge 흔적이 나오면 `MANUAL` 이다 — 교과 14 에서 `17_evaluate_bridge.py` 로 평가한 결과라면 정상, 교과 8 안에서 만들어졌다면 안 된다.
- 해시는 파일 내용 SHA-256 의 앞 12자리로, `src/train_detector.py` 의 `sha256_short` 와 같은 방식이다. Weight 를 다시 학습·교체했는데 기록 문서를 갱신하지 않으면 `FAIL` 이 난다 (기록과 파일이 어긋났다는 뜻).
- 촬영 묶음이 여러 역할에 걸친 경우(G00·G09·G12)는 `MANUAL` 로 표시한다 — 분할 예외가 `docs/project/split_policy.md` 에 문서화되어 있는지 사람이 확인한다.
- 사진·GPU 를 쓰는 항목(Detection 실행, Auto Label, 재현)은 이 스크립트가 판정하지 않는다.
