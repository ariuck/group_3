"""개선 분석 — Baseline 과 exp001~003 을 같은 Dataset Version(kimchi_v4)·같은 Validation 에서 비교한다.

    python scripts/plot_improvement.py

입력 (모두 Git 에 있는 기록. 사진·모델·GPU 없이 다시 만들 수 있다)
    runs/<실행>/results.csv                 epoch 별 Validation 지표
    reports/02_baseline/baseline_training_condition.md, reports/04_improvement/exp00N_training_condition.md    학습 시간 · GPU 메모리
출력
    reports/04_improvement/improvement_summary.csv                       비교 표 (reports/04_improvement/baseline_vs_improved.md 의 숫자 근거)
    reports/figures/comparison/improvement_summary.svg    2×2 그림 (표준 라이브러리만 사용 — matplotlib 불필요)

숫자는 학습 중 Validation 지표다. best epoch 는 Validation 으로 고른 값이라 약간 낙관적이므로,
마지막 10 epoch 평균(흔들림 확인용)을 같이 낸다. Frozen Test 는 쓰지 않는다.
"""
import argparse
import csv
import html
import re
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS = PROJECT_ROOT / "runs"
REPORTS = PROJECT_ROOT / "reports"
OUT_CSV = REPORTS / "04_improvement" / "improvement_summary.csv"
OUT_SVG = REPORTS / "figures" / "comparison" / "improvement_summary.svg"

# (실행 이름, 짧은 이름, 학습 조건 문서, 색, 이 단계에서 바뀐 것)
STEPS = [
    ("baseline_v4", "Baseline", "02_baseline/baseline_training_condition.md", "#7f7f7f", "imgsz 640 (기준)"),
    ("exp001_v4_imgsz1280", "exp001", "04_improvement/exp001_training_condition.md", "#0072B2", "imgsz 640 → 1280"),
    ("exp002_v4_imgsz1920", "exp002", "04_improvement/exp002_training_condition.md", "#E69F00", "imgsz 1280 → 1920 (batch 16 → 6)"),
    ("exp003_v4_imgsz1920_epoch100", "exp003", "04_improvement/exp003_training_condition.md", "#009E73", "epochs 50 → 100"),
]
MAP = "metrics/mAP50-95(B)"
FONT = "Noto Sans CJK KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


# ── 데이터 ────────────────────────────────────────────────────
def load_rows(run):
    path = RUNS / run / "results.csv"
    with path.open(encoding="utf-8") as f:
        return [{k.strip(): float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def f1(p, r):
    return 2 * p * r / (p + r) if p + r else 0.0


def parse_condition(doc):
    """학습 조건 문서에서 (걸린 분, GPU 최대 메모리 GB). 없으면 (None, None)"""
    path = REPORTS / doc
    if not path.is_file():
        return None, None
    text = path.read_text(encoding="utf-8")
    t = re.search(r"걸린 시간 \| (?:(\d+)시간 )?(\d+)분 (\d+)초", text)
    g = re.search(r"GPU 최대 사용 메모리 \| ([\d.]+) GB", text)
    minutes = (int(t.group(1) or 0) * 60 + int(t.group(2)) + int(t.group(3)) / 60) if t else None
    return minutes, (float(g.group(1)) if g else None)


def summarize(run, doc):
    rows = load_rows(run)
    best = max(rows, key=lambda r: r[MAP])
    last10 = [r[MAP] for r in rows[-10:]]
    val_min = min(rows, key=lambda r: r["val/cls_loss"])
    p, r = best["metrics/precision(B)"], best["metrics/recall(B)"]
    minutes, gpu = parse_condition(doc)
    return {
        "rows": rows,
        "epochs_done": len(rows),
        "best_epoch": int(best["epoch"]),
        "precision": p, "recall": r, "f1": f1(p, r),
        "map50": best["metrics/mAP50(B)"], "map50_95": best[MAP],
        "last10_mean": statistics.mean(last10), "last10_std": statistics.pstdev(last10),
        "val_cls_min_epoch": int(val_min["epoch"]),
        "val_train_cls_ratio": rows[-1]["val/cls_loss"] / rows[-1]["train/cls_loss"],
        "minutes": minutes, "gpu_gb": gpu,
    }


def build():
    out = []
    for run, short, doc, color, change in STEPS:
        s = summarize(run, doc)
        s.update(run=run, short=short, color=color, change=change)
        out.append(s)
    base = out[0]
    for i, s in enumerate(out):
        prev = out[i - 1] if i else None
        s["d_base"] = s["map50_95"] - base["map50_95"]
        s["d_prev"] = s["map50_95"] - prev["map50_95"] if prev else None
        s["d_prev_last10"] = s["last10_mean"] - prev["last10_mean"] if prev else None
        s["d_prev_minutes"] = (s["minutes"] - prev["minutes"]) if prev and s["minutes"] and prev["minutes"] else None
    return out


def write_csv(data):
    cols = ["run", "change", "epochs_done", "best_epoch", "precision", "recall", "f1", "map50", "map50_95",
            "last10_mean_map50_95", "last10_std_map50_95", "d_map50_95_vs_baseline", "d_map50_95_vs_prev",
            "d_last10_vs_prev", "train_minutes", "extra_minutes_vs_prev", "gpu_max_gb",
            "val_cls_min_epoch", "val_over_train_cls_loss"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fmt = lambda v, n=4: "" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else v)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for s in data:
            w.writerow([s["run"], s["change"], s["epochs_done"], s["best_epoch"], fmt(s["precision"]), fmt(s["recall"]),
                        fmt(s["f1"]), fmt(s["map50"]), fmt(s["map50_95"]), fmt(s["last10_mean"]), fmt(s["last10_std"]),
                        fmt(s["d_base"]), fmt(s["d_prev"]), fmt(s["d_prev_last10"]), fmt(s["minutes"], 1),
                        fmt(s["d_prev_minutes"], 1), fmt(s["gpu_gb"], 1), s["val_cls_min_epoch"],
                        fmt(s["val_train_cls_ratio"], 2)])


# ── SVG (표준 라이브러리만) ───────────────────────────────────
def esc(s):
    return html.escape(str(s), quote=True)


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke="none", rx=0, opacity=1.0):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{max(h, 0):.1f}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" opacity="{opacity}"/>')

    def line(self, x1, y1, x2, y2, stroke="#ccc", sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=12, anchor="start", weight="normal", fill="#222"):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
                 f'fill="{fill}">{esc(s)}</text>')

    def poly(self, pts, stroke, sw=2):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')

    def dot(self, x, y, color, r=4):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#fff" stroke-width="1.5"/>')

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(self.parts)
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
            f'font-family="{FONT}">\n<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>\n{body}\n</svg>\n',
            encoding="utf-8")


