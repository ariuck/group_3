/* 조각김치 이물검출 — Final Model 시연 화면 (외부 라이브러리 없음) */
"use strict";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const API_BASE = location.pathname.startsWith("/demo/") ? "/demo" : "";
const COLORS = ["#16a34a", "#dc2626", "#2563eb", "#9333ea", "#6b7280", "#ea580c", "#0d9488"];
const BAD = "#e11d74", WARN = "#f59e0b";
const KIND_KO = { TP: "맞힘", CLASS_ERROR: "종류 틀림", FP: "오검출", FN: "놓침", PRED: "예측" };

const S = {
  info: null, images: [], uploads: [], list: "all", group: "all", classFilter: new Set(),
  cur: null, res: null, done: new Map(), viewed: [],
  img: null, imgId: null, view: { s: 1, x: 0, y: 0 }, fitScale: 1,
  mode: "pred", labels: true, conf: 0.25, hidden: new Set(),
  hover: -1, allRunning: false, summaryOn: false, sweep: null,
  steps: new Set(),
};

/* ── 공통 ─────────────────────────────────────────────── */
async function api(path, opt = {}) {
  const r = await fetch(API_BASE + path, opt);
  const ct = r.headers.get("content-type") || "";
  const body = ct.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error((body && body.detail) || r.statusText);
  return body;
}
function toast(msg, err = false) {
  const el = document.createElement("div");
  el.className = "toast" + (err ? " err" : "");
  el.innerHTML = msg;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), err ? 6500 : 3500);
}
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const nameOf = (c) => (S.info ? S.info.names[c] : c);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const shortTime = (id) => { const m = /^(\d{6})_(\d{2})(\d{2})(\d{2})/.exec(id); return m ? `${m[1].slice(2, 4)}.${m[1].slice(4)} ${m[2]}:${m[3]}:${m[4]}` : id; };
const pct = (v) => (v == null || isNaN(v) ? "–" : (v * 100).toFixed(1) + "%");
const icon = (id) => `<svg><use href="#i-${id}"/></svg>`;

/* ── 시연 순서 버튼 ───────────────────────────────────── */
function markStep(id) {
  if (!S.steps.has(id)) { S.steps.add(id); }
  renderSteps();
}
function renderSteps() {
  const order = ["pick", "pred", "cmp", "conf", "all", "report"];
  const next = order.find((s) => !S.steps.has(s));
  $$(".step").forEach((b) => {
    const s = b.dataset.step;
    b.classList.toggle("done", S.steps.has(s));
    b.classList.toggle("on", (s === "pred" && S.mode === "pred") || (s === "cmp" && S.mode === "cmp" && S.res));
    b.classList.toggle("next", s === next);
  });
}
function flash(sel) { const el = $(sel); el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); el.scrollIntoView({ block: "nearest", behavior: "smooth" }); }

function doStep(s) {
  if (s === "pick") {
    if (!S.cur) { const l = visibleList(); if (l.length) select(l[0].id); }
    else flash("#gallery");
  } else if (s === "pred") { ensureImage(); setMode("pred"); }
  else if (s === "cmp") { ensureImage(); setMode("cmp"); }
  else if (s === "conf") { ensureImage(); setConf(S.conf < 0.4 ? 0.5 : 0.25); flash("#confCard"); markStep("conf"); toast(`확신도 기준을 <b>${S.conf.toFixed(2)}</b> 로 바꿨습니다 — 오른쪽 결과와 사진의 박스가 바로 바뀝니다`); }
  else if (s === "all") { flash("#sumCard"); if (!S.allRunning) runAll(); }
  else if (s === "report") openReport();
}
function ensureImage() { if (!S.cur) { const l = visibleList(); if (l.length) select(l[0].id); } }

/* ── 시작 ─────────────────────────────────────────────── */
async function boot() {
  bindUI();
  resize();
  renderSteps();
  await loadInfo();
  try { S.images = await api("/api/images"); } catch (e) { toast("사진 목록을 불러오지 못했습니다: " + esc(e.message), true); }
  buildFilters();
  renderGallery();
  const m = /img=([^&]+)/.exec(location.hash);
  const initial = new URLSearchParams(location.hash.slice(1));
  if (initial.has("conf")) setConf(Math.max(0.05, Math.min(0.95, Number(initial.get("conf")) || 0.25)), false);
  if (initial.get("mode") === "cmp" || initial.get("mode") === "gt") setMode(initial.get("mode"));
  if (m) await select(decodeURIComponent(m[1]));
  if (initial.get("scene") === "report") openReport();
  if (initial.get("scene") === "threshold") flash("#confCard");
  notifyPresentation("g3-demo:ready");
}

async function loadInfo() {
  try { S.info = await api("/api/info"); } catch (e) { setStatus("err", "서버 연결 안 됨"); return; }
  const i = S.info;
  $("#modelLine").textContent = `${i.run} · YOLO11s · imgsz ${i.imgsz} · ${i.dataset} · sha256 ${i.sha}`;
  const v = i.metrics.val, t = i.metrics.test;
  $("#metricChips").innerHTML = [
    t && `<div class="metric hl" title="Final 확정 뒤 정식 평가 1회 — 모델의 공식 성능"><b>${t.map50_95.toFixed(3)}</b><span>Frozen Test mAP50-95</span></div>`,
    v && `<div class="metric" title="Final 을 고르는 데 쓴 점수"><b>${v.map50_95.toFixed(3)}</b><span>Validation mAP50-95</span></div>`,
  ].filter(Boolean).join("");
  setConf(i.default_conf, false);
  pollReady();
}
async function pollReady() {
  for (;;) {
    const i = await api("/api/info").catch(() => null);
    if (i) S.info = i;
    if (!i) setStatus("err", "서버 연결 안 됨");
    else if (i.error) { setStatus("err", "모델 오류"); toast(esc(i.error), true); return; }
    else if (i.ready) { setStatus("ok", `준비 완료 · ${i.device}`); if (S.cur && !S.res) predict(S.cur); return; }
    else setStatus("", "모델 준비 중…");
    await new Promise((r) => setTimeout(r, 900));
  }
}
function setStatus(cls, text) { const el = $("#status"); el.className = "status " + cls; el.querySelector("b").textContent = text; }

