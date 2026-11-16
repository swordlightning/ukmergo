"""Build data/timetable.json from the hand transcriptions in data/raw.

    python3 tools/make_json.py
"""
import os, sys, json, re, math, datetime
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from build_trips import build
from corrections import CORRECTIONS, FORCED_LINKS, DROP_MARK

ROOT = os.path.join(os.path.dirname(__file__), '..')
SIGN_BASE = 'https://www.ukmergesautobusai.lt/miesto-marsrutu-failai/'

DEFAULT_HEADSIGN = {
    ('1', 'narbuto'): 'Autobusų stotis', ('1', 'pienine'): 'Autobusų stotis',
    ('1', 'dukstyna'): 'Pieninė', ('1', 'as'): 'Pieninė',
    ('2', 'pasile'): 'Biofabrikas', ('2', 'kokliu'): 'Biofabrikas', ('2', 'deltuva'): 'Koklių f.',
    ('2', 'weekend-east'): 'Pašilė',
    ('3', 'to-zaliasis'): 'Žaliasis vienkiemis', ('3', 'to-turgus'): 'Turgus',
    ('4', 'out-workday'): 'Pašilė', ('4', 'out-weekend'): 'Pašilė', ('4', 'in-varine'): 'Autobusų stotis',
    ('4', 'in'): 'Autobusų stotis',
    ('5', 'to-pasile'): 'Pašilė', ('5', 'to-narbuto'): 'Narbuto',
    ('6', 'out-workday'): 'Žaliasis vienkiemis', ('6', 'out-weekend'): 'Žaliasis vienkiemis',
    ('6', 'in'): 'Autobusų stotis',
    ('7', 'narbuto'): 'Narbuto',
}
# footnote text -> destination it implies (None = only a remark about the route)
NOTE_DEST = [
    (r'iki dukstynos', 'Dukstyna'), (r'iki deltuvos', 'Deltuva'), (r'iki varinės', 'Varinė'),
    (r'iki koklių', 'Koklių'), (r'iki žiedo', 'Žiedo g.'), (r'iki b(io)?fabriko', 'Biofabrikas'),
    (r'iki autobusų stoties', 'Autobusų stotis'), (r'iki pašilės|į pašilę', 'Pašilė'),
]
VIA_NOTES = [(r'užsuka į dukstyną|pro dukstyną', 'užsuka į Dukstyną'), (r'užsuka į linų', 'užsuka į Linų g.'),
             (r'nuo varinės', 'važiuoja nuo Varinės')]

ROUTES = {
    '1': 'Autobusų stotis (Dukstyna) – Pieninė',
    '2': 'Biofabrikas – Autobusų stotis – Koklių f. (Deltuva, Pašilė)',
    '3': 'Turgus – Žaliasis vienkiemis (tik šeštadieniais)',
    '4': 'Autobusų stotis – Pašilė (Varinė)',
    '5': 'Narbuto – Autobusų stotis – Pašilė (Linų g.)',
    '6': 'Autobusų stotis – Žaliasis vienkiemis',
    '7': 'Autobusų stotis – Žaliasis vienkiemis – Narbuto',
}

DIRECTION_WORDS = {'link-centro': 'į centrą', 'link-as': 'į autobusų stotį', 'link-pienines': 'į Pieninę',
                   'link-dukstynos': 'į Dukstyną', 'link-deltuvos': 'į Deltuvą', 'link-zaliojo-vnk': 'į Žaliąjį vnk.',
                   '9link-zaliojo-vnk': 'į Žaliąjį vnk.', 'link-pasiles': 'į Pašilę', 'link-narbuto': 'į Narbuto',
                   'link-gamyklu': 'į Gamyklų g.', 'link-pivonijos': 'į Pivonijos g.',
                   'link-biofabriko': 'į Biofabriką'}

# Lithuanian public holidays (buses run the weekend timetable). Verify each year.
HOLIDAYS = ['2026-12-24', '2026-12-25', '2026-12-26', '2027-01-01', '2027-02-16', '2027-03-11',
            '2027-03-28', '2027-03-29', '2027-05-01', '2027-06-24', '2027-07-06', '2027-08-15',
            '2027-11-01', '2027-11-02', '2027-12-24', '2027-12-25', '2027-12-26']


def hhmm(m):
    return f'{m // 60:02d}:{m % 60:02d}'


def station_id(file):
    base = re.sub(r'-(9?link-.*|is-varines|pries-biofabrika.*|uz-biofabriko.*|dariaus-ir-gireno|vytauto-g.*)$', '', file)
    return {'dukstyvos-kaimas': 'dukstynos-kaimas'}.get(base, base)