class Panel:
    """제목이 있는 사각 영역과 그 안의 그래프 영역(px, py, pw, ph)"""

    def __init__(self, svg, x, y, w, h, title, subtitle=None):
        self.svg = svg
        svg.rect(x, y, w, h, fill="#fff", stroke="#d0d4da", rx=8)
        svg.text(x + 16, y + 26, title, size=15, weight="bold")
        if subtitle:
            svg.text(x + 16, y + 45, subtitle, size=11, fill="#555")
        self.px, self.py = x + 54, y + (62 if subtitle else 46)
        self.pw, self.ph = w - 54 - 18, h - (62 if subtitle else 46) - 40
        self.ymin = self.ymax = None

    def yaxis(self, ymin, ymax, ticks, fmt="{:.1f}"):
        self.ymin, self.ymax = ymin, ymax
        for t in ticks:
            y = self.y(t)
            self.svg.line(self.px, y, self.px + self.pw, y, stroke="#e5e7eb" if t != ymin else "#9ca3af")
            self.svg.text(self.px - 6, y + 4, fmt.format(t), size=11, anchor="end", fill="#555")

    def y(self, v):
        return self.py + self.ph - (v - self.ymin) / (self.ymax - self.ymin) * self.ph

    def groups(self, labels, series, value_fmt="{:.3f}", label_size=10):
        """series: [(이름, 값 리스트, 색, 투명도)] — 그룹마다 막대 여러 개"""
        n, k = len(labels), len(series)
        gw = self.pw / n
        bw = gw * 0.78 / k
        for i, lab in enumerate(labels):
            gx = self.px + i * gw + gw * 0.11
            for j, (_, vals, color, op) in enumerate(series):
                v = vals[i]
                if v is None:
                    continue
                x, y = gx + j * bw, self.y(v)
                self.svg.rect(x, y, bw - 2, self.y(self.ymin) - y, fill=color, opacity=op)
                self.svg.text(x + (bw - 2) / 2, y - 4, value_fmt.format(v), size=label_size, anchor="middle")
            self.svg.text(self.px + i * gw + gw / 2, self.py + self.ph + 18, lab, size=12, anchor="middle")


