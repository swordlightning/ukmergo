"""Chain printed stop departures (data/raw) into trips along the patterns in
patterns.py. Prints a report of everything that did not fit cleanly."""
import os, sys, json, statistics
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from parse_raw import load_all
from patterns import PATTERNS, PATTERN_DAYS, AS_FROM_VYTAUTO_NOTE

TOL = 2          # minutes a stop time may differ from the typical running time
MAX_SKIP = 3     # stops a trip may skip between two printed times
MAX_OFFSET = 45  # longest running time considered between two stops of a pattern


AFTER_AS = {'ligonine-link-centro', 'kudirkos-link-centro', 'autoservisas', 'as-vytauto-g-link-dukstynos',
            'sodai-link-dukstynos', 'dukstynos-kaimas-link-dukstynos', 'zaliasis-vienkiemis'}


def j_after_as_forbidden(trip, key):
    """A trip whose footnote says it only runs to the bus station ends there."""
    ends_at_as = any('iki autobusų stoties' in d['note'].lower() for _, d in trip)
    return ends_at_as and key.partition('|')[0] in AFTER_AS


def key_match(dep, key):
    f, _, hs = key.partition('|')
    return dep['file'] == f and (not hs or hs in dep['headsign'])


def build(corrections=None, forced=None, drop_mark=None):
    deps = load_all()
    for i, d in enumerate(deps):
        d['id'] = i
    corrections = corrections or {}
    for d in deps:
        c = corrections.get((d['file'], d['route'], d['day'], d['min']))
        if c is not None:
            d['printed'] = d['min']
            d['min'] = c
    for d in deps:
        if drop_mark and (d['file'], d['route'], d['day'], d['min']) in drop_mark:
            d['mark'], d['note'] = '', ''
    forced = forced or {}
    # AS main sign: entries leaving from the Vytauto g. stop duplicate that sign
    skipped = [d for d in deps if d['file'] == 'as' and AS_FROM_VYTAUTO_NOTE in d['note']]
    skip_ids = {d['id'] for d in skipped}
    used = set(skip_ids)
    trips, warnings = [], []
    days = sorted({d['day'] for d in deps})
    # pass 1: trips that start at the first stop of a pattern; pass 2: the rest
    for first_only in (True, False):
      for route, pats in PATTERNS.items():
        for pname, keys in pats:
            for day in days:
                if day not in PATTERN_DAYS.get((route, pname), days):
                    continue
                pos = []
                for k in keys:
                    pos.append(sorted((d for d in deps if d['route'] == route and d['day'] == day
                                       and key_match(d, k)), key=lambda d: d['min']))
                n = len(keys)
                # typical running time between positions i<j: the offset that lines up
                # the most printed departures (computed on departures not yet used)
                def best_offset(i, j, only_unused):
                    A = [a['min'] for a in pos[i] if not only_unused or a['id'] not in used]
                    B = [b['min'] for b in pos[j] if not only_unused or b['id'] not in used]
                    best, best_n = None, 0
                    for e in range(0, MAX_OFFSET + 1):
                        c = sum(1 for a in A if any(abs(b - a - e) <= 1 for b in B))
                        if c > best_n:
                            best, best_n = e, c
                    return best
                E = {}
                for i in range(n):
                    for j in range(i + 1, min(n, i + MAX_SKIP + 2)):
                        e = best_offset(i, j, True)
                        if e is None:
                            e = best_offset(i, j, False)
                        if e is not None:
                            E[i, j] = e
                for i in range(1 if first_only else n):
                    for a in pos[i]:
                        if a['id'] in used:
                            continue
                        trip, ci, ct = [(i, a)], i, a['min']
                        for j in range(i + 1, n):
                            f = forced.get((route, day, trip[-1][1]['file'], ct))
                            if f:
                                # a forced link: skip ahead to exactly that stop and time
                                if f[0] == keys[j].partition('|')[0]:
                                    cands = [b for b in pos[j] if b['min'] == f[1] and b['id'] not in used]
                                    if cands:
                                        trip.append((j, cands[0]))
                                        ci, ct = j, cands[0]['min']
                                continue
                            if j - ci - 1 > MAX_SKIP:
                                break
                            if (ci, j) not in E:
                                continue
                            if j_after_as_forbidden(trip, keys[j]):
                                break
                            exp = ct + E[ci, j]
                            cands = [b for b in pos[j] if b['id'] not in used and b['id'] not in {x[1]['id'] for x in trip}
                                     and abs(b['min'] - exp) <= TOL and b['min'] >= ct]
                            if cands:
                                b = min(cands, key=lambda b: abs(b['min'] - exp))
                                trip.append((j, b))
                                ci, ct = j, b['min']
                        if len(trip) >= 2:
                            for _, d in trip:
                                used.add(d['id'])
                            trips.append({'route': route, 'pattern': pname, 'day': day,
                                          'stops': [(keys[j].partition('|')[0], d) for j, d in trip]})
    orphans = [d for d in deps if d['id'] not in used]
    return deps, trips, orphans, skipped


def fmt(m):
    return f'{m // 60}:{m % 60:02d}'


if __name__ == '__main__':
    deps, trips, orphans, skipped = build()
    print(f'{len(deps)} printed departures, {len(skipped)} AS duplicates of Vytauto g., '
          f'{len(trips)} trips, {len(orphans)} not placed in any trip')
    for o in sorted(orphans, key=lambda d: (d['route'], d['day'], d['file'], d['min'])):
        print(f"  ORPHAN r{o['route']} {o['day']:8s} {o['file']:38s} {fmt(o['min'])}{o['mark']}  [{o['headsign']}]")
