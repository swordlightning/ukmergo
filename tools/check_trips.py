"""Flag trip segments whose running time differs from the usual time between
the same two stops (likely printing errors), plus very short trips."""
import os, sys, statistics
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from build_trips import build, fmt
from corrections import CORRECTIONS, FORCED_LINKS, DROP_MARK


def check(trips):
    seg = defaultdict(list)
    for t in trips:
        st = t['stops']
        for (a, da), (b, db) in zip(st, st[1:]):
            seg[a, b].append(db['min'] - da['min'])
    typical = {k: statistics.median_low(v) for k, v in seg.items()}
    issues = []
    for t in trips:
        st = t['stops']
        for (a, da), (b, db) in zip(st, st[1:]):
            d, e = db['min'] - da['min'], typical[a, b]
            if abs(d - e) >= 2 and len(seg[a, b]) >= 3:
                issues.append((t, a, da, b, db, d, e))
    return typical, issues


if __name__ == '__main__':
    deps, trips, orphans, _ = build(CORRECTIONS, FORCED_LINKS, DROP_MARK)
    print(f'{len(trips)} trips, orphans:', ', '.join(f"r{o['route']} {o['day']} {o['file']} {fmt(o['min'])}" for o in orphans))
    typical, issues = check(trips)
    for t, a, da, b, db, d, e in issues:
        print(f"r{t['route']} {t['day']:8s} {t['pattern']:12s} {a} {fmt(da['min'])} -> {b} {fmt(db['min'])}"
              f"  took {d} min, usually {e}  (trip starts {t['stops'][0][0]} {fmt(t['stops'][0][1]['min'])})")
    short = [t for t in trips if len(t['stops']) <= 3]
    print(f'\n{len(issues)} unusual segments, {len(short)} trips with <=3 stops:')
    for t in short:
        print(f"  r{t['route']} {t['day']} {t['pattern']}: " + ', '.join(f'{k} {fmt(d["min"])}' for k, d in t['stops']))
