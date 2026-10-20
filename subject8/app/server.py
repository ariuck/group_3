"""Final Model 시연 프로그램 — FastAPI 서버 + 브라우저 화면 (발표 15번 슬라이드 '라이브 시연'에서 넘어온다).

    cd subject8
    .venv/bin/python app/server.py                 # http://127.0.0.1:8000  (모델 Load · 예열 후 준비)
    .venv/bin/python app/server.py --port 8010     # 다른 포트
    .venv/bin/python app/server.py --cpu           # GPU 없이 (느림)

보여 주는 것
    - Final Model(models/final/final_best.pt)로 Validation 사진을 예측하고 정답(GT)과 비교 (TP · Class 틀림 · 오검출 · 놓침)
    - confidence 기준을 움직이면 판정이 바로 바뀐다 (예측은 conf 0.05 로 한 번만 하고 기준은 화면에서 거른다)
    - Validation 104장 일괄 채점 (박스 개수 기준 — mAP 가 아님)
    - 사진 끌어다 놓기로 새 사진 예측 (정답이 없으면 예측만), YOLO TXT 후보 내려받기 (Auto Label 후보 — 사람이 검수한 뒤에만 정답)

지키는 것
    - Frozen Test · Bridge Holdout 사진은 목록에 없고, 같은 이름의 사진을 올려도 거절한다 (교과 8 규칙)
    - 127.0.0.1 에만 열린다. 올린 사진은 메모리에만 두고 디스크에 저장하지 않는다 (회사 사진 · NDA)
    - 저장소 맨 위 presentation/ 이 있으면 /presentation/ 으로 같이 열어, 발표 ↔ 시연을 한 주소에서 오간다
"""
import argparse
import csv
import os
import re
import sys
import threading
import time
from collections import Counter, OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))      # src · app 을 패키지로 불러온다
os.chdir(PROJECT_ROOT)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from src import registry  # noqa: E402
from src.constants import DEFAULT_DATASET_VERSION  # noqa: E402
from src.inference import load_gt, match  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import sha256_short  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
PRESENTATION = REPO_ROOT / "presentation"
PREDICT_CONF = 0.05            # 예측은 이 값으로 한 번만 — 화면의 기준(기본 0.25)은 그 위에서 거른다
DEFAULT_CONF = 0.25            # 08 · 09 와 같은 기준
MAX_UPLOAD = 40 * 1024 * 1024
MAX_UPLOADS_KEPT = 30
KO_NAMES = {0: "나뭇잎·종이", 1: "플라스틱·돌·금속", 2: "나뭇가지", 3: "벌레",
            4: "고무장갑", 5: "병해·갈변", 6: "파·고추"}
SCENE = {"김치+대상 객체": "김치+이물", "대상 객체 단독": "이물 단독", "판단 어려움": "판단 어려움", "정상 김치": "정상 김치"}