def draw(data):
    W, H = 1200, 850
    svg = Svg(W, H)
    svg.text(30, 34, "개선 분석 — Baseline vs exp001~003", size=20, weight="bold")
    svg.text(30, 54, "같은 Dataset(kimchi_v4)·같은 Validation 132장 · YOLO11n · seed 42 · 학습 중 Validation 지표 (Frozen Test 아님)",
             size=12, fill="#555")
    names = [s["short"] for s in data]

    # A. mAP50-95
    a = Panel(svg, 30, 70, 560, 360, "A. Validation mAP50-95",
              "진한 막대 = best epoch · 옅은 막대 = 마지막 10 epoch 평균 (흔들림을 뺀 값)")
    a.yaxis(0, 0.9, [0, 0.2, 0.4, 0.6, 0.8], "{:.1f}")
    a.groups(names, [("best", [s["map50_95"] for s in data], "#0072B2", 1.0),
                     ("last10", [s["last10_mean"] for s in data], "#0072B2", 0.45)], label_size=10)

    # B. P / R / F1
    b = Panel(svg, 610, 70, 560, 360, "B. Precision · Recall · F1 (best epoch)",
              "exp003 은 exp002 보다 Precision·F1 이 낮다")
    b.yaxis(0, 1.0, [0, 0.25, 0.5, 0.75, 1.0], "{:.2f}")
    b.groups(names, [("Precision", [s["precision"] for s in data], "#56B4E9", 1.0),
                     ("Recall", [s["recall"] for s in data], "#CC79A7", 1.0),
                     ("F1", [s["f1"] for s in data], "#444444", 1.0)], value_fmt="{:.2f}", label_size=9)
    lx = b.px + b.pw - 215      # 제목 줄 오른쪽 끝에 범례
    for i, (nm, col) in enumerate((("Precision", "#56B4E9"), ("Recall", "#CC79A7"), ("F1", "#444444"))):
        x = lx + (0, 78, 142)[i]
        svg.rect(x, 87, 10, 10, fill=col)
        svg.text(x + 14, 96, nm, size=11)

    # C. epoch 별 Val mAP50-95 곡선
    c = Panel(svg, 30, 450, 560, 360, "C. epoch 별 Validation mAP50-95", "점 = best epoch")
    c.yaxis(0, 0.9, [0, 0.2, 0.4, 0.6, 0.8], "{:.1f}")      # 초반 epoch(0 근처)도 영역 안에 들어오게 0 부터
    max_ep = max(s["epochs_done"] for s in data)
    xs = lambda e: c.px + (e - 1) / (max_ep - 1) * c.pw
    for t in (1, 25, 50, 75, 100):
        if t <= max_ep:
            svg.text(xs(t), c.py + c.ph + 18, str(t), size=11, anchor="middle", fill="#555")
    svg.text(c.px + c.pw / 2, c.py + c.ph + 34, "epoch", size=11, anchor="middle", fill="#555")
    for s in data:
        svg.poly([(xs(r["epoch"]), c.y(r[MAP])) for r in s["rows"]], s["color"])
        svg.dot(xs(s["best_epoch"]), c.y(s["map50_95"]), s["color"])
    for i, s in enumerate(data):
        ly = c.py + c.ph - 12 - (len(data) - 1 - i) * 17
        svg.line(c.px + c.pw - 150, ly - 4, c.px + c.pw - 128, ly - 4, stroke=s["color"], sw=3)
        svg.text(c.px + c.pw - 122, ly, s["short"], size=11)

    # D. 학습 비용과 상승폭
    d = Panel(svg, 610, 450, 560, 360, "D. 학습 시간 (분)", "위 = best mAP50-95 상승(전 단계 대비) · 아래 = GPU 최대 메모리")
    ymax = 50
    d.yaxis(0, ymax, [0, 10, 20, 30, 40], "{:.0f}")
    gw = d.pw / len(data)
    for i, s in enumerate(data):
        if s["minutes"] is None:
            continue
        bw = gw * 0.5
        x = d.px + i * gw + (gw - bw) / 2
        y = d.y(s["minutes"])
        svg.rect(x, y, bw, d.y(0) - y, fill=s["color"])
        svg.text(x + bw / 2, y - 22, f'{s["minutes"]:.1f}분', size=12, anchor="middle", weight="bold")
        gain = "기준" if s["d_prev"] is None else f'{s["d_prev"]:+.3f}'
        svg.text(x + bw / 2, y - 7, f"mAP {gain}", size=11, anchor="middle", fill="#333")
        svg.text(d.px + i * gw + gw / 2, d.py + d.ph + 18, s["short"], size=12, anchor="middle")
        if s["gpu_gb"] is not None:
            svg.text(d.px + i * gw + gw / 2, d.py + d.ph + 34, f'GPU {s["gpu_gb"]:.1f}GB', size=11, anchor="middle", fill="#555")

    svg.text(30, 835, "만든 곳: scripts/plot_improvement.py · 숫자: reports/04_improvement/improvement_summary.csv", size=11, fill="#777")
    svg.save(OUT_SVG)


def main():
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    missing = [r for r, *_ in STEPS if not (RUNS / r / "results.csv").is_file()]
    if missing:
        sys.exit(f"results.csv 가 없는 실행: {', '.join(missing)}")
    data = build()
    write_csv(data)
    draw(data)
    print(f"{'실행':<30}{'best':>7}{'ep':>4}{'last10':>8}{'±':>7}{'P':>7}{'R':>7}{'F1':>7}{'분':>6}")
    for s in data:
        print(f"{s['run']:<30}{s['map50_95']:>7.4f}{s['best_epoch']:>4}{s['last10_mean']:>8.4f}{s['last10_std']:>7.4f}"
              f"{s['precision']:>7.3f}{s['recall']:>7.3f}{s['f1']:>7.3f}{(s['minutes'] or 0):>6.1f}")
    print(f"\n 저장: {OUT_CSV.relative_to(PROJECT_ROOT)}, {OUT_SVG.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
