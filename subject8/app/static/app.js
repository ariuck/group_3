/* 조각김치 이물검출 — Final Model 시연 화면 (외부 라이브러리 없음) */
"use strict";

const $ = (s) => document.querySelector(s);
const COLORS = ["#3fb950", "#f85149", "#4493f8", "#b07cf6", "#8b949e", "#f0883e", "#2dd4bf"];
const BAD = "#ff3ea5", WARN = "#facc15";
const KIND_KO = { TP: "맞힘", CLASS_ERROR: "종류 틀림", FP: "오검출", FN: "놓침", PRED: "예측" };

const S = {
  info: null, images: [], uploads: [], tab: "val", group: "all", classFilter: new Set(),
  cur: null,            // 현재 사진 id
  res: null,            // 현재 판정 결과 (서버 judge)
  done: new Map(),      // id → 판정 요약 (갤러리 배지)
  img: null, imgId: null,
  view: { s: 1, x: 0, y: 0 }, mode: "cmp", labels: true, conf: 0.25,
  hover: -1, busy: false, prefetching: false, allRunning: false, summaryOn: false,
};

/* ── 공통 ─────────────────────────────────────────────── */
async function api(path, opt = {}) {
  const r = await fetch(path, opt);
  const ct = r.headers.get("content-type") || "";
  const body = ct.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error((body && body.detail) || r.statusText);
  return body;
}
function toast(msg, err = false) {
  const el = document.createElement("div");
  el.className = "toast" + (err ? " err" : "");
  el.textContent = msg;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), err ? 6000 : 3200);
}
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const nameOf = (c) => (S.info ? S.info.names[c] : c);
const shortTime = (id) => { const m = /^(\d{6})_(\d{2})(\d{2})(\d{2})/.exec(id); return m ? `${m[1].slice(2, 4)}.${m[1].slice(4)} ${m[2]}:${m[3]}:${m[4]}` : id; };
const pct = (v) => (v == null || isNaN(v) ? "–" : (v * 100).toFixed(1) + "%");

/* ── 시작 ─────────────────────────────────────────────── */
async function boot() {
  bindUI();
  resize();
  await loadInfo();
  try {
    S.images = await api("/api/images");
  } catch (e) { toast("사진 목록을 불러오지 못했습니다: " + e.message, true); }
  $("#valCount").textContent = S.images.length;
  buildFilters();
  renderGallery();
  const m = /img=([^&]+)/.exec(location.hash);
  if (m) select(decodeURIComponent(m[1]));
}

async function loadInfo() {
  try {
    S.info = await api("/api/info");
  } catch (e) {
    setStatus("err", "서버 연결 안 됨");
    return;
  }
  const i = S.info;
  $("#modelLine").textContent = `${i.run} · YOLO11s · imgsz ${i.imgsz} · ${i.dataset} · sha256 ${i.sha}`;
  const v = i.metrics.val, t = i.metrics.test;
  $("#metricChips").innerHTML = [
    v && `<div class="chip"><b>${v.map50_95.toFixed(3)}</b><span>Validation mAP50-95</span></div>`,
    t && `<div class="chip hl"><b>${t.map50_95.toFixed(3)}</b><span>Frozen Test mAP50-95 (${t.images}장)</span></div>`,
    t && `<div class="chip"><b>${t.precision.toFixed(2)} / ${t.recall.toFixed(2)}</b><span>Test Precision / Recall</span></div>`,
  ].filter(Boolean).join("");
  S.conf = i.default_conf;
  setConf(S.conf, false);
  pollReady();
}

async function pollReady() {
  while (true) {
    const i = S.info = await api("/api/info").catch(() => null);
    if (!i) { setStatus("err", "서버 연결 안 됨"); }
    else if (i.error) { setStatus("err", "모델 오류"); toast(i.error, true); return; }
    else if (i.ready) { setStatus("ok", `준비 완료 · ${i.device}`); if (S.cur && !S.res) predict(S.cur); return; }
    else setStatus("", "모델 준비 중…");
    await new Promise((r) => setTimeout(r, 900));
  }
}
function setStatus(cls, text) {
  const el = $("#status");
  el.className = "status " + cls;
  el.querySelector("b").textContent = text;
}

