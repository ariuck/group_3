# `subject8/scripts/10_train_v2.py`

> 지난 Version(v1~v4) 개선 실험 재현용 — [`06_train_baseline`](06_train_baseline.md) 의 Baseline 조건에서 변수 하나를 바꾼다 (가이드 20장 한 변수 실험). 실험별 바꾸는 값 `EXPERIMENTS` 는 공식 Version 실험([`11_train_v5`](11_train_v5.md))도 가져다 쓴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/10_train_v2.py)

## 사용법

```bash
cd subject8
python scripts/03_build_split.py --version kimchi_v4 --copy-files   # 먼저 그 Version 폴더 (data/yolo_v4)
python scripts/10_train_v2.py                                # kimchi_v4 exp001
python scripts/10_train_v2.py --exp exp002                   # kimchi_v4 exp002
python scripts/10_train_v2.py --exp exp003                   # kimchi_v4 exp003
python scripts/10_train_v2.py --version kimchi_v2            # 이력 (exp001 만)
```

| Dataset Version | 역할 | 출력 (Weight → `models/history/<Version>/<실행>.pt`, 조건 기록 → `reports/history/<Version>/<실행>_training_condition.md`) |
|---|---|---|
| `kimchi_v4` | exp001 imgsz 640 → 1280 (Baseline = `baseline_v4`) | `runs/exp001_v4_imgsz1280/` |
| `kimchi_v4` + `--exp exp002` | exp002 imgsz 1280 → 1920 · batch 6 | `runs/exp002_v4_imgsz1920/` |
| `kimchi_v4` + `--exp exp003` | exp003 epochs 50 → 100 | `runs/exp003_v4_imgsz1920_epoch100/` |
| `kimchi_v3` · `kimchi_v2` | 이력 (데이터 개선 과정) | `runs/history_v3_imgsz1280/` · `runs/history_v2_imgsz1280/` |
| `kimchi_v1` | 예비 실험 (해상도 가설 첫 확인) | `runs/pilot_v1_imgsz1280/` (Weight 보관·기록 없음) |

입력: 그 Version 의 dataset yaml · 학습 폴더 · manifest ([`split_builder`](../src/split_builder.md) 의 꼬리표 폴더)

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `EXPERIMENTS` | 실험별로 06 `BASELINE` 에서 바꾸는 값과 비교 대상 (+ 선택 `run_name`, `note`). exp001 `imgsz=1280`, exp002 `imgsz=1920, batch=6`, exp003 exp002 + `epochs=100` |
| `CONDITION` | `main()` 안에서 `BASELINE` + 실험의 바꾸는 값 |
| `RUN_NAMES` | Dataset Version → exp001 실행 폴더 이름 |
| `NOT_KEPT` | Weight·조건 기록을 남기지 않는 실행 (`pilot_v1_imgsz1280`) |
| `SPLIT_NOTES` | 조건 기록 메모에 넣을 버전별 데이터 설명 |
| `main()` | `--version` 폴더로 06 의 `precheck()` → [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관([`registry.weight_path`](../src/registry.md)) · 조건 기록 |

## 핵심 동작

- 06 파일을 모듈로 불러와 `BASELINE`·`precheck` 를 그대로 쓰고, `DATA_YAML`·`MANIFEST_DIR`·`YOLO_DIR` 만 그 Version 폴더로 바꾼다. 06 조건이 바뀌면 이 스크립트도 따라가므로 "바꾼 변수 하나" 가 유지된다.
- 학습 점검(가이드 17.4)이 모두 통과해야 Weight 를 보관한다.
- 근거는 6일차 H4(작은 이물 FN)와 예비 실험 `pilot_v1_imgsz1280` (kimchi_v1, mAP50-95 0.351 → 0.519).

## 의존성

- **사용하는 것**: [`scripts/06_train_baseline`](06_train_baseline.md), [`src/registry`](../src/registry.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행 (지난 Version 재현), [`11_train_v5`](11_train_v5.md) 가 `EXPERIMENTS` 를 가져다 쓴다

## 주의사항

- 실행 폴더나 보관 Weight 가 이미 있으면 멈춘다 (덮어쓰지 않음).
- 2026-10-14 이름 정리: 실행 폴더는 처음에 `baseline_kimchi_vN`, `exp001_v1_imgsz1280`(→ `pilot`), `baseline_v2`(→ `pilot` 의 첫 이름) 로 만들어졌다. 각 `args.yaml` 의 `name`·`save_dir` 은 처음 이름으로 남아 있다.
- RTX 3060 12GB 기준 exp001(1280 · batch 16) GPU 약 9.2GB · 50 epoch 약 10분, exp002(1920 · batch 6) 약 9.7GB · 약 25분.
- exp002 의 batch 6 은 메모리 때문이다 (batch 8 은 12.9GB 로 넘쳐 공유 메모리를 쓰며 2.2s/it 로 느려짐). Ultralytics `nbs=64` gradient 누적으로 갱신 1번당 사진 수는 64 · 66장으로 거의 같다.
- Baseline 과 비교할 때 이 Weight 는 **imgsz 1280**, Baseline 은 **640** 으로 각자 학습 조건대로 평가한다.