/* ── 왼쪽: 목록 ───────────────────────────────────────── */
function buildFilters() {
  const groups = ["all", ...[...new Set(S.images.map((x) => x.group))].sort()];
  $("#groupChips").innerHTML = groups.map((g) => `<button class="chip ${g === S.group ? "on" : ""}" data-g="${g}">${g === "all" ? "전체" : g}</button>`).join("");
  const present = new Set(S.images.flatMap((x) => Object.keys(x.classes).map(Number)));
  $("#classChips").innerHTML = [...present].sort().map((c) =>
    `<button class="chip ${S.classFilter.has(c) ? "on" : ""}" data-c="${c}"><i style="background:${COLORS[c]}"></i>${nameOf(c)}</button>`).join("");
}
const hasErr = (id) => { const d = S.done.get(id); return d && d.fn + d.fp + d.ce > 0; };
function visibleList() {
  if (S.list === "up") return S.uploads;
  return S.images.filter((x) => (S.group === "all" || x.group === S.group)
    && [...S.classFilter].every((c) => x.classes[c])
    && (S.list !== "err" || hasErr(x.id))
    && (S.list !== "new" || !S.viewed.includes(x.id)));
}
function renderCounts() {
  $("#cAll").textContent = S.images.length;
  $("#cErr").textContent = S.images.filter((x) => hasErr(x.id)).length;
  $("#cNew").textContent = S.images.filter((x) => !S.viewed.includes(x.id)).length;
  $("#cUp").textContent = S.uploads.length;
}
function renderGallery() {
  renderCounts();
  const list = visibleList();
  $("#filters").style.display = S.list === "up" ? "none" : "";
  if (!list.length) {
    const msg = { up: "아래 <b>새 사진 올리기</b>로 사진을 추가하세요", err: "틀린 것이 있는 사진이 아직 없습니다<br><small>⑤ 전체 채점을 하면 모든 사진을 판정합니다</small>", new: "모든 사진을 봤습니다" }[S.list] || "조건에 맞는 사진이 없습니다";
    $("#gallery").innerHTML = `<div class="none">${msg}</div>`;
  } else {
    $("#gallery").innerHTML = list.map((x) => {
      const d = S.done.get(x.id);
      const badge = d ? (d.fn + d.fp + d.ce === 0 ? `<span class="badge ok" title="모두 맞힘">✓ ${d.tp}</span>` : `<span class="badge bad" title="놓침 ${d.fn} · 오검출 ${d.fp} · 종류 틀림 ${d.ce}">✕ ${d.fn + d.fp + d.ce}</span>`)
        : (x.source === "upload" ? `<span class="badge">새 사진</span>` : "");
      const dots = Object.keys(x.classes || {}).map((c) => `<span class="dot" style="background:${COLORS[c]}" title="${nameOf(c)}"></span>`).join("");
      return `<div class="thumb ${x.id === S.cur ? "on" : ""}" data-id="${esc(x.id)}" title="${esc(x.title || x.id)}">
        <img loading="lazy" src="${API_BASE}/api/images/${encodeURIComponent(x.id)}/thumb" alt="">${badge}
        <div class="cap"><span class="t">${x.group ? x.group + " · " : ""}${x.source === "upload" ? esc((x.title || "").slice(0, 16)) : shortTime(x.id)}</span>${dots}</div></div>`;
    }).join("");
  }
  const on = $("#gallery .thumb.on");
  if (on) on.scrollIntoView({ block: "nearest" });
  updatePos();
}

/* ── 선택 · 예측 ─────────────────────────────────────── */
function select(id) {
  if (!id) return;
  S.cur = id; S.res = null; S.hover = -1;
  if (!S.viewed.includes(id)) S.viewed.push(id);
  history.replaceState(null, "", "#img=" + encodeURIComponent(id));
  $("#empty").style.display = "none";
  renderGallery(); renderPanel(); draw();
  loadImage(id);
  markStep("pick");
  if (S.info && S.info.ready) return predict(id);
}
function loadImage(id) {
  const im = new Image();
  im.onload = () => { if (S.cur !== id) return; S.img = im; S.imgId = id; fit(); renderDets(); };
  im.onerror = () => toast("사진을 열 수 없습니다", true);
  im.src = `${API_BASE}/api/images/${encodeURIComponent(id)}/full`;
}
async function predict(id) {
  if (!S.done.has(id)) scanning(true);
  try {
    const r = await api(`/api/images/${encodeURIComponent(id)}/predict?conf=${S.conf}`, { method: "POST" });
    if (S.cur === id) setResult(r);
  } catch (e) { if (S.cur === id) toast(esc(e.message), true); }
  finally { if (S.cur === id) scanning(false); }
}
const rejudge = debounce(async () => {
  if (S.cur && S.res) {
    try { const r = await api(`/api/images/${encodeURIComponent(S.cur)}/judge?conf=${S.conf}`); if (r.id === S.cur) setResult(r); } catch (e) { /* 예측 전 */ }
  }
  if (S.summaryOn) loadSummary();
}, 40);
function doneOf(r) { return r.counts ? { tp: r.counts.tp, fp: r.counts.fp, fn: r.counts.fn, ce: r.counts.class_error } : { tp: r.preds.length, fp: 0, fn: 0, ce: 0 }; }
function setResult(r) {
  S.res = r;
  S.done.set(r.id, doneOf(r));
  if (S.mode === "pred") markStep("pred");
  if (S.mode === "cmp" && r.counts) markStep("cmp");
  renderGallery(); renderPanel(); draw(); renderSteps();
}
function scanning(on) {
  $("#scan").classList.toggle("on", on);
  if (on) $("#scanLabel").textContent = `AI 가 이물을 찾는 중… YOLO11s · ${S.info ? S.info.imgsz : ""}px`;
}
function step(d) {
  const list = visibleList(); if (!list.length) return;
  let i = list.findIndex((x) => x.id === S.cur);
  i = i < 0 ? 0 : Math.min(list.length - 1, Math.max(0, i + d));
  if (list[i].id !== S.cur) select(list[i].id);
}
function nextError() {
  const list = S.list === "up" ? S.uploads : S.images;
  const i = list.findIndex((x) => x.id === S.cur);
  const order = [...list.slice(i + 1), ...list.slice(0, Math.max(0, i))];
  const hit = order.find((x) => hasErr(x.id));
  if (hit) { if (S.list === "new") setList("all"); select(hit.id); }
  else toast(S.done.size < S.images.length ? "틀린 사진을 더 찾으려면 <b>⑤ 전체 채점</b>을 먼저 하세요" : "이 기준에서 틀린 것이 있는 사진이 더 없습니다");
}
function updatePos() {
  const list = visibleList(), i = list.findIndex((x) => x.id === S.cur);
  $("#pos").textContent = i < 0 ? "–" : `${i + 1} / ${list.length}`;
}

