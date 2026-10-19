# 실험 인수인계 · 3대 분산 학습 계획 (kimchi_v5)

> 작성 2026-10-19 · 정리 담당 ariuck (`feature/ariuck`). 이 문서만 보고 다른 PC 에서 이어서 실험할 수 있게 쓴다.

## 1. 지금까지 (요약)

- **공식 Dataset `kimchi_v5`** — v4 Val 의 누수(132장 중 83장이 Train 과 같은 촬영 묶음)를 없앤 재분할. Train 558 / Val 104 / Test 82 / Bridge 156. 기준 [`kimchi_v5_split.md`](kimchi_v5_split.md)
- **실험 8개** (같은 Val 104장, mAP50-95): baseline 0.470 → 1280 0.646 → 1920 0.704 → **11s·1920·증강(exp007) 0.724 (현재 최고)**. 전체 표·개선점·한계: [`reports/04_improvement/baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md), 판정 [`experiment_log.csv`](../../reports/04_improvement/experiment_log.csv), 모델 목록 [`models/README.md`](../../models/README.md)
- **Final Model 은 아직 정하지 않았다.** 아래 분산 실험 결과를 보고 8일차에 Val 근거로 정한다.
- **Frozen Test(G07·G14)·Bridge Holdout 은 쓰지 않는다.** 예측 스크립트도 막혀 있다.

## 2. 3대 분산 계획

세 PC 모두 학원 컴퓨터로 사양이 같다 (RTX 3060 12GB). 모든 실험은 **exp007 (YOLO11s · imgsz 1920 · batch 3 · 증강 flipud 0.5·hsv_v 0.6 · 50 epoch)** 에서 한 변수씩 바꾼다. 조건은 `scripts/11_train_v5.py` 의 `RUNS` · `scripts/14_train_tiles_v5.py` 의 `TILE_EXPS` 에 **이미 다 등록**돼 있어서, 각자 명령만 실행한다 (코드를 고치지 않으므로 브랜치끼리 충돌하지 않음).

| 담당 · 브랜치 | 실험 | 바꾸는 것 (exp007 대비) | 알고 싶은 것 | 예상 시간 |
|---|---|---|---|---|
| **상우** · `feature/sonny` | exp008 | epochs 50 → 100 | exp007 이 50 epoch 에서 아직 오르는 중 → 더 오르나 | 약 1시간 30분 |
| | exp013 | seed 42 → 7 | 같은 조건 반복 시 점수가 얼마나 흔들리나 (0.02 차이가 의미 있나) | 약 45분 |
| | exp012 | imgsz 1920 → 1280 (batch 6) | 더 가볍고 빠른 후보 (교과 14 현장용) | 약 25분 |
| **동연** · `feature/ariuck` (정리 담당 겸) | exp010 | 입력: 원본 → 2×2 타일링 | 큰 모델 + 타일링이 작은 이물(갈변·가지)에 더 효과적인가 | 약 3시간 |
| **혜성** · `feat/hyesung` | exp009 | YOLO11s → **11m** (batch 2) | 모델을 더 키우면 더 오르나 | 약 2시간 30분~3시간 |
| | exp011 | 증강 끄기 | 11s 에서 증강이 실제로 도움이 되나 (효과 분리) | 약 45분 |

- 11m 메모리 측정 (2026-10-19, 이 사양): imgsz 1920 · batch 2 = **9.8GB** (12GB 안). 넘치면(속도가 갑자기 몇 배 느려짐 · `out of memory`) 멈추고 알려 준다 — batch 1 로 낮추지 않는다 (BatchNorm 이 불안정해짐).
- 한 PC 에서는 **한 번에 하나만** 학습한다 (같이 돌리면 메모리가 넘쳐 꺼진 적 있음). 아래 명령은 `&&` 로 차례로 이어서 돌린다.

## 3. 각 PC 에서 실행하는 법

### 처음 한 번 (세 PC 공통)

```bash
# 1) 저장소 받기 (이미 있으면 cd ~/group_3 && git fetch origin)
git clone https://github.com/ariuck/group_3.git ~/group_3

# 2) 회사 원본 폴더 2개를 그대로 subject7/data/raw/ 에 복사 (USB — 외부 클라우드·메신저 금지)
#    subject7/data/raw/이물검출_학습데이터1/…  subject7/data/raw/이물검출_학습데이터2/…
```

### 상우 — `feature/sonny`

```bash
cd ~/group_3 && git fetch origin && git checkout feature/sonny && git pull
cd subject8 && python3 scripts/00_setup.py                 # 마지막에 "같은 데이터 · 같은 분할 ✓"
.venv/bin/python scripts/11_train_v5.py --run exp008 && \
.venv/bin/python scripts/11_train_v5.py --run exp013 && \
.venv/bin/python scripts/11_train_v5.py --run exp012       # 약 2시간 40분
```

### 동연 — `feature/ariuck`

```bash
cd ~/group_3 && git fetch origin && git checkout feature/ariuck && git pull
cd subject8 && python3 scripts/00_setup.py
.venv/bin/python scripts/14_train_tiles_v5.py --exp exp010  # 조각 만들기 → 학습 → 원본 Val 채점, 약 3시간
```

### 혜성 — `feat/hyesung`

```bash
cd ~/group_3 && git fetch origin && git checkout feat/hyesung && git merge origin/main   # 최신 main 반영
cd subject8 && python3 scripts/00_setup.py
.venv/bin/python scripts/11_train_v5.py --run exp009 && \
.venv/bin/python scripts/11_train_v5.py --run exp011       # 약 3시간 30분
```

- 학습 화면을 닫아도 계속 돌게 하려면 `nohup <명령> > train.log 2>&1 &` 로 실행하고 `tail -f train.log` 로 본다.
- 각 실험이 끝나면 화면 마지막에 `PASS … Weight 별도 보관` 과 `(참고) best epoch N: mAP50 … / mAP50-95 …` 가 나온다. 이 숫자를 커밋 메시지에 적는다.

## 4. 브랜치에 무엇이 올라가나

**모델도 올라간다** (`models/improved/<실행>.pt` — 11s 약 19MB, 11m 약 40MB). 김치 사진만 빼고 결과를 다 올려서 다른 PC 에서 바로 평가·예측·그래프를 볼 수 있게 한다.

| 올린다 (자기 실험 이름이 들어간 것만) | 내용 | 크기 |
|---|---|---|
| `runs/<실행>/results.csv` · `args.yaml` | epoch 별 학습 기록 · 실제로 쓴 설정 | 작음 |
| `runs/<실행>/*.png` · `labels.jpg` | Confusion Matrix · PR 곡선 · 학습 곡선 · 박스 분포 그림 (사진 아님) | 약 1.6MB |
| `models/improved/<실행>.pt` | 학습된 모델 (best epoch) | 19~40MB |
| `reports/04_improvement/<실행>_training_condition.md` | 학습 조건 · GPU · 시간 · 점검 결과 | 작음 |
| (동연) `reports/04_improvement/tiling_eval_exp010.csv` | 타일링 원본 단위 채점 | 작음 |

| 올리지 않는다 | 이유 |
|---|---|
| 김치 사진 · `runs/<실행>/*_batch*.jpg` · `runs/<실행>/weights/` · `data/` | 회사 사진 (`.gitignore` 가 자동으로 막음) · `weights/` 는 `models/` 와 중복 |
| `models/README.md` · `reports/runs_summary.csv` · `reports/figures/` · `experiment_log.csv` | 여러 사람이 같이 고치면 충돌 → 정리 담당(동연)이 합친 뒤 한 번에 만든다 |
| `scripts/` · `src/` · `docs/` | 고칠 일이 생기면 따로 알려 준다 |

```bash
# 상우 예 (실험마다 한 번씩, 또는 셋을 한꺼번에) — 실행 이름은 학습 화면·runs/ 폴더 이름 그대로
cd ~/group_3
R=exp008_v5_s_imgsz1920_aug_epoch100
git add subject8/runs/$R subject8/models/improved/$R.pt subject8/reports/04_improvement/${R}_training_condition.md
git status                                  # 초록색이 위 파일들뿐인지 확인 (사진·weights 가 없어야 함)
git commit -m "feat(subject8): $R — Val mAP50-95 0.xxx · 학습 N분"
git push origin feature/sonny               # 혜성: feat/hyesung · 동연: feature/ariuck
```

| 담당 | 실행 이름 (`R=`) |
|---|---|
| 상우 | `exp008_v5_s_imgsz1920_aug_epoch100` · `exp013_v5_s_imgsz1920_aug_seed7` · `exp012_v5_s_imgsz1280_aug` |
| 동연 | `exp010_v5_s_tile2x2_aug` (+ `tiling_eval_exp010.csv`) |
| 혜성 | `exp009_v5_m_imgsz1920_aug` · `exp011_v5_s_imgsz1920` |

푸시한 뒤 정리 담당(동연)에게 알려 준다. 특이사항(메모리 넘침, 중간에 꺼짐 등)도 같이.

## 5. 정리 담당이 합칠 때 (동연 · `feature/ariuck`)

```bash
cd ~/group_3 && git checkout feature/ariuck && git fetch origin
git merge origin/feature/sonny origin/feat/hyesung          # 실행 이름이 달라 충돌 없음
cd subject8 && .venv/bin/python scripts/plot_runs.py          # 그래프 · runs_summary · models/README
# experiment_log.csv 에 실험별 한 줄 + 판정, baseline_vs_improved.md 표·개선점 갱신
.venv/bin/python ../subject7/tools/check_docs.py . && .venv/bin/python scripts/qa_acceptance_check.py
cd .. && git add -A subject8 && git commit -m "…" && git fetch . feature/ariuck:main && git push origin main feature/ariuck
```

## 6. 판정 기준 (모두 같은 Val 104장)


- 비교 대상(exp007 = 0.724)보다 **mAP50-95 +0.02 이상**이면 채택, 그 밖은 보류·기각. exp013 결과로 흔들림 폭이 0.02 보다 크면 기준을 다시 정한다.
- 타일링(exp010)은 학습 중 Val 이 조각 단위라 `tiling_eval_exp010.csv` (원본 단위, 같은 코드로 잰 exp007 과 비교) 로 판정한다.
- 점수만이 아니라 **학습 시간 · 예측 속도 · Class 별(특히 갈변·벌레)** 도 함께 적는다.

## 7. 알아 둘 것

- GPU 메모리 측정 (RTX 3060 12GB): 11n·2560·batch 3 = 10.8GB · 11s·1920·batch 3 = 9.0GB · 11s·2560 은 batch 2 도 13.6GB (불가). 2560 은 학습 5시간 → 이번 계획에서 뺐다. 11m·1920·batch 2 = 9.8GB.
- 학습이 끝났는데 조건 기록에서 오류가 나면 학습을 다시 하지 말고 `python scripts/11_train_v5.py --run <실험> --report-only`.
- 실행 폴더·Weight 가 이미 있으면 스크립트가 멈춘다 (덮어쓰지 않음). 실패한 실행을 다시 하려면 `runs/<실행>/` 만 지운다 (`results.csv` 가 없을 때만).
- 갈변(작은 점)은 Train 에 4개뿐이라 이번 실험들로도 크게 좋아지기 어렵다 — 한계로 기록돼 있다 ([`baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md) 3장).

## 8. 2라운드 — 6명 동시, 오늘 Final Model 확정 (2026-10-19)

### 1라운드 결과 (같은 Val 104장, mAP50-95)

| 실험 | 결과 | 알게 된 것 |
|---|---|---|
| exp008 (exp007 + epoch 100) | 0.727 | +0.003 — 학습량을 늘려도 거의 안 오름 (시간 2배) |
| **exp013 (exp007 과 seed 만 다름)** | 0.714 | **seed 만 바꿔도 ±0.01 흔들림** → 0.01 안쪽 차이는 의미 없음 · 후보는 seed 2개 이상 평균으로 비교 |
| exp012 (해상도 1280) | 0.680 | -0.044 — 11s 에서도 해상도가 중요 |
| exp010 (11s + 타일링) | 0.723 (원본 단위, exp007 0.729) | 효과 없음 — 11s 는 원본 1920 만으로 충분 |
| exp010b (exp010 을 혜성 PC 에서 다시) | 0.723 | **다른 PC 에서 소수 4자리까지 같음 — 재현성 확인** |
| 추론 옵션 (exp007·exp008, `15_eval_inference_options.py`) | TTA 0.716 · agnostic_nms 0.715 (기본 0.731) | 둘 다 손해 → **Final 은 기본 추론 설정** |

### 2라운드 설계 — Final 후보 3개 × seed 2~3개

남은 질문은 "11s·1920(지금 최고)보다 **해상도를 더**(2240) 또는 **모델을 더**(11m) 키우면 나아지나" 하나다. seed 흔들림이 ±0.01 이라 후보마다 seed 2개 이상을 돌려 **평균**으로 비교한다.

| 후보 | 조건 | seed 42 | seed 7 | seed 123 | 평균 (2026-10-19 현재) |
|---|---|---|---|---|---|
| **A** | 11s · 1920 · 증강 (= exp007) | exp007 0.724 ✅ | exp013 0.714 ✅ | exp014 0.707 ✅ | **0.715** (3개) |
| **B** | 11s · **2240** · 증강 · batch 2 (9.4GB) | exp015 0.726 ✅ | exp016 0.732 ✅ | **exp018** (3라운드 · 상우, 학습 중) | **0.729** (2개) |
| **C** | **11m** · 1920 · 증강 · batch 2 (9.8GB) | exp009 0.730 ✅ | ~~exp017~~ 중단 · 제외 | — | 0.730 (1개) |
| (참고) | 11s · 1920 · 증강 끄기 | exp011 0.716 ✅ — exp007 대비 -0.008, 증강 유지 | | | |

### 6명 배정 (각 PC 실험 1개 — 약 1~1.5시간, 모두 RTX 3060)

| 담당 · 브랜치 | 실험 | 명령 (`cd ~/group_3/subject8` 에서) | 상태 |
|---|---|---|---|
| 혜성 · `feat/hyesung` | exp009 (후보 C seed 42) | `.venv/bin/python scripts/11_train_v5.py --run exp009` | 완료 0.730 |
| 상우 · `feature/sonny` | exp011 (증강 끄기) | `.venv/bin/python scripts/11_train_v5.py --run exp011` | 완료 0.716 |
| 동연 · `feature/ariuck` (정리 담당) | exp015 (후보 B seed 42) | `.venv/bin/python scripts/11_train_v5.py --run exp015` | 완료 0.726 |
| **동훈** · `feature/donghun` | exp016 (후보 B seed 7) | `.venv/bin/python scripts/11_train_v5.py --run exp016` | 완료 0.732 (석범 몫과 바뀜, 커밋 제목의 0.xxx 는 입력 실수) |
| 이후영 · `feature/huyoung` | exp017 (후보 C seed 7) | `.venv/bin/python scripts/11_train_v5.py --run exp017` | **중단 · 제외** — 19 epoch 검증 중 메모리 부족으로 강제 종료(`Killed`, GPU 9.95GB) |
| **석범** · `feature/seokbeom` | exp014 (후보 A seed 123) | `.venv/bin/python scripts/11_train_v5.py --run exp014` | 완료 0.707 (동훈 몫과 바뀜) |

- 동훈·석범은 실험을 서로 바꿔 돌렸다 (입력 실수). 결과는 누가 돌려도 같으므로(exp010·010b 재현성) 그대로 끝내고, **커밋할 때 실제로 돌린 실험 이름(R)을 쓰고 자기 브랜치로 푸시**한다. 팀원 5 의 브랜치는 GitHub 이름으로 짐작한 것 — 사람에 맞게 바꿔도 된다. 새 브랜치면 `git checkout -b <이름> origin/main`.
- 학습은 Ubuntu(WSL) 터미널에서 **창에서 바로** 돌리는 것을 권한다 (진행 표시줄이 실시간으로 보임). `nohup … &` 로 돌렸다면 `tail -f` 는 진행 표시줄이 줄을 바꾸지 않아 멈춘 것처럼 보이니, 확인은 `pgrep -af 11_train_v5; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv; tr '\r' '\n' < train_exp0NN.log | grep '/50 ' | tail -1` 로 한다.
- **새로 시작하는 4명은 먼저 최신 main 을 받는다** (exp014~017 조건이 main 에 있음): `cd ~/group_3 && git fetch origin && git checkout <브랜치> && git merge origin/main` → `cd subject8 && python3 scripts/00_setup.py` → 위 명령.
- 혜성·상우는 이미 돌리고 있는 exp009·exp011 을 그대로 끝낸다 (조건은 1라운드 때 등록된 것과 같음).
- 끝나면 3·4장 방법대로 **자기 실험 이름이 들어간 파일만** 커밋·푸시 (`runs/<실행>/`, `models/improved/<실행>.pt`, `reports/04_improvement/<실행>_training_condition.md`). 실행 이름: `exp014_v5_s_imgsz1920_aug_seed123` · `exp015_v5_s_imgsz2240_aug` · `exp016_v5_s_imgsz2240_aug_seed7` · `exp017_v5_m_imgsz1920_aug_seed7` · `exp009_v5_m_imgsz1920_aug` · `exp011_v5_s_imgsz1920`

### 3라운드 — exp018 (후보 B seed 123)

후보 A 는 seed 3개(exp007·013·014), B 는 2개라 평균 비교가 기울어 있다 → B 에 seed 123 을 더한다. 상우 · `feature/sonny`: `git merge origin/feat/hyesung` 후 `.venv/bin/python scripts/11_train_v5.py --run exp018` (실행 이름 `exp018_v5_s_imgsz2240_aug_seed123`, GPU 9.4GB).

- **중간 판정 (2026-10-19):** B 평균 0.729 가 A 0.715 보다 0.014 높다 (0.01 기준 넘음).
- **exp017(C seed 7)은 제외한다.** 이후영 PC 에서 19 epoch 검증 중 메모리 부족으로 강제 종료됐다. 18 epoch 까지의 값은 50 epoch 실행과 비교할 수 없어 쓰지 않는다. 다시 돌려도 C 평균이 B 보다 0.01 이상 높으려면 exp017 이 0.748 이상이어야 해서(같은 조건 seed 42 는 0.730) 결론이 바뀔 가능성이 낮다 → C 는 seed 1개로 판단: **B 와 같은 수준이라 더 가벼운 B**.
- **exp018 이 나오면 정하는 것은 "다음 개선 실험의 기반 조건 = B" 까지다.** Final 모델 확정(아래 3~5)은 B 기반 개선 실험이 끝난 뒤에 한다 — Frozen Test 는 한 번만 보므로 먼저 쓰지 않는다.

### Final 확정 순서 (개선 실험이 모두 끝난 뒤)

1. 6명 푸시 → `feature/ariuck` 에 합치기 → `python scripts/plot_runs.py`
2. **후보별 seed 평균** + B 기반 개선 실험(채택 기준 +0.02, seed 2개 이상) (A: exp007·013·014 / B: exp015·016·018 / C: exp009 — exp017 제외) 을 비교
   - 가장 높은 후보를 고르되, **평균 차이가 0.01 안이면 더 가볍고 빠른 쪽**(A → B → C 순)을 고른다 (흔들림 안의 차이라서)
3. 고른 후보 안에서 Val mAP50-95 가 가장 높은 실행을 Final 로 → `models/final/final_best.pt` 복사 · `src/registry.py` 의 `OFFICIAL["final"]` 에 실행 이름
4. `reports/final_model_selection.md` 작성 (후보별 평균·흔들림, Class 별, 학습·예측 시간, 선택 이유, 원본 Weight·sha256)
5. **그다음에만** Frozen Test 한 번: `python scripts/16_evaluate_final_test.py` → `reports/05_final/final_metrics.csv`
6. 커밋 → main 병합 → 푸시