/* ── 왼쪽: 갤러리 ─────────────────────────────────────── */
function buildFilters() {
  const groups = ["all", ...[...new Set(S.images.map((x) => x.group))].sort()];
  $("#groupSeg").innerHTML = groups.map((g) => `<button data-g="${g}" class="${g === S.group ? "on" : ""}">${g === "all" ? "전체" : g}</button>`).join("");
  $("#groupSeg").onclick = (e) => {
    const b = e.target.closest("button"); if (!b) return;
    S.group = b.dataset.g; buildFilters(); renderGallery();
  };
  const present = new Set(S.images.flatMap((x) => Object.keys(x.classes).map(Number)));
  $("#classChips").innerHTML = [...present].sort().map((c) =>
    `<button class="cchip ${S.classFilter.has(c) ? "on" : ""}" data-c="${c}" style="${S.classFilter.has(c) ? `color:${COLORS[c]}` : ""}"><i style="background:${COLORS[c]}"></i>${nameOf(c)}</button>`).join("");
  $("#classChips").onclick = (e) => {
    const b = e.target.closest(".cchip"); if (!b) return;
    const c = +b.dataset.c;
    S.classFilter.has(c) ? S.classFilter.delete(c) : S.classFilter.add(c);
    buildFilters(); renderGallery();
  };
}

function visibleList() {
  if (S.tab === "up") return S.uploads;
  return S.images.filter((x) => (S.group === "all" || x.group === S.group)
    && [...S.classFilter].every((c) => x.classes[c]));
}

function renderGallery() {
  const list = visibleList();
  $("#filters").style.display = S.tab === "val" ? "" : "none";
  if (!list.length) {
    $("#gallery").innerHTML = `<div class="none">${S.tab === "up" ? "아래 상자에 사진을 끌어다 놓으세요" : "조건에 맞는 사진이 없습니다"}</div>`;
    return;
  }
  $("#gallery").innerHTML = list.map((x) => {
    const d = S.done.get(x.id);
    const badge = d ? (d.fn + d.fp + d.ce === 0 ? `<span class="badge ok">✓ ${d.tp}</span>` : `<span class="badge bad">✕ ${d.fn + d.fp + d.ce}</span>`)
      : (x.source === "upload" ? `<span class="badge">새 사진</span>` : "");
    const dots = Object.keys(x.classes || {}).map((c) => `<span class="dot" style="background:${COLORS[c]}"></span>`).join("");
    return `<div class="thumb ${x.id === S.cur ? "on" : ""}" data-id="${x.id}" title="${x.title || x.id}">
      <img loading="lazy" src="/api/images/${encodeURIComponent(x.id)}/thumb" alt="">
      ${badge}<div class="cap"><span class="t">${x.group ? x.group + " · " : ""}${x.source === "upload" ? (x.title || "").slice(0, 18) : shortTime(x.id)}</span>${dots}</div></div>`;
  }).join("");
  const on = $("#gallery .thumb.on");
  if (on) on.scrollIntoView({ block: "nearest" });
}

/* ── 선택 · 예측 ─────────────────────────────────────── */
async function select(id) {
  if (!id) return;
  S.cur = id; S.res = null; S.hover = -1;
  history.replaceState(null, "", "#img=" + encodeURIComponent(id));
  renderGallery();
  updatePos();
  $("#empty").style.display = "none";
  loadImage(id);
  if (S.info && S.info.ready) predict(id);
}

function loadImage(id) {
  const im = new Image();
  im.onload = () => { if (S.cur !== id) return; S.img = im; S.imgId = id; fit(); draw(); };
  im.onerror = () => toast("사진을 열 수 없습니다", true);
  im.src = `/api/images/${encodeURIComponent(id)}/full`;
}

async function predict(id) {
  const cached = S.done.has(id);
  if (!cached) scanning(true);
  try {
    const r = await api(`/api/images/${encodeURIComponent(id)}/predict?conf=${S.conf}`, { method: "POST" });
    if (S.cur !== id) return;
    setResult(r);
  } catch (e) {
    if (S.cur === id) toast(e.message, true);
  } finally {
    if (S.cur === id) scanning(false);
  }
  prefetchNext();
}

const rejudge = debounce(async () => {
  if (!S.cur || !S.res) return;
  try {
    const r = await api(`/api/images/${encodeURIComponent(S.cur)}/judge?conf=${S.conf}`);
    if (r.id === S.cur) setResult(r);
  } catch (e) { /* 예측 전이면 무시 */ }
  if (S.summaryOn) loadSummary();
}, 40);

function setResult(r) {
  S.res = r;
  if (r.counts) S.done.set(r.id, { tp: r.counts.tp, fp: r.counts.fp, fn: r.counts.fn, ce: r.counts.class_error });
  else S.done.set(r.id, { tp: r.preds.length, fp: 0, fn: 0, ce: 0 });
  renderGallery(); renderPanel(); draw();
}

async function prefetchNext() {           // 다음 사진을 미리 예측해 두면 넘길 때 바로 뜬다
  if (S.prefetching || S.allRunning) return;
  const list = visibleList(), i = list.findIndex((x) => x.id === S.cur);
  const nxt = list[i + 1];
  if (!nxt || S.done.has(nxt.id) || nxt.source === "upload") return;
  S.prefetching = true;
  try {
    const r = await api(`/api/images/${encodeURIComponent(nxt.id)}/predict?conf=${S.conf}`, { method: "POST" });
    S.done.set(r.id, r.counts ? { tp: r.counts.tp, fp: r.counts.fp, fn: r.counts.fn, ce: r.counts.class_error } : { tp: 0, fp: 0, fn: 0, ce: 0 });
    renderGallery();
  } catch (e) { /* 무시 */ }
  S.prefetching = false;
}

