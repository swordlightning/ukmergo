/* UkmerGO – user interface: map, search boxes, my location, results. */
(function () {
  'use strict';
  const R = window.Router;
  const UKMERGE = [55.2495, 24.7710];
  const VIEWBOX = '24.66,55.30,24.86,55.19';   // Nominatim search area (lon,lat,lon,lat)
  const BOUNDS = L.latLngBounds([55.19, 24.66], [55.30, 24.86]);
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const Q = (title) => ` <span class="q" title="${esc(title)}">(?)</span>`;

  let data = null;
  const state = { from: null, to: null, results: null, sel: 0 };

  // ---------- map ----------
  const map = L.map('map', { zoomControl: true, maxBounds: BOUNDS.pad(0.5) }).setView(UKMERGE, 14);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);
  const stopLayer = L.layerGroup().addTo(map);
  const routeLayer = L.layerGroup().addTo(map);
  const pinIcon = cls => L.divIcon({ className: '', html: `<div class="pin ${cls}"></div>`, iconSize: [26, 26], iconAnchor: [13, 26] });
  const markers = { from: null, to: null };

  function setPoint(which, p) {
    state[which] = p;
    $(which + 'Input').value = p ? p.label : '';
    if (markers[which]) { map.removeLayer(markers[which]); markers[which] = null; }
    if (p) {
      markers[which] = L.marker([p.lat, p.lon], { icon: pinIcon(which === 'from' ? 'a' : 'b'), draggable: true, title: which === 'from' ? 'Iš kur' : 'Į kur' })
        .addTo(map)
        .on('dragend', e => { const ll = e.target.getLatLng(); setPoint(which, { lat: ll.lat, lon: ll.lng, label: 'Pasirinkta vieta žemėlapyje' }); planIfReady(); });
    }
  }

  map.on('click', e => {
    if (!BOUNDS.contains(e.latlng)) return;
    const which = !state.from ? 'from' : 'to';
    setPoint(which, { lat: e.latlng.lat, lon: e.latlng.lng, label: 'Pasirinkta vieta žemėlapyje' });
    planIfReady();
  });

  // ---------- time ----------
  function now() { return new Date(); }
  function startTime() {
    if ($('whenSel').value === 'at' && $('whenInput').value) {
      const d = new Date($('whenInput').value);
      if (!isNaN(d)) return d;
    }
    return now();
  }
  function localInputValue(d) {
    const p = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
  }
  $('whenSel').addEventListener('change', () => {
    const at = $('whenSel').value === 'at';
    $('whenInput').hidden = !at;
    if (at && !$('whenInput').value) $('whenInput').value = localInputValue(now());
  });

  // ---------- search boxes ----------
  function norm(s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }

  function localMatches(q) {
    const n = norm(q), seen = new Set(), out = [];
    Object.entries(data.stations).forEach(([id, st]) => {
      if (norm(st.name).includes(n) && !seen.has(st.name)) {
        seen.add(st.name);
        out.push({ lat: st.lat, lon: st.lon, label: st.name + ' (stotelė)', sub: 'Autobusų stotelė' + (st.approx ? ' – vieta apytikslė (?)' : '') });
      }
    });
    return out.slice(0, 5);
  }

  let geoTimer = null, geoAbort = null;
  async function geocode(q) {
    if (geoAbort) geoAbort.abort();
    geoAbort = new AbortController();
    const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=6&countrycodes=lt&bounded=1'
      + '&accept-language=lt&viewbox=' + VIEWBOX + '&q=' + encodeURIComponent(q);
    const res = await fetch(url, { signal: geoAbort.signal, headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error('paieška nepavyko');
    const js = await res.json();
    return js.map(r => {
      const a = r.address || {};
      const street = [a.road, a.house_number].filter(Boolean).join(' ');
      const name = r.name && r.name !== a.road ? r.name : '';
      const label = [name, street].filter(Boolean).join(', ') || r.display_name.split(',')[0];
      return { lat: +r.lat, lon: +r.lon, label, sub: r.display_name.split(',').slice(1, 3).join(',').trim() };
    });
  }

  function attachSearch(which) {
    const input = $(which + 'Input'), list = $(which + 'List');
    let items = [], active = -1;
    function render() {
      list.innerHTML = items.map((it, i) =>
        `<li role="option" id="${which}-o${i}" aria-selected="${i === active}">${esc(it.label)}${it.sub ? `<small>${esc(it.sub)}</small>` : ''}</li>`).join('');
      list.hidden = !items.length;
    }
    function choose(i) {
      const it = items[i]; if (!it) return;
      setPoint(which, { lat: it.lat, lon: it.lon, label: it.label });
      items = []; render();
      map.setView([it.lat, it.lon], Math.max(map.getZoom(), 15));
      planIfReady();
    }
    input.addEventListener('input', () => {
      state[which] = null;
      const q = input.value.trim();
      active = -1;
      if (q.length < 2) { items = []; render(); return; }
      items = localMatches(q); render();
      clearTimeout(geoTimer);
      if (q.length < 3) return;
      geoTimer = setTimeout(async () => {          // Nominatim allows 1 request per second
        try {
          const found = await geocode(q + ', Ukmergė');
          if (input.value.trim() !== q) return;
          items = localMatches(q).concat(found).slice(0, 8); render();
          if (!items.length) { list.innerHTML = '<li aria-disabled="true">Nieko nerasta</li>'; list.hidden = false; }
        } catch (e) { if (e.name !== 'AbortError') { items = localMatches(q); render(); } }
      }, 600);
    });
    input.addEventListener('keydown', e => {
      if (list.hidden) return;
      if (e.key === 'ArrowDown') { active = Math.min(items.length - 1, active + 1); render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); render(); e.preventDefault(); }
      else if (e.key === 'Enter' && items.length) { choose(active < 0 ? 0 : active); e.preventDefault(); }
      else if (e.key === 'Escape') { items = []; render(); }
    });
    list.addEventListener('mousedown', e => {
      const li = e.target.closest('li[id]'); if (!li) return;
      e.preventDefault(); choose(+li.id.split('-o')[1]);
    });
    input.addEventListener('blur', () => setTimeout(() => { items = []; render(); }, 150));
  }

  // ---------- my location ----------
  $('locBtn').addEventListener('click', () => {
    if (!navigator.geolocation) { showMsg('Jūsų naršyklė nepalaiko vietos nustatymo.', true); return; }
    const b = $('locBtn'); b.classList.add('busy');
    navigator.geolocation.getCurrentPosition(pos => {
      b.classList.remove('busy');
      const p = { lat: pos.coords.latitude, lon: pos.coords.longitude, label: 'Mano vieta' };
      if (!BOUNDS.contains([p.lat, p.lon])) { showMsg('Atrodo, kad esate ne Ukmergėje – pasirinkite pradžios tašką žemėlapyje ar paieškoje.', true); return; }
      setPoint('from', p); map.setView([p.lat, p.lon], 16); planIfReady();
    }, err => {
      b.classList.remove('busy');
      showMsg(err.code === 1 ? 'Neleista naudoti vietos. Leiskite tai naršyklės nustatymuose arba įveskite adresą.' : 'Nepavyko nustatyti vietos.', true);
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  });

  $('swapBtn').addEventListener('click', () => {
    const a = state.from, b = state.to;
    setPoint('from', b); setPoint('to', a); planIfReady();
  });

  // ---------- planning ----------
  function showMsg(text, err) { $('results').innerHTML = `<p class="msg${err ? ' err' : ''}">${esc(text)}</p>`; }

  function planIfReady() { if (state.from && state.to) plan(); }

  // Text typed but nothing picked from the list: take the first match.
  async function resolveTyped(which) {
    if (state[which]) return true;
    const q = $(which + 'Input').value.trim();
    if (q.length < 2) return false;
    let found = localMatches(q);
    if (!found.length) { try { found = await geocode(q + ', Ukmergė'); } catch (e) { found = []; } }
    if (!found.length) return false;
    setPoint(which, { lat: found[0].lat, lon: found[0].lon, label: found[0].label });
    return true;
  }

  $('planForm').addEventListener('submit', async e => {
    e.preventDefault();
    if (!data) { showMsg('Tvarkaraščiai dar įkeliami – palaukite akimirką.', true); return; }
    const okFrom = await resolveTyped('from'), okTo = await resolveTyped('to');
    if (!okFrom || !okTo) {
      const which = !okFrom ? '„Iš kur“' : '„Į kur“';
      showMsg($(!okFrom ? 'fromInput' : 'toInput').value.trim()
        ? `Nepavyko rasti vietos laukelyje ${which}. Pabandykite kitaip (pvz. „Vilniaus g. 10“) arba pažymėkite tašką žemėlapyje.`
        : 'Pasirinkite, iš kur ir į kur keliaujate (įveskite adresą, paspauskite ◎ „Mano vieta“ arba žemėlapį).', true);
      return;
    }
    plan();
  });

  function plan() {
    if (!data) return;
    const d = startTime();
    const t0 = d.getHours() * 60 + d.getMinutes();
    const service = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const r = R.plan(data, state.from, state.to, service, t0, 3);
    const opts = [r.walk, ...r.bus].sort((a, b) => a.arr - b.arr || (a.kind === 'walk' ? -1 : 1));
    state.results = { opts, best: r.best, t0 };
    state.sel = opts.indexOf(r.best);
    renderResults();
  }

  function busBadge(route) { return `<span class="bus r${esc(route)}">${esc(route)}</span>`; }
  function stopName(id) {
    const s = data.stops[id];
    return esc(s.name) + (s.towards ? ` <span class="dir">(${esc(s.towards)})</span>` : '') + (s.approx ? Q('Stotelės vieta žemėlapyje apytikslė.') : '');
  }
  function minTxt(m) { return m < 60 ? `${m} min` : `${Math.floor(m / 60)} val. ${m % 60} min`; }
  function mTxt(m) { return m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`; }

  function renderResults() {
    const { opts, best, t0 } = state.results;
    let html = '';
    opts.forEach((o, i) => {
      const buses = o.legs.filter(l => l.type === 'bus');
      const unc = o.kind === 'bus' && (o.uncertain.length || o.approxStops.length);
      const summary = o.kind === 'walk'
        ? `🚶 Visas kelias pėsčiomis · ${mTxt(o.m)}`
        : buses.map(l => (l.stayOn ? '→ ' : '') + busBadge(l.route)).join(' ') + ` · 🚶 ${o.walkMin} min` +
          (o.transfers > 0 ? ` · ${o.transfers} persėd.` : '');
      const wait = o.dep - t0;
      html += `<div class="opt${i === state.sel ? ' sel' : ''}" data-i="${i}" tabindex="0" role="button" aria-expanded="${i === state.sel}">
        <div class="top"><span class="times">${R.fmt(o.dep)} → ${R.fmt(o.arr)}${unc ? Q('Šiame kelyje yra neaiškumų – žr. žemiau.') : ''}</span>
        <span class="dur">${minTxt(o.dur)}</span></div>
        <div class="badges">${o === best ? '<span class="tag">Greičiausia</span>' : ''} ${summary}
          ${o.kind === 'bus' && wait > 0 ? ` · išeiti po ${minTxt(wait)}` : ''}</div>
        ${steps(o)}
        ${unc ? `<div class="why"><b>(?) Kodėl gali būti netikslu:</b><ul>${o.uncertain.map(u => `<li>${esc(u)}</li>`).join('')}
          ${o.approxStops.length ? `<li>Apytikslė stotelės vieta: ${o.approxStops.map(s => esc(data.stops[s].name)).join(', ')}.</li>` : ''}</ul></div>` : ''}
      </div>`;
    });
    if (opts.length === 1) html += '<p class="msg">Tinkamo autobuso artimiausiu metu nerasta – siūlome eiti pėsčiomis.</p>';
    $('results').innerHTML = html;
    $('results').querySelectorAll('.opt').forEach(el => {
      const pick = () => { state.sel = +el.dataset.i; renderResults(); };
      el.addEventListener('click', pick);
      el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
    });
    drawOption(opts[state.sel]);
  }

  function steps(o) {
    const li = o.legs.map((l, i) => {
      if (l.type === 'walk') {
        const to = l.to === 'dest' ? esc(state.to.label) : stopName(l.to);
        const what = l.from === 'origin' && l.to === 'dest' ? `Eikite iki: ${to}` : `Eikite iki ${to}`;
        return `<li><span class="t">${R.fmt(l.dep)}</span><span class="d">🚶 ${what}<small>${l.min} min · ~${mTxt(l.m * R.DETOUR)}</small></span></li>`;
      }
      const unc = l.uncertain && l.uncertain.length ? Q(l.uncertain.join(' ')) : '';
      const head = l.stayOn
        ? `Likite autobuse – jis toliau važiuoja kaip ${busBadge(l.route)} → ${esc(l.headsign)}`
        : `${busBadge(l.route)} → ${esc(l.headsign)} iš stotelės ${stopName(l.from)}`;
      return `<li><span class="t">${R.fmt(l.dep)}${unc}</span><span class="d">🚌 ${head}
        <small>Važiuokite ${l.stops.length - 1} st. iki ${stopName(l.to)} · atvyksite ${R.fmt(l.arr)}</small></span></li>`;
    }).join('');
    return `<ol class="steps">${li}<li><span class="t">${R.fmt(o.arr)}</span><span class="d">🏁 ${esc(state.to.label)}</span></li></ol>`;
  }

  function drawOption(o) {
    routeLayer.clearLayers();
    if (!o) return;
    const pts = [];
    const ll = id => id === 'origin' ? [state.from.lat, state.from.lon] : id === 'dest' ? [state.to.lat, state.to.lon] : [data.stops[id].lat, data.stops[id].lon];
    o.legs.forEach(l => {
      if (l.type === 'walk') {
        const line = [ll(l.from), ll(l.to)];
        L.polyline(line, { color: '#4b5563', weight: 4, dashArray: '2 8', lineCap: 'round' }).addTo(routeLayer)
          .bindTooltip('Pėsčiomis (tiesi linija – tikras kelias gali būti kitoks)');
        pts.push(...line);
      } else {
        const line = l.stops.map(s => ll(s.stop));
        const color = getComputedStyle(document.documentElement).getPropertyValue('--r' + l.route).trim() || '#1d4ed8';
        L.polyline(line, { color, weight: 6, opacity: .9 }).addTo(routeLayer).bindTooltip(`Autobusas ${l.route} → ${l.headsign}`);
        l.stops.forEach((s, i) => L.circleMarker(ll(s.stop), { radius: i === 0 || i === l.stops.length - 1 ? 6 : 3, color, weight: 2, fillColor: '#fff', fillOpacity: 1 })
          .addTo(routeLayer).bindTooltip(`${data.stops[s.stop].name} ${R.fmt(s.time)}`));
        pts.push(...line);
      }
    });
    if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.15), { maxZoom: 16, animate: false });
  }

  // ---------- stops on the map ----------
  function drawStops() {
    Object.entries(data.stops).forEach(([id, s]) => {
      const m = L.circleMarker([s.lat, s.lon], { radius: 4, color: '#16213a', weight: 2, fillColor: s.approx ? '#fde68a' : '#fff', fillOpacity: 1 })
        .addTo(stopLayer);
      m.bindTooltip(s.name + (s.towards ? ` (${s.towards})` : ''));
      m.on('click', e => {
        L.DomEvent.stopPropagation(e);
        const d = now(), t0 = d.getHours() * 60 + d.getMinutes();
        const deps = R.departures(data, id, new Date(d.getFullYear(), d.getMonth(), d.getDate()), t0, 6);
        const rows = deps.map(x => `<tr><td><b>${R.fmt(x.time)}</b>${x.trip.uncertain ? Q(x.trip.uncertain.join(' ')) : ''}</td>
          <td>${busBadge(x.trip.route)}</td><td>→ ${esc(x.trip.headsign)}</td></tr>`).join('');
        L.popup().setLatLng([s.lat, s.lon]).setContent(
          `<b>${esc(s.name)}</b>${s.towards ? ` <small>(${esc(s.towards)})</small>` : ''}${s.approx ? Q('Stotelės vieta apytikslė.') : ''}
           <div style="margin:4px 0">${deps.length ? 'Artimiausi išvykimai šiandien:' : 'Šiandien daugiau išvykimų nėra.'}</div>
           <table>${rows}</table>
           <div style="margin-top:6px"><a href="#" data-stop="${esc(id)}" data-w="from">Iš čia</a> · <a href="#" data-stop="${esc(id)}" data-w="to">Į čia</a>
           · <a href="${esc(s.sign)}" target="_blank" rel="noopener">Tvarkaraštis</a></div>`).openOn(map);
      });
    });
    map.on('popupopen', e => {
      e.popup.getElement().querySelectorAll('a[data-stop]').forEach(a => a.addEventListener('click', ev => {
        ev.preventDefault();
        const s = data.stops[a.dataset.stop];
        setPoint(a.dataset.w, { lat: s.lat, lon: s.lon, label: s.name + ' (stotelė)' });
        map.closePopup(); planIfReady();
      }));
    });
  }

  // ---------- start ----------
  attachSearch('from'); attachSearch('to');
  showMsg('Įkeliami tvarkaraščiai…');
  fetch('data/timetable.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(js => { data = js; drawStops(); $('results').innerHTML = ''; })
    .catch(() => showMsg('Nepavyko įkelti tvarkaraščių. Atnaujinkite puslapį.', true));
})();
