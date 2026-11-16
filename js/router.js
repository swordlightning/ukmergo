/* UkmerGO route planner.
 *
 * Finds the earliest arrival from A to B using walking and the city buses.
 * Algorithm: Connection Scan (CSA) – every bus trip is cut into "connections"
 * (bus leaves stop X at time t1, arrives at the next stop Y at time t2), sorted by
 * departure time and scanned once. Works in the browser and in Node (tests).
 */
(function (root) {
  'use strict';

  const WALK_M_PER_MIN = 75;      // ~4.5 km/h
  const DETOUR = 1.3;             // streets are longer than a straight line
  const MAX_ACCESS_M = 1500;      // longest walk to the first / from the last stop
  const MAX_TRANSFER_M = 400;     // longest walk between two stops when changing bus
  const TRANSFER_BUFFER = 1;      // minutes needed to change to another bus
  const CONTINUE_MAX_GAP = 12;    // same bus continues as the next trip (terminus turn-round)

  function distM(a, b) {
    const k = Math.cos((a.lat + b.lat) / 2 * Math.PI / 180);
    return Math.hypot((a.lat - b.lat) * 111320, (a.lon - b.lon) * 111320 * k);
  }
  function walkMin(m) { return Math.max(1, Math.ceil(m * DETOUR / WALK_M_PER_MIN)); }
  function toMin(hhmm) { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; }
  function fmt(min) {
    const m = ((Math.round(min) % 1440) + 1440) % 1440;
    return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
  }
  function isoDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  /** Which timetables run on this date: Set of 'workday' | 'weekend' | 'saturday'. */
  function dayTypes(date, data) {
    const holidays = new Set((data.calendar && data.calendar.holidays) || []);
    const dow = date.getDay(); // 0 = Sunday
    const t = new Set();
    if (holidays.has(isoDate(date)) || dow === 0 || dow === 6) t.add('weekend'); else t.add('workday');
    if (dow === 6) t.add('saturday');
    return t;
  }

  /** Prepare a planner for one service date. */
  function prepare(data, date) {
    const stops = data.stops;
    const ids = Object.keys(stops);
    // trips running today (offset 0) and yesterday's after-midnight part (offset -1440)
    const prev = new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1);
    const today = dayTypes(date, data), yday = dayTypes(prev, data);
    const trips = [];
    data.trips.forEach(t => {
      if (today.has(t.days)) trips.push({ t, off: 0 });
      if (yday.has(t.days) && toMin(t.stops[t.stops.length - 1][1]) >= 1440) trips.push({ t, off: -1440 });
    });
    const conns = [];
    trips.forEach((x, ti) => {
      x.times = x.t.stops.map(s => toMin(s[1]) + x.off);
      for (let i = 0; i < x.t.stops.length - 1; i++) {
        conns.push({ ti, i, from: x.t.stops[i][0], to: x.t.stops[i + 1][0], dep: x.times[i], arr: x.times[i + 1] });
      }
    });
    conns.sort((a, b) => a.dep - b.dep || a.arr - b.arr);
    // walking between nearby stops
    const near = {};
    ids.forEach(a => {
      near[a] = [];
      ids.forEach(b => {
        if (a === b) return;
        const d = distM(stops[a], stops[b]);
        if (d <= MAX_TRANSFER_M) near[a].push({ to: b, min: walkMin(d), m: d });
      });
    });
    // the same bus continues as another trip of the same route (e.g. at Koklių, Žaliasis vnk.)
    const cont = trips.map(() => []);
    trips.forEach((a, ai) => {
      const last = a.t.stops[a.t.stops.length - 1][0], tEnd = a.times[a.times.length - 1];
      trips.forEach((b, bi) => {
        if (ai === bi || a.t.route !== b.t.route) return;
        const first = b.t.stops[0][0], gap = b.times[0] - tEnd;
        if (gap >= 0 && gap <= CONTINUE_MAX_GAP && distM(stops[last], stops[first]) <= 300) cont[ai].push(bi);
      });
      // keep only the first continuation in time
      cont[ai].sort((x, y) => trips[x].times[0] - trips[y].times[0]);
      cont[ai] = cont[ai].slice(0, 1);
    });
    return { data, date, trips, conns, near, cont };
  }

  /** Earliest-arrival search. from/to: {lat, lon}. t0: minutes after midnight. */
  function search(P, from, to, t0) {
    const stops = P.data.stops;
    const S = {}, J = {};            // best arrival time and how we got there
    Object.keys(stops).forEach(id => { S[id] = Infinity; });
    const egress = {};
    Object.keys(stops).forEach(id => {
      const da = distM(from, stops[id]);
      if (da <= MAX_ACCESS_M) { S[id] = t0 + walkMin(da); J[id] = { kind: 'access', min: walkMin(da), m: da }; }
      const de = distM(stops[id], to);
      if (de <= MAX_ACCESS_M) egress[id] = { min: walkMin(de), m: de };
    });
    const board = new Array(P.trips.length).fill(null); // {conn index of first connection used, from where}
    const C = P.conns;
    for (let k = 0; k < C.length; k++) {
      const c = C[k];
      if (c.dep < t0) continue;
      let b = board[c.ti];
      if (!b) {
        const j = J[c.from];
        const need = j && j.kind === 'bus' ? TRANSFER_BUFFER : 0;
        if (S[c.from] + need <= c.dep) { b = board[c.ti] = { first: k, prevJ: j, stop: c.from }; }
      }
      if (!b) continue;
      if (c.arr < S[c.to]) {
        S[c.to] = c.arr;
        J[c.to] = { kind: 'bus', ti: c.ti, boardK: b.first, alightK: k };
        P.near[c.to].forEach(n => {
          if (c.arr + n.min < S[n.to]) { S[n.to] = c.arr + n.min; J[n.to] = { kind: 'walk', from: c.to, min: n.min, m: n.m }; }
        });
      }
      // last connection of the trip: the same bus may go on as the next trip
      const tr = P.trips[c.ti];
      if (c.i === tr.t.stops.length - 2) {
        P.cont[c.ti].forEach(ni => {
          if (!board[ni]) {
            const firstK = C.findIndex(x => x.ti === ni && x.i === 0);
            if (firstK >= 0) board[ni] = { first: firstK, continued: { ti: c.ti, boardK: b.first, alightK: k }, stop: P.trips[ni].t.stops[0][0] };
          }
        });
      }
    }
    // best stop to leave the bus network
    let best = null;
    Object.keys(egress).forEach(id => {
      if (S[id] === Infinity || !J[id] || J[id].kind === 'access') return;
      const arr = S[id] + egress[id].min;
      if (!best || arr < best.arr) best = { stop: id, arr };
    });
    if (!best) return null;
    return rebuild(P, J, board, best, egress[best.stop], from, to, t0);
  }

  function rebuild(P, J, board, best, eg, from, to, t0) {
    const C = P.conns, stops = P.data.stops, legs = [];
    legs.push({ type: 'walk', from: best.stop, to: 'dest', min: eg.min, m: eg.m, dep: best.arr - eg.min, arr: best.arr });
    let id = best.stop, guard = 0;
    while (guard++ < 50) {
      const j = J[id];
      if (j.kind === 'access') {
        const first = legs[legs.length - 1];
        legs.push({ type: 'walk', from: 'origin', to: id, min: j.min, m: j.m, dep: first.dep - j.min, arr: first.dep });
        break;
      }
      if (j.kind === 'walk') {
        const next = legs[legs.length - 1];
        legs.push({ type: 'walk', from: j.from, to: id, min: j.min, m: j.m, dep: next.dep - j.min, arr: next.dep, transfer: true });
        id = j.from; continue;
      }
      // bus leg, possibly made of several trips of the same vehicle
      let seg = { ti: j.ti, boardK: j.boardK, alightK: j.alightK };
      while (true) {
        const tr = P.trips[seg.ti], b = C[seg.boardK], a = C[seg.alightK];
        const stopsOn = tr.t.stops.slice(b.i, a.i + 2).map((s, n) => ({ stop: s[0], time: tr.times[b.i + n] }));
        legs.push({ type: 'bus', trip: tr.t, route: tr.t.route, headsign: tr.t.headsign, from: b.from, to: a.to,
                    dep: b.dep, arr: a.arr, stops: stopsOn, uncertain: tr.t.uncertain || null });
        const bd = board[seg.ti];
        if (bd && bd.continued && bd.first === seg.boardK) {
          legs[legs.length - 1].continued = true;
          seg = bd.continued; continue;
        }
        id = b.from; break;
      }
    }
    legs.reverse();
    // after reversing, mark legs where the passenger stays on the same bus
    for (let i = 1; i < legs.length; i++) if (legs[i].continued) { legs[i].stayOn = true; delete legs[i].continued; }
    legs.forEach(l => { delete l.continued; });
    // a walk between two buses starts when the first bus arrives
    for (let i = 1; i < legs.length; i++) if (legs[i].transfer) { legs[i].dep = legs[i - 1].arr; legs[i].arr = legs[i].dep + legs[i].min; }
    // the walk to the first stop starts as late as possible
    const firstBus = legs.find(l => l.type === 'bus');
    if (legs[0].type === 'walk' && firstBus) { legs[0].arr = firstBus.dep; legs[0].dep = firstBus.dep - legs[0].min; }
    const dep = legs[0].dep, arr = legs[legs.length - 1].arr;
    const buses = legs.filter(l => l.type === 'bus');
    const uncertain = [];
    buses.forEach(l => (l.uncertain || []).forEach(r => { if (!uncertain.includes(r)) uncertain.push(r); }));
    const approxStops = [];
    buses.forEach(l => [l.from, l.to].forEach(s => { if (stops[s].approx && !approxStops.includes(s)) approxStops.push(s); }));
    return { kind: 'bus', dep, arr, dur: arr - dep, legs, transfers: buses.filter(l => !l.stayOn).length - 1,
             walkMin: legs.filter(l => l.type === 'walk').reduce((s, l) => s + l.min, 0), uncertain, approxStops };
  }

  /** Up to `count` bus options leaving at or after t0, plus the walking option. */
  function plan(data, from, to, date, t0, count) {
    count = count || 3;
    const P = prepare(data, date);
    const direct = distM(from, to);
    const walk = { kind: 'walk', dep: t0, arr: t0 + walkMin(direct), dur: walkMin(direct), m: direct,
                   legs: [{ type: 'walk', from: 'origin', to: 'dest', min: walkMin(direct), m: direct, dep: t0, arr: t0 + walkMin(direct) }] };
    // Search again and again, each time leaving one minute after the previous
    // option, then keep only options that no other option beats (leaves later
    // and arrives no later, or same times with fewer changes / less walking).
    const found = [];
    let t = t0;
    for (let n = 0; n < 40; n++) {
      const r = search(P, from, to, t);
      if (!r) break;
      found.push(r);
      t = r.dep + 1;
      const distinct = new Set(found.map(o => o.arr)).size;
      if (distinct > count || t > t0 + 240) break;
    }
    const better = (a, b) => a.dep >= b.dep && a.arr <= b.arr &&
      (a.dep > b.dep || a.arr < b.arr || a.transfers < b.transfers || (a.transfers === b.transfers && a.walkMin < b.walkMin));
    const out = found.filter(o => !found.some(p => p !== o && better(p, o)))
      .filter((o, i, arr) => arr.findIndex(p => p.dep === o.dep && p.arr === o.arr) === i)
      .sort((a, b) => a.arr - b.arr || b.dep - a.dep)
      .slice(0, count);
    // the fastest way overall (walking wins ties: no waiting, no risk)
    const best = out.length && out[0].arr < walk.arr ? out[0] : walk;
    return { walk, bus: out, best };
  }

  /** Next departures from one stop. */
  function departures(data, stopId, date, t0, n) {
    const P = prepare(data, date), res = [];
    P.trips.forEach(x => x.t.stops.forEach((s, i) => {
      if (s[0] === stopId && i < x.t.stops.length - 1 && x.times[i] >= t0) res.push({ time: x.times[i], trip: x.t });
    }));
    res.sort((a, b) => a.time - b.time);
    return res.slice(0, n || 6);
  }

  const api = { plan, search, prepare, departures, dayTypes, distM, walkMin, toMin, fmt, isoDate,
                WALK_M_PER_MIN, DETOUR, MAX_ACCESS_M, MAX_TRANSFER_M };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Router = api;
})(this);