function scanning(on) {
  $("#scan").classList.toggle("on", on);
  if (on) $("#scanLabel").textContent = `예측 중… YOLO11s · imgsz ${S.info ? S.info.imgsz : ""}`;
}

function step(d) {
  const list = visibleList();
  if (!list.length) return;
  let i = list.findIndex((x) => x.id === S.cur);
  i = i < 0 ? 0 : Math.min(list.length - 1, Math.max(0, i + d));
  select(list[i].id);
}
function updatePos() {
  const list = visibleList(), i = list.findIndex((x) => x.id === S.cur);
  $("#pos").textContent = i < 0 ? "–" : `${i + 1} / ${list.length}`;
}

/* ── 오른쪽 패널 ─────────────────────────────────────── */
function renderPanel() {
  const r = S.res;
  if (!r) return;
  $("#ms").textContent = r.ms ? `모델 ${r.ms.inference ?? "–"} ms · 전체 ${Math.round(r.ms.total)} ms` : "";
  if (r.counts) {
    const c = r.counts;
    const rec = c.gt ? c.tp / c.gt : null, prec = c.pred ? c.tp / c.pred : null;
    $("#stats").innerHTML = `
      <div class="stat tp"><b>${c.tp}</b><span>맞힘</span></div>
      <div class="stat ce"><b>${c.class_error}</b><span>종류 틀림</span></div>
      <div class="stat fp"><b>${c.fp}</b><span>오검출</span></div>
      <div class="stat fn"><b>${c.fn}</b><span>놓침</span></div>
      <div class="wide"><span>정답 <b>${c.gt}</b></span><span>예측 <b>${c.pred}</b></span><span>찾은 비율 <b>${pct(rec)}</b></span><span>맞은 비율 <b>${pct(prec)}</b></span></div>`;
    const rows = Object.entries(r.per_class).map(([k, d]) => {
      const z = (v) => (v ? `<td>${v}</td>` : `<td class="z">0</td>`);
      const b = (v) => (v ? `<td class="bad">${v}</td>` : `<td class="z">0</td>`);
      return `<tr><td><span class="nm"><i style="background:${COLORS[k]}"></i>${nameOf(k)}</span></td>${z(d.gt)}${z(d.pred)}${z(d.tp)}${b(d.fn)}${b((d.fp || 0) + (d.class_error || 0))}</tr>`;
    }).join("");
    $("#clsTable").innerHTML = `<tr><th>Class</th><th>정답</th><th>예측</th><th>맞힘</th><th>놓침</th><th>틀림</th></tr>${rows}`;
  } else {
    $("#stats").innerHTML = `<div class="stat"><b>${r.preds.length}</b><span>검출</span></div><div class="only" style="grid-column:span 3">정답(라벨)이 없는 사진 — 예측만 표시합니다</div>`;
    $("#clsTable").innerHTML = "";
  }
  renderDets();
  renderHud();
}

function detRows() {
  const r = S.res; if (!r) return [];
  const rows = r.preds.map((p, i) => ({ ...p, i, type: "pred" }));
  if (r.gt) r.gt.forEach((g, j) => { if (g.missed) rows.push({ cls: g.cls, conf: null, box: g.box, kind: "FN", j, type: "gt" }); });
  return rows;
}

function renderDets() {
  const rows = detRows();
  $("#detCount").textContent = S.res ? `(${S.res.preds.length}개 · 기준 ${S.conf.toFixed(2)})` : "";
  if (!rows.length) { $("#dets").innerHTML = `<li class="empty-li">이 기준에서는 검출이 없습니다</li>`; return; }
  $("#dets").innerHTML = rows.map((d, n) => {
    const w = S.img ? Math.round((d.box[2] - d.box[0]) * S.img.naturalWidth) : 0;
    const extra = d.kind === "CLASS_ERROR" && d.gt != null ? ` → 정답 ${nameOf(S.res.gt[d.gt].cls)}` : "";
    return `<li data-n="${n}" class="${S.hover === n ? "hl" : ""}">
      <span class="bar" style="background:${COLORS[d.cls]}"></span>
      <span class="nm">${nameOf(d.cls)}${extra}<small>${w ? w + "px" : ""}${d.type === "gt" ? " · 정답 박스" : ""}</small></span>
      <span>${d.conf == null ? `<div class="confnum">–</div>` : `<div class="confbar"><i style="width:${d.conf * 100}%;background:${COLORS[d.cls]}"></i></div><div class="confnum">${d.conf.toFixed(2)}</div>`}</span>
      <span class="kind ${d.kind}">${KIND_KO[d.kind]}</span></li>`;
  }).join("");
}