/* ── 오른쪽: 이 사진 ─────────────────────────────────── */
function renderPanel() {
  const r = S.res;
  if (!r) {
    $("#ms").textContent = "";
    $("#stats").innerHTML = S.cur ? `<p class="help">예측 중입니다…</p>` : `<p class="help">사진을 고르면 결과가 여기에 나옵니다.</p>`;
    $("#clsTable").innerHTML = ""; renderDets(); renderHud(); return;
  }
  $("#ms").textContent = r.ms ? `AI ${r.ms.inference ?? "–"}ms · 전체 ${Math.round(r.ms.total)}ms` : "";
  if (r.counts) {
    const c = r.counts, z = (v, cls) => (v ? cls : "zero");
    $("#stats").innerHTML = `<div class="stats">
      <div class="stat ${z(c.tp, "tp")}" title="같은 Class 로 정답과 겹침"><b>${c.tp}</b><span>맞힘</span></div>
      <div class="stat ${z(c.class_error, "ce")}" title="위치는 맞는데 종류를 틀림"><b>${c.class_error}</b><span>종류 틀림</span></div>
      <div class="stat ${z(c.fp, "fp")}" title="이물이 없는 곳에 박스"><b>${c.fp}</b><span>오검출</span></div>
      <div class="stat ${z(c.fn, "fn")}" title="정답인데 찾지 못함"><b>${c.fn}</b><span>놓침</span></div></div>
      <div class="ratio"><span>정답 <b>${c.gt}</b> · 예측 <b>${c.pred}</b></span><span>찾은 비율 <b>${pct(c.gt ? c.tp / c.gt : null)}</b></span><span>맞은 비율 <b>${pct(c.pred ? c.tp / c.pred : null)}</b></span></div>`;
    const rows = Object.entries(r.per_class).map(([k, d]) => {
      const z2 = (v) => (v ? `<td>${v}</td>` : `<td class="z">0</td>`), b = (v) => (v ? `<td class="bad">${v}</td>` : `<td class="z">0</td>`);
      return `<tr><td><span class="nm"><i style="background:${COLORS[k]}"></i>${nameOf(k)}</span></td>${z2(d.gt)}${z2(d.pred)}${z2(d.tp)}${b(d.fn)}${b((d.fp || 0) + (d.class_error || 0))}</tr>`;
    }).join("");
    $("#clsTable").innerHTML = `<tr><th>Class</th><th>정답</th><th>예측</th><th>맞힘</th><th>놓침</th><th>틀림</th></tr>${rows}`;
  } else {
    $("#stats").innerHTML = `<div class="stats"><div class="stat"><b>${r.preds.length}</b><span>검출</span></div><div class="only">정답(라벨)이 없는 사진<br>예측만 표시합니다</div></div>`;
    $("#clsTable").innerHTML = "";
  }
  renderDets(); renderHud();
}
function detRows() {
  const r = S.res; if (!r) return [];
  const rows = r.preds.map((p, i) => ({ ...p, i, type: "pred" }));
  if (r.gt) r.gt.forEach((g, j) => { if (g.missed) rows.push({ cls: g.cls, conf: null, box: g.box, kind: "FN", j, type: "gt" }); });
  return rows;
}
function renderDets() {
  const rows = detRows();
  $("#detCount").textContent = S.res ? `${S.res.preds.length}개 · 기준 ${S.conf.toFixed(2)}` : "";
  if (!S.res) { $("#dets").innerHTML = `<li class="empty-li">사진을 고르면 찾은 박스가 여기에 나옵니다</li>`; return; }
  if (!rows.length) { $("#dets").innerHTML = `<li class="empty-li">이 기준에서는 찾은 이물이 없습니다</li>`; return; }
  $("#dets").innerHTML = rows.map((d, n) => {
    const w = S.img ? Math.round((d.box[2] - d.box[0]) * S.img.naturalWidth) : 0;
    const extra = d.kind === "CLASS_ERROR" && d.gt != null ? `<small>정답은 ${nameOf(S.res.gt[d.gt].cls)} · ${w}px</small>` : `<small>${w ? w + "px" : ""}${d.type === "gt" ? " · 정답 박스" : ""}</small>`;
    const border = d.kind === "FP" || d.kind === "FN" ? BAD : d.kind === "CLASS_ERROR" ? WARN : COLORS[d.cls];
    return `<li data-n="${n}" class="${S.hover === n ? "hl" : ""}">
      <canvas class="crop" width="88" height="88" data-n="${n}" style="border-color:${border}"></canvas>
      <span class="nm">${nameOf(d.cls)}${extra}</span>
      <span>${d.conf == null ? `<div class="confnum">–</div>` : `<div class="confbar"><i style="width:${d.conf * 100}%;background:${COLORS[d.cls]}"></i></div><div class="confnum">확신 ${d.conf.toFixed(2)}</div>`}</span>
      <span class="kind ${d.kind}">${KIND_KO[d.kind]}</span></li>`;
  }).join("");
  if (S.img && S.imgId === S.cur) $$("#dets canvas.crop").forEach((c) => drawCrop(c, rows[+c.dataset.n].box));
}
function drawCrop(c, b) {          // 검출 박스 주변을 작게 잘라 보여 준다 (작은 이물 확인용)
  const W = S.img.naturalWidth, H = S.img.naturalHeight, g = c.getContext("2d");
  const x1 = b[0] * W, y1 = b[1] * H, x2 = b[2] * W, y2 = b[3] * H;
  const m = Math.max(x2 - x1, y2 - y1) * 0.6 + 12, cx = (x1 + x2) / 2, cy = (y1 + y2) / 2, half = Math.max(x2 - x1, y2 - y1) / 2 + m;
  g.fillStyle = "#e5e7eb"; g.fillRect(0, 0, c.width, c.height);
  g.drawImage(S.img, cx - half, cy - half, half * 2, half * 2, 0, 0, c.width, c.height);
}
function renderHud() {
  const r = S.res;
  if (!r) { $("#hudCounts").innerHTML = ""; $("#hudMeta").innerHTML = ""; $("#legend").innerHTML = ""; return; }
  if (r.counts && S.mode === "cmp") {
    const c = r.counts;
    $("#hudCounts").innerHTML = `<span><span class="n" style="color:var(--ok)">${c.tp}</span><span class="k">맞힘</span></span>
      <span><span class="n" style="color:var(--warn)">${c.class_error}</span><span class="k">종류 틀림</span></span>
      <span><span class="n" style="color:var(--bad)">${c.fp}</span><span class="k">오검출</span></span>
      <span><span class="n" style="color:var(--bad)">${c.fn}</span><span class="k">놓침</span></span>`;
  } else if (S.mode === "gt" && r.gt) $("#hudCounts").innerHTML = `<span><span class="n">${r.gt.length}</span><span class="k">정답 박스 (사람이 그린 라벨)</span></span>`;
  else $("#hudCounts").innerHTML = `<span><span class="n" style="color:var(--acc)">${r.preds.length}</span><span class="k">AI 가 찾은 이물 · 기준 ${S.conf.toFixed(2)}</span></span>`;
  $("#hudMeta").textContent = `${r.title}${r.group ? " · " + r.group : ""}${r.scene ? " · " + r.scene : ""} · ${r.w}×${r.h}px${r.source === "upload" ? " · 올린 사진" : " · Validation"}`;
  const classes = [...new Set([...(r.gt || []).map((g) => g.cls), ...r.preds.map((p) => p.cls)])].sort();
  const key = S.mode === "cmp" && r.counts
    ? `<div class="row"><span><i style="border-color:#475467"></i>예측(색=Class)</span><span><i style="border-color:${WARN}"></i>종류 틀림</span><span><i style="border-color:${BAD};border-style:dashed"></i>오검출 · ✕ 놓침</span></div>`
    : S.mode === "gt" ? `<div class="row"><span><i style="border-color:#475467;border-style:dashed"></i>정답 박스(색=Class)</span></div>` : "";
  $("#legend").innerHTML = `${key}<div class="lt">CLASS — 눌러서 숨기기</div><div class="row">${classes.map((c) =>
    `<span class="cls ${S.hidden.has(c) ? "off" : ""}" data-c="${c}" style="pointer-events:auto"><i style="background:${COLORS[c]}"></i>${nameOf(c)}</span>`).join("")}</div>`;
}

