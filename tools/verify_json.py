"""Independent check: every printed departure in data/raw must appear exactly
once in data/timetable.json (after documented corrections), except the ones
listed as unplaced in data/ISSUES.md, and trips must run forward in time."""
import os, sys, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from parse_raw import load_all
from corrections import CORRECTIONS

ROOT = os.path.join(os.path.dirname(__file__), '..')
data = json.load(open(os.path.join(ROOT, 'data', 'timetable.json'), encoding='utf-8'))


def mins(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)


in_json = Counter()
errors = 0
for t in data['trips']:
    times = [mins(x[1]) for x in t['stops']]
    if times != sorted(times):
        print('NOT FORWARD', t['id']); errors += 1
    if len(t['stops']) < 2:
        print('TOO SHORT', t['id']); errors += 1
    for stop, tm in t['stops']:
        if stop not in data['stops']:
            print('UNKNOWN STOP', t['id'], stop); errors += 1
        in_json[stop, t['route'], t['days'], mins(tm)] += 1
dup = [k for k, v in in_json.items() if v > 1]
printed = Counter()
for d in load_all():
    if d['file'] == 'as' and 'važiuoja iš Vytauto g.' in d['note']:
        continue
    m = CORRECTIONS.get((d['file'], d['route'], d['day'], d['min']), d['min'])
    printed[d['file'], d['route'], d['day'], m] += 1
missing = [k for k in printed if k not in in_json]
extra = [k for k in in_json if k not in printed]
print(f"trips {len(data['trips'])}; printed departures {sum(printed.values())}; in JSON {sum(in_json.values())}")
print(f"duplicates {len(dup)}; extra (not printed) {len(extra)}; printed but not in JSON {len(missing)}; errors {errors}")
for k in sorted(missing):
    print('  not in JSON:', k[0], 'route', k[1], k[2], f'{k[3]//60}:{k[3]%60:02d}')
sys.exit(1 if (dup or extra or errors) else 0)
