(function () {
  var data = [];
  var q = document.getElementById('q'), cong = document.getElementById('cong'),
      cau = document.getElementById('cau'), party = document.getElementById('party'),
      tbody = document.querySelector('#tbl tbody'), count = document.getElementById('count');
  var names = window.CAUCUS_NAMES || {};

  function cell(t) {
    if (!t) return '<td style="color:var(--muted)">–</td>';
    var c = t.c.map(function (k) { return names[k] || k; }).join(', ');
    return '<td>' + t.sd + (c ? '<br><span style="font-size:0.8rem">' + c + '</span>' : '') + '</td>';
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
    count.textContent = rows.length + '명';
    tbody.innerHTML = rows.slice(0, 600).map(function (m) {
      var dot = m.party === 'D' ? 'var(--d)' : (m.party === 'R' ? 'var(--r)' : 'var(--muted)');
      return '<tr><td>' + m.name + '</td><td><span class="dot" style="background:' + dot + '"></span>' + m.party + '</td>' +
        '<td class="num">' + (m.dim1 === null ? '' : m.dim1.toFixed(3)) + '</td>' +
        [116, 117, 118, 119].map(function (c) { return cell(m.terms[c]); }).join('') + '</tr>';
    }).join('');
  }

  fetch('data/members.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d.sort(function (a, b) { return a.name.localeCompare(b.name); });
    [q, cong, cau, party].forEach(function (el) { el.addEventListener('input', render); });
    render();
  });
})();