function renderHud() {
  const r = S.res;
  if (!r) { $("#hudCounts").innerHTML = ""; $("#hudMeta").innerHTML = ""; $("#legend").innerHTML = ""; return; }
  if (r.counts && S.mode === "cmp") {
    const c = r.counts;
    $("#hudCounts").innerHTML = `<span><span class="n" style="color:var(--ok)">${c.tp}</span><span class="k">맞힘</span></span>
      <span><span class="n" style="color:${WARN}">${c.class_error}</span><span class="k">종류 틀림</span></span>
      <span><span class="n" style="color:${BAD}">${c.fp}</span><span class="k">오검출</span></span>
      <span><span class="n" style="color:${BAD}">${c.fn}</span><span class="k">놓침</span></span>`;
  } else if (S.mode === "gt" && r.gt) {
    $("#hudCounts").innerHTML = `<span><span class="n">${r.gt.length}</span><span class="k">정답 박스</span></span>`;
  } else {
    $("#hudCounts").innerHTML = `<span><span class="n">${r.preds.length}</span><span class="k">검출 (기준 ${S.conf.toFixed(2)})</span></span>`;
  }
  const w = r.w, h = r.h;
  $("#hudMeta").textContent = `${r.title}${r.group ? " · " + r.group : ""}${r.scene ? " · " + r.scene : ""} · ${w}×${h}${r.source === "upload" ? " · 올린 사진" : " · Validation"}`;
  $("#legend").innerHTML = S.mode === "cmp" && r.counts ? `
    <div><i style="border-color:#ddd"></i>예측 (색 = Class)</div>
    <div><i style="border-color:${WARN};border-style:solid"></i>종류 틀림</div>
    <div><i style="border-color:${BAD};border-style:dashed"></i>오검출 · 놓친 정답(✕)</div>` :
    S.mode === "gt" ? `<div><i style="border-color:#ddd;border-style:dashed"></i>정답 박스 (색 = Class)</div>` : "";
}

/* ── 그리기 (확대 · 이동) ─────────────────────────────── */
const cv = $("#canvas"), ctx = cv.getContext("2d");
function resize() {
  const r = $("#stage").getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
  draw();
}
function fit() {
  if (!S.img) return;
  const r = $("#stage").getBoundingClientRect(), pad = 24;
  const s = Math.min((r.width - pad * 2) / S.img.naturalWidth, (r.height - pad * 2) / S.img.naturalHeight);
  S.view = { s, x: (r.width - S.img.naturalWidth * s) / 2, y: (r.height - S.img.naturalHeight * s) / 2 };
  S.fitScale = s;
  draw();
}
function zoomAt(f, cx, cy) {
  const v = S.view, ns = Math.max(S.fitScale * 0.5, Math.min(8, v.s * f));
  v.x = cx - (cx - v.x) * ns / v.s; v.y = cy - (cy - v.y) * ns / v.s; v.s = ns;
  draw();
}
function zoomToBox(b) {
  if (!S.img) return;
  const r = $("#stage").getBoundingClientRect(), W = S.img.naturalWidth, H = S.img.naturalHeight;
  const bw = (b[2] - b[0]) * W, bh = (b[3] - b[1]) * H;
  const s = Math.min(6, Math.min(r.width / (bw * 4), r.height / (bh * 4)));
  S.view = { s, x: r.width / 2 - ((b[0] + b[2]) / 2) * W * s, y: r.height / 2 - ((b[1] + b[3]) / 2) * H * s };
  draw();
}
const toScreen = (b) => {
  const W = S.img.naturalWidth, H = S.img.naturalHeight, v = S.view;
  return [v.x + b[0] * W * v.s, v.y + b[1] * H * v.s, v.x + b[2] * W * v.s, v.y + b[3] * H * v.s];
};

function shapes() {               // 지금 모드에서 그릴 박스 목록 (목록 번호 n 과 같은 순서)
  const r = S.res; if (!r) return [];
  if (S.mode === "gt") return (r.gt || []).map((g) => ({ cls: g.cls, box: g.box, kind: "GT", dashed: true }));
  const rows = detRows();
  if (S.mode === "pred") return rows.filter((d) => d.type === "pred").map((d) => ({ ...d, kind: "PRED", n: rows.indexOf(d) }));
  return rows.map((d, n) => ({ ...d, n }));
}

