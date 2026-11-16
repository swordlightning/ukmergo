"""Parse data/raw/*.txt stop timetables into a flat list of departures.

Each departure: stop file, stop name, route, headsign, daytype, minutes since
midnight, footnote mark ('' / '*' / '**' / '***'), footnote text.
"""
import os, re, json, sys

RAW = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
DAYTYPES = {'workday', 'weekend', 'saturday', 'sunday'}


def parse_file(path):
    stop = None
    blocks = []          # list of dict(route, headsign, rows{daytype:[(min,mark)]}, notes{mark:text})
    cur = None
    for raw in open(path, encoding='utf-8'):
        line = raw.rstrip('\n')
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith('stop:'):
            stop = s[5:].strip()
        elif s.startswith('source:'):
            pass
        elif s.startswith('route '):
            m = re.match(r'route (\d+) \| (.+)$', s)
            if not m:
                raise ValueError(f'{path}: bad route line {s!r}')
            cur = {'route': m.group(1), 'headsign': m.group(2).strip(), 'rows': {}, 'notes': {}}
            blocks.append(cur)
        elif s.startswith('note '):
            m = re.match(r'note (\*+): (.*)$', s)
            if not m:
                raise ValueError(f'{path}: bad note line {s!r}')
            cur['notes'][m.group(1)] = m.group(2).strip()
        elif s.startswith('remark:'):
            cur.setdefault('remarks', []).append(s[7:].strip())
        else:
            m = re.match(r'(\w+): (.*)$', s)
            if not m or m.group(1) not in DAYTYPES:
                raise ValueError(f'{path}: bad line {s!r}')
            times = []
            for tok in m.group(2).split():
                t = re.fullmatch(r'(\d{1,2}):(\d{2})(\**)', tok)
                if not t:
                    raise ValueError(f'{path}: bad time {tok!r}')
                h, mi = int(t.group(1)), int(t.group(2))
                if mi > 59 or h > 24:
                    raise ValueError(f'{path}: bad time {tok!r}')
                times.append((h * 60 + mi, t.group(3)))
            mins = [x[0] for x in times]
            if mins != sorted(mins):
                raise ValueError(f'{path}: times not sorted in {s!r}')
            if len(set(mins)) != len(mins):
                raise ValueError(f'{path}: duplicate time in {s!r}')
            cur['rows'][m.group(1)] = times
    # every mark used must have a note (unless remark explains)
    for b in blocks:
        used = {mk for rows in b['rows'].values() for _, mk in rows if mk}
        missing = used - set(b['notes'])
        if missing:
            print(f'WARN {os.path.basename(path)} route {b["route"]}: marks without note {missing}', file=sys.stderr)
    return stop, blocks


def load_all():
    out = []
    for f in sorted(os.listdir(RAW)):
        if not f.endswith('.txt'):
            continue
        stop, blocks = parse_file(os.path.join(RAW, f))
        for b in blocks:
            for dt, rows in b['rows'].items():
                for mins, mark in rows:
                    out.append({'file': f[:-4], 'stop': stop, 'route': b['route'], 'headsign': b['headsign'],
                                'day': dt, 'min': mins, 'mark': mark, 'note': b['notes'].get(mark, '') if mark else ''})
    return out


if __name__ == '__main__':
    deps = load_all()
    print(len(deps), 'departures')
    from collections import Counter
    print(Counter((d['route'], d['day']) for d in deps))
