"""시연 보고서 — 시연이 끝난 뒤 결과를 HTML 한 파일로 만든다 (브라우저에서 저장 · 인쇄해 PDF).

build_report(demo, conf, viewed, include_crops, include_all) 이 돌려주는 HTML 에 들어가는 것
    1. 요약       모델 · 공식 성능(Frozen Test) · 이번 시연 기준의 Validation 일괄 채점 결과
    2. 기준별     확신도 기준 0.05 ~ 0.95 에서 찾은 비율 · 맞은 비율 · F1 (그래프 + 표)
    3. Class 별   정답 · 맞힘 · 놓침 · 오검출 · 찾은 비율
    4. 본 사진    시연 중에 연 사진과 그 결과
    5. 틀린 박스  오검출 · 종류 틀림 · 놓침 목록 (선택: 사진 조각 — 회사 사진이라 외부 공유 금지)
    6. 읽는 법 · 한계

숫자는 server.py 의 Demo.judge (= src/inference.match, IoU 0.5) 그대로다. 서버 디스크에는 아무것도 저장하지 않는다.
"""
import base64
import html
import time
from typing import Dict, List

import cv2

COLORS = ["#16a34a", "#dc2626", "#2563eb", "#9333ea", "#6b7280", "#ea580c", "#0d9488"]
KIND_KO = {"TP": "맞힘", "CLASS_ERROR": "종류 틀림", "FP": "오검출", "FN": "놓침"}
MAX_ERROR_ROWS = 300
MAX_CROPS = 80

e = html.escape


def _pct(v):
    return "–" if v is None else f"{v * 100:.1f}%"


def _ratio(a, b):
    return a / b if b else None


def _crop_b64(img, box, size=150) -> str:
    """박스 주변(박스 크기만큼 여유)을 잘라 JPEG base64. 박스는 굵은 테두리로 표시"""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box[0] * w, box[1] * h, box[2] * w, box[3] * h
    bw, bh = max(x2 - x1, 8), max(y2 - y1, 8)
    m = max(bw, bh, 60)
    cx1, cy1 = int(max(0, x1 - m)), int(max(0, y1 - m))
    cx2, cy2 = int(min(w, x2 + m)), int(min(h, y2 + m))
    crop = img[cy1:cy2, cx1:cx2].copy()
    if crop.size == 0:
        return ""
    cv2.rectangle(crop, (int(x1 - cx1), int(y1 - cy1)), (int(x2 - cx1), int(y2 - cy1)), (54, 24, 229), max(2, int(m / 40)))
    s = size / max(crop.shape[:2])
    crop = cv2.resize(crop, (max(1, int(crop.shape[1] * s)), max(1, int(crop.shape[0] * s))), interpolation=cv2.INTER_AREA)
    return base64.b64encode(cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 82])[1]).decode()