function draw() {
  const dpr = window.devicePixelRatio || 1;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (!S.img || S.imgId !== S.cur) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const v = S.view;
  ctx.imageSmoothingQuality = "high";
  ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 24;
  ctx.drawImage(S.img, v.x, v.y, S.img.naturalWidth * v.s, S.img.naturalHeight * v.s);
  ctx.shadowBlur = 0;
  $("#zoomLabel").textContent = Math.round(v.s * 100) + "%";
  const list = shapes();
  const hl = S.hover;
  list.forEach((d) => {
    const [x1, y1, x2, y2] = toScreen(d.box);
    const on = hl >= 0 && d.n === hl, dim = hl >= 0 && !on;
    const col = COLORS[d.cls];
    ctx.globalAlpha = dim ? 0.35 : 1;
    ctx.lineWidth = on ? 3.5 : 2;
    if (d.kind === "FN") {                      // 놓친 정답: 점선 + ✕
      ctx.strokeStyle = BAD; ctx.setLineDash([6, 4]); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.setLineDash([]); ctx.lineWidth = on ? 3 : 2;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.moveTo(x2, y1); ctx.lineTo(x1, y2); ctx.stroke();
    } else {
      ctx.strokeStyle = col; ctx.setLineDash(d.dashed ? [7, 4] : []); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1); ctx.setLineDash([]);
      if (d.kind === "FP" || d.kind === "CLASS_ERROR") {
        const g = 4; ctx.lineWidth = 2;
        ctx.strokeStyle = d.kind === "FP" ? BAD : WARN; ctx.setLineDash(d.kind === "FP" ? [5, 4] : []);
        ctx.strokeRect(x1 - g, y1 - g, x2 - x1 + g * 2, y2 - y1 + g * 2); ctx.setLineDash([]);
      }
    }
    if (on) { ctx.fillStyle = "rgba(255,255,255,.08)"; ctx.fillRect(x1, y1, x2 - x1, y2 - y1); }
    if (S.labels && !dim) label(d, x1, y1, col);
    ctx.globalAlpha = 1;
  });
}

function label(d, x, y, col) {
  let t = d.kind === "GT" ? `정답 ${nameOf(d.cls)}` : d.kind === "FN" ? `놓침 · ${nameOf(d.cls)}` : `${nameOf(d.cls)} ${d.conf.toFixed(2)}`;
  if (d.kind === "FP") t += " · 오검출";
  if (d.kind === "CLASS_ERROR") t += " · 종류 틀림";
  ctx.font = "600 12px " + getComputedStyle(document.body).fontFamily;
  const w = ctx.measureText(t).width + 10, h = 18, ty = y - h - 3 < 0 ? y + 3 : y - h - 3;
  ctx.fillStyle = d.kind === "FN" || d.kind === "FP" ? BAD : d.kind === "CLASS_ERROR" ? WARN : col;
  roundRect(x, ty, w, h, 4); ctx.fill();
  ctx.fillStyle = d.kind === "CLASS_ERROR" ? "#111" : "#fff";
  ctx.fillText(t, x + 5, ty + 13);
}
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }

function hitTest(mx, my) {
  let best = -1, area = Infinity;
  shapes().forEach((d) => {
    if (d.n == null) return;
    const [x1, y1, x2, y2] = toScreen(d.box);
    if (mx >= x1 - 4 && mx <= x2 + 4 && my >= y1 - 4 && my <= y2 + 4) {
      const a = (x2 - x1) * (y2 - y1); if (a < area) { area = a; best = d.n; }
    }
  });
  return best;
}
function setHover(n, mx, my) {
  if (n !== S.hover) { S.hover = n; draw(); document.querySelectorAll("#dets li").forEach((li) => li.classList.toggle("hl", +li.dataset.n === n)); }
  const tip = $("#tip");
  if (n < 0 || mx == null) { tip.style.display = "none"; return; }
  const d = detRows()[n]; if (!d) return;
  const W = S.img.naturalWidth, H = S.img.naturalHeight;
  tip.innerHTML = `<b style="color:${COLORS[d.cls]}">${nameOf(d.cls)}</b> · <span class="kind ${d.kind}">${KIND_KO[d.kind]}</span><br>
    ${d.conf != null ? `확신도 <b>${d.conf.toFixed(3)}</b> · ` : ""}크기 ${Math.round((d.box[2] - d.box[0]) * W)}×${Math.round((d.box[3] - d.box[1]) * H)}px`;
  tip.style.display = "block"; tip.style.left = mx + 14 + "px"; tip.style.top = my + 14 + "px";
}

