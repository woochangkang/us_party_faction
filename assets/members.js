(function () {
  var data = [];
  var q = document.getElementById('q'), cong = document.getElementById('cong'),
      cau = document.getElementById('cau'), party = document.getElementById('party'),
      tbody = document.querySelector('#tbl tbody'), count = document.getElementById('count');
  var names = window.CAUCUS_NAMES || {};

  // 연속된 대를 구간으로 묶는다: [106,107,108,111] -> "106–108, 111"
  function ranges(cs) {
    cs = cs.map(Number).sort(function (a, b) { return a - b; });
    var out = [], s = cs[0], p = cs[0];
    for (var i = 1; i <= cs.length; i++) {
      if (cs[i] === p + 1) { p = cs[i]; continue; }
      out.push(s === p ? String(s) : s + '–' + p);
      s = p = cs[i];
    }
    return out.join(', ');
  }

  function history(m) {
    var by = {};
    Object.keys(m.terms).forEach(function (c) {
      m.terms[c].c.forEach(function (k) { (by[k] = by[k] || []).push(c); });
    });
    var ks = Object.keys(by);
    if (!ks.length) return '<span style="color:var(--muted)">–</span>';
    return ks.map(function (k) { return (names[k] || k) + ' ' + ranges(by[k]); }).join('<br>');
  }

  function served(m) {
    var cs = Object.keys(m.terms);
    var sd = [];
    cs.forEach(function (c) { if (sd.indexOf(m.terms[c].sd) < 0) sd.push(m.terms[c].sd); });
    return ranges(cs) + ' <span style="color:var(--muted);font-size:0.8rem">(' + sd.join(', ') + ')</span>';
  }

  function render() {
    var s = q.value.trim().toLowerCase(), g = cong.value, k = cau.value, p = party.value;
    var rows = data.filter(function (m) {
      if (s && m.name.toLowerCase().indexOf(s) < 0) return false;
      if (p && m.party !== p) return false;
      if (g && !m.terms[g]) return false;
      if (k) {
        var ts = g ? [m.terms[g]] : Object.keys(m.terms).map(function (x) { return m.terms[x]; });
        if (!ts.some(function (t) { return t && t.c.indexOf(k) >= 0; })) return false;
      }
      return true;
    });
    count.textContent = rows.length + '명' + (rows.length > 600 ? ' (처음 600명 표시 — 이름·대·계파로 좁혀 보세요)' : '');
    tbody.innerHTML = rows.slice(0, 600).map(function (m) {
      var dot = m.party === 'D' ? 'var(--d)' : (m.party === 'R' ? 'var(--r)' : 'var(--muted)');
      return '<tr><td>' + m.name + '</td><td><span class="dot" style="background:' + dot + '"></span>' + m.party + '</td>' +
        '<td class="num">' + (m.dim1 === null ? '' : m.dim1.toFixed(3)) + '</td>' +
        '<td style="white-space:normal">' + served(m) + '</td><td style="white-space:normal">' + history(m) + '</td></tr>';
    }).join('');
  }

  fetch('data/members.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d.sort(function (a, b) { return a.name.localeCompare(b.name); });
    [q, cong, cau, party].forEach(function (el) { el.addEventListener('input', render); });
    render();
  });
})();
