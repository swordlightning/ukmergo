// node test/router.test.js
const assert = require('assert');
const fs = require('fs');
const R = require('../js/router.js');
const data = JSON.parse(fs.readFileSync(__dirname + '/../data/timetable.json', 'utf8'));
const S = data.stops;
let n = 0;
function test(name, f) { f(); n++; console.log('ok -', name); }

const mon = new Date(2026, 10, 16);   // Monday 16 Nov 2026
const sat = new Date(2026, 10, 21);
const sun = new Date(2026, 10, 22);
const xmas = new Date(2026, 11, 25);  // Friday, public holiday

test('day types', () => {
  assert.deepStrictEqual([...R.dayTypes(mon, data)], ['workday']);
  assert.deepStrictEqual([...R.dayTypes(sat, data)].sort(), ['saturday', 'weekend']);
  assert.deepStrictEqual([...R.dayTypes(sun, data)], ['weekend']);
  assert.deepStrictEqual([...R.dayTypes(xmas, data)], ['weekend']);
});

test('every trip runs forward and every stop has coordinates', () => {
  data.trips.forEach(t => {
    const m = t.stops.map(s => R.toMin(s[1]));
    m.forEach((x, i) => i && assert(x >= m[i - 1], t.id));
    t.stops.forEach(s => assert(S[s[0]] && typeof S[s[0]].lat === 'number', s[0]));
  });
});

// standing exactly at a stop: Pieninė -> Ligoninė (route 1 towards AS), Monday 5:10
test('Pieninė 5:10 -> Ligoninė uses the 5:15 route 1 bus', () => {
  const r = R.plan(data, S['pienine'], S['ligonine-link-as'], mon, R.toMin('05:10'));
  const o = r.bus[0];
  const bus = o.legs.filter(l => l.type === 'bus');
  assert.strictEqual(bus.length, 1);
  assert.strictEqual(bus[0].route, '1');
  assert.strictEqual(R.fmt(bus[0].dep), '05:15');
  assert.strictEqual(R.fmt(bus[0].arr), '05:33');   // printed at Ligoninė
});

test('result times match printed stop times exactly', () => {
  const r = R.plan(data, S['zaliasis-vienkiemis'], S['kudirkos-link-as'], mon, R.toMin('07:50'));
  const bus = r.bus[0].legs.find(l => l.type === 'bus');
  const printed = bus.trip.stops.find(s => s[0] === bus.from)[1];
  assert.strictEqual(R.fmt(bus.dep), printed);
});

test('no bus before the first departure is invented (Sunday, route 3 is Saturday only)', () => {
  const ids = new Set();
  R.prepare(data, sun).trips.forEach(x => ids.add(x.t.route + x.t.days));
  assert(!ids.has('3saturday'));
  assert(R.prepare(data, sat).trips.some(x => x.t.route === '3'));
});

test('short distance: walking wins', () => {
  const r = R.plan(data, S['kauno'], S['senasis-pastas'], mon, R.toMin('12:00'));
  assert(r.walk.dur <= 6);
  assert.strictEqual(r.best, r.walk);
});

test('a trip across town with a change of bus is found and is consistent', () => {
  const r = R.plan(data, S['dukstyna'], S['pienine'], mon, R.toMin('12:00'));
  assert(r.bus.length > 0);
  r.bus.forEach(o => {
    let t = o.dep;
    o.legs.forEach(l => { assert(l.dep >= t - 0.01, 'legs overlap'); t = l.arr; });
    assert.strictEqual(o.arr, t);
  });
});

test('after-midnight trip of route 5 is found on the same evening', () => {
  const r = R.plan(data, S['pasile'], S['kauno'], mon, R.toMin('23:50'));
  const bus = r.bus.length && r.bus[0].legs.find(l => l.type === 'bus');
  assert(bus, 'no night bus');
  assert.strictEqual(R.fmt(bus.dep), '00:06');
});

test('uncertain trips are reported', () => {
  const r = R.plan(data, S['kokliu'], S['kauno'], mon, R.toMin('20:00'));
  const o = r.bus[0];
  assert(o.uncertain.length > 0, 'Koklių 20:08 (corrected time) should be marked uncertain');
});
test('options are not dominated by each other', () => {
  const r = R.plan(data, S['as'], S['pienine'], mon, R.toMin('08:00'));
  assert(r.bus.length >= 2);
  r.bus.forEach(a => r.bus.forEach(b => {
    if (a !== b) assert(!(b.dep >= a.dep && b.arr <= a.arr && (b.dep > a.dep || b.arr < a.arr)));
  }));
  assert.strictEqual(R.fmt(r.best.legs.find(l => l.type === 'bus').dep), '08:15');
});
console.log(n + ' tests passed');