/* ── Val 전체 채점 ─────────────────────────────────────── */
async function runAll() {
  if (S.allRunning) { S.allRunning = false; return; }
  if (!S.info || !S.info.ready) { toast("모델이 아직 준비되지 않았습니다", true); return; }
  S.allRunning = true; S.summaryOn = true;
  const btn = $("#btnAll"); btn.textContent = "멈추기";
  const prog = $("#prog"); prog.classList.add("on");
  const todo = S.images.filter((x) => !S.done.has(x.id));
  let n = S.images.length - todo.length;
  const t0 = performance.now();
  for (const x of todo) {
    if (!S.allRunning) break;
    try {
      const r = await api(`/api/images/${encodeURIComponent(x.id)}/predict?conf=${S.conf}`, { method: "POST" });
      S.done.set(r.id, { tp: r.counts.tp, fp: r.counts.fp, fn: r.counts.fn, ce: r.counts.class_error });
    } catch (e) { toast(e.message, true); break; }
    n++;
    prog.querySelector("i").style.width = (n / S.images.length * 100) + "%";
    prog.querySelector("span").textContent = `${n} / ${S.images.length}`;
    if (n % 8 === 0) { renderGallery(); loadSummary(); }
  }
  S.allRunning = false; btn.textContent = "다시 합치기";
  renderGallery(); await loadSummary();
  if (n === S.images.length) toast(`Validation ${n}장 채점 완료 (${((performance.now() - t0) / 1000).toFixed(0)}초)`);
}

async function loadSummary() {
  let s;
  try { s = await api(`/api/summary?conf=${S.conf}`); } catch (e) { return; }
  if (!s.images) return;
  const c = s.counts, rec = c.gt ? c.tp / c.gt : 0, prec = c.pred ? c.tp / c.pred : 0;
  const bars = Object.entries(s.per_class).filter(([, d]) => d.gt).map(([k, d]) => {
    const r = (d.tp || 0) / d.gt;
    return `<div class="rbar"><span class="nm" style="display:flex;gap:6px;align-items:center"><i style="width:8px;height:8px;border-radius:2px;background:${COLORS[k]}"></i>${nameOf(k)}</span>
      <div class="track"><i style="width:${r * 100}%;background:${COLORS[k]}"></i></div><span class="v">${d.tp || 0}/${d.gt} ${(r * 100).toFixed(0)}%</span></div>`;
  }).join("");
  $("#summary").innerHTML = `
    <div class="sumgrid">
      <div class="stat"><b>${pct(rec)}</b><span>찾은 비율 (${c.tp}/${c.gt})</span></div>
      <div class="stat"><b>${pct(prec)}</b><span>맞은 비율 (${c.tp}/${c.pred})</span></div>
    </div>
    <div class="stats">
      <div class="stat tp"><b>${c.tp}</b><span>맞힘</span></div><div class="stat ce"><b>${c.class_error}</b><span>종류 틀림</span></div>
      <div class="stat fp"><b>${c.fp}</b><span>오검출</span></div><div class="stat fn"><b>${c.fn}</b><span>놓침</span></div>
    </div>
    <div class="rbars">${bars}</div>
    <p class="note">${s.images}/${s.of}장 · 기준 ${s.conf.toFixed(2)} · IoU 0.5 · 박스 개수 기준 (mAP 가 아님)${s.inference_ms ? ` · 모델 중앙값 ${s.inference_ms} ms/장` : ""}<br>
    병해·갈변(작은 반점)은 거의 찾지 못합니다 — 알려진 한계 (모델 정보 참고)</p>`;
}

/* ── 업로드 ─────────────────────────────────────────── */
async function uploadFiles(files) {
  for (const f of files) {
    if (!f.type.startsWith("image/")) { toast(`${f.name}: 사진이 아닙니다`, true); continue; }
    try {
      const r = await api("/api/upload", { method: "POST", body: f, headers: { "X-Filename": encodeURIComponent(f.name), "Content-Type": "application/octet-stream" } });
      if (r.source === "val") { toast(`${f.name}: Validation 사진이라 정답과 비교합니다`); S.tab = "val"; setTab("val"); select(r.id); continue; }
      S.uploads.unshift({ id: r.id, title: r.title, source: "upload", classes: {} });
      $("#upCount").textContent = S.uploads.length;
      setTab("up"); select(r.id);
    } catch (e) { toast(`${f.name}: ${e.message}`, true); }
  }
}
function setTab(t) {
  S.tab = t;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("on", b.dataset.tab === t));
  renderGallery(); updatePos();
}

/* ── YOLO TXT 후보 ───────────────────────────────────── */
function saveTxt() {
  const r = S.res; if (!r) { toast("먼저 사진을 예측하세요", true); return; }
  const lines = r.preds.map((p) => {
    const [x1, y1, x2, y2] = p.box;
    return `${p.cls} ${((x1 + x2) / 2).toFixed(6)} ${((y1 + y2) / 2).toFixed(6)} ${(x2 - x1).toFixed(6)} ${(y2 - y1).toFixed(6)}`;
  });
  const stem = (r.title || r.id).replace(/\.[^.]+$/, "");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([lines.join("\n") + (lines.length ? "\n" : "")], { type: "text/plain" }));
  a.download = `${stem}.txt`; a.click(); URL.revokeObjectURL(a.href);
  toast(`${stem}.txt — 후보 ${lines.length}개 (기준 ${S.conf.toFixed(2)}) · 사람 검수 후 정답으로 확정`);
}

