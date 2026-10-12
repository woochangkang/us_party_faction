(function () {
  // 대별 DW-NOMINATE 산점도: 하원·상원 두 패널. 색 = 당적, 모양 = 계파(하원만). 커서에서 가장 가까운 마커의 의원 정보를 띄운다.
  var W = 440, H = 440, M = { l: 44, r: 12, t: 12, b: 40 };
  var SHAPES = { cpc: 'tri', populist: 'triL', bluedog: 'square', ndc: 'diamond', hfc: 'triD', teaparty: 'hex',
                 liberty: 'star', mainstreet: 'penta', rmsp: 'plus', rsc: 'circle', psc: 'cross', '': 'dot' };
  var PARTY = { D: '민주당', R: '공화당', O: '무소속·기타' };
  var data, names, years, sel = document.getElementById('ncong'), tip = document.getElementById('ntip');
  var NS = 'http://www.w3.org/2000/svg';

  function sx(v) { return M.l + (v + 1.05) / 2.1 * (W - M.l - M.r); }
  function sy(v) { return M.t + (1.05 - v) / 2.1 * (H - M.t - M.b); }
  function el(n, a) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); return e; }

  // 마커 경로: 중심 0,0, 반지름 r
  function shapePath(s, r) {
    var p = [], i, a;
    function poly(n, rot, rad) { var q = []; for (i = 0; i < n; i++) { a = rot + i * 2 * Math.PI / n; q.push((rad * Math.cos(a)).toFixed(2) + ',' + (rad * Math.sin(a)).toFixed(2)); } return 'M' + q.join('L') + 'Z'; }
    switch (s) {
      case 'tri': return poly(3, -Math.PI / 2, r * 1.15);
      case 'triD': return poly(3, Math.PI / 2, r * 1.15);
      case 'triL': return poly(3, Math.PI, r * 1.15);
      case 'square': return poly(4, Math.PI / 4, r * 1.2);
      case 'diamond': return poly(4, 0, r * 1.25);
      case 'penta': return poly(5, -Math.PI / 2, r * 1.1);
      case 'hex': return poly(6, 0, r * 1.05);
      case 'star':
        for (i = 0; i < 10; i++) { a = -Math.PI / 2 + i * Math.PI / 5; var rr = i % 2 ? r * 0.5 : r * 1.25; p.push((rr * Math.cos(a)).toFixed(2) + ',' + (rr * Math.sin(a)).toFixed(2)); }
        return 'M' + p.join('L') + 'Z';
      case 'plus': var t = r * 0.38; return 'M' + -t + ',' + -r + 'H' + t + 'V' + -t + 'H' + r + 'V' + t + 'H' + t + 'V' + r + 'H' + -t + 'V' + t + 'H' + -r + 'V' + -t + 'H' + -t + 'Z';
      case 'cross': return 'M' + -r + ',' + -r + 'L' + r + ',' + r + 'M' + r + ',' + -r + 'L' + -r + ',' + r;
      case 'dot': r = r * 0.45; // fallthrough
      default: return 'M' + r + ',0A' + r + ',' + r + ' 0 1,1 ' + -r + ',0A' + r + ',' + r + ' 0 1,1 ' + r + ',0Z';
    }
  }
  function color(p) { return p === 'D' ? 'var(--d)' : p === 'R' ? 'var(--r)' : 'var(--muted)'; }

  function axes(svg) {
    [-1, -0.5, 0, 0.5, 1].forEach(function (v) {
      svg.appendChild(el('line', { x1: sx(v), x2: sx(v), y1: M.t, y2: H - M.b, class: v === 0 ? 'nom-zero' : 'nom-gl' }));
      svg.appendChild(el('line', { y1: sy(v), y2: sy(v), x1: M.l, x2: W - M.r, class: v === 0 ? 'nom-zero' : 'nom-gl' }));
      var tx = el('text', { x: sx(v), y: H - M.b + 14, 'text-anchor': 'middle', class: 'nom-tick' }); tx.textContent = v; svg.appendChild(tx);
      var ty = el('text', { x: M.l - 6, y: sy(v) + 3, 'text-anchor': 'end', class: 'nom-tick' }); ty.textContent = v; svg.appendChild(ty);
    });
    var xl = el('text', { x: (M.l + W - M.r) / 2, y: H - 6, 'text-anchor': 'middle', class: 'nom-label' }); xl.textContent = 'DW-NOMINATE 1차원 (진보 ← → 보수)'; svg.appendChild(xl);
    var yl = el('text', { x: 12, y: (M.t + H - M.b) / 2, 'text-anchor': 'middle', class: 'nom-label', transform: 'rotate(-90 12 ' + (M.t + H - M.b) / 2 + ')' }); yl.textContent = 'DW-NOMINATE 2차원'; svg.appendChild(yl);
  }

  function draw(box, rows, chamber, c) {
    box.innerHTML = '';
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'nom-svg', role: 'img',
      'aria-label': c + '대 ' + chamber + ' 의원 ' + rows.length + '명의 DW-NOMINATE 분포' });
    axes(svg);
    var g = el('g', {}); svg.appendChild(g);
    var pts = [];
    // 계파 없는 점을 먼저(아래), 계파 점을 위에
    rows.slice().sort(function (a, b) { return (a[6] ? 1 : 0) - (b[6] ? 1 : 0); }).forEach(function (m) {
      // 상원은 계파 자료가 없으므로 모든 점을 보통 크기의 원으로 그린다
      var sen = chamber === '상원';
      var x = sx(m[3]), y = sy(m[4]), s = sen ? 'circle' : (SHAPES[m[6]] || 'dot'), r = (m[6] || sen) ? 4.6 : 3.4;
      var path = el('path', { d: shapePath(s, r), transform: 'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ')',
        class: 'nom-mark' + (m[6] || sen ? '' : ' nom-plain') });
      if (s === 'cross') { path.setAttribute('stroke', color(m[1])); path.setAttribute('stroke-width', '2'); path.setAttribute('fill', 'none'); }
      else path.setAttribute('fill', color(m[1]));
      g.appendChild(path); pts.push({ x: x, y: y, m: m, el: path });
    });
    var ring = el('circle', { r: 8, class: 'nom-ring', visibility: 'hidden' }); svg.appendChild(ring);
    function locate(ev) {
      var pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
      var p = pt.matrixTransform(svg.getScreenCTM().inverse()), best = null, bd = 144;
      pts.forEach(function (q) { var d = (q.x - p.x) * (q.x - p.x) + (q.y - p.y) * (q.y - p.y); if (d < bd) { bd = d; best = q; } });
      return best;
    }
    function show(ev) {
      var q = locate(ev);
      if (!q) { hide(); return; }
      ring.setAttribute('cx', q.x); ring.setAttribute('cy', q.y); ring.setAttribute('visibility', 'visible');
      var m = q.m, cs = m[5].length ? m[5].map(function (k) { return names[k] || k; }).join(', ') : (chamber === '상원' ? '자료 없음(상원)' : '없음 또는 미확인');
      tip.innerHTML = '<b>' + m[0] + '</b><br>' + (PARTY[m[1]] || m[1]) + ' · ' + m[2] + ' · ' + c + '대 ' + chamber +
        '<br>1차원 ' + m[3].toFixed(3) + ' · 2차원 ' + m[4].toFixed(3) + '<br>계파: ' + cs;
      tip.hidden = false;
      var tw = tip.offsetWidth, th = tip.offsetHeight, left = ev.clientX + 14, top = ev.clientY + 14;
      if (left + tw > window.innerWidth - 8) left = ev.clientX - tw - 14;
      if (top + th > window.innerHeight - 8) top = ev.clientY - th - 14;
      tip.style.left = Math.max(8, left) + 'px'; tip.style.top = Math.max(8, top) + 'px';
    }
    function hide() { ring.setAttribute('visibility', 'hidden'); tip.hidden = true; }
    svg.addEventListener('pointermove', show);
    svg.addEventListener('pointerdown', show);
    svg.addEventListener('pointerleave', hide);
    box.appendChild(svg);
  }

  function legend(covered) {
    var h = covered.map(function (k) {
      return '<span><svg width="14" height="14" viewBox="-7 -7 14 14" aria-hidden="true"><path d="' + shapePath(SHAPES[k], 4.6) + '" ' +
        (SHAPES[k] === 'cross' ? 'stroke="var(--fg)" stroke-width="2" fill="none"' : 'fill="var(--fg)"') + '/></svg> ' + names[k] + '</span>';
    });
    h.push('<span><svg width="14" height="14" viewBox="-7 -7 14 14" aria-hidden="true"><path d="' + shapePath('dot', 3.4) + '" fill="var(--muted)"/></svg> 계파 없음/미확인</span>');
    h.push('<span><span class="sw" style="background:var(--d)"></span>민주당</span><span><span class="sw" style="background:var(--r)"></span>공화당</span><span><span class="sw" style="background:var(--muted)"></span>무소속·기타</span>');
    document.getElementById('nlegend').innerHTML = '<b style="color:var(--fg)">하원 계파 모양:</b> ' + h.join('');
  }

  function render() {
    var c = sel.value, d = data[c];
    draw(document.getElementById('house'), d.house, '하원', c);
    draw(document.getElementById('senate'), d.senate, '상원', c);
    document.getElementById('hcount').textContent = d.house.length + '명';
    document.getElementById('scount').textContent = d.senate.length + '명';
    legend(d.covered);
  }

  function step(k) { var i = sel.selectedIndex - k; if (i >= 0 && i < sel.options.length) { sel.selectedIndex = i; render(); } }
  fetch('data/nominate.json').then(function (r) { return r.json(); }).then(function (j) {
    data = j.congress; names = j.names; years = j.years;
    sel.addEventListener('change', render);
    document.getElementById('nprev').addEventListener('click', function () { step(-1); });
    document.getElementById('nnext').addEventListener('click', function () { step(1); });
    render();
  });
})();
