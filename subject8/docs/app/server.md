# `subject8/app/server.py`

> **Final Model 시연 프로그램** — FastAPI 서버 + 브라우저 화면(`app/static/`). 발표 15번 슬라이드 "라이브 시연 ②"의 **시연 프로그램 열기** 버튼으로 넘어오고, `← 발표로`(Backspace)로 돌아간다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../app/server.py)

## 사용법

```bash
cd subject8
.venv/bin/python app/server.py               # http://127.0.0.1:8000 — 오른쪽 위 "● 준비 완료" 가 뜨면 시작 (모델 Load · 예열 약 5초)
.venv/bin/python app/server.py --port 8010   # 다른 포트
.venv/bin/python app/server.py --cpu         # GPU 없이 (느림)
```

- 발표자료도 같은 서버가 `http://127.0.0.1:8000/presentation/` 으로 연다 (저장소 맨 위 `presentation/` 이 있을 때). 이렇게 열면 발표 → 시연 → 발표가 한 탭에서 오간다.
- 발표자료를 파일(더블클릭)로 열어도 15번의 버튼은 `http://127.0.0.1:8000/` 로 간다. 이때 서버가 켜져 있어야 한다.
- 주소 끝에 `#img=<사진 이름>` 을 붙이면 그 사진을 바로 예측한다 (15번의 백업 1~3 링크).
- 끄기: 서버를 켠 터미널에서 `Ctrl+C` (백그라운드로 켰다면 `pkill -f app/server.py`).

## 화면

| 영역 | 내용 |
|---|---|
| 위 | 모델 이름 · imgsz · Weight 해시, Validation · Frozen Test mAP50-95, 준비 상태(GPU 이름), 모델 정보 · 단축키 · ← 발표로 |
| 왼쪽 | Validation 104장 썸네일 (촬영 묶음 · Class 로 거르기, 예측한 사진은 ✓ 맞힘 수 / ✕ 틀린 수 배지), 올린 사진 탭, 끌어다 놓기 |
| 가운데 | 4K 원본 위에 박스 — **예측 / 정답 / 비교** (비교 = 맞힘 · 종류 틀림(노랑) · 오검출(분홍 점선) · 놓친 정답(✕)). 휠 확대 · 끌어 이동 · 더블클릭 맞춤 · 박스 위에 마우스를 올리면 Class · 확신도 · 크기 |
| 오른쪽 | 확신도 기준 슬라이더(기본 0.25) · 이 사진 결과(맞힘 · 종류 틀림 · 오검출 · 놓침, Class 별 표, 모델 ms) · 검출 목록(누르면 그 박스로 확대) · YOLO TXT 후보 저장 · **Validation 104장 일괄 채점** |

단축키: `←/→` 사진 · `1/2/3` 예측·정답·비교 · `[`/`]` 기준 ∓0.05 · `+/-/0` 확대·축소·맞춤 · `F` 전체화면 · `S` TXT 저장 · `A` 일괄 채점 · `I` 모델 정보 · `?` 단축키 · `Backspace` 발표로

## API

| 메서드 · 경로 | 내용 |
|---|---|
| `GET /api/info` | 실행 이름 · Weight · sha256 · imgsz · 준비 상태 · 장치 · Class 이름 · Val/Test 성능(`runs_summary.csv` · `05_final/final_metrics.csv`) |
| `GET /api/images` | Validation 사진 목록 (촬영 묶음 · 장면 · Class 별 정답 수) |
| `GET /api/images/{id}/thumb` · `/full` | 썸네일(1/8 디코드 · 메모리 캐시) · 원본 |
| `POST /api/images/{id}/predict?conf=` | 예측(처음 한 번, conf 0.05) + 그 기준의 판정 |
| `GET /api/images/{id}/judge?conf=` | 이미 예측한 결과를 다른 기준으로 다시 판정 (재예측 없음) |
| `POST /api/upload` | 사진 원본 바이트 + `X-Filename` 헤더 → 메모리에만 보관, Val 사진 이름이면 Val 로 취급 |
| `GET /api/summary?conf=` | 예측이 끝난 Validation 사진 전체 합계 (TP · CLASS_ERROR · FP · FN, Class 별) |

판정은 [`src/inference.py`](../src/inference.md) 의 `match()` 그대로다 (IoU 0.5, 같은 Class → TP, 다른 Class → CLASS_ERROR). 그래서 `08_predict_images.py` · `09_collect_failures.py` 와 숫자가 같다 — 2026-10-20 일괄 채점(기준 0.25): **맞힘 506 · 종류 틀림 1 · 오검출 31 · 놓침 34** (예측 538 · 정답 541), 104장 약 12초, 모델 중앙값 38.5 ms/장.

## 설계 메모

- **예측은 conf 0.05 로 한 번만** 하고 기준은 판정 때 거른다. 낮은 확신도 박스는 NMS 에서 높은 박스를 지우지 못하므로, 0.25 로 거른 결과는 0.25 로 예측한 결과와 같다 (위 숫자로 확인).
- 사진은 한 장씩, GPU 는 잠금 하나로 순서대로 쓴다. 모델 Load 는 서버가 뜬 뒤 뒤에서 하므로 화면이 먼저 열리고 상태가 "준비 완료"로 바뀐다.
- 다음 사진을 미리 예측해 두어 `→` 로 넘길 때 바로 뜬다.

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md) (`resolve("final")`, `run_args`), [`src/inference`](../src/inference.md) (`load_gt`, `match`), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md) (`sha256_short`), FastAPI · uvicorn (`requirements.txt`)
- **사용하는 곳**: 발표자료 [`presentation/index.html`](../../../presentation/README.md) 15번 슬라이드

## 주의사항 (보안 · 교과 8 규칙)

- **127.0.0.1 에서만** 연다 (`--host` 를 바꾸지 않는 것을 권장 — 화면에 회사 사진이 보인다).
- **Frozen Test · Bridge Holdout 사진은 목록에 없고, 같은 이름의 사진을 올려도 403 으로 거절**한다 (`split_manifest.csv` 의 역할 기준). 이름을 바꿔 올린 사진까지는 막지 못한다 — 시연자는 Validation 사진만 쓴다.
- 올린 사진은 **메모리에만** 두고(최근 30장) 디스크에 저장하지 않는다. 서버를 끄면 사라진다.
- TXT 후보는 **Auto Label 후보**다. 교과 7 라벨링 도구에서 사람이 확인 · 수정 · 승인한 뒤에만 정답으로 쓴다.
- 일괄 채점 숫자는 **박스 개수 기준**(IoU 0.5)이라 mAP 와 다르다. 성능은 Frozen Test mAP50-95 0.639 로 말한다.
- 학습이 돌고 있는 PC 에서는 GPU 메모리가 모자랄 수 있다 (2240 예측 약 1.1GB 추가).