/* ── 모달 ───────────────────────────────────────────── */
function modal(html) { $("#modalBody").innerHTML = html; $("#modal").hidden = false; }
function showInfo() {
  const i = S.info; if (!i) return;
  const v = i.metrics.val || {}, t = i.metrics.test || {};
  const f = (x) => (x == null ? "–" : x.toFixed(3));
  modal(`<h2>Final Model — ${i.run}</h2>
    <table><tr><th>Weight</th><td><code>${i.weight}</code> · sha256 ${i.sha}</td></tr>
      <tr><th>조건</th><td>YOLO11s · imgsz ${i.imgsz} · 증강(상하반전 · 밝기) · Dataset ${i.dataset}</td></tr>
      <tr><th>실행 장치</th><td>${i.device || "–"} · 예측 conf ${i.predict_conf} (화면에서 기준으로 거름)</td></tr></table>
    <h4>성능</h4>
    <table><tr><th></th><th>Precision</th><th>Recall</th><th>mAP50</th><th>mAP50-95</th></tr>
      <tr><td>Validation 104장 (선택에 쓴 점수)</td><td>${f(v.precision)}</td><td>${f(v.recall)}</td><td>${f(v.map50)}</td><td>${f(v.map50_95)}</td></tr>
      <tr><td><b>Frozen Test ${t.images || ""}장 (최종 성능)</b></td><td>${f(t.precision)}</td><td>${f(t.recall)}</td><td>${f(t.map50)}</td><td><b>${f(t.map50_95)}</b></td></tr></table>
    <h4>알려진 한계 — 시연에서 같이 말하기</h4>
    <ul><li><b>병해·갈변(작은 반점)</b>은 거의 찾지 못합니다 (Val Recall 0.13 · Test 0). Train 갈변은 대부분 잎 전체가 변한 큰 조각이라 다른 물체입니다.</li>
      <li>나뭇잎·종이는 Test 에서 오검출이 많습니다 (Precision 0.37).</li>
      <li>정상 김치(이물 없음) 사진이 데이터에 없어 정상 제품 오검출률은 재지 못했습니다.</li>
      <li>평가 사진은 Train 과 같은 날 · 같은 소품으로 찍었습니다 — 현장 성능이 아닙니다.</li></ul>
    <h4>이 프로그램이 지키는 것</h4>
    <ul><li>Frozen Test · Bridge Holdout 사진은 목록에 없고, 같은 이름의 사진을 올려도 거절합니다.</li>
      <li>127.0.0.1 에서만 열리며 올린 사진은 메모리에만 두고 저장하지 않습니다.</li>
      <li>TXT 후보는 Auto Label 후보입니다 — 사람이 검수한 뒤에만 정답입니다.</li></ul>`);
}
function showHelp() {
  modal(`<h2>단축키</h2><div class="keysgrid">
    <span><kbd>←</kbd><kbd>→</kbd></span><span>이전 · 다음 사진 (고르면 바로 예측)</span>
    <span><kbd>1</kbd><kbd>2</kbd><kbd>3</kbd></span><span>예측 · 정답 · 비교 보기</span>
    <span><kbd>L</kbd></span><span>라벨 글자 켜기 · 끄기</span>
    <span><kbd>[</kbd><kbd>]</kbd></span><span>확신도 기준 −/+ 0.05</span>
    <span><kbd>+</kbd><kbd>-</kbd><kbd>0</kbd></span><span>확대 · 축소 · 맞춤 (휠 · 끌기도 가능, 더블클릭 = 맞춤)</span>
    <span><kbd>F</kbd></span><span>사진 영역 전체화면</span>
    <span><kbd>S</kbd></span><span>YOLO TXT 후보 저장</span>
    <span><kbd>A</kbd></span><span>Validation 전체 채점</span>
    <span><kbd>I</kbd> · <kbd>?</kbd></span><span>모델 정보 · 단축키</span>
    <span><kbd>Backspace</kbd></span><span>발표자료로 돌아가기</span></div>`);
}

function goBack() {
  if (document.referrer && /presentation/.test(document.referrer)) history.back();
  else if (S.info && S.info.presentation) location.href = "/presentation/index.html#15";
  else history.back();
}