def main():
    deps, trips, orphans, skipped = build(CORRECTIONS, FORCED_LINKS, DROP_MARK)
    gtfs = json.load(open(os.path.join(ROOT, 'data', 'stops_from_gtfs.json'), encoding='utf-8'))
    sign_urls = {}
    files_html = os.environ.get('SIGN_PAGE')  # optional: local copy of the "spausdinimui" page
    if files_html and os.path.exists(files_html):
        for u in re.findall(r'"(/uploads/ECB/[^"]+\.jpg)"', open(files_html, encoding='utf-8', errors='replace').read()):
            sign_urls[re.sub(r'_\d+\.jpg$', '', os.path.basename(u))] = 'https://www.ukmergesautobusai.lt' + u

    # stops (one per printed sign) and stations (one per stop name)
    stops, stations = {}, {}
    for d in deps:
        f = d['file']
        if f in stops:
            continue
        name = d['stop'].rstrip('*')
        m = re.search(r'(9?link-[a-z-]+)$', f)
        stops[f] = {'name': name, 'station': station_id(f),
                    'towards': DIRECTION_WORDS.get(m.group(1)) if m else None,
                    'sign': sign_urls.get(f, SIGN_BASE)}
    # coordinates: only exact name matches against the official GTFS export, station level
    alias = {'Autobusų stotis': ['Autobusų stotis', 'Ukmergės autobusų stotis'], 'Senasis paštas': ['Senas paštas'],
             'Anykščių': ['Anykščių g.'], 'Pieninė': ['Ukmergės pieninė'], 'Linų': ['Linų g.'],
             'Kęstučio a.': ['Kęstučio a.', 'Kęstučio aikštė']}
    for f, s in stops.items():
        st = stations.setdefault(s['station'], {'name': re.sub(r' \(.*\)$', '', s['name']), 'stops': []})
        st['stops'].append(f)
    for sid, st in stations.items():
        names = alias.get(st['name'], [st['name']])
        pts = [(g['lat'], g['lon']) for g in gtfs if g['name'] in names]
        spread = max((math.dist((a[0] * 111320, a[1] * 63600), (b[0] * 111320, b[1] * 63600))
                      for a in pts for b in pts), default=0)
        if pts and spread <= 150:
            st['lat'] = round(sum(p[0] for p in pts) / len(pts), 6)
            st['lon'] = round(sum(p[1] for p in pts) / len(pts), 6)
            st['coordSource'] = 'GTFS (visimarsrutai.lt) name match – verify on the map'
        else:
            st['lat'] = st['lon'] = None
            st['coordSource'] = 'missing' if not pts else f'ambiguous ({len(pts)} GTFS points {spread:.0f} m apart)'
        st['stops'].sort()

    out_trips = []
    counter = Counter()
    for t in sorted(trips, key=lambda t: (int(t['route']), t['day'], t['stops'][0][1]['min'], t['pattern'])):
        notes = [d['note'].lower() for _, d in t['stops'] if d['note']]
        dests = Counter()
        via = set()
        for n in notes:
            for rx, dest in NOTE_DEST:
                if re.search(rx, n):
                    dests[dest] += 1
            for rx, v in VIA_NOTES:
                if re.search(rx, n):
                    via.add(v)
        headsign = DEFAULT_HEADSIGN[t['route'], t['pattern']]
        if dests:
            top, cnt = dests.most_common(1)[0]
            if cnt * 2 > sum(dests.values()):  # clear majority of the trip's footnotes
                headsign = top
        counter[t['route'], t['day']] += 1
        tid = f"{t['route']}-{t['day'][:2]}-{counter[t['route'], t['day']]:03d}"
        trip = {'id': tid, 'route': t['route'], 'days': t['day'], 'headsign': headsign,
                'stops': [[k, hhmm(d['min'])] for k, d in t['stops']]}
        if via:
            trip['via'] = sorted(via)
        fixed = [k for k, d in t['stops'] if 'printed' in d]
        if fixed:
            trip['corrected'] = {k: hhmm(d['printed']) for k, d in t['stops'] if 'printed' in d}
        out_trips.append(trip)

    data = {
        'meta': {
            'name': 'UkmerGO – Ukmergės miesto autobusų tvarkaraštis',
            'source': 'https://www.ukmergesautobusai.lt/miesto-marsrutu-failai/ (stop signs, UAB Ukmergės autobusų parkas)',
            'validFrom': '2026-10-19',
            'generated': datetime.date.today().isoformat(),
            'times': 'HH:MM local time (Europe/Vilnius); 24:xx = after midnight of the same service day',
            'tripStops': 'Only times printed on stop signs. The final stop (terminus arrival) is often not printed.',
            'corrected': 'Trips with "corrected" contain a time fixed from an obvious misprint: {stop: printed time}. See data/ISSUES.md.',
        },
        'calendar': {
            'workday': 'Monday–Friday, except public holidays',
            'weekend': 'Saturday, Sunday and public holidays',
            'saturday': 'Saturday (route 3 only)',
            'holidays': HOLIDAYS,
            'holidaysNote': 'Lithuanian public holidays, to be verified each year.',
        },
        'routes': {r: {'name': n} for r, n in ROUTES.items()},
        'stations': dict(sorted(stations.items())),
        'stops': dict(sorted(stops.items())),
        'trips': out_trips,
    }
    with open(os.path.join(ROOT, 'data', 'timetable.json'), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"{len(out_trips)} trips, {len(stops)} stops, {len(stations)} stations, "
          f"{sum(1 for s in stations.values() if s['lat'])} stations with coordinates, {len(orphans)} unplaced departures")
    return data, orphans


if __name__ == '__main__':
    main()
