# `src/bbox/bbox_diff.py`

> 원본(RAW) BBox 와 지금 BBox 를 비교해 **그대로 / 수정 / 추가 / 삭제** 로 나눈다. 화면의 `RAW 와 비교(Diff)` 와 QA 요약의 BBox 변화 집계에 쓰인다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/bbox/bbox_diff.py)

## 역할

"같은 BBox 인가"를 두 단계로 판단한다.

1. **그대로**: Class 가 같고 네 좌표가 모두 `tol`(0.5px) 이내 → 저장·불러오기 반올림 오차는 무시
2. **수정**: 남은 것들 중 겹침(IoU)이 `iou_min`(0.3) 이상인 쌍을 **IoU 가 큰 쌍부터** 짝지음. Class 가 달라도 짝이 된다 (Class 변경도 "수정")
3. 짝이 없는 지금 BBox → **추가**, 짝이 없는 원본 BBox → **삭제**

## 주요 구성요소

| 이름 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `DIFF_TOL_PX` | – | 0.5 | "그대로" 허용 오차 (원본 픽셀) |
| `DIFF_IOU_MIN` | – | 0.3 | "수정" 으로 짝지을 최소 IoU |
| `box_iou(a, b)` | BBox 2개 | 0~1 | 픽셀 BBox 겹침 비율 |
| `same_box(a, b, tol)` | BBox 2개 | `bool` | Class 같고 좌표 차이 ≤ tol |
| `diff_boxes(raw, current, tol, iou_min)` | 원본 목록, 지금 목록 | dict | `unchanged`(지금 번호), `modified`([(원본, 지금)]), `added`(지금 번호), `deleted`(원본 번호) |
| `diff_summary(result)` | 위 결과 | `str` | `추가 1 · 수정 1 · 삭제 1 · 그대로 4` |

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md) (Diff 표시), [`tools/qa_summary`](../../tools/qa_summary.md) (BBox 변화 집계), [`tests/test_bbox_diff`](../../tests/test_bbox_diff.md)

## 사용 예

```python
from src.bbox.bbox_diff import diff_boxes, diff_summary

r = diff_boxes(raw_boxes, boxes)
print(diff_summary(r))          # 추가 0 · 수정 1 · 삭제 0 · 그대로 3
for ri, ci in r["modified"]:
    ...                          # 원래 위치(raw[ri])는 회색 점선, 지금 위치(boxes[ci])는 주황
```

## 주의사항

- 결과는 **번호(index)** 만 담는다. 좌표가 필요하면 원래 목록에서 꺼낸다.
- ①단계는 앞에서부터 처음 맞는 원본과 짝짓는(greedy) 방식이다. 완전히 같은 BBox 가 중복으로 있어도 개수만큼만 "그대로"가 된다.
- 크게 옮긴 BBox(IoU < 0.3)는 "수정"이 아니라 "삭제 1 + 추가 1"로 나온다.