/* ── 이벤트 ─────────────────────────────────────────── */
function setConf(v, apply = true) {
  S.conf = Math.round(Math.min(0.95, Math.max(0.05, v)) * 100) / 100;
  $("#conf").value = S.conf; $("#confVal").textContent = S.conf.toFixed(2);
  document.querySelectorAll(".presets button").forEach((b) => b.classList.toggle("on", +b.dataset.c === S.conf));
  if (apply) rejudge();
}
function setMode(m) {
  S.mode = m; S.hover = -1;
  document.querySelectorAll("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.mode === m));
  renderHud(); draw();
}

function bindUI() {
  window.addEventListener("resize", () => { resize(); fit(); });
  new ResizeObserver(() => { resize(); }).observe($("#stage"));
  document.querySelectorAll(".tab").forEach((b) => b.onclick = () => setTab(b.dataset.tab));
  $("#gallery").onclick = (e) => { const t = e.target.closest(".thumb"); if (t) select(t.dataset.id); };
  $("#modeSeg").onclick = (e) => { const b = e.target.closest("button"); if (b) setMode(b.dataset.mode); };
  $("#optLabels").onchange = (e) => { S.labels = e.target.checked; draw(); };
  $("#conf").oninput = (e) => setConf(+e.target.value);
  document.querySelector(".presets").onclick = (e) => { const b = e.target.closest("button"); if (b) setConf(+b.dataset.c); };
  $("#btnPrev").onclick = () => step(-1); $("#btnNext").onclick = () => step(1);
  $("#btnFit").onclick = fit;
  const center = () => { const r = $("#stage").getBoundingClientRect(); return [r.width / 2, r.height / 2]; };
  $("#btnZoomIn").onclick = () => zoomAt(1.4, ...center());
  $("#btnZoomOut").onclick = () => zoomAt(1 / 1.4, ...center());
  $("#btnFull").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : $(".viewer").requestFullscreen());
  $("#btnTxt").onclick = saveTxt;
  $("#btnAll").onclick = runAll;
  $("#btnInfo").onclick = showInfo; $("#btnHelp").onclick = showHelp; $("#btnBack").onclick = goBack;
  $("#modalX").onclick = () => ($("#modal").hidden = true);
  $("#modal").onclick = (e) => { if (e.target.id === "modal") $("#modal").hidden = true; };

  $("#dets").addEventListener("mousemove", (e) => { const li = e.target.closest("li[data-n]"); if (li) setHover(+li.dataset.n); });
  $("#dets").addEventListener("mouseleave", () => setHover(-1));
  $("#dets").onclick = (e) => { const li = e.target.closest("li[data-n]"); if (li) { const d = detRows()[+li.dataset.n]; if (d) { if (S.mode === "gt") setMode("cmp"); zoomToBox(d.box); } } };

  const stage = $("#stage");
  let drag = null;
  stage.addEventListener("wheel", (e) => { e.preventDefault(); const r = stage.getBoundingClientRect(); zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - r.left, e.clientY - r.top); }, { passive: false });
  stage.addEventListener("mousedown", (e) => { drag = { x: e.clientX, y: e.clientY, vx: S.view.x, vy: S.view.y, moved: false }; stage.classList.add("drag"); });
  window.addEventListener("mouseup", () => { drag = null; stage.classList.remove("drag"); });
  stage.addEventListener("mousemove", (e) => {
    const r = stage.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    if (drag) { S.view.x = drag.vx + e.clientX - drag.x; S.view.y = drag.vy + e.clientY - drag.y; drag.moved = true; draw(); return; }
    if (S.img && S.res) setHover(hitTest(mx, my), mx, my);
  });
  stage.addEventListener("mouseleave", () => setHover(-1));
  stage.addEventListener("dblclick", fit);

  const over = (on) => (e) => { e.preventDefault(); stage.classList.toggle("over", on); $("#drop").classList.toggle("over", on); };
  [stage, $("#drop")].forEach((el) => {
    el.addEventListener("dragover", over(true)); el.addEventListener("dragleave", over(false));
    el.addEventListener("drop", (e) => { over(false)(e); uploadFiles([...e.dataTransfer.files]); });
  });
  $("#fileInput").onchange = (e) => { uploadFiles([...e.target.files]); e.target.value = ""; };

  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type !== "range" && e.target.type !== "checkbox") return;
    if (!$("#modal").hidden) { if (e.key === "Escape") $("#modal").hidden = true; return; }
    const k = e.key;
    if (k === "ArrowRight") { e.preventDefault(); step(1); }
    else if (k === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (k === "1") setMode("pred"); else if (k === "2") setMode("gt"); else if (k === "3") setMode("cmp");
    else if (k === "l" || k === "L") { $("#optLabels").checked = S.labels = !S.labels; draw(); }
    else if (k === "[") setConf(S.conf - 0.05); else if (k === "]") setConf(S.conf + 0.05);
    else if (k === "+" || k === "=") zoomAt(1.4, ...center()); else if (k === "-") zoomAt(1 / 1.4, ...center()); else if (k === "0") fit();
    else if (k === "f" || k === "F") $("#btnFull").click();
    else if (k === "s" || k === "S") saveTxt();
    else if (k === "a" || k === "A") runAll();
    else if (k === "i" || k === "I") showInfo(); else if (k === "?") showHelp();
    else if (k === "Backspace") { e.preventDefault(); goBack(); }
  });
}

boot();