class Demo:
    """모델 · 사진 목록 · 예측 결과를 한곳에 둔다 (서버 프로세스 하나에 하나)"""

    def __init__(self, device: Optional[str]):
        self.device = device
        self.lock = threading.Lock()                   # GPU 하나 — 예측은 한 번에 하나씩
        self.model = None
        self.ready = False
        self.error = ""
        self.weight, self.run = registry.resolve("final")
        self.args = registry.run_args(self.run)
        self.imgsz = int(self.args["imgsz"])
        builder = SplitBuilder(PROJECT_ROOT, DEFAULT_DATASET_VERSION)
        self.val_img = builder.yolo_dir / "images" / "val"
        self.val_lbl = builder.yolo_dir / "labels" / "val"
        self.meta, self.blocked = {}, {}
        with (builder.manifest_dir / "split_manifest.csv").open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                name, role = r["이미지 파일명"], r["split"]
                self.meta[name] = {"group": r["capture_group"], "scene": SCENE.get(r["이미지 유형"], r["이미지 유형"])}
                if role in ("test", "bridge_holdout"):
                    self.blocked[name] = role
        self.items: Dict[str, Dict] = {}               # id → {path|data, gt, preds, ms, w, h, title, source}
        self.uploads: "OrderedDict[str, bytes]" = OrderedDict()
        self.thumbs: "OrderedDict[str, bytes]" = OrderedDict()
        self.upload_seq = 0
        self.names = dict(KO_NAMES)
        self.metrics = self._metrics()

    # ── 준비 ─────────────────────────────────────────────
    def _metrics(self) -> Dict:
        out = {"val": None, "test": None}
        rs = PROJECT_ROOT / "reports" / "runs_summary.csv"
        if rs.is_file():
            for r in csv.DictReader(rs.open(encoding="utf-8-sig")):
                if r["run"] == self.run:
                    out["val"] = {k: float(r[k]) for k in ("precision", "recall", "map50", "map50_95")}
        fm = PROJECT_ROOT / "reports" / "05_final" / "final_metrics.csv"
        if fm.is_file():
            for r in csv.DictReader(fm.open(encoding="utf-8-sig")):
                if r.get("model_version") == self.run:
                    out["test"] = {k: float(r[k]) for k in ("precision", "recall", "map50", "map50_95")}
                    out["test"]["images"] = int(r["images"])
        return out

    def load(self):
        try:
            import torch
            from ultralytics import YOLO
            if self.device is None:
                self.device = "0" if torch.cuda.is_available() else "cpu"
            self.gpu = torch.cuda.get_device_name(0) if self.device != "cpu" and torch.cuda.is_available() else "CPU"
            self.model = YOLO(str(self.weight))
            self.model.predict(np.zeros((self.imgsz, self.imgsz, 3), np.uint8), imgsz=self.imgsz,
                               device=self.device, verbose=False)            # 예열 (첫 예측이 느린 것을 미리)
            self.ready = True
            print(f" 준비 완료: {self.run} · imgsz {self.imgsz} · {self.gpu}")
        except Exception as e:  # 화면에 이유를 보여 준다
            self.error = f"{type(e).__name__}: {e}"
            print(" 모델 준비 실패:", self.error)

    # ── 사진 ─────────────────────────────────────────────
    def val_list(self) -> List[Dict]:
        out = []
        for p in sorted(self.val_img.glob("*.jpg")) if self.val_img.is_dir() else []:
            gt = load_gt(self.val_lbl / f"{p.stem}.txt")
            m = self.meta.get(p.name, {})
            it = self.items.get(p.name)
            out.append({"id": p.name, "group": m.get("group", ""), "scene": m.get("scene", ""),
                        "classes": dict(Counter(int(b[0]) for b in gt)), "gt": len(gt),
                        "done": bool(it and it.get("preds") is not None)})
        return out

    def thumb(self, iid: str) -> bytes:
        if iid in self.thumbs:
            self.thumbs.move_to_end(iid)
            return self.thumbs[iid]
        if iid in self.uploads:
            img = cv2.imdecode(np.frombuffer(self.uploads[iid], np.uint8), cv2.IMREAD_REDUCED_COLOR_8)
        else:
            img = cv2.imread(str(self._val_path(iid)), cv2.IMREAD_REDUCED_COLOR_8)   # 1/8 크기로 바로 읽음 (빠름)
        if img is None:
            raise HTTPException(404, "사진을 읽을 수 없습니다")
        w = 360
        img = cv2.resize(img, (w, int(img.shape[0] * w / img.shape[1])), interpolation=cv2.INTER_AREA)
        data = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 78])[1].tobytes()
        self.thumbs[iid] = data
        while len(self.thumbs) > 400:
            self.thumbs.popitem(last=False)
        return data

    def _val_path(self, name: str) -> Path:
        if name in self.blocked:
            raise HTTPException(403, f"{name} 은 {self.blocked[name]} 사진이라 교과 8 에서 예측하지 않습니다")
        p = self.val_img / name
        if not re.fullmatch(r"[\w.\-]+\.jpe?g", name) or not p.is_file():
            raise HTTPException(404, f"Validation 사진이 아닙니다: {name}")
        return p

    def add_upload(self, filename: str, data: bytes) -> Dict:
        base = Path(filename or "upload.jpg").name
        if base in self.blocked:
            raise HTTPException(403, f"'{base}' 은 {'Frozen Test' if self.blocked[base] == 'test' else 'Bridge Holdout'} 사진입니다. "
                                     "교과 8 시연에서는 예측하지 않습니다.")
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, "사진이 너무 큽니다 (40MB 이하)")
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(415, "사진(JPG · PNG)이 아닙니다")
        if base in self.meta and (self.val_img / base).is_file():   # Val 사진을 올리면 Val 로 취급 (정답 비교 가능)
            return {"id": base, "title": base, "source": "val"}
        self.upload_seq += 1
        iid = f"upload-{self.upload_seq}"
        self.uploads[iid] = data
        while len(self.uploads) > MAX_UPLOADS_KEPT:
            old, _ = self.uploads.popitem(last=False)
            self.items.pop(old, None)
            self.thumbs.pop(old, None)
        self.items[iid] = {"title": base, "source": "upload", "gt": None, "preds": None}
        return {"id": iid, "title": base, "source": "upload"}

    def image_bytes(self, iid: str):
        if iid in self.uploads:
            return self.uploads[iid]
        return self._val_path(iid)

    # ── 예측 · 판정 ───────────────────────────────────────
    def predict(self, iid: str) -> Dict:
        if not self.ready:
            raise HTTPException(503, self.error or "모델을 준비하는 중입니다")
        it = self.items.get(iid)
        if it and it.get("preds") is not None:
            return it
        if iid in self.uploads:
            img = cv2.imdecode(np.frombuffer(self.uploads[iid], np.uint8), cv2.IMREAD_COLOR)
            gt, title, source = None, self.items[iid]["title"], "upload"
        else:
            path = self._val_path(iid)
            img = cv2.imread(str(path))
            gt, title, source = load_gt(self.val_lbl / f"{path.stem}.txt"), iid, "val"
        h, w = img.shape[:2]
        with self.lock:
            t0 = time.perf_counter()
            r = self.model.predict(img, imgsz=self.imgsz, conf=PREDICT_CONF, device=self.device,
                                   max_det=300, verbose=False)[0]
            total = (time.perf_counter() - t0) * 1000
        preds = [(int(c), float(p), *map(float, b)) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxyn)]
        it = {"title": title, "source": source, "gt": gt, "preds": preds, "w": w, "h": h,
              "ms": {"total": round(total, 1), **{k: round(v, 1) for k, v in r.speed.items()}}}
        if iid in self.meta:
            it.update(self.meta[iid])
        self.items[iid] = it
        return it

    def judge(self, iid: str, conf: float) -> Dict:
        it = self.predict(iid)
        keep = [i for i, p in enumerate(it["preds"]) if p[1] >= conf]
        preds = [it["preds"][i] for i in keep]
        gt = it["gt"]
        out = {"id": iid, "title": it["title"], "source": it["source"], "w": it["w"], "h": it["h"], "ms": it["ms"],
               "conf": conf, "group": it.get("group", ""), "scene": it.get("scene", ""),
               "preds": [{"cls": p[0], "conf": round(p[1], 4), "box": [round(v, 5) for v in p[2:]]} for p in preds],
               "gt": None, "counts": None, "per_class": None}
        if gt is None:
            for p in out["preds"]:
                p["kind"] = "PRED"
            return out
        res = match(gt, preds)
        fn = set(res["fn"])
        for i, p in enumerate(out["preds"]):
            kind, j = res["pred_kind"][i]
            p["kind"], p["gt"] = kind, j
        out["gt"] = [{"cls": g[0], "box": [round(v, 5) for v in g[1:]], "missed": j in fn} for j, g in enumerate(gt)]
        out["counts"] = {"tp": res["tp"], "class_error": res["class_error"], "fp": res["fp"], "fn": res["fn_count"],
                         "gt": len(gt), "pred": len(preds)}
        out["per_class"] = self._per_class(gt, out["preds"], fn)
        return out

    @staticmethod
    def _per_class(gt, preds, fn) -> Dict[int, Dict]:
        pc = {}
        for j, g in enumerate(gt):
            d = pc.setdefault(g[0], Counter())
            d["gt"] += 1
            d["fn"] += j in fn
        for p in preds:
            d = pc.setdefault(p["cls"], Counter())
            d["pred"] += 1
            d[{"TP": "tp", "CLASS_ERROR": "class_error", "FP": "fp"}[p["kind"]]] += 1
        return {c: dict(v) for c, v in sorted(pc.items())}

    def summary(self, conf: float) -> Dict:
        """예측이 끝난 Validation 사진 전체를 같은 기준으로 합친다"""
        total, per = Counter(), {}
        n = 0
        for iid in sorted(self.items):
            it = self.items[iid]
            if it.get("source") != "val" or it.get("preds") is None:
                continue
            j = self.judge(iid, conf)
            n += 1
            for k, v in j["counts"].items():
                total[k] += v
            for c, d in j["per_class"].items():
                acc = per.setdefault(c, Counter())
                acc.update(d)
        ms = [self.items[i]["ms"]["inference"] for i in self.items if self.items[i].get("source") == "val"
              and self.items[i].get("preds") is not None and "inference" in self.items[i]["ms"]]
        return {"images": n, "of": len(self.val_list()), "conf": conf, "counts": dict(total),
                "per_class": {c: dict(v) for c, v in sorted(per.items())},
                "inference_ms": round(float(np.median(ms)), 1) if ms else None}

    def val_done(self) -> List[str]:
        return sorted(i for i, it in self.items.items() if it.get("source") == "val" and it.get("preds") is not None)

    def sweep(self, step: float = 0.05) -> Dict:
        """확신도 기준별 박스 개수 결과 (예측이 끝난 Validation 사진). 기준마다 재예측 없이 다시 판정만 한다"""
        ids = self.val_done()
        rows = []
        for k in range(1, int(round(0.95 / step)) + 1):
            conf = round(k * step, 2)
            if conf < PREDICT_CONF:
                continue
            t = Counter()
            for iid in ids:
                t.update(self.judge(iid, conf)["counts"])
            p = t["tp"] / t["pred"] if t["pred"] else 0.0
            r = t["tp"] / t["gt"] if t["gt"] else 0.0
            f1 = 2 * p * r / (p + r) if p + r else 0.0
            rows.append({"conf": conf, "tp": t["tp"], "class_error": t["class_error"], "fp": t["fp"], "fn": t["fn"],
                         "gt": t["gt"], "pred": t["pred"], "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)})
        best = max(rows, key=lambda x: x["f1"]) if rows else None
        return {"images": len(ids), "of": len(self.val_list()), "rows": rows, "best": best}

    def read_image(self, iid: str):
        if iid in self.uploads:
            return cv2.imdecode(np.frombuffer(self.uploads[iid], np.uint8), cv2.IMREAD_COLOR)
        return cv2.imread(str(self._val_path(iid)))


# ── FastAPI ───────────────────────────────────────────────
def create_app(device: Optional[str] = None) -> FastAPI:
    demo = Demo(device)

    @asynccontextmanager
    async def lifespan(_):
        threading.Thread(target=demo.load, daemon=True).start()   # 화면은 바로 열리고, 모델은 뒤에서 준비
        yield

    app = FastAPI(title="조각김치 이물검출 시연", docs_url=None, redoc_url=None, lifespan=lifespan)

    @app.get("/api/info")
    def info():
        return {"run": demo.run, "weight": demo.weight.relative_to(PROJECT_ROOT).as_posix(),
                "sha": sha256_short(demo.weight), "imgsz": demo.imgsz, "dataset": DEFAULT_DATASET_VERSION,
                "ready": demo.ready, "error": demo.error, "device": getattr(demo, "gpu", None),
                "names": demo.names, "metrics": demo.metrics, "default_conf": DEFAULT_CONF, "predict_conf": PREDICT_CONF,
                "presentation": (PRESENTATION / "index.html").is_file()}

    @app.get("/api/images")
    def images():
        return demo.val_list()

    @app.get("/api/images/{iid}/thumb")
    def thumb(iid: str):
        return Response(demo.thumb(iid), media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})

    @app.get("/api/images/{iid}/full")
    def full(iid: str):
        src = demo.image_bytes(iid)
        if isinstance(src, bytes):
            kind = "image/png" if src[:8] == b"\x89PNG\r\n\x1a\n" else "image/webp" if src[8:12] == b"WEBP" else "image/jpeg"
            return Response(src, media_type=kind)
        return FileResponse(src, media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})

    @app.post("/api/images/{iid}/predict")
    def predict(iid: str, conf: float = DEFAULT_CONF):
        return demo.judge(iid, max(PREDICT_CONF, min(conf, 0.99)))

    @app.get("/api/images/{iid}/judge")
    def judge(iid: str, conf: float = DEFAULT_CONF):
        if iid not in demo.items or demo.items[iid].get("preds") is None:
            raise HTTPException(409, "아직 예측하지 않은 사진입니다")
        return demo.judge(iid, max(PREDICT_CONF, min(conf, 0.99)))

    @app.post("/api/upload")
    async def upload(request: Request):
        data = await request.body()                     # multipart 없이 원본 바이트 + X-Filename 헤더
        name = request.headers.get("x-filename", "upload.jpg")
        try:
            from urllib.parse import unquote
            name = unquote(name)
        except Exception:
            pass
        return demo.add_upload(name, data)

    @app.get("/api/summary")
    def summary(conf: float = DEFAULT_CONF):
        return demo.summary(max(PREDICT_CONF, min(conf, 0.99)))

    @app.get("/api/sweep")
    def sweep():
        return demo.sweep()

    @app.post("/api/report")
    async def report(request: Request):
        """시연 보고서 (HTML 한 파일) — 브라우저가 미리보기 · 저장 · 인쇄(PDF). 서버 디스크에는 저장하지 않는다"""
        from app.report import build_report
        body = await request.json()
        conf = max(PREDICT_CONF, min(float(body.get("conf", DEFAULT_CONF)), 0.99))
        viewed = [str(v) for v in body.get("viewed", [])][:300]
        html = build_report(demo, conf=conf, viewed=viewed, include_crops=bool(body.get("crops", False)),
                            include_all=bool(body.get("all", True)), presenter=str(body.get("presenter", ""))[:60])
        return Response(html, media_type="text/html; charset=utf-8")

    @app.exception_handler(HTTPException)
    async def _err(_, e: HTTPException):
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)

    if PRESENTATION.is_dir():
        app.mount("/presentation", StaticFiles(directory=str(PRESENTATION), html=True), name="presentation")
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
    return app


def main():
    ap = argparse.ArgumentParser(description="Final Model 시연 프로그램 (FastAPI)")
    ap.add_argument("--host", default="127.0.0.1", help="기본 127.0.0.1 (이 PC 에서만). 회사 사진이 보이므로 바꾸지 않는 것을 권장")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--cpu", action="store_true", help="GPU 를 쓰지 않음 (느림)")
    args = ap.parse_args()
    import uvicorn
    print("=" * 65)
    print(f" 시연 프로그램: http://{args.host}:{args.port}/   (발표자료: http://{args.host}:{args.port}/presentation/)")
    print("=" * 65)
    uvicorn.run(create_app("cpu" if args.cpu else None), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
