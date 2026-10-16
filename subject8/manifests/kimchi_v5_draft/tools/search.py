"""평가 split 3개를 촬영 묶음 단위로 고를 때, Train 을 최대로 하는 조합 탐색.
G00 은 각 평가 split 에 6장(c6 30박스) 고정, G09·G17·G00나머지는 Train 고정."""
import itertools
S = {  # c0,c1,c2,c3,c5, imgs
 "G01": (0,5,0,0,0,1), "G02": (0,50,0,0,0,10), "G03": (17,147,19,10,0,39), "G04": (15,45,185,5,0,50),
 "G05": (7,214,8,11,3,48), "G06": (12,333,28,11,0,76), "G07": (10,90,21,13,3,26), "G08": (0,127,0,0,0,25),
 "G10": (6,46,248,10,3,50), "G11": (0,127,0,0,7,25), "G12": (198,154,33,19,6,75), "G13": (185,51,15,5,12,50),
 "G14": (13,50,179,10,13,50), "G15": (20,45,10,174,1,50), "G16": (175,58,14,5,1,50)}
names = list(S)
def run(floor, floor5, must_train=("G16",)):
    cand = [n for n in names if n not in must_train]
    feas = []
    for r in range(1, 5):
        for c in itertools.combinations(cand, r):
            t = [sum(S[n][k] for n in c) for k in range(6)]
            if min(t[:4]) >= floor and t[4] >= floor5:
                feas.append((t[5], frozenset(c)))
    # 최소 조합만
    feas = [f for f in feas if not any(g[1] < f[1] for g in feas)]
    best = []
    for a, b, c in itertools.combinations(feas, 3):
        if a[1] & b[1] or a[1] & c[1] or b[1] & c[1]:
            continue
        best.append((a[0] + b[0] + c[0], a, b, c))
    best.sort(key=lambda x: x[0])
    print(f"\n== floor {floor}, c5 floor {floor5}")
    for tot, *sp in best[:6]:
        print(f"train {900 - tot - 18}: " + " | ".join(f"{'+'.join(sorted(s[1]))}({s[0]+6})" for s in sorted(sp, key=lambda s: s[0])))
for f5 in (15, 12, 10):
    run(15, f5)
run(10, 10)
