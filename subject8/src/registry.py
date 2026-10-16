"""모델 등록부 — 실행 이름 하나로 Weight 위치 · Dataset Version · 학습 조건을 찾는다.

규칙 (models/README.md 와 같음)
  runs/<실행>/weights/best.pt  →  공식 Version : models/<역할>/<실행>.pt      (역할: baseline · improved)
                                   지난 Version : models/history/<Version>/<실행>.pt
  공식 이름 (가이드 산출물):  models/baseline/baseline_best.pt = OFFICIAL["baseline"] 의 복사본
                              models/final/final_best.pt       = OFFICIAL["final"] 의 복사본 (8일차)
공식 Version 은 src/constants.py 의 DEFAULT_DATASET_VERSION, 공식 실행은 아래 OFFICIAL 한 곳에서 정한다.
"""
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

from src.constants import DEFAULT_DATASET_VERSION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS = PROJECT_ROOT / "models"
RUNS = PROJECT_ROOT / "runs"

# 가이드 이름이 가리키는 실행 (공식 Version 의 실행이어야 한다)
OFFICIAL: Dict[str, Optional[str]] = {"baseline": "baseline_v5", "final": None}
ALIASES: Dict[str, Path] = {"baseline": MODELS / "baseline" / "baseline_best.pt",
                            "final": MODELS / "final" / "final_best.pt"}
VERSION_RE = re.compile(r"(?:^|_)v(\d+)(?:_|$)")
TILE_RE = re.compile(r"tile(\d)x(\d)")
TILE_OVERLAP = 0.2


def run_version(run: str) -> str:
    """실행 이름의 _v<N> → kimchi_v<N> (예: exp002_v5_imgsz1920 → kimchi_v5)"""
    m = VERSION_RE.search(run)
    if not m:
        raise ValueError(f"실행 이름에 _v<N> 이 없습니다: {run}")
    return f"kimchi_v{m.group(1)}"


def run_role(run: str) -> str:
    return "baseline" if run.startswith("baseline") else "improved"


def weight_path(run: str) -> Path:
    """이 실행의 Weight 를 보관할 위치 (공식 Version 이면 역할 폴더, 아니면 history/<Version>)"""
    version = run_version(run)
    if version == DEFAULT_DATASET_VERSION:
        return MODELS / run_role(run) / f"{run}.pt"
    return MODELS / "history" / version / f"{run}.pt"


def find_weight(run: str) -> Path:
    """보관된 Weight 찾기 — 정해진 위치에 없으면 models/ 아래 같은 이름을 찾는다"""
    p = weight_path(run)
    if p.is_file():
        return p
    found = sorted(MODELS.rglob(f"{run}.pt"))
    if not found:
        raise FileNotFoundError(f"Weight 가 없습니다: {run}.pt (models/README.md 의 목록 확인)")
    return found[0]


def resolve(name: str) -> Tuple[Path, str]:
    """'baseline' · 'final' · 실행 이름 · .pt 경로 → (Weight 경로, 실행 이름)"""
    if name in ALIASES:
        run = OFFICIAL[name]
        if run is None or not ALIASES[name].is_file():
            raise FileNotFoundError(f"{name} 공식 Weight 가 아직 없습니다: {ALIASES[name]}")
        return ALIASES[name], run
    if name.endswith(".pt"):
        p = Path(name)
        return p, p.stem
    return find_weight(name), name


def run_args(run: str) -> Dict:
    """runs/<실행>/args.yaml (학습 때 실제로 쓴 imgsz · batch · epochs …)"""
    return yaml.safe_load((RUNS / run / "args.yaml").read_text(encoding="utf-8"))


def run_tiles(run: str):
    """타일링 실행이면 ((가로, 세로), 겹침), 아니면 None (예: exp004_v5_tile2x2)"""
    m = TILE_RE.search(run)
    return ((int(m.group(1)), int(m.group(2))), TILE_OVERLAP) if m else None
