"""공식 Version kimchi_v5 (C안 재분할) 학습 — 06 Baseline 조건 + 한 변수 개선 실험을 v5 에서 한다.

    python scripts/00_setup.py                       # 먼저 data/yolo (v5) 준비
    python scripts/11_train_v5.py --run exp001       # 하나만 (all = 차례로 전부, 이미 Weight 가 있으면 멈춤)
    python scripts/11_train_v5.py --run exp005 --report-only   # 학습은 끝났는데 조건 기록만 다시

  baseline : imgsz 640                         → runs/baseline_v5/
  exp001   : imgsz 1280                        → runs/exp001_v5_imgsz1280/
  exp002   : imgsz 1920 · batch 6              → runs/exp002_v5_imgsz1920/
  exp003   : exp002 + epochs 100               → runs/exp003_v5_imgsz1920_epoch100/
  exp005   : exp002 + 증강 (flipud · hsv_v)    → runs/exp005_v5_imgsz1920_aug/
  (exp004 타일링은 14_train_tiles_v5.py)
  Weight → models/baseline · improved/<실행>.pt (src/registry.py)
  조건 기록 → reports/02_baseline/baseline_training_condition.md (baseline), reports/04_improvement/<실행>_training_condition.md

조건은 06(BASELINE)·10(EXPERIMENTS) 에서 그대로 가져온다. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.
분할 기준: docs/project/kimchi_v5_split.md
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)  # dataset.yaml 의 path: data/yolo 는 이 폴더 기준

from src import registry  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import (  # noqa: E402
    best_epoch_metrics, check_training, copy_weight, rel, sha256_short, train_detector, write_condition_report,
)

# 10 을 불러오면 06(tb)도 함께 불러온다 — 조건은 두 곳에서만 관리
_spec = importlib.util.spec_from_file_location("train_v2", PROJECT_ROOT / "scripts" / "10_train_v2.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
tb = ex.tb

DATASET_VERSION = "kimchi_v5"
paths = SplitBuilder(PROJECT_ROOT, DATASET_VERSION)
# 06 의 precheck 가 v5 폴더를 보게 한다
tb.DATA_YAML, tb.MANIFEST_DIR, tb.YOLO_DIR = paths.dataset_yaml, paths.manifest_dir, paths.yolo_dir

_EXP007 = {"model_name": "yolo11s.pt", "imgsz": 1920, "batch": 3, "flipud": 0.5, "hsv_v": 0.6}   # exp007 조건 (v5 Val 최고 0.724)
_AUG_TEXT = "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp007 과 같음"
RUNS = {
    "baseline": {"change": {}, "run_name": "baseline_v5", "title": "kimchi_v5 Baseline"},
    "exp001": {"change": ex.EXPERIMENTS["exp001"]["change"], "run_name": "exp001_v5_imgsz1280",
               "title": "kimchi_v5 개선 실험 exp001", "compare": "baseline_v5 (imgsz 640)"},
    "exp002": {"change": ex.EXPERIMENTS["exp002"]["change"], "run_name": "exp002_v5_imgsz1920",
               "title": "kimchi_v5 개선 실험 exp002", "compare": "exp001_v5 (imgsz 1280)",
               "note": ex.EXPERIMENTS["exp002"]["note"]},
    "exp003": {"change": ex.EXPERIMENTS["exp003"]["change"], "run_name": "exp003_v5_imgsz1920_epoch100",
               "title": "kimchi_v5 개선 실험 exp003", "compare": "exp002_v5 (epochs 50)",
               "note": ex.EXPERIMENTS["exp003"]["note"]},
    # 바꾸는 변수 하나 = 증강 설정 (가이드 참고자료 "Augmentation: 기본 → 밝기/Scale 등 강화")
    # 근거: v5 Val 은 Train 이 못 본 촬영 묶음(다른 날·다른 조명) — exp002_v5 는 Train loss 가 계속 내려가는데 Val dfl_loss 는 30 epoch 뒤 멈춤(과적합 신호)
    #   flipud 0 → 0.5 : 위에서 내려다본 사진이라 위아래 뒤집어도 같은 장면 (이물 방향은 원래 제각각)
    #   hsv_v 0.4 → 0.6: 날짜마다 다른 밝기
    "exp005": {"change": {**ex.EXPERIMENTS["exp002"]["change"], "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp005_v5_imgsz1920_aug",
               "title": "kimchi_v5 개선 실험 exp005", "compare": "exp002_v5 (기본 증강)",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4)",
               "note": "exp002_v5 와 다른 변수는 증강 설정 하나 (flipud 0 → 0.5, hsv_v 0.4 → 0.6). 이미지 파일은 만들지 않고 학습 중에만 변형한다. Val 은 원본."},
    # 두 변수 동시 변경 실험 (사용자 결정 2026-10-16) — exp002 대비 2개, exp005(증강) 대비는 1개라 각 효과를 따로 읽는다.
    # RTX 3060 12GB 측정: 11n·2560·batch 3 = 10.8GB, 11s·1920·batch 3 = 9.0GB (11s·2560 은 batch 2 도 13.6GB 로 넘쳐 제외)
    "exp006": {"change": {"imgsz": 2560, "batch": 3, "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp006_v5_imgsz2560_aug", "title": "kimchi_v5 개선 실험 exp006",
               "compare": "exp005_v5 (imgsz 1920 · 같은 증강) — exp002_v5 대비로는 해상도·증강 두 변수",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp005 와 같음",
               "note": "exp005_v5 와 다른 변수는 imgsz(1920 → 2560) 하나 (batch 6 → 3 은 GPU 메모리 때문, nbs=64 gradient 누적으로 갱신 1번당 사진 수는 거의 같음). "
                       "exp002_v5 대비로는 해상도·증강 두 변수를 함께 바꾼 실험이다."},
    "exp007": {"change": {"model_name": "yolo11s.pt", "imgsz": 1920, "batch": 3, "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp007_v5_s_imgsz1920_aug", "title": "kimchi_v5 개선 실험 exp007",
               "compare": "exp005_v5 (YOLO11n · 같은 증강) — exp002_v5 대비로는 모델 크기·증강 두 변수",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp005 와 같음",
               "note": "exp005_v5 와 다른 변수는 모델 크기(YOLO11n → YOLO11s) 하나 (batch 6 → 3 은 GPU 메모리 때문). "
                       "exp002_v5 대비로는 모델 크기·증강 두 변수를 함께 바꾼 실험이다."},
    # ── 3대 분산 실험 (docs/project/experiment_handoff.md) — 모두 exp007(11s · 1920 · 증강) 기준, 한 변수씩 ──
    "exp008": {"change": {**_EXP007, "epochs": 100}, "run_name": "exp008_v5_s_imgsz1920_aug_epoch100",
               "title": "kimchi_v5 개선 실험 exp008", "compare": "exp007_v5 (epochs 50)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 epochs(50 → 100) 하나. exp007 의 best epoch 가 마지막(50)이라 학습 부족 가능성 확인."},
    "exp009": {"change": {**_EXP007, "model_name": "yolo11m.pt", "batch": 2}, "run_name": "exp009_v5_m_imgsz1920_aug",
               "title": "kimchi_v5 개선 실험 exp009", "compare": "exp007_v5 (YOLO11s)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 모델 크기(YOLO11s → YOLO11m) 하나 (batch 3 → 2 는 GPU 메모리 — 12GB 에서 넘치면 batch 1 대신 GPU 큰 PC 에서)."},
    "exp011": {"change": {k: v for k, v in _EXP007.items() if k not in ("flipud", "hsv_v")}, "run_name": "exp011_v5_s_imgsz1920",
               "title": "kimchi_v5 개선 실험 exp011", "compare": "exp007_v5 (증강 있음)",
               "note": "exp007_v5 와 다른 변수는 증강 하나 (flipud·hsv_v 를 기본값으로). 큰 모델에서 증강이 실제로 도움이 되는지 분리."},
    "exp012": {"change": {**_EXP007, "imgsz": 1280, "batch": 6}, "run_name": "exp012_v5_s_imgsz1280_aug",
               "title": "kimchi_v5 개선 실험 exp012", "compare": "exp007_v5 (imgsz 1920)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 imgsz(1920 → 1280) 하나 (batch 3 → 6). 예측 속도가 중요한 현장(교과 14)용 가벼운 후보."},
    "exp013": {"change": {**_EXP007, "seed": 7}, "run_name": "exp013_v5_s_imgsz1920_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp013", "compare": "exp007_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 seed 만 다르다 (42 → 7). 같은 조건에서 점수가 얼마나 흔들리는지 재서, 실험 사이 0.02 차이가 의미 있는지 판단한다."},
    # ── 2라운드 (Final 후보 3개 × seed 2개 — docs/project/experiment_handoff.md 8장) ──
    # exp013 결과 seed 만 바꿔도 ±0.01 흔들림 → 후보마다 seed 2개 이상 평균으로 비교한다
    "exp014": {"change": {**_EXP007, "seed": 123}, "run_name": "exp014_v5_s_imgsz1920_aug_seed123",
               "title": "kimchi_v5 반복 실험 exp014", "compare": "exp007_v5 · exp013_v5 (같은 조건 seed 42 · 7)", "augmentation": _AUG_TEXT,
               "note": "exp007 조건의 세 번째 seed (123). 후보 A(11s · 1920) 의 seed 평균·흔들림을 잰다."},
    "exp015": {"change": {**_EXP007, "imgsz": 2240, "batch": 2}, "run_name": "exp015_v5_s_imgsz2240_aug",
               "title": "kimchi_v5 개선 실험 exp015", "compare": "exp007_v5 (imgsz 1920)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 imgsz(1920 → 2240) 하나 (batch 3 → 2, GPU 9.4GB 측정). 11n 에서 해상도 효과가 컸고(+0.038), 11s·2560 은 메모리 초과라 2240."},
    "exp016": {"change": {**_EXP007, "imgsz": 2240, "batch": 2, "seed": 7}, "run_name": "exp016_v5_s_imgsz2240_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp016", "compare": "exp015_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp015 조건의 두 번째 seed (7). 후보 B(11s · 2240) 의 seed 평균."},
    "exp017": {"change": {**_EXP007, "model_name": "yolo11m.pt", "batch": 2, "seed": 7}, "run_name": "exp017_v5_m_imgsz1920_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp017", "compare": "exp009_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp009 조건(YOLO11m · 1920 · batch 2, GPU 9.8GB 측정)의 두 번째 seed (7). 후보 C(11m · 1920) 의 seed 평균."},
    "exp018": {"change": {**_EXP007, "imgsz": 2240, "batch": 2, "seed": 123}, "run_name": "exp018_v5_s_imgsz2240_aug_seed123",
               "title": "kimchi_v5 반복 실험 exp018", "compare": "exp015_v5 · exp016_v5 (같은 조건 seed 42 · 7)", "augmentation": _AUG_TEXT,
               "note": "exp015 조건(11s · 2240 · batch 2)의 세 번째 seed (123). 후보 B 를 후보 A(exp007·013·014) 와 같은 seed 3개 평균으로 비교한다."},
}


# ── 4라운드 (밤샘 · 2026-10-19) — 기반 B(exp015 조건), 방향 6개 × seed 3개 (docs/project/experiment_handoff.md 9장) ──
# 근거: 갈변 mAP50-95 0.1 (나머지 클래스 0.80~0.92). Train 갈변은 잎 전체(대부분 200px 이상), Val 갈변은 작은 반점(중앙값 25px)
#   반점 복제 ×10 : 100px 미만 갈변이 있는 Train 사진 8장을 학습 목록에 10번씩 (사진 파일은 그대로, 목록만)
#   반점 합성     : 그 반점들을 갈변 없는 Train 사진 150장의 배추 위에 3개씩 붙인 사진을 추가 (data/yolo_v5_r4/, Git 제외)
#   2560 · batch 1: 해상도 1280 0.680 → 1920 0.715 → 2240 0.735 로 아직 오르는 중 (2560 · batch 2 는 12GB 초과, batch 1 은 7.4GB)
#   반점 복원     : kimchi_v3 라벨 개정 때 Train 반점 20 → 8 (Val 41 → 15, Test 14 → 14 그대로) — 지운 Train 반점을 되살려 Val·Test 기준에 맞춤.
#                   공식 kimchi_v5 라벨은 그대로 두고 이 실험의 학습 목록에만 쓴다 (data/yolo_v5_r4/restore, Git 제외)
_B = {**_EXP007, "imgsz": 2240, "batch": 2}
_B2560 = {**_EXP007, "imgsz": 2560, "batch": 1}
_R4_DIRECTIONS = [   # (태그, 설명, 학습 조건, 데이터 변경)
    ("os10", "B + 반점 복제 ×10", _B, {"oversample": 10}),
    ("cp", "B + 반점 합성", _B, {"synth": True}),
    ("2560", "11s · 2560 · batch 1 (B 에서 해상도만)", _B2560, {}),
    ("rs_os10", "B + Train 반점 복원 + 복제 ×10", _B, {"restore": True, "oversample": 10}),
    ("2560_os10", "2560 + 반점 복제 ×10", _B2560, {"oversample": 10}),
    ("2560_cp", "2560 + 반점 합성", _B2560, {"synth": True}),
]
# B 의 같은 seed 실행과 짝지어 비교. seed 5개 평균으로 판정 (B 의 seed 3개가 0.726~0.746 로 0.02 흔들림 = 채택 기준과 같음)
_R4_SEEDS = [(42, "", "exp015_v5"), (7, "_seed7", "exp016_v5"), (123, "_seed123", "exp018_v5"), (1, "_seed1", "exp049_v5"), (2, "_seed2", "exp050_v5")]
for _i, (_tag, _desc, _cond, _data) in enumerate(_R4_DIRECTIONS):
    for _j, (_seed, _suffix, _pair) in enumerate(_R4_SEEDS):
        _key = f"exp{19 + _i * 3 + _j:03d}" if _j < 3 else f"exp{37 + _i * 2 + _j - 3:03d}"   # seed 1·2 는 exp037~048
        RUNS[_key] = {"change": {**_cond, "seed": _seed}, "data": _data, "run_name": f"{_key}_v5_r4_{_tag}{_suffix}",
                      "title": f"kimchi_v5 4라운드 {_key} ({_desc})", "compare": f"{_pair} (B · 같은 seed {_seed}) · B seed 3개 평균 0.735",
                      "augmentation": _AUG_TEXT,
                      "note": f"4라운드 방향 '{_desc}' 의 seed {_seed}. 갈변(작은 반점) 개선이 목적이라 클래스별 갈변 mAP 도 함께 본다."}

for _key, _seed in (("exp049", 1), ("exp050", 2)):   # B 자체도 seed 5개로 (exp015·016·018 + 2개)
    RUNS[_key] = {"change": {**_B, "seed": _seed}, "run_name": f"{_key}_v5_s_imgsz2240_aug_seed{_seed}",
                  "title": f"kimchi_v5 반복 실험 {_key}", "compare": "exp015_v5 · exp016_v5 · exp018_v5 (같은 조건 seed 42 · 7 · 123)", "augmentation": _AUG_TEXT,
                  "note": f"B(11s · 2240 · batch 2) 의 seed {_seed}. 4라운드 방향들과 seed 5개 평균으로 비교하기 위한 기준."}

R4_DIR = PROJECT_ROOT / "data" / "yolo_v5_r4"   # 생성 데이터 (data/yolo*/ 라 Git 제외 · 어느 PC 에서나 같은 결과로 다시 만든다)
SPECK_MAX_PX = 100        # 이보다 작은 갈변 박스 = 반점
SYNTH_IMAGES, SYNTH_PER_IMAGE, SYNTH_SEED = 150, 3, 0
S7_FINAL_LABELS = PROJECT_ROOT.parent / "subject7" / "data" / "final" / "labels"   # 교과 7 최종 라벨 (kimchi_v3 개정 전)


def _read_labels(label_path):
    return [line.split() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def speck_sources():
    """Train 에서 긴 변 SPECK_MAX_PX 미만 갈변 박스 [(이미지, (cx, cy, w, h) px)]"""
    from PIL import Image
    out = []
    for lp in sorted((paths.yolo_dir / "labels" / "train").glob("*.txt")):
        img = paths.yolo_dir / "images" / "train" / f"{lp.stem}.jpg"
        size = None
        for r in _read_labels(lp):
            if r[0] != "5":
                continue
            if size is None:
                with Image.open(img) as im:
                    size = im.size
            W, H = size
            cx, cy, w, h = float(r[1]) * W, float(r[2]) * H, float(r[3]) * W, float(r[4]) * H
            if max(w, h) < SPECK_MAX_PX:
                out.append((img, (cx, cy, w, h)))
    return out


def make_synth():
    """반점 합성 사진을 R4_DIR/synth 에 만든다 (이미 있으면 그대로). 같은 seed · 같은 Train 이면 어느 PC 에서나 같다."""
    import random
    import numpy as np
    from PIL import Image, ImageFilter
    out_img, out_lbl = R4_DIR / "synth" / "images" / "train", R4_DIR / "synth" / "labels" / "train"
    done = R4_DIR / "synth" / f"done_{SYNTH_IMAGES}x{SYNTH_PER_IMAGE}_seed{SYNTH_SEED}.txt"
    if done.is_file():
        return sorted(out_img.glob("*.jpg"))
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SYNTH_SEED)
    pad = 4
    specks = []
    for img, (cx, cy, w, h) in speck_sources():
        with Image.open(img) as im:
            specks.append(im.convert("RGB").crop((int(cx - w / 2) - pad, int(cy - h / 2) - pad, int(cx + w / 2) + pad, int(cy + h / 2) + pad)))
    targets = [lp for lp in sorted((paths.yolo_dir / "labels" / "train").glob("*.txt")) if all(r[0] != "5" for r in _read_labels(lp))]
    print(f" 반점 합성: 반점 {len(specks)}개 → 갈변 없는 Train {len(targets)}장 중 {SYNTH_IMAGES}장에 {SYNTH_PER_IMAGE}개씩")
    pasted = 0
    for lp in rng.sample(targets, SYNTH_IMAGES):
        im = Image.open(paths.yolo_dir / "images" / "train" / f"{lp.stem}.jpg").convert("RGB")
        W, H = im.size
        sat = np.asarray(im.convert("HSV"))[..., 1]
        rows = _read_labels(lp)
        taken = [(float(r[1]) * W, float(r[2]) * H, float(r[3]) * W / 2 + 40, float(r[4]) * H / 2 + 40) for r in rows]   # 기존 박스 + 여유 40px
        new = []
        for _ in range(SYNTH_PER_IMAGE):
            sp = rng.choice(specks)
            if rng.random() < 0.5:
                sp = sp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            sp = sp.rotate(90 * rng.randrange(4), expand=True)
            s = rng.uniform(0.8, 1.25)
            sp = sp.resize((max(2 * pad + 4, round(sp.width * s)), max(2 * pad + 4, round(sp.height * s))))
            for _try in range(200):
                x, y = rng.randint(int(W * 0.05), int(W * 0.95) - sp.width), rng.randint(int(H * 0.05), int(H * 0.95) - sp.height)
                mx, my = x + sp.width / 2, y + sp.height / 2
                if sat[max(0, int(my) - 60):int(my) + 60, max(0, int(mx) - 60):int(mx) + 60].mean() < 60:   # 배추 위만 (배경 S 약 25, 배추 70 이상)
                    continue
                if any(abs(mx - tx) < tw + sp.width / 2 and abs(my - ty) < th + sp.height / 2 for tx, ty, tw, th in taken):
                    continue
                mask = Image.new("L", sp.size, 0)
                mask.paste(255, (pad // 2, pad // 2, sp.width - pad // 2, sp.height - pad // 2))
                im.paste(sp, (x, y), mask.filter(ImageFilter.GaussianBlur(pad / 2)))
                bw, bh = sp.width - 2 * pad, sp.height - 2 * pad
                new.append(f"5 {mx / W:.6f} {my / H:.6f} {bw / W:.6f} {bh / H:.6f}")
                taken.append((mx, my, sp.width / 2 + 40, sp.height / 2 + 40))
                pasted += 1
                break
        im.save(out_img / f"{lp.stem}_r4sp.jpg", quality=95)
        (out_lbl / f"{lp.stem}_r4sp.txt").write_text("\n".join([" ".join(r) for r in rows] + new) + "\n", encoding="utf-8")
    done.write_text(f"pasted {pasted}\n", encoding="utf-8")
    print(f" 반점 합성 완료: 사진 {SYNTH_IMAGES}장 · 반점 {pasted}개 → {rel(out_img)}")
    return sorted(out_img.glob("*.jpg"))


def restore_specks():
    """교과 7 최종 라벨에는 있었는데 kimchi_v3 개정 때 지운 Train 반점(긴 변 SPECK_MAX_PX 미만 갈변)을 되살린 라벨을
    R4_DIR/restore 에 만든다 (사진은 원본 심볼릭 링크). 반환 {stem: 학습 목록에 쓸 사진 경로}"""
    from PIL import Image
    final = {lp.stem: lp for lp in S7_FINAL_LABELS.rglob("*.txt") if lp.name != "classes.txt"}
    out_img, out_lbl = R4_DIR / "restore" / "images" / "train", R4_DIR / "restore" / "labels" / "train"
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)
    restored, n = {}, 0
    for lp in sorted((paths.yolo_dir / "labels" / "train").glob("*.txt")):
        if lp.stem not in final:
            continue
        rows = _read_labels(lp)
        img = paths.yolo_dir / "images" / "train" / f"{lp.stem}.jpg"
        cur = [(float(r[1]), float(r[2])) for r in rows if r[0] == "5"]
        add, size = [], None
        for r in _read_labels(final[lp.stem]):
            if len(r) != 5 or r[0] != "5":
                continue
            cx, cy, w, h = map(float, r[1:5])
            if any(abs(cx - a) < 0.002 and abs(cy - b) < 0.002 for a, b in cur):   # 지금도 있는 박스
                continue
            if size is None:
                with Image.open(img) as im:
                    size = im.size
            if max(w * size[0], h * size[1]) < SPECK_MAX_PX:
                add.append(r)
        if add:
            link = out_img / f"{lp.stem}.jpg"
            if not link.exists():
                link.symlink_to(img.resolve())
            (out_lbl / f"{lp.stem}.txt").write_text("\n".join(" ".join(r) for r in rows + add) + "\n", encoding="utf-8")
            restored[lp.stem] = os.path.abspath(link)
            n += len(add)
    print(f" 반점 복원: Train {len(restored)}장에 반점 {n}개 (kimchi_v3 개정 때 지운 것)")
    return restored


# ── 5라운드 (2026-10-20): Final(exp050) 확정 뒤 갈변 진단 — Final 을 바꾸지 않는다 (Frozen Test 를 이미 봄) ──
# 진단 결과: 복제 모델(exp019)은 Train 반점 8개를 conf 0.35~0.95 로 모두 찾는데 Val 반점은 15개 중 2개 (외움).
#            Val 반점 20~31px 13개 중 9~10개는 conf 0.001 에서도 예측 박스가 아예 없다 (후보조차 안 나옴).
#   P2 검출층 : stride 8 격자에서 반점(입력 약 12px)은 1~2칸 → stride 4 층을 더해 후보가 나오게 (configs/yolo11s-p2.yaml)
#               batch 2 는 13.1GB 라 batch 1 (6.7GB). nbs 64 누적이라 실제 갱신 단위는 batch 2 와 같다
#   변형 합성 : 반점을 "다른 개체"로 — 원본 반점 8개 + 중간 갈변(100~200px)을 반점 크기로 줄인 것을 원천으로,
#               하나씩 회전 · 찌그러뜨림 · 색 · 번짐을 바꾸고 반점 픽셀만(둘레보다 어두운 곳) 붙인다 (data/yolo_v5_r4/synth2, Git 제외)
P2_CFG = PROJECT_ROOT / "configs" / "yolo11s-p2.yaml"
_P2 = {**_B, "model_name": str(P2_CFG), "transfer": "yolo11s.pt", "batch": 1}
_R5_DIRECTIONS = [   # (태그, 설명, 학습 조건, 데이터 변경)
    ("p2", "B + P2 검출층 (batch 1)", _P2, {}),
    ("cp2", "B + 변형 반점 합성", _B, {"synth2": True}),
    ("p2_cp2", "P2 + 변형 반점 합성", _P2, {"synth2": True}),
]
for _i, (_tag, _desc, _cond, _data) in enumerate(_R5_DIRECTIONS):
    for _j, (_seed, _suffix, _pair) in enumerate(_R4_SEEDS):
        _key = f"exp{51 + _i * 5 + _j:03d}"   # exp051~065
        RUNS[_key] = {"change": {**_cond, "seed": _seed}, "data": _data, "run_name": f"{_key}_v5_r5_{_tag}{_suffix}",
                      "title": f"kimchi_v5 5라운드 {_key} ({_desc})", "compare": f"{_pair} (B · 같은 seed {_seed}) · B seed 5개 평균 0.739 · 갈변 0.108",
                      "augmentation": _AUG_TEXT,
                      "note": f"5라운드(갈변 진단) '{_desc}' 의 seed {_seed}. Final(exp050) 확정 뒤의 진단 실험이라 Final 을 바꾸지 않는다. 클래스별 갈변 mAP 로 본다."}

SYNTH2_IMAGES, SYNTH2_PER_IMAGE, SYNTH2_SEED = 150, 3, 0
SYNTH2_SRC_MAX_PX = 200            # 원천: 이보다 작은 Train 갈변 (반점 8개 + 중간 갈변)
SYNTH2_SIZE_PX = (18, 45)          # 붙일 때 긴 변 (원본 px) — Val · Test 반점 20~31px 근처


def make_synth2():
    """변형 반점 합성 사진을 R4_DIR/synth2 에 만든다 (이미 있으면 그대로). 같은 seed · 같은 Train 이면 어느 PC 에서나 같다."""
    import random
    import cv2
    import numpy as np
    from PIL import Image
    out_img, out_lbl = R4_DIR / "synth2" / "images" / "train", R4_DIR / "synth2" / "labels" / "train"
    done = R4_DIR / "synth2" / f"done_{SYNTH2_IMAGES}x{SYNTH2_PER_IMAGE}_seed{SYNTH2_SEED}.txt"
    if done.is_file():
        return sorted(out_img.glob("*.jpg"))
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SYNTH2_SEED)
    nrng = np.random.default_rng(SYNTH2_SEED)
    srcs = []   # (RGB 패치 ndarray, 원래 긴 변 px) — 박스보다 25% 넓게 잘라 둘레 배추를 함께
    for lp in sorted((paths.yolo_dir / "labels" / "train").glob("*.txt")):
        rows = [r for r in _read_labels(lp) if r[0] == "5"]
        if not rows:
            continue
        im = np.asarray(Image.open(paths.yolo_dir / "images" / "train" / f"{lp.stem}.jpg").convert("RGB"))
        H, W = im.shape[:2]
        for r in rows:
            cx, cy, w, h = float(r[1]) * W, float(r[2]) * H, float(r[3]) * W, float(r[4]) * H
            if max(w, h) >= SYNTH2_SRC_MAX_PX:
                continue
            x0, y0 = int(max(0, cx - w * 0.625)), int(max(0, cy - h * 0.625))
            x1, y1 = int(min(W, cx + w * 0.625)), int(min(H, cy + h * 0.625))
            srcs.append((im[y0:y1, x0:x1].copy(), max(w, h)))
    targets = [lp for lp in sorted((paths.yolo_dir / "labels" / "train").glob("*.txt")) if all(r[0] != "5" for r in _read_labels(lp))]
    print(f" 변형 합성: 원천 갈변 {len(srcs)}개 (긴 변 {SYNTH2_SRC_MAX_PX}px 미만) → 갈변 없는 Train {len(targets)}장 중 {SYNTH2_IMAGES}장에 {SYNTH2_PER_IMAGE}개씩")

    def variant(patch):
        """반점 하나를 다른 개체처럼: 크기 · 찌그러뜨림 · 회전 · 색 · 번짐. 반환 (RGB, alpha 0~1, 박스 w, h)"""
        ph, pw = patch.shape[:2]
        target = rng.uniform(*SYNTH2_SIZE_PX) * 1.25                      # 둘레 포함 크기
        s = target / max(ph, pw)
        sx, sy = s * rng.uniform(0.75, 1.3), s * rng.uniform(0.75, 1.3)   # 가로세로 따로 → 모양 변형
        p = cv2.resize(patch, (max(6, round(pw * sx)), max(6, round(ph * sy))), interpolation=cv2.INTER_AREA)
        ph, pw = p.shape[:2]
        ang, shear = rng.uniform(0, 360), rng.uniform(-0.25, 0.25)
        M = cv2.getRotationMatrix2D((pw / 2, ph / 2), ang, 1.0)
        M[0, 1] += shear
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(ph * sin + pw * cos) + 2, int(ph * cos + pw * sin) + 2
        M[0, 2] += nw / 2 - pw / 2
        M[1, 2] += nh / 2 - ph / 2
        p = cv2.warpAffine(p, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # 반점 픽셀만 붙인다 (네모 · 원판 자국 방지): 패치 둘레(배추) 밝기보다 어두운 픽셀 = 반점, 경계는 살짝만 부드럽게
        L = cv2.cvtColor(p, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
        ring = np.concatenate([L[:2].ravel(), L[-2:].ravel(), L[:, :2].ravel(), L[:, -2:].ravel()])
        a = np.clip((np.median(ring) - L - 10) / 25, 0, 1)
        core = np.zeros((nh, nw), np.float32)
        cv2.ellipse(core, (nw // 2, nh // 2), (max(2, int(nw * 0.45)), max(2, int(nh * 0.45))), 0, 0, 360, 1.0, -1)
        a = cv2.GaussianBlur(a * core, (0, 0), 0.6)
        hsv = cv2.cvtColor(p, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[..., 0] = (hsv[..., 0] + rng.uniform(-4, 4)) % 180             # 갈색 범위 안에서 색조
        hsv[..., 1] *= rng.uniform(0.8, 1.3)
        hsv[..., 2] *= rng.uniform(0.7, 1.05)                              # 진하게 쪽으로 (Val 반점은 진한 갈색)
        p = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB)
        if rng.random() < 0.25:
            p = cv2.GaussianBlur(p, (0, 0), rng.uniform(0.3, 0.7))         # 가끔 초점 흐림
        ys, xs = np.where(a > 0.3)
        if len(xs) < 6:
            return None   # 둘레보다 어두운 픽셀이 거의 없음 → 다른 원천으로
        cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
        return p, a, float(xs.max() - xs.min() + 3), float(ys.max() - ys.min() + 3), cx, cy

    pasted = 0
    for lp in rng.sample(targets, SYNTH2_IMAGES):
        im = np.asarray(Image.open(paths.yolo_dir / "images" / "train" / f"{lp.stem}.jpg").convert("RGB")).astype(np.float32)
        H, W = im.shape[:2]
        sat = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_RGB2HSV)[..., 1]
        rows = _read_labels(lp)
        taken = [(float(r[1]) * W, float(r[2]) * H, float(r[3]) * W / 2 + 40, float(r[4]) * H / 2 + 40) for r in rows]
        new = []
        for _ in range(SYNTH2_PER_IMAGE):
            v = None
            while v is None:
                v = variant(srcs[int(nrng.integers(len(srcs)))][0])
            p, a, bw, bh, ox, oy = v
            ph, pw = p.shape[:2]
            for _try in range(200):
                x, y = rng.randint(int(W * 0.05), int(W * 0.95) - pw), rng.randint(int(H * 0.05), int(H * 0.95) - ph)
                mx, my = x + pw / 2, y + ph / 2
                if sat[max(0, int(my) - 60):int(my) + 60, max(0, int(mx) - 60):int(mx) + 60].mean() < 60:   # 배추 위만
                    continue
                if any(abs(mx - tx) < tw + pw / 2 and abs(my - ty) < th + ph / 2 for tx, ty, tw, th in taken):
                    continue
                im[y:y + ph, x:x + pw] = im[y:y + ph, x:x + pw] * (1 - a[..., None]) + p.astype(np.float32) * a[..., None]
                new.append(f"5 {(x + ox) / W:.6f} {(y + oy) / H:.6f} {bw / W:.6f} {bh / H:.6f}")   # 박스 = 실제로 붙은 반점 픽셀
                taken.append((mx, my, pw / 2 + 40, ph / 2 + 40))
                pasted += 1
                break
        Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(out_img / f"{lp.stem}_r5sp.jpg", quality=95)
        (out_lbl / f"{lp.stem}_r5sp.txt").write_text("\n".join([" ".join(r) for r in rows] + new) + "\n", encoding="utf-8")
    done.write_text(f"sources {len(srcs)} pasted {pasted}\n", encoding="utf-8")
    print(f" 변형 합성 완료: 사진 {SYNTH2_IMAGES}장 · 반점 {pasted}개 → {rel(out_img)}")
    return sorted(out_img.glob("*.jpg"))


def r4_data_yaml(run_name, data):
    """4라운드 데이터 변경(복제 · 합성)이 있으면 학습 목록 txt 와 yaml 을 R4_DIR 에 만들어 경로를 돌려준다. Val 은 그대로."""
    import yaml
    if not data:
        return paths.dataset_yaml
    R4_DIR.mkdir(parents=True, exist_ok=True)
    train = {p.stem: os.path.abspath(p) for p in sorted((paths.yolo_dir / "images" / "train").glob("*.jpg"))}
    speck_stems = {img.stem for img, _ in speck_sources()}
    if data.get("restore"):
        restored = restore_specks()
        train.update(restored)   # 복원한 사진은 restore 폴더 경로로 (라벨을 그 옆에서 읽음)
        speck_stems |= set(restored)
    files = list(train.values())
    if data.get("oversample"):
        files += [train[st] for st in sorted(speck_stems)] * (data["oversample"] - 1)
        print(f" 반점 복제: 사진 {len(speck_stems)}장 × {data['oversample']} → 학습 목록 {len(files)}줄")
    if data.get("synth"):
        files += [str(p.resolve()) for p in make_synth()]
        print(f" 반점 합성 추가 → 학습 목록 {len(files)}줄")
    if data.get("synth2"):
        files += [str(p.resolve()) for p in make_synth2()]
        print(f" 변형 반점 합성 추가 → 학습 목록 {len(files)}줄")
    lst = R4_DIR / f"train_{run_name}.txt"
    lst.write_text("\n".join(files) + "\n", encoding="utf-8")
    cfg = yaml.safe_load(paths.dataset_yaml.read_text(encoding="utf-8"))
    cfg.update({"path": str(paths.yolo_dir.resolve()), "train": str(lst.resolve()), "val": "images/val"})
    cfg.pop("test", None)
    out = R4_DIR / f"{run_name}.yaml"
    out.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out
REPORT_DIR = PROJECT_ROOT / "reports" / "04_improvement"
BASELINE_REPORT = PROJECT_ROOT / "reports" / "02_baseline" / "baseline_training_condition.md"   # 가이드 이름 (산출물 2)
# 06 BASELINE 에 없는 증강 값의 Ultralytics 8.4 기본값 (조건 기록에 "기본 → 바꾼 값" 으로 적는다)
ULTRALYTICS_DEFAULTS = {"flipud": 0.0, "fliplr": 0.5, "hsv_h": 0.015, "hsv_s": 0.7, "hsv_v": 0.4, "degrees": 0.0,
                        "translate": 0.1, "scale": 0.5, "mosaic": 1.0, "mixup": 0.0}


def finished_result(run_name):
    """이미 끝난 실행의 결과 dict (조건 기록만 다시 쓸 때) — 시작 = args.yaml, 종료 = results.csv 수정 시각"""
    import torch
    from datetime import datetime
    d = PROJECT_ROOT / "runs" / run_name
    start = datetime.fromtimestamp((d / "args.yaml").stat().st_mtime)
    end = datetime.fromtimestamp((d / "results.csv").stat().st_mtime)
    return {"save_dir": d, "best": d / "weights" / "best.pt", "last": d / "weights" / "last.pt",
            "results_csv": d / "results.csv", "start": start, "end": end, "seconds": round((end - start).total_seconds()),
            "optimizer": tb.BASELINE["optimizer"], "lr0": tb.BASELINE["lr0"], "device": 0,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}


def train_one(key, counts, report_only=False):
    spec = RUNS[key]
    cond = dict(tb.BASELINE, **spec["change"])
    run_name = spec["run_name"]
    weight = registry.weight_path(run_name)
    report = BASELINE_REPORT if key == "baseline" else REPORT_DIR / f"{run_name}_training_condition.md"
    if weight.exists() and not report_only:
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {weight} (덮어쓰지 않음)")
    print("=" * 65)
    print(f" [Subject 08] {run_name} (Dataset {DATASET_VERSION})" + (" — 조건 기록만" if report_only else ""))
    print("=" * 65)
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in cond.items()))

    if report_only:
        result = finished_result(run_name)
    else:
        result = train_detector(data_yaml=str(r4_data_yaml(run_name, spec.get("data"))), project=str(PROJECT_ROOT / "runs"), name=run_name, **cond)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())
    if ok:
        if not weight.exists():
            copy_weight(result["best"], weight)
        checks["Weight 별도 보관"] = (weight.is_file(), f"`{rel(weight)}` (sha256 {sha256_short(weight)})")

    ref = best_epoch_metrics(result["results_csv"])
    notes = [
        f"Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `{rel(paths.yolo_dir)}/train·val` 이 manifest 와 정확히 같은지 확인했다.",
        "kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). "
        "기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.",
    ]
    if spec["change"]:
        notes.append("Baseline(06) 조건에서 " + ", ".join(f"{k} {tb.BASELINE.get(k, ULTRALYTICS_DEFAULTS.get(k))} → {v}"
                                                         for k, v in spec["change"].items())
                     + f" 으로 바꿨다. 비교 대상: {spec['compare']}.")
    if spec.get("note"):
        notes.append(spec["note"])
    if spec.get("data", {}).get("restore"):
        notes.append("Train 반점 복원: 교과 7 최종 라벨에는 있었는데 kimchi_v3 개정 때 지운 Train 갈변 반점(긴 변 100px 미만)을 이 실험의 학습 라벨에만 되살렸다 "
                     f"(`{rel(R4_DIR)}/restore`, Git 제외). 공식 kimchi_v5 라벨 · Val · Test 는 그대로.")
    if spec.get("data", {}).get("oversample"):
        notes.append(f"학습 목록만 바꿨다: 긴 변 {SPECK_MAX_PX}px 미만 갈변이 있는 Train 사진을 {spec['data']['oversample']}번씩 넣음 (사진 파일·라벨은 그대로, Val 그대로).")
    if spec.get("data", {}).get("synth"):
        notes.append(f"반점 합성 사진 {SYNTH_IMAGES}장을 Train 에 추가: 긴 변 {SPECK_MAX_PX}px 미만 갈변 반점을 갈변 없는 Train 사진의 배추 위에 "
                     f"{SYNTH_PER_IMAGE}개씩 붙임 (seed {SYNTH_SEED}, `{rel(R4_DIR)}/synth`, Git 제외). Val 은 원본 그대로.")
    if spec.get("data", {}).get("synth2"):
        notes.append(f"변형 반점 합성 사진 {SYNTH2_IMAGES}장을 Train 에 추가: 긴 변 {SYNTH2_SRC_MAX_PX}px 미만 Train 갈변(반점 + 중간 갈변)을 "
                     f"긴 변 {SYNTH2_SIZE_PX[0]}~{SYNTH2_SIZE_PX[1]}px 로 줄여, 하나씩 회전 · 찌그러뜨림 · 색 · 번짐을 바꾸고 반점 픽셀(둘레보다 어두운 곳)만 "
                     f"갈변 없는 Train 사진의 배추 위에 {SYNTH2_PER_IMAGE}개씩 붙임 (seed {SYNTH2_SEED}, `{rel(R4_DIR)}/synth2`, Git 제외). Val 은 원본 그대로.")
    if cond.get("transfer"):
        notes.append(f"모델 구조: `{rel(Path(cond['model_name']))}` (YOLO11s + P2 검출층). COCO `{cond['transfer']}` 에서 이름 · 모양이 같은 층만 이어받음 "
                     "(backbone 전체 + head 앞부분, P2 갈래와 Detect 는 새로 학습).")
    if ref:
        notes.append(f"참고 — best.pt 가 저장된 epoch {ref['epoch']} 의 학습 중 Validation: "
                     f"P {ref['precision']:.3f} · R {ref['recall']:.3f} · mAP50 {ref['map50']:.3f} · mAP50-95 {ref['map50_95']:.3f}")
    manifest = rel(paths.manifest_dir)
    write_condition_report(
        report,
        f"{spec['title']} 학습 조건 (`{run_name}`)",
        {
            "Model": (f"YOLO{Path(cond['model_name']).stem[4:]} (`{rel(Path(cond['model_name']))}`, COCO `{cond['transfer']}` 에서 맞는 층만 이어받음)"
                      if cond.get("transfer") else f"YOLO{Path(cond['model_name']).stem[4:]} (`{cond['model_name']}`, COCO 사전학습 · pretrained=True)"),
            "Dataset Version": f"`{DATASET_VERSION}`",
            "Train / Val Manifest": f"`{manifest}/train.csv` {counts['train']}장 (sha256 {sha256_short(paths.manifest_dir / 'train.csv')}) / "
                                    f"`{manifest}/val.csv` {counts['val']}장 (sha256 {sha256_short(paths.manifest_dir / 'val.csv')})",
            "Data 설정": f"`{rel(paths.dataset_yaml)}` (Class ID 0~6, Class 4 미사용)",
            "Epoch": cond["epochs"],
            "Batch": cond["batch"],
            "Image Size": cond["imgsz"],
            "Seed": f"{cond['seed']} (deterministic=True)",
            "Optimizer": cond["optimizer"],
            "Learning Rate (lr0)": cond["lr0"],
            "Augmentation": spec.get("augmentation", "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)"),
        },
        result,
        checks,
        notes=notes,
    )
    for k, (passed, detail) in checks.items():
        print(f" {'PASS' if passed else 'FAIL'}  {k}: {detail}")
    if ref:
        print(f" (참고) best epoch {ref['epoch']}: mAP50 {ref['map50']:.3f} / mAP50-95 {ref['map50_95']:.3f}")
    print(f" 기록: {rel(report)} · 걸린 시간: {result['seconds'] // 60}분 {result['seconds'] % 60}초")
    return ok


def main():
    ap = argparse.ArgumentParser(description="kimchi_v5 학습 (baseline · exp001~065)")
    ap.add_argument("--run", default="all", choices=["all", *RUNS])
    ap.add_argument("--report-only", action="store_true", help="학습은 끝났는데 조건 기록이 없을 때 기록만 다시 쓴다")
    args = ap.parse_args()
    dataset_version, counts = tb.precheck()
    if dataset_version != DATASET_VERSION:
        raise RuntimeError(f"{rel(paths.yolo_dir)} 가 {dataset_version} 입니다.\n"
                           f"  python scripts/03_build_split.py --version {DATASET_VERSION} --copy-files")
    print(f" Dataset {dataset_version}: train {counts['train']}장 / val {counts['val']}장 (manifest 와 폴더 일치)")
    for key in (RUNS if args.run == "all" else [args.run]):
        if not train_one(key, counts, args.report_only):
            sys.exit(1)


if __name__ == "__main__":
    main()
