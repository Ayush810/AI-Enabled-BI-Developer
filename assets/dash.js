// Minimal stand-in for the claude.ai dashboard runtime, so the same page runs on GitHub Pages.
// It loads each dataset from a CSV in ./data, runs dash.calc functions, and redraws every
// registered dash.draw element when data arrives or the window is resized.
(function () {
  const SOURCES = window.DASH_SOURCES || {};
  const store = {};
  const calcs = {};
  const draws = [];
  let scheduled = false;

  const result = (status, data) => ({status, data: data || [], columns: (data && data.columns) || [], meta: [], refreshing: false, message: ''});

  function load(id) {
    if (store[id] || !SOURCES[id]) return;
    store[id] = result('loading');
    d3.csv(SOURCES[id]).then((rows) => {
      store[id] = result('ok', rows);
      schedule();
    }).catch((err) => {
      store[id] = Object.assign(result('error'), {message: String(err)});
      schedule();
    });
  }

  function data(id) {
    if (calcs[id]) {
      const c = calcs[id];
      const inputs = c.inputs.map(data);
      if (inputs.some((x) => x.status !== 'ok')) return result(inputs.find((x) => x.status !== 'ok').status);
      if (!c.cache) c.cache = c.fn(...inputs.map((x) => x.data));
      return result('ok', c.cache);
    }
    if (!SOURCES[id]) return result('missing');
    load(id);
    return store[id];
  }

  function hiddenUp(el) {
    for (let n = el; n; n = n.parentElement) if (n.hasAttribute && n.hasAttribute('hidden')) return true;
    return false;
  }

  function run(name) {
    for (const d of draws) {
      if (name && d.name !== name) continue;
      for (const el of document.querySelectorAll(`[data-draw="${d.name}"]`)) {
        if (hiddenUp(el)) continue;
        try { d.fn(el); } catch (e) { console.error('draw', d.name, e); }
      }
    }
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; run(); });
  }

  window.dash = {
    data,
    calc(id, {inputs, fn}) { calcs[id] = {inputs, fn, cache: null}; },
    loader() {},
    draw(name, fn) {
      if (typeof fn === 'function') { draws.push({name, fn}); schedule(); } else run(name);
    },
    onData(fn) { draws.push({name: '__ondata__', fn: () => fn()}); schedule(); },
    refresh() {},
    params: () => ({}),
    setParams() {},
    resetParams() {},
    setLink(id) { try { history.replaceState(null, '', '#' + id); } catch (e) { /* ignore */ } },
    colors: ['#3b6fd8', '#d9622b', '#2f9e6b', '#a95bd1', '#1f9bb3', '#d6416b', '#7a8a2e', '#8a6a3b'],
  };

  for (const id of Object.keys(SOURCES)) load(id);
  let w = window.innerWidth;
  window.addEventListener('resize', () => { if (window.innerWidth !== w) { w = window.innerWidth; schedule(); } });
})();