/* ── 그리기 ─────────────────────────────────────────── */
const cv = $("#canvas"), ctx = cv.getContext("2d");
function resize() { const r = $("#stage").getBoundingClientRect(), dpr = window.devicePixelRatio || 1; cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr); draw(); }
function fit() {
  if (!S.img) return;
  const r = $("#stage").getBoundingClientRect(), pad = 28;
  const s = Math.min((r.width - pad * 2) / S.img.naturalWidth, (r.height - pad * 2) / S.img.naturalHeight);
  S.view = { s, x: (r.width - S.img.naturalWidth * s) / 2, y: (r.height - S.img.naturalHeight * s) / 2 }; S.fitScale = s; draw();
}
function zoomAt(f, cx, cy) { const v = S.view, ns = Math.max(S.fitScale * 0.5, Math.min(8, v.s * f)); v.x = cx - (cx - v.x) * ns / v.s; v.y = cy - (cy - v.y) * ns / v.s; v.s = ns; draw(); }
function zoomToBox(b) {
  if (!S.img) return;
  const r = $("#stage").getBoundingClientRect(), W = S.img.naturalWidth, H = S.img.naturalHeight;
  const bw = Math.max(40, (b[2] - b[0]) * W), bh = Math.max(40, (b[3] - b[1]) * H);
  const s = Math.min(6, Math.min(r.width / (bw * 5), r.height / (bh * 5)));
  S.view = { s, x: r.width / 2 - ((b[0] + b[2]) / 2) * W * s, y: r.height / 2 - ((b[1] + b[3]) / 2) * H * s }; draw();
}
const toScreen = (b) => { const W = S.img.naturalWidth, H = S.img.naturalHeight, v = S.view; return [v.x + b[0] * W * v.s, v.y + b[1] * H * v.s, v.x + b[2] * W * v.s, v.y + b[3] * H * v.s]; };
function shapes() {
  const r = S.res; if (!r) return [];
  let list;
  if (S.mode === "gt") list = (r.gt || []).map((g) => ({ cls: g.cls, box: g.box, kind: "GT", dashed: true }));
  else { const rows = detRows(); list = S.mode === "pred" ? rows.filter((d) => d.type === "pred").map((d) => ({ ...d, kind: "PRED", n: rows.indexOf(d) })) : rows.map((d, n) => ({ ...d, n })); }
  return list.filter((d) => !S.hidden.has(d.cls));
}
function draw() {
  const dpr = window.devicePixelRatio || 1;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
  if (!S.img || S.imgId !== S.cur) { $("#zoomLabel").textContent = "–"; return; }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const v = S.view;
  ctx.imageSmoothingQuality = "high";
  ctx.shadowColor = "rgba(16,24,40,.18)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 6;
  ctx.drawImage(S.img, v.x, v.y, S.img.naturalWidth * v.s, S.img.naturalHeight * v.s);
  ctx.shadowColor = "transparent"; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
  $("#zoomLabel").textContent = Math.round(v.s * 100) + "%";
  const hl = S.hover;
  shapes().forEach((d) => {
    const [x1, y1, x2, y2] = toScreen(d.box), on = hl >= 0 && d.n === hl, dim = hl >= 0 && !on, col = COLORS[d.cls];
    ctx.globalAlpha = dim ? 0.3 : 1;
    if (d.kind === "FN") {
      ctx.lineWidth = on ? 3.5 : 2.5; ctx.strokeStyle = BAD; ctx.setLineDash([6, 4]); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1); ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.moveTo(x2, y1); ctx.lineTo(x1, y2); ctx.stroke();
    } else {
      ctx.lineWidth = 4.5; ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.setLineDash(d.dashed ? [7, 4] : []); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.lineWidth = on ? 3.5 : 2.5; ctx.strokeStyle = col; ctx.strokeRect(x1, y1, x2 - x1, y2 - y1); ctx.setLineDash([]);
      if (d.kind === "FP" || d.kind === "CLASS_ERROR") {
        const g = 5; ctx.lineWidth = 2.5; ctx.strokeStyle = d.kind === "FP" ? BAD : WARN; ctx.setLineDash(d.kind === "FP" ? [6, 4] : []);
        ctx.strokeRect(x1 - g, y1 - g, x2 - x1 + g * 2, y2 - y1 + g * 2); ctx.setLineDash([]);
      }
    }
    if (on) { ctx.fillStyle = "rgba(79,70,229,.10)"; ctx.fillRect(x1, y1, x2 - x1, y2 - y1); }
    if (S.labels && !dim) label(d, x1, y1, col);
    ctx.globalAlpha = 1;
  });
}
function label(d, x, y, col) {
  let t = d.kind === "GT" ? `정답 · ${nameOf(d.cls)}` : d.kind === "FN" ? `놓침 · ${nameOf(d.cls)}` : `${nameOf(d.cls)} ${d.conf.toFixed(2)}`;
  if (d.kind === "FP") t += " · 오검출"; if (d.kind === "CLASS_ERROR") t += " · 종류 틀림";
  ctx.font = "700 12px " + getComputedStyle(document.body).fontFamily;
  const w = ctx.measureText(t).width + 12, h = 20, ty = y - h - 4 < 0 ? y + 4 : y - h - 4;
  ctx.fillStyle = d.kind === "FN" || d.kind === "FP" ? BAD : d.kind === "CLASS_ERROR" ? WARN : col;
  ctx.shadowColor = "rgba(16,24,40,.25)"; ctx.shadowBlur = 4;
  roundRect(x, ty, w, h, 5); ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = "transparent";
  ctx.fillStyle = "#fff"; ctx.fillText(t, x + 6, ty + 14);
}
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function hitTest(mx, my) {
  let best = -1, area = Infinity;
  shapes().forEach((d) => { if (d.n == null) return; const [x1, y1, x2, y2] = toScreen(d.box); if (mx >= x1 - 5 && mx <= x2 + 5 && my >= y1 - 5 && my <= y2 + 5) { const a = (x2 - x1) * (y2 - y1); if (a < area) { area = a; best = d.n; } } });
  return best;
}
function setHover(n, mx, my) {
  if (n !== S.hover) { S.hover = n; draw(); $$("#dets li").forEach((li) => li.classList.toggle("hl", +li.dataset.n === n)); }
  const tip = $("#tip");
  if (n < 0 || mx == null) { tip.style.display = "none"; return; }
  const d = detRows()[n]; if (!d) return;
  const W = S.img.naturalWidth, H = S.img.naturalHeight;
  tip.innerHTML = `<b style="color:${COLORS[d.cls]}">${nameOf(d.cls)}</b> &nbsp;<span class="kind ${d.kind}">${KIND_KO[d.kind]}</span><br>
    ${d.conf != null ? `확신도 <b>${d.conf.toFixed(3)}</b> · ` : ""}크기 ${Math.round((d.box[2] - d.box[0]) * W)}×${Math.round((d.box[3] - d.box[1]) * H)}px`;
  tip.style.display = "block"; tip.style.left = mx + 14 + "px"; tip.style.top = my + 14 + "px";
}

