"""원본(RAW) BBox 와 지금 BBox 를 비교한다 (화면과 무관한 순수 함수).

BBox 는 {"cls": 2, "x1":.., "y1":.., "x2":.., "y2":..} (원본 이미지 픽셀).

비교 결과 4가지:
    unchanged : 원본과 같음                              (지금 BBox 번호)
    modified  : 원본과 같은 BBox 인데 위치·크기·Class 가 바뀜   [(원본 번호, 지금 번호), ...]
    added     : 원본에 없던 새 BBox                        (지금 BBox 번호)
    deleted   : 원본에는 있었는데 지워짐                     (원본 번호)

'같은 BBox 인가'는 두 단계로 판단한다.
    ① 모든 값이 거의 같으면(tol 픽셀 이내, Class 같음) 그대로
    ② 남은 것들 중 겹침(IoU)이 iou_min 이상이면 '수정'으로 짝지음 (겹침이 큰 쌍부터)
"""

DIFF_TOL_PX = 0.5      # 이 정도 차이는 같은 BBox 로 본다 (저장·불러오기 반올림 오차)
DIFF_IOU_MIN = 0.3     # 이 이상 겹치면 같은 BBox 를 고친 것으로 본다


def box_iou(a, b):
    """두 BBox 의 겹침 비율 (0~1)."""
    iw = min(a["x2"], b["x2"]) - max(a["x1"], b["x1"])
    ih = min(a["y2"], b["y2"]) - max(a["y1"], b["y1"])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    area_a = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    area_b = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def same_box(a, b, tol=DIFF_TOL_PX):
    return a["cls"] == b["cls"] and all(abs(a[k] - b[k]) <= tol for k in ("x1", "y1", "x2", "y2"))


def diff_boxes(raw, current, tol=DIFF_TOL_PX, iou_min=DIFF_IOU_MIN):
    """raw(원본 BBox 목록) 와 current(지금 BBox 목록) 를 비교한다 → {"unchanged","modified","added","deleted"}"""
    raw_left = set(range(len(raw)))
    cur_left = set(range(len(current)))
    unchanged = []

    for ci in sorted(cur_left):                                   # ① 거의 똑같은 것끼리 짝짓기
        for ri in sorted(raw_left):
            if same_box(raw[ri], current[ci], tol):
                unchanged.append(ci)
                raw_left.discard(ri)
                cur_left.discard(ci)
                break

    pairs = sorted(((box_iou(raw[ri], current[ci]), ri, ci) for ri in raw_left for ci in cur_left),
                   key=lambda t: (-t[0], t[1], t[2]))
    modified = []
    for iou, ri, ci in pairs:                                     # ② 겹침이 큰 쌍부터 '수정'으로 짝짓기
        if iou < iou_min:
            break
        if ri in raw_left and ci in cur_left:
            modified.append((ri, ci))
            raw_left.discard(ri)
            cur_left.discard(ci)

    return {"unchanged": sorted(unchanged), "modified": sorted(modified, key=lambda t: t[1]),
            "added": sorted(cur_left), "deleted": sorted(raw_left)}


def diff_summary(result):
    """사람이 읽는 한 줄 요약."""
    return (f"추가 {len(result['added'])} · 수정 {len(result['modified'])} · "
            f"삭제 {len(result['deleted'])} · 그대로 {len(result['unchanged'])}")
