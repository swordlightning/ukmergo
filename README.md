# UkmerGO

A simple trip planner for Ukmergė (Lithuania): enter an address or use your
location, and get the fastest way to your destination by walking, by city bus,
or by both.

Status: **bus timetable data is ready**. The web app itself has not been
started yet.

## Data

| File | What it is |
|---|---|
| `data/raw/*.txt` | Hand transcription of all 80 stop timetable signs (valid from 2026-10-19), one file per sign, exactly as printed. Format: `data/raw/FORMAT.md` |
| `data/timetable.json` | Generated: routes, stops, stations, calendar and **291 trips** with a time at every stop. This is what the app reads. |
| `data/ISSUES.md` | Misprints found in the official signs, what was corrected (with evidence) and what is still unclear. |
| `data/stops_from_gtfs.json` | 49 city stop coordinates from the official GTFS export (visimarsrutai.lt). |

### `timetable.json` in short

```jsonc
{
  "calendar": { "workday": "...", "weekend": "...", "saturday": "...", "holidays": ["2026-12-24", ...] },
  "routes":   { "1": { "name": "Autobusų stotis (Dukstyna) – Pieninė" }, ... },
  "stations": { "kauno": { "name": "Kauno", "lat": 55.2464, "lon": 24.7572, "stops": ["kauno", "kauno-link-centro"] } },
  "stops":    { "kauno-link-centro": { "name": "Kauno", "station": "kauno", "towards": "į centrą", "sign": "https://..." } },
  "trips": [
    { "id": "1-wo-005", "route": "1", "days": "workday", "headsign": "Autobusų stotis",
      "stops": [["pienine", "05:15"], ["umega-link-as", "05:17"], ["pramones-link-centro", "05:20"], ...] }
  ]
}
```

* `days` is `workday` (Mon–Fri), `weekend` (Sat, Sun, public holidays) or `saturday` (route 3).
* Times after midnight are written as `24:xx`.
* A *stop* is one physical sign (one side of the street); a *station* groups the signs with the same name.

### Rebuilding

```bash
python3 tools/make_json.py     # data/raw -> data/timetable.json
python3 tools/verify_json.py   # checks every printed time ends up in the JSON exactly once
python3 tools/check_trips.py   # lists unusual running times between stops
```

When the operator publishes a new timetable, update the files in `data/raw/` and rebuild.

How it works: `tools/patterns.py` holds the stop order of every route (worked out
from the times). `tools/build_trips.py` walks each route and links each stop's
printed time to the next stop's time when the running time matches. `tools/corrections.py`
lists the few misprints that were fixed and why.