/* ── Validation 전체 채점 ─────────────────────────────── */
async function runAll() {
  if (S.allRunning) { S.allRunning = false; return; }
  if (!S.info || !S.info.ready) { toast("모델이 아직 준비되지 않았습니다", true); return; }
  S.allRunning = true; S.summaryOn = true;
  const btn = $("#btnAll"); btn.innerHTML = `${icon("minus")}멈추기`;
  const prog = $("#prog"); prog.classList.add("on");
  const todo = S.images.filter((x) => !S.done.has(x.id));
  let n = S.images.length - todo.length; const t0 = performance.now();
  const upd = () => { prog.querySelector("i").style.width = (n / S.images.length * 100) + "%"; btn.innerHTML = `${icon("minus")}멈추기 · ${n}/${S.images.length}장`; };
  upd();
  for (const x of todo) {
    if (!S.allRunning) break;
    try { const r = await api(`/api/images/${encodeURIComponent(x.id)}/predict?conf=${S.conf}`, { method: "POST" }); S.done.set(r.id, doneOf(r)); }
    catch (e) { toast(esc(e.message), true); break; }
    n++; upd();
    if (n % 10 === 0) { renderGallery(); loadSummary(false); }
  }
  const finished = n === S.images.length;
  S.allRunning = false; prog.classList.remove("on");
  btn.innerHTML = finished ? `${icon("check")}채점 완료 · 기준을 바꾸면 바로 다시 계산` : `${icon("play")}이어서 채점하기 (${n}/${S.images.length})`;
  btn.classList.toggle("primary", !finished); btn.classList.toggle("outline", finished);
  renderGallery(); await loadSummary(true);
  if (finished) { markStep("all"); doneDialog((performance.now() - t0) / 1000); }
}
async function loadSummary(withSweep = true) {
  let s; try { s = await api(`/api/summary?conf=${S.conf}`); } catch (e) { return; }
  if (!s.images) return;
  if (withSweep || !S.sweep) { try { S.sweep = await api("/api/sweep"); } catch (e) { /* 무시 */ } }
  const c = s.counts, rec = c.gt ? c.tp / c.gt : 0, prec = c.pred ? c.tp / c.pred : 0;
  const bars = Object.entries(s.per_class).filter(([, d]) => d.gt).map(([k, d]) => {
    const r = (d.tp || 0) / d.gt;
    return `<div class="rbar"><span class="nm"><i style="background:${COLORS[k]}"></i>${nameOf(k)}</span><div class="track"><i style="width:${r * 100}%;background:${COLORS[k]}"></i></div><span class="v">${d.tp || 0}/${d.gt} · ${(r * 100).toFixed(0)}%</span></div>`;
  }).join("");
  const best = S.sweep && S.sweep.best;
  $("#summary").innerHTML = `
    <div class="sumgrid"><div class="stat"><b>${pct(rec)}</b><span>찾은 비율 (${c.tp}/${c.gt})</span></div><div class="stat"><b>${pct(prec)}</b><span>맞은 비율 (${c.tp}/${c.pred})</span></div></div>
    <div class="stats"><div class="stat tp"><b>${c.tp}</b><span>맞힘</span></div><div class="stat ce"><b>${c.class_error}</b><span>종류 틀림</span></div>
      <div class="stat fp"><b>${c.fp}</b><span>오검출</span></div><div class="stat fn"><b>${c.fn}</b><span>놓침</span></div></div>
    ${S.sweep && S.sweep.rows.length ? `<div class="chartbox"><h4>기준별 결과 <small>그래프를 누르면 그 기준 적용</small></h4>${sweepSvg(S.sweep.rows, S.conf, best)}
      <div class="lg"><span style="--c:#16a34a">찾은 비율</span><span style="--c:#2563eb">맞은 비율</span><span style="--c:#4f46e5">F1</span><span style="--c:#e11d74">지금 기준</span></div></div>` : ""}
    <div class="rbars">${bars}</div>
    <p class="help">${s.images}/${s.of}장 · 기준 ${s.conf.toFixed(2)} · IoU 0.5 · <b>박스 개수 기준(mAP 아님)</b>${s.inference_ms ? ` · AI 중앙값 ${s.inference_ms}ms/장` : ""}<br>병해·갈변(작은 반점)은 거의 찾지 못합니다 — 알려진 한계</p>
    <div class="sumbtns">${best ? `<button class="btn small outline" id="btnBest" title="F1 이 가장 높은 기준">${icon("slider")}F1 최고 ${best.conf.toFixed(2)} 적용</button>` : ""}
      <button class="btn small primary" id="btnReport2">${icon("report")}보고서 만들기</button></div>`;
  const svg = $("#summary svg.sw");
  if (svg) svg.addEventListener("click", (e) => { const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * 300; setConf(0.05 + Math.max(0, Math.min(1, (x - 30) / 262)) * 0.9); });
  if ($("#btnBest")) $("#btnBest").onclick = () => setConf(best.conf);
  $("#btnReport2").onclick = openReport;
}
function sweepSvg(rows, cur, best) {
  const W = 300, H = 150, L = 30, R = 8, T = 8, B = 20;
  const X = (c) => L + (c - 0.05) / 0.9 * (W - L - R), Y = (v) => T + (1 - v) * (H - T - B);
  let s = `<svg class="sw" viewBox="0 0 ${W} ${H}">`;
  [0, 0.5, 1].forEach((v) => { s += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e4e7ec"/><text x="${L - 4}" y="${Y(v) + 3}" font-size="9" fill="#98a2b3" text-anchor="end">${v * 100}%</text>`; });
  [0.05, 0.25, 0.5, 0.75, 0.95].forEach((c) => { s += `<text x="${X(c)}" y="${H - 6}" font-size="9" fill="#98a2b3" text-anchor="middle">${c.toFixed(2)}</text>`; });
  s += `<line x1="${X(cur)}" x2="${X(cur)}" y1="${T}" y2="${H - B}" stroke="#e11d74" stroke-dasharray="3 3" stroke-width="1.5"/>`;
  [["recall", "#16a34a", 1.8], ["precision", "#2563eb", 1.8], ["f1", "#4f46e5", 2.6]].forEach(([k, col, w]) => {
    s += `<polyline fill="none" stroke="${col}" stroke-width="${w}" points="${rows.map((r) => `${X(r.conf).toFixed(1)},${Y(r[k]).toFixed(1)}`).join(" ")}"/>`;
  });
  if (best) s += `<circle cx="${X(best.conf)}" cy="${Y(best.f1)}" r="4" fill="#4f46e5"/>`;
  return s + "</svg>";
}
function doneDialog(sec) {
  const s = S.sweep, best = s && s.best;
  modal(`<h2>${icon("check")}Validation ${S.images.length}장 채점 완료</h2>
    <p class="lead">${sec.toFixed(0)}초 걸렸습니다. 이제 확신도 기준을 바꾸면 전체 결과가 바로 다시 계산되고, 결과를 보고서로 만들 수 있습니다.</p>
    <div class="okline">기준 ${S.conf.toFixed(2)} 에서의 결과는 오른쪽 <b>Validation 전체 채점</b> 카드에 있습니다.${best ? ` F1 이 가장 높은 기준은 <b>${best.conf.toFixed(2)}</b> 입니다 (참고용).` : ""}</div>
    <div class="mbtns"><button class="btn" id="mClose">닫기</button><button class="btn outline" id="mErr">${icon("alert")}틀린 사진 보기</button><button class="btn primary" id="mReport">${icon("report")}보고서 만들기</button></div>`);
  $("#mClose").onclick = closeModal; $("#mErr").onclick = () => { closeModal(); setList("err"); nextError(); }; $("#mReport").onclick = openReport;
}

/* ── 보고서 ─────────────────────────────────────────── */
let lastReport = null;
function openReport() {
  const all = S.images.length && [...S.images].every((x) => S.done.has(x.id));
  const nVal = S.images.filter((x) => S.done.has(x.id)).length;
  modal(`<h2>${icon("report")}시연 보고서 만들기</h2>
    <p class="lead">지금까지의 시연 결과를 <b>HTML 한 파일</b>로 만듭니다. 브라우저에서 바로 보고, 저장하거나 인쇄(PDF)할 수 있습니다. 서버에는 저장하지 않습니다.</p>
    ${all ? `<div class="okline">Validation ${S.images.length}장 채점 완료 — 전체 결과 · 기준별 그래프 · Class 별 결과 · 틀린 박스 목록이 들어갑니다.</div>`
          : `<div class="infoline">Validation 전체 채점 전입니다 (${nVal}/${S.images.length}장). 지금 만들면 <b>본 사진만</b> 담깁니다. <button class="btn small primary" id="rRunAll" style="margin-left:6px">${icon("play")}전체 채점 먼저 하기</button></div>`}
    <h4>담을 내용</h4>
    <div class="form">
      <label>확신도 기준</label><div><input type="number" id="rConf" min="0.05" max="0.95" step="0.05" value="${S.conf.toFixed(2)}"> <small>지금 화면의 기준</small></div>
      <label>시연자 (선택)</label><div><input type="text" id="rName" placeholder="예: 3조 손상우"></div>
      <label>본 사진</label><div><small>${S.viewed.length}장 — 시연 중에 연 사진과 그 결과</small></div>
      <label>포함</label><div style="display:flex;flex-direction:column;gap:8px">
        <label class="opt"><input type="checkbox" id="rAll" ${all ? "checked" : ""} ${nVal ? "" : "disabled"}><span>틀린 박스 목록은 Validation 전체로<small>끄면 본 사진에서만 모읍니다</small></span></label>
        <label class="opt"><input type="checkbox" id="rCrops"><span>틀린 박스의 <b>사진 조각</b> 넣기<small>박스 주변을 잘라 넣습니다 (최대 80개)</small></span></label>
        <div class="warnline" id="rWarn" hidden>사진 조각은 <b>회사 제공 사진</b>입니다. 이 보고서는 외부 저장소 · 클라우드 · 메신저에 올리지 말고, Git 에도 올리지 마세요.</div>
      </div>
    </div>
    <div class="mbtns"><button class="btn" id="rCancel">닫기</button><button class="btn outline" id="rPreview">${icon("eye")}미리보기</button>
      <button class="btn outline" id="rPrint">${icon("print")}인쇄 · PDF</button><button class="btn primary" id="rSave">${icon("download")}HTML 저장</button></div>
    <iframe class="preview" id="rFrame" hidden title="보고서 미리보기"></iframe>`, true);
  $("#rCrops").onchange = (e) => ($("#rWarn").hidden = !e.target.checked);
  $("#rCancel").onclick = closeModal;
  if ($("#rRunAll")) $("#rRunAll").onclick = () => { closeModal(); runAll(); };
  $("#rPreview").onclick = () => makeReport("preview");
  $("#rPrint").onclick = () => makeReport("print");
  $("#rSave").onclick = () => makeReport("save");
}
async function makeReport(how) {
  const conf = Math.min(0.95, Math.max(0.05, +$("#rConf").value || S.conf));
  const body = { conf, viewed: S.viewed, crops: $("#rCrops").checked, all: $("#rAll").checked, presenter: $("#rName").value };
  const btn = $(how === "save" ? "#rSave" : how === "print" ? "#rPrint" : "#rPreview"); const old = btn.innerHTML;
  btn.disabled = true; btn.textContent = "만드는 중…";
  try {
    const html = await api("/api/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    lastReport = html;
    const fr = $("#rFrame"); fr.hidden = false; fr.srcdoc = html;
    if (how === "save") {
      const d = new Date(), p = (n) => String(n).padStart(2, "0");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      a.download = `시연보고서_${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${body.crops ? "_사진포함" : ""}.html`;
      a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      toast(`보고서를 저장했습니다${body.crops ? " — <b>사진 조각 포함: 외부 공유 금지</b>" : ""}`);
    }
    if (how === "print") fr.onload = () => { fr.contentWindow.focus(); fr.contentWindow.print(); fr.onload = null; };
    markStep("report");
  } catch (e) { toast("보고서를 만들지 못했습니다: " + esc(e.message), true); }
  btn.disabled = false; btn.innerHTML = old;
}

/* ── 업로드 · 라벨 후보 ─────────────────────────────── */
async function uploadFiles(files) {
  for (const f of files) {
    if (!f.type.startsWith("image/")) { toast(`${esc(f.name)}: 사진이 아닙니다`, true); continue; }
    try {
      const r = await api("/api/upload", { method: "POST", body: f, headers: { "X-Filename": encodeURIComponent(f.name), "Content-Type": "application/octet-stream" } });
      if (r.source === "val") { toast(`${esc(f.name)}: Validation 사진이라 정답과 비교합니다`); setList("all"); select(r.id); continue; }
      S.uploads.unshift({ id: r.id, title: r.title, source: "upload", classes: {} });
      setList("up"); select(r.id);
    } catch (e) { toast(`${esc(f.name)}: ${esc(e.message)}`, true); }
  }
}
function setList(t) { S.list = t; $$("#listSeg button").forEach((b) => b.classList.toggle("on", b.dataset.list === t)); renderGallery(); }
function saveTxt() {
  const r = S.res; if (!r) { toast("먼저 사진을 고르세요", true); return; }
  const lines = r.preds.map((p) => { const [x1, y1, x2, y2] = p.box; return `${p.cls} ${((x1 + x2) / 2).toFixed(6)} ${((y1 + y2) / 2).toFixed(6)} ${(x2 - x1).toFixed(6)} ${(y2 - y1).toFixed(6)}`; });
  const stem = (r.title || r.id).replace(/\.[^.]+$/, ""), a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([lines.join("\n") + (lines.length ? "\n" : "")], { type: "text/plain" }));
  a.download = `${stem}.txt`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  toast(`<b>${esc(stem)}.txt</b> — 라벨 후보 ${lines.length}개 (기준 ${S.conf.toFixed(2)}) · 사람 검수 후 정답으로 확정`);
}

/* ── 모달 ───────────────────────────────────────────── */
function modal(html, wide = false) { $("#modalBody").innerHTML = html; $("#modalBox").classList.toggle("wide", wide); $("#modal").hidden = false; }
function closeModal() { $("#modal").hidden = true; }
function showInfo() {
  const i = S.info; if (!i) return;
  const v = i.metrics.val || {}, t = i.metrics.test || {}, f = (x) => (x == null ? "–" : x.toFixed(3));
  modal(`<h2>${icon("info")}Final Model — ${esc(i.run)}</h2>
    <table><tr><th>Weight</th><td><code>${esc(i.weight)}</code> · sha256 ${esc(i.sha)}</td></tr>
      <tr><th>조건</th><td>YOLO11s · 입력 ${i.imgsz}px · 증강(상하반전 · 밝기) · Dataset ${esc(i.dataset)}</td></tr>
      <tr><th>실행 장치</th><td>${esc(i.device || "–")} · 확신도 ${i.predict_conf} 로 한 번 예측하고 기준은 화면에서 거름</td></tr></table>
    <h4>성능</h4>
    <table><tr><th></th><th>Precision</th><th>Recall</th><th>mAP50</th><th>mAP50-95</th></tr>
      <tr><td>Validation 104장 <small>(선택에 쓴 점수)</small></td><td>${f(v.precision)}</td><td>${f(v.recall)}</td><td>${f(v.map50)}</td><td>${f(v.map50_95)}</td></tr>
      <tr><td><b>Frozen Test ${t.images || ""}장</b> <small>(최종 성능)</small></td><td>${f(t.precision)}</td><td>${f(t.recall)}</td><td>${f(t.map50)}</td><td><b>${f(t.map50_95)}</b></td></tr></table>
    <h4>알려진 한계 — 시연에서 같이 말하기</h4>
    <ul><li><b>병해·갈변(작은 반점)</b>은 거의 찾지 못합니다 (Val Recall 0.13 · Test 0). Train 갈변은 대부분 잎 전체가 변한 큰 조각이라 다른 물체입니다.</li>
      <li>나뭇잎·종이는 Test 에서 오검출이 많습니다 (Precision 0.37).</li>
      <li>정상 김치(이물 없음) 사진이 없어 정상 제품 오검출률은 재지 못했습니다. 평가 사진은 Train 과 같은 날 · 같은 소품입니다.</li></ul>
    <h4>이 프로그램이 지키는 것</h4>
    <ul><li>Frozen Test · Bridge Holdout 사진은 목록에 없고, 같은 이름의 사진을 올려도 거절합니다.</li>
      <li>127.0.0.1 에서만 열리며 올린 사진은 메모리에만 두고 저장하지 않습니다.</li>
      <li>라벨 후보(TXT)는 Auto Label 후보입니다 — 사람이 검수한 뒤에만 정답입니다.</li></ul>`);
}
function showHelp() {
  modal(`<h2>${icon("help")}사용 방법</h2>
    <p class="lead">위의 <b>①~⑥ 버튼</b>을 차례로 누르면 시연 순서대로 진행됩니다. 끝난 단계에는 초록 ✓ 가 붙고, 다음에 할 단계가 반짝입니다.</p>
    <div class="feat">
      <div><b><span class="n">1</span>${icon("photo")}사진 고르기</b><p>왼쪽 목록에서 사진을 누르면 바로 AI 가 예측합니다. 목록 위에서 <b>틀린 사진 · 안 본 사진</b>만 거르거나, 촬영 묶음 · Class 로 거를 수 있습니다.</p></div>
      <div><b><span class="n">2</span>${icon("box")}예측 보기</b><p>AI 가 찾은 이물 박스만 보여 줍니다. 박스 색 = 이물 종류(Class), 숫자 = 확신도.</p></div>
      <div><b><span class="n">3</span>${icon("compare")}정답과 비교</b><p>사람이 그린 정답과 맞춰 <b>맞힘 · 종류 틀림 · 오검출 · 놓침</b>을 표시합니다. 위 왼쪽에 개수가 나옵니다.</p></div>
      <div><b><span class="n">4</span>${icon("slider")}기준 바꿔 보기</b><p>확신도 기준을 0.25 ↔ 0.50 으로 바꿉니다. 낮추면 많이 찾지만 오검출이 늘고, 높이면 반대입니다. 오른쪽 슬라이더로 직접 움직여도 됩니다.</p></div>
      <div><b><span class="n">5</span>${icon("grid")}전체 채점</b><p>Validation 104장을 한 번에 예측해 합칩니다(약 15초). 기준별 그래프 · Class 별 찾은 비율이 나오고, 그래프를 누르면 그 기준이 적용됩니다.</p></div>
      <div><b><span class="n">6</span>${icon("report")}보고서 만들기</b><p>요약 · 기준별 결과 · Class 별 결과 · 본 사진 · 틀린 박스 목록을 HTML 한 파일로 만듭니다. 미리보기 · 저장 · 인쇄(PDF).</p></div>
    </div>
    <h4>사진 위 표시</h4>
    <div class="colorkey"><span><i style="border-color:#475467"></i>예측 박스 (색 = Class)</span><span><i style="border-color:#475467;border-style:dashed"></i>정답 박스</span>
      <span><i style="border-color:${WARN}"></i>종류 틀림</span><span><i style="border-color:${BAD};border-style:dashed"></i>오검출</span><span style="color:${BAD};font-weight:700">✕ 놓친 정답</span></div>
    <h4>그 밖의 기능</h4>
    <ul><li><b>다음 오류</b>: 틀린 것이 있는 다음 사진으로 바로 갑니다.</li>
      <li><b>검출 목록</b>: 박스마다 작은 확대 사진이 붙어 있고, 누르면 사진이 그 박스로 확대됩니다.</li>
      <li><b>Class 숨기기</b>: 사진 오른쪽 아래 범례의 Class 를 누르면 그 Class 박스를 숨깁니다.</li>
      <li><b>라벨 후보 저장</b>: 이 사진의 예측을 YOLO TXT 로 내려받습니다 (Auto Label 후보).</li>
      <li><b>새 사진 올리기</b>: 끌어다 놓으면 예측만 보여 줍니다 (정답이 없으므로).</li></ul>
    <h4>단축키</h4>
    <div class="keysgrid"><span><kbd>←</kbd><kbd>→</kbd></span><span>이전 · 다음 사진</span><span><kbd>E</kbd></span><span>다음 오류</span>
      <span><kbd>1</kbd><kbd>2</kbd><kbd>3</kbd></span><span>예측 · 정답 · 비교</span><span><kbd>L</kbd></span><span>이름표 켜기 · 끄기</span>
      <span><kbd>[</kbd><kbd>]</kbd></span><span>기준 −/+ 0.05</span><span><kbd>+</kbd><kbd>-</kbd><kbd>0</kbd></span><span>확대 · 축소 · 맞춤</span>
      <span><kbd>A</kbd></span><span>전체 채점</span><span><kbd>R</kbd></span><span>보고서 만들기</span>
      <span><kbd>S</kbd></span><span>라벨 후보 저장</span><span><kbd>F</kbd></span><span>사진 전체화면</span>
      <span><kbd>H</kbd> · <kbd>I</kbd></span><span>사용 방법 · 모델 정보</span><span><kbd>Backspace</kbd></span><span>발표로 돌아가기</span></div>`, true);
}
function presentationReturn() {
  const raw = new URLSearchParams(location.search).get("return");
  if (!raw) return null;
  try { const u = new URL(raw); return /^https?:$/.test(u.protocol) && u.hostname === location.hostname ? u : null; } catch { return null; }
}
function notifyPresentation(type) {
  const dest = presentationReturn();
  if (window.parent !== window && dest) window.parent.postMessage({ type }, dest.origin);
}
function goBack() {
  const dest = presentationReturn();
  if (window.parent !== window && dest) { notifyPresentation("g3-demo:close"); return; }
  if (dest) location.href = dest.href;
  else if (document.referrer && /presentation/.test(document.referrer)) history.back();
  else if (S.info && S.info.presentation) location.href = (API_BASE || "") + "/presentation/index.html#16";
  else history.back();
}

/* ── 이벤트 ─────────────────────────────────────────── */
function setConf(v, apply = true) {
  const old = S.conf;
  S.conf = Math.round(Math.min(0.95, Math.max(0.05, v)) * 100) / 100;
  $("#conf").value = S.conf; $("#confVal").textContent = S.conf.toFixed(2);
  $$(".presets button").forEach((b) => b.classList.toggle("on", +b.dataset.c === S.conf));
  if (apply && old !== S.conf) { rejudge(); if (S.res) markStep("conf"); }
}
function setMode(m) {
  S.mode = m; S.hover = -1;
  $$("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.mode === m));
  if (S.res && m === "pred") markStep("pred");
  if (S.res && m === "cmp" && S.res.counts) markStep("cmp");
  renderHud(); draw(); renderSteps();
}
function bindUI() {
  window.addEventListener("resize", () => { resize(); fit(); });
  new ResizeObserver(() => resize()).observe($("#stage"));
  $("#flow").onclick = (e) => { const b = e.target.closest(".step"); if (b) doStep(b.dataset.step); };
  $("#listSeg").onclick = (e) => { const b = e.target.closest("button"); if (b) setList(b.dataset.list); };
  $("#groupChips").onclick = (e) => { const b = e.target.closest(".chip"); if (!b) return; S.group = b.dataset.g; buildFilters(); renderGallery(); };
  $("#classChips").onclick = (e) => { const b = e.target.closest(".chip"); if (!b) return; const c = +b.dataset.c; S.classFilter.has(c) ? S.classFilter.delete(c) : S.classFilter.add(c); buildFilters(); renderGallery(); };
  $("#gallery").onclick = (e) => { const t = e.target.closest(".thumb"); if (t) select(t.dataset.id); };
  $("#modeSeg").onclick = (e) => { const b = e.target.closest("button"); if (b) { ensureImage(); setMode(b.dataset.mode); } };
  $("#btnLabels").onclick = () => { S.labels = !S.labels; $("#btnLabels").classList.toggle("on", S.labels); draw(); };
  $("#btnLabels").classList.add("on");
  $("#conf").oninput = (e) => setConf(+e.target.value);
  $(".presets").onclick = (e) => { const b = e.target.closest("button"); if (b) setConf(+b.dataset.c); };
  $("#btnPrev").onclick = () => step(-1); $("#btnNext").onclick = () => step(1); $("#btnNextErr").onclick = nextError;
  const center = () => { const r = $("#stage").getBoundingClientRect(); return [r.width / 2, r.height / 2]; };
  $("#btnZoomIn").onclick = () => zoomAt(1.4, ...center()); $("#btnZoomOut").onclick = () => zoomAt(1 / 1.4, ...center());
  $("#btnFit").onclick = fit;
  $("#btnFull").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : $("#viewer").requestFullscreen());
  $("#btnTxt").onclick = saveTxt; $("#btnAll").onclick = runAll;
  $("#btnInfo").onclick = showInfo; $("#btnHelp").onclick = showHelp; $("#btnHelp2").onclick = showHelp; $("#btnBack").onclick = goBack;
  $("#btnReport").onclick = openReport;
  $("#btnStart").onclick = () => doStep("pick"); $("#btnUpload2").onclick = () => $("#fileInput").click();
  $("#modalX").onclick = closeModal; $("#modal").onclick = (e) => { if (e.target.id === "modal") closeModal(); };
  $("#legend").addEventListener("click", (e) => { const c = e.target.closest(".cls"); if (!c) return; const k = +c.dataset.c; S.hidden.has(k) ? S.hidden.delete(k) : S.hidden.add(k); renderHud(); draw(); });
  $("#dets").addEventListener("mousemove", (e) => { const li = e.target.closest("li[data-n]"); if (li) setHover(+li.dataset.n); });
  $("#dets").addEventListener("mouseleave", () => setHover(-1));
  $("#dets").onclick = (e) => { const li = e.target.closest("li[data-n]"); if (!li) return; const d = detRows()[+li.dataset.n]; if (d) { if (S.mode === "gt") setMode("cmp"); S.hidden.delete(d.cls); zoomToBox(d.box); } };

  const stage = $("#stage"); let drag = null;
  stage.addEventListener("wheel", (e) => { if (!S.img) return; e.preventDefault(); const r = stage.getBoundingClientRect(); zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - r.left, e.clientY - r.top); }, { passive: false });
  stage.addEventListener("mousedown", (e) => { if (e.target.closest(".legend,.empty-card")) return; drag = { x: e.clientX, y: e.clientY, vx: S.view.x, vy: S.view.y }; stage.classList.add("drag"); });
  window.addEventListener("mouseup", () => { drag = null; stage.classList.remove("drag"); });
  stage.addEventListener("mousemove", (e) => {
    const r = stage.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    if (drag) { S.view.x = drag.vx + e.clientX - drag.x; S.view.y = drag.vy + e.clientY - drag.y; draw(); return; }
    if (S.img && S.res && !e.target.closest(".legend")) setHover(hitTest(mx, my), mx, my);
  });
  stage.addEventListener("mouseleave", () => setHover(-1));
  stage.addEventListener("dblclick", (e) => { if (!e.target.closest(".legend")) fit(); });
  const over = (on) => (e) => { e.preventDefault(); stage.classList.toggle("over", on); $("#drop").classList.toggle("over", on); };
  [stage, $("#drop")].forEach((el) => { el.addEventListener("dragover", over(true)); el.addEventListener("dragleave", over(false)); el.addEventListener("drop", (e) => { over(false)(e); uploadFiles([...e.dataTransfer.files]); }); });
  $("#fileInput").onchange = (e) => { uploadFiles([...e.target.files]); e.target.value = ""; };

  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && !["range", "checkbox"].includes(e.target.type)) return;
    if (!$("#modal").hidden) { if (e.key === "Escape") closeModal(); return; }
    if (e.key === "Escape" && window.parent !== window) { e.preventDefault(); goBack(); return; }
    const k = e.key.toLowerCase();
    if (e.key === "ArrowRight") { e.preventDefault(); step(1); } else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (k === "1") { ensureImage(); setMode("pred"); } else if (k === "2") { ensureImage(); setMode("gt"); } else if (k === "3") { ensureImage(); setMode("cmp"); }
    else if (k === "l") $("#btnLabels").click(); else if (k === "e") nextError();
    else if (k === "[") setConf(S.conf - 0.05); else if (k === "]") setConf(S.conf + 0.05);
    else if (k === "+" || k === "=") zoomAt(1.4, ...center()); else if (k === "-") zoomAt(1 / 1.4, ...center()); else if (k === "0") fit();
    else if (k === "f") $("#btnFull").click(); else if (k === "s") saveTxt(); else if (k === "a") runAll(); else if (k === "r") openReport();
    else if (k === "i") showInfo(); else if (k === "h" || k === "?") showHelp();
    else if (e.key === "Backspace") { e.preventDefault(); goBack(); }
  });
}

boot();