def _sweep_svg(rows: List[Dict], cur: float, best: Dict, w=720, h=260) -> str:
    """기준(가로) × 비율(세로) 선 그래프 — 찾은 비율(Recall) · 맞은 비율(Precision) · F1"""
    if not rows:
        return ""
    L, R, T, B = 48, 16, 16, 34
    X = lambda c: L + (c - 0.05) / 0.90 * (w - L - R)          # noqa: E731
    Y = lambda v: T + (1 - v) * (h - T - B)                      # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="확신도 기준별 결과">']
    for v in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{L}" x2="{w - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>'
                   f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" class="ax" text-anchor="end">{int(v * 100)}%</text>')
    for c in (0.05, 0.25, 0.5, 0.75, 0.95):
        out.append(f'<text x="{X(c):.1f}" y="{h - 12}" class="ax" text-anchor="middle">{c:.2f}</text>')
    out.append(f'<text x="{(L + w - R) / 2:.0f}" y="{h - 1}" class="ax" text-anchor="middle">확신도 기준 (conf)</text>')
    out.append(f'<line x1="{X(cur):.1f}" x2="{X(cur):.1f}" y1="{T}" y2="{h - B}" class="cur"/>'
               f'<text x="{X(cur) + 4:.1f}" y="{T + 12}" class="curt">이번 기준 {cur:.2f}</text>')
    for key, col, name in (("recall", "#16a34a", "찾은 비율"), ("precision", "#2563eb", "맞은 비율"), ("f1", "#4f46e5", "F1")):
        pts = " ".join(f"{X(r['conf']):.1f},{Y(r[key]):.1f}" for r in rows)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{3 if key == "f1" else 2}"/>')
    if best:
        out.append(f'<circle cx="{X(best["conf"]):.1f}" cy="{Y(best["f1"]):.1f}" r="5" fill="#4f46e5"/>')
    out.append("</svg>")
    return "".join(out)


def build_report(demo, conf: float, viewed: List[str], include_crops: bool = False,
                 include_all: bool = True, presenter: str = "") -> str:
    names = demo.names
    m = demo.metrics
    now = time.strftime("%Y-%m-%d %H:%M")
    val_ids = demo.val_done()
    n_val = len(demo.val_list())
    summ = demo.summary(conf) if val_ids else None
    sw = demo.sweep() if val_ids else {"rows": [], "best": None}
    viewed = [v for v in dict.fromkeys(viewed) if v in demo.items and demo.items[v].get("preds") is not None]
    judged_viewed = [demo.judge(v, conf) for v in viewed]

    # 틀린 박스: 전체 채점이 있으면 Validation 전체, 없으면 본 사진
    err_src = val_ids if (include_all and val_ids) else viewed
    errors = []
    for iid in err_src:
        j = demo.judge(iid, conf)
        if j["gt"] is None:
            continue
        for p in j["preds"]:
            if p["kind"] in ("FP", "CLASS_ERROR"):
                gt_name = names[j["gt"][p["gt"]]["cls"]] if p["kind"] == "CLASS_ERROR" and p.get("gt") is not None else ""
                errors.append((iid, j, p["kind"], p["cls"], p["conf"], p["box"], gt_name))
        for g in j["gt"]:
            if g["missed"]:
                errors.append((iid, j, "FN", g["cls"], None, g["box"], ""))
    order = {"FN": 0, "CLASS_ERROR": 1, "FP": 2}
    errors.sort(key=lambda x: (order[x[2]], x[3], x[0]))

    crops = {}
    if include_crops:
        by_img = {}
        for k, (iid, *_rest) in enumerate(errors[:MAX_CROPS]):
            by_img.setdefault(iid, []).append(k)
        for iid, ks in by_img.items():                   # 사진은 한 번씩만, 한 장씩 읽는다 (4K)
            img = demo.read_image(iid)
            if img is None:
                continue
            for k in ks:
                crops[k] = _crop_b64(img, errors[k][5])
            del img

    # ── 1. 요약 ──
    test, val = m.get("test") or {}, m.get("val") or {}
    cards = [
        ("Frozen Test mAP50-95", f"{test.get('map50_95', 0):.3f}" if test else "–", f"공식 최종 성능 · {test.get('images', '')}장", "hl"),
        ("Validation mAP50-95", f"{val.get('map50_95', 0):.3f}" if val else "–", "Final 선택에 쓴 점수", ""),
    ]
    if summ and summ["images"]:
        c = summ["counts"]
        cards += [("찾은 비율 (Recall)", _pct(_ratio(c["tp"], c["gt"])), f"맞힘 {c['tp']} / 정답 {c['gt']}", ""),
                  ("맞은 비율 (Precision)", _pct(_ratio(c["tp"], c["pred"])), f"맞힘 {c['tp']} / 예측 {c['pred']}", "")]
    card_html = "".join(f'<div class="card {cls}"><div class="k">{e(k)}</div><div class="v">{v}</div><div class="s">{e(s)}</div></div>'
                        for k, v, s, cls in cards)
    counts_html = ""
    if summ and summ["images"]:
        c = summ["counts"]
        counts_html = f"""<div class="counts">
          <div><b class="ok">{c['tp']}</b>맞힘</div><div><b class="warn">{c['class_error']}</b>종류 틀림</div>
          <div><b class="bad">{c['fp']}</b>오검출</div><div><b class="bad">{c['fn']}</b>놓침</div></div>
          <p class="note">Validation {summ['images']}/{summ['of']}장 · 확신도 기준 {conf:.2f} · IoU 0.5 · 박스 개수 기준
          {f"· 모델 예측 중앙값 {summ['inference_ms']} ms/장" if summ.get('inference_ms') else ""}</p>"""
        if summ["images"] < summ["of"]:
            counts_html += f'<p class="warnbox">Validation {summ["of"]}장 중 {summ["images"]}장만 예측했습니다 — 전체 숫자가 아닙니다. 시연 화면의 「⑤ 전체 채점」을 끝낸 뒤 다시 만드세요.</p>'
    else:
        counts_html = '<p class="warnbox">Validation 일괄 채점을 하지 않아 전체 결과가 없습니다. 이 보고서는 시연에서 본 사진만 담습니다.</p>'

    # ── 2. 기준별 ──
    sweep_html = ""
    if sw["rows"]:
        best = sw["best"]
        rows = "".join(
            f'<tr class="{"cur" if abs(r["conf"] - conf) < 1e-6 else ""}{" best" if best and r["conf"] == best["conf"] else ""}">'
            f'<td>{r["conf"]:.2f}</td><td>{r["tp"]}</td><td>{r["class_error"]}</td><td>{r["fp"]}</td><td>{r["fn"]}</td>'
            f'<td>{_pct(r["recall"])}</td><td>{_pct(r["precision"])}</td><td>{r["f1"]:.3f}</td></tr>'
            for r in sw["rows"] if round(r["conf"] * 100) % 10 == 5 or abs(r["conf"] - conf) < 1e-6 or (best and r["conf"] == best["conf"]))
        sweep_html = f"""<h2>2. 확신도 기준별 결과</h2>
        <p>기준을 낮추면 놓침이 줄고 오검출이 늘어납니다. 현장에서는 <b>놓침과 오검출 중 무엇이 더 위험한지</b>로 기준을 정합니다 (교과 14 과제).
        F1(두 비율의 조화평균)이 가장 높은 기준은 <b>{best['conf']:.2f}</b> (F1 {best['f1']:.3f}) — 이 값은 Validation 으로 고른 것이라 참고용입니다.</p>
        {_sweep_svg(sw["rows"], conf, best)}
        <div class="legend"><span style="--c:#16a34a">찾은 비율 (Recall)</span><span style="--c:#2563eb">맞은 비율 (Precision)</span><span style="--c:#4f46e5">F1</span></div>
        <table><tr><th>기준</th><th>맞힘</th><th>종류 틀림</th><th>오검출</th><th>놓침</th><th>찾은 비율</th><th>맞은 비율</th><th>F1</th></tr>{rows}</table>"""

    # ── 3. Class 별 ──
    class_html = ""
    if summ and summ["images"]:
        rows = []
        for cid, d in summ["per_class"].items():
            cid = int(cid)
            gt, tp = d.get("gt", 0), d.get("tp", 0)
            r = _ratio(tp, gt)
            bar = f'<div class="bar"><i style="width:{(r or 0) * 100:.0f}%;background:{COLORS[cid]}"></i></div>' if gt else ""
            rows.append(f'<tr><td><span class="sw" style="background:{COLORS[cid]}"></span>{e(names[cid])}</td><td>{gt}</td><td>{d.get("pred", 0)}</td>'
                        f'<td>{tp}</td><td class="{"badc" if d.get("fn") else ""}">{d.get("fn", 0)}</td>'
                        f'<td class="{"badc" if d.get("fp") else ""}">{d.get("fp", 0) + d.get("class_error", 0)}</td><td>{_pct(r)}</td><td class="barcell">{bar}</td></tr>')
        class_html = f"""<h2>3. Class 별 결과 <small>Validation · 기준 {conf:.2f}</small></h2>
        <table><tr><th>Class</th><th>정답</th><th>예측</th><th>맞힘</th><th>놓침</th><th>오검출·종류 틀림</th><th>찾은 비율</th><th></th></tr>{''.join(rows)}</table>"""

    # ── 4. 본 사진 ──
    viewed_html = ""
    if judged_viewed:
        rows = []
        for j in judged_viewed:
            c = j["counts"] or {}
            src = "Validation" if j["source"] == "val" else "올린 사진"
            if c:
                rows.append(f'<tr><td class="mono">{e(j["title"])}</td><td>{src}</td><td>{e(j.get("group", ""))}</td><td>{c["gt"]}</td><td>{c["pred"]}</td>'
                            f'<td class="okc">{c["tp"]}</td><td class="{"warnc" if c["class_error"] else ""}">{c["class_error"]}</td>'
                            f'<td class="{"badc" if c["fp"] else ""}">{c["fp"]}</td><td class="{"badc" if c["fn"] else ""}">{c["fn"]}</td></tr>')
            else:
                rows.append(f'<tr><td class="mono">{e(j["title"])}</td><td>{src}</td><td></td><td>–</td><td>{len(j["preds"])}</td><td colspan="4" class="muted">정답 없음 — 예측만</td></tr>')
        viewed_html = f"""<h2>4. 시연에서 본 사진 <small>{len(judged_viewed)}장 · 기준 {conf:.2f}</small></h2>
        <table><tr><th>사진</th><th>구분</th><th>묶음</th><th>정답</th><th>예측</th><th>맞힘</th><th>종류 틀림</th><th>오검출</th><th>놓침</th></tr>{''.join(rows)}</table>"""

    # ── 5. 틀린 박스 ──
    err_html = ""
    if errors:
        kinds = {k: sum(1 for x in errors if x[2] == k) for k in ("FN", "CLASS_ERROR", "FP")}
        rows = []
        for k, (iid, j, kind, c, cf, box, gt_name) in enumerate(errors[:MAX_ERROR_ROWS]):
            W, H = j["w"], j["h"]
            size = f"{round((box[2] - box[0]) * W)}×{round((box[3] - box[1]) * H)}"
            img = f'<img src="data:image/jpeg;base64,{crops[k]}" alt="">' if k in crops and crops[k] else ""
            rows.append(f'<tr><td class="kind {kind}">{KIND_KO[kind]}</td><td><span class="sw" style="background:{COLORS[c]}"></span>{e(names[c])}'
                        f'{f" <small>→ 정답 {e(gt_name)}</small>" if gt_name else ""}</td><td>{"–" if cf is None else f"{cf:.2f}"}</td>'
                        f'<td class="mono">{size}</td><td class="mono">{e(j["title"])}</td><td>{e(j.get("group", ""))}</td>'
                        + (f'<td class="crop">{img}</td>' if include_crops else "") + "</tr>")
        more = f'<p class="note">{len(errors) - MAX_ERROR_ROWS}건은 생략했습니다.</p>' if len(errors) > MAX_ERROR_ROWS else ""
        scope = f"Validation {len(err_src)}장" if err_src is val_ids else f"시연에서 본 사진 {len(err_src)}장"
        err_html = f"""<h2 class="pb">5. 틀린 박스 목록 <small>{scope} · 기준 {conf:.2f}</small></h2>
        <p>놓침 <b>{kinds['FN']}</b> · 종류 틀림 <b>{kinds['CLASS_ERROR']}</b> · 오검출 <b>{kinds['FP']}</b> — 놓침 → 종류 틀림 → 오검출 순, Class 별로 정렬.
        크기는 원본 사진 픽셀입니다.{' 사진 조각은 처음 ' + str(MAX_CROPS) + '건까지 넣었습니다.' if include_crops else ''}</p>
        <table class="errs"><tr><th>판정</th><th>Class</th><th>확신도</th><th>크기(px)</th><th>사진</th><th>묶음</th>{'<th>사진 조각</th>' if include_crops else ''}</tr>{''.join(rows)}</table>{more}"""

    warn_photo = ('<div class="warnbox strong">이 보고서에는 <b>회사 제공 사진의 조각</b>이 들어 있습니다. NDA · 기관 보안정책에 따라 '
                  '<b>외부 저장소 · 클라우드 · 메신저에 올리지 마세요.</b> Git 에도 올리지 않습니다.</div>') if include_crops and crops else ""

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>시연 보고서 · {e(demo.run)} · {now}</title>
<style>
:root{{--ink:#101828;--mut:#667085;--line:#e4e7ec;--acc:#4f46e5;--ok:#16a34a;--bad:#e11d74;--warn:#ca8a04}}
*{{box-sizing:border-box}} body{{margin:0;background:#f4f5f8;color:var(--ink);font:14px/1.55 "Pretendard","Noto Sans KR","Malgun Gothic",system-ui,sans-serif}}
.page{{max-width:980px;margin:24px auto;background:#fff;border:1px solid var(--line);border-radius:14px;padding:44px 52px;box-shadow:0 8px 30px rgba(16,24,40,.06)}}
header{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid var(--acc);padding-bottom:14px;margin-bottom:22px}}
header h1{{margin:0;font-size:26px;letter-spacing:-.3px}} header .meta{{text-align:right;color:var(--mut);font-size:12.5px}}
.kick{{color:var(--acc);font-weight:700;font-size:13px}}
h2{{font-size:18px;margin:30px 0 10px;padding-left:10px;border-left:4px solid var(--acc)}} h2 small{{color:var(--mut);font-weight:500;font-size:13px;margin-left:6px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.card{{border:1px solid var(--line);border-radius:12px;padding:12px 14px}} .card.hl{{border-color:var(--acc);background:#eef2ff}}
.card .k{{font-size:12px;color:var(--mut)}} .card .v{{font-size:26px;font-weight:800;letter-spacing:-.5px}} .card.hl .v{{color:var(--acc)}} .card .s{{font-size:11.5px;color:var(--mut)}}
.counts{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}} .counts div{{border:1px solid var(--line);border-radius:12px;padding:10px;text-align:center;color:var(--mut);font-size:12.5px}}
.counts b{{display:block;font-size:24px;color:var(--ink)}} b.ok,.okc{{color:var(--ok)!important}} b.bad,.badc{{color:var(--bad)!important;font-weight:700}} b.warn,.warnc{{color:var(--warn)!important;font-weight:700}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}} th{{text-align:left;color:var(--mut);font-weight:600;border-bottom:2px solid var(--line);padding:6px 8px;white-space:nowrap}}
td{{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:middle}} tr.cur td{{background:#eef2ff;font-weight:700}} tr.best td:first-child::after{{content:" ★F1";color:var(--acc);font-size:11px}}
.sw{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
.bar{{height:8px;background:#f2f4f7;border-radius:99px;overflow:hidden;min-width:120px}} .bar i{{display:block;height:100%;border-radius:99px}} .barcell{{width:160px}}
.mono{{font-family:ui-monospace,Consolas,monospace;font-size:11.5px}} .muted{{color:var(--mut)}} .note{{color:var(--mut);font-size:12px;margin:6px 0}}
.kind{{font-weight:700;white-space:nowrap}} .kind.FN,.kind.FP{{color:var(--bad)}} .kind.CLASS_ERROR{{color:var(--warn)}}
.crop img{{height:84px;border-radius:6px;border:1px solid var(--line);display:block}}
.warnbox{{background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:10px;padding:10px 14px;font-size:13px;margin:10px 0}} .warnbox.strong{{background:#fff1f2;border-color:#fecdd3;color:#9f1239}}
.chart{{width:100%;height:auto;margin:6px 0}} .chart .grid{{stroke:#eaecf0}} .chart .ax{{font-size:11px;fill:#667085}} .chart .cur{{stroke:#e11d74;stroke-dasharray:4 4}} .chart .curt{{font-size:11px;fill:#e11d74;font-weight:700}}
.legend{{display:flex;gap:16px;font-size:12px;color:var(--mut)}} .legend span::before{{content:"";display:inline-block;width:18px;height:3px;background:var(--c);margin-right:6px;vertical-align:3px;border-radius:2px}}
ul{{padding-left:18px}} li{{margin:3px 0}} footer{{margin-top:30px;border-top:1px solid var(--line);padding-top:12px;color:var(--mut);font-size:11.5px;display:flex;justify-content:space-between}}
.model td:first-child{{color:var(--mut);width:150px}}
@media print{{body{{background:#fff}} .page{{border:0;box-shadow:none;margin:0;max-width:none;padding:0}} h2{{break-after:avoid}} tr{{break-inside:avoid}} .pb{{break-before:page}} @page{{size:A4;margin:14mm}}}}
</style></head><body><div class="page">
<header><div><div class="kick">AI Campus 3조 · 교과 8 Vision 객체검출 · 라이브 시연</div><h1>조각김치 이물검출 — Final Model 시연 보고서</h1></div>
<div class="meta">{now}{f"<br>시연 {e(presenter)}" if presenter else ""}<br>{e(demo.run)}</div></header>
{warn_photo}
<h2>1. 요약</h2>
<div class="cards">{card_html}</div>
{counts_html}
<table class="model"><tr><td>모델</td><td><b>{e(demo.run)}</b> · YOLO11s · imgsz {demo.imgsz} · Weight <span class="mono">{e(demo.weight.name)}</span> (sha256 {e(_sha(demo))})</td></tr>
<tr><td>데이터</td><td>Dataset kimchi_v5 · Validation {n_val}장 (Train 이 보지 못한 촬영 묶음 G05 · G13 + G00 6장) · Frozen Test · Bridge Holdout 은 시연에 쓰지 않음</td></tr>
<tr><td>실행 장치</td><td>{e(str(getattr(demo, "gpu", "")))} · 예측 확신도 0.05 로 한 번 예측 후 기준 {conf:.2f} 로 판정</td></tr></table>
{sweep_html}
{class_html}
{viewed_html}
{err_html}
<h2>6. 읽는 법 · 한계</h2>
<ul>
<li><b>판정</b>: 예측과 정답 박스가 IoU 0.5 이상 겹치고 Class 가 같으면 <b>맞힘</b>, Class 가 다르면 <b>종류 틀림</b>, 어떤 정답과도 겹치지 않으면 <b>오검출</b>, 어떤 예측과도 겹치지 않은 정답은 <b>놓침</b> (<span class="mono">src/inference.py</span> 와 같은 규칙).</li>
<li>이 보고서의 비율은 <b>박스 개수 기준</b>이라 mAP 와 다릅니다. 모델의 공식 성능은 <b>Frozen Test mAP50-95 {test.get('map50_95', 0):.3f}</b> 입니다 (Final 확정 뒤 정식 평가 1회).</li>
<li>Validation 은 Final Model 을 고르는 데 쓴 데이터라 결과가 실제보다 조금 좋게 나올 수 있습니다.</li>
<li><b>병해·갈변(작은 반점)</b>은 거의 찾지 못합니다 — Train 갈변은 대부분 잎 전체가 변한 큰 조각이라 다른 물체입니다 (데이터 과제, 교과 14).</li>
<li>정상 김치(이물 없음) 사진이 데이터에 없어 정상 제품 오검출률은 측정하지 못했습니다. 평가 사진은 Train 과 같은 날 · 같은 소품으로 찍었습니다.</li>
</ul>
<footer><span>subject8/app/server.py · app/report.py 가 만든 보고서 — 서버에는 저장하지 않음</span><span>AI캠퍼스 교육용 100% 가상 생성 데이터</span></footer>
</div></body></html>"""


def _sha(demo) -> str:
    from src.train_detector import sha256_short
    return sha256_short(demo.weight)
