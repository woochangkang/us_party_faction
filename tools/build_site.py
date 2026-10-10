"""us_party_faction 사이트 빌드.

원천: factions/rosters_hist/ (NIS 프로젝트 폴더, 비공개). 이 스크립트가 공개용 데이터만 data/로 복사하고 HTML을 만든다.
공개 범위(2026-10-10 결정):
  - 106-115대(Clarke 2020 수기 코딩)는 계파별 인원·변화 '집계'만. 의원 단위 행은 싣지 않는다
    (Dataverse doi:10.7910/DVN/SYYMJ0 에 명시 라이선스가 없음).
  - 의원 단위 명단·변화는 116-119대만. 116대 의원별 변화 상태는 115대 명단을 드러내므로 싣지 않는다(117대부터).
  - RMSP(Partnership)와 Main Street Caucus는 별도 계열.
실행: python3.11 tools/build_site.py
"""
import html, json, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/Users/kang/Library/CloudStorage/Dropbox/_NIS/_US_Congress/factions/rosters_hist'
DATA = os.path.join(ROOT, 'data')
os.makedirs(DATA, exist_ok=True)
E = html.escape

CAUCUS = {  # key: (한국어, 영어, 정당계열 색 변수, 설명)
    'cpc': ('의회진보연합', 'Congressional Progressive Caucus', 'd', '민주당 진보 계파.'),
    'ndc': ('신민주연합', 'New Democrat Coalition', 'd', '민주당 중도·친기업 계파.'),
    'bluedog': ('청견민주', 'Blue Dog Coalition', 'd', '민주당 재정보수 계파.'),
    'rmsp': ('메인스트리트파트너십', 'Republican Main Street Partnership', 'r',
             '공화당 중도 성향 외부 단체(의회 밖 조직). 하원 코커스인 Main Street Caucus와 별개로 집계한다.'),
    'mainstreet': ('메인스트리트코커스', 'Main Street Caucus', 'r', '공화당 하원 코커스. 공식 명단은 118대부터 확보.'),
    'rsc': ('공화당연구위원회', 'Republican Study Committee', 'r', '공화당 보수 계파(하원 공화당 최대 계파).'),
    'hfc': ('프리덤코커스', 'House Freedom Caucus', 'r', '공화당 강경 보수 계파. 공식 명단을 공개하지 않는다.'),
    'psc': ('문제해결코커스', 'Problem Solvers Caucus', 'b', '양당 의원이 함께 속한 초당파 코커스.'),
}
AGG_ONLY = {'teaparty': 'Tea Party Caucus', 'liberty': 'Liberty Caucus', 'populist': 'Populist Caucus'}
SRC_LABEL = {'clarke2020': 'Clarke(2020) 수기 코딩', 'wayback_official': '공식 명단(Wayback 보관본)',
             'official_current': '공식 명단(현재본)', 'wikipedia_secondary': 'Wikipedia(2차)', 'wapo_secondary': 'WaPo(2차)'}
STATUS = {'stayed': '잔류', 'joined_new_member': '가입(신인·복귀)', 'joined_from_house': '가입(기존 의원)',
          'left_still_in_house': '이탈(하원 잔류)', 'left_house': '이탈(하원 퇴장)'}
CONGRESS_YEARS = {c: f'{1789 + 2 * (c - 1)}–{1789 + 2 * (c - 1) + 2}' for c in range(106, 120)}

# ---------------- 데이터 ----------------
counts = pd.read_csv(os.path.join(SRC, 'panel_counts.csv'))
counts['caucus'] = counts.caucus.str.lower()
summ = pd.read_csv(os.path.join(SRC, 'caucus_transition_summary.csv'))
rost = pd.read_csv(os.path.join(SRC, 'caucus_rosters_by_congress.csv'))
rost = rost[rost.congress >= 116]
trans = pd.read_csv(os.path.join(SRC, 'caucus_transitions.csv'))
trans = trans[trans.from_congress >= 116]
ev = pd.read_csv(os.path.join(SRC, 'roster_panel_long.csv'))
ev['caucus'] = ev.caucus.str.lower()
ev = ev[ev.congress >= 116]
panel = pd.read_csv(os.path.join(SRC, 'roster_panel.csv'))
panel = panel[panel.congress >= 116]
assert (rost.congress >= 116).all() and (ev.congress >= 116).all() and (panel.congress >= 116).all()

# 공개 CSV
counts.drop(columns=['n_icpsr_in_sources']).to_csv(os.path.join(DATA, 'caucus_counts_106_119.csv'), index=False)
summ.to_csv(os.path.join(DATA, 'caucus_change_summary_106_119.csv'), index=False)
pcols = ['congress', 'icpsr', 'bioname', 'bioguide_id', 'party', 'state', 'district', 'nominate_dim1', 'nominate_dim2'] + \
        ['cpc', 'ndc', 'bluedog', 'rmsp', 'mainstreet', 'rsc', 'hfc', 'psc']
panel[pcols].to_csv(os.path.join(DATA, 'members_116_119.csv'), index=False)
trans.to_csv(os.path.join(DATA, 'caucus_change_members_117_119.csv'), index=False)
ev[['caucus', 'congress', 'icpsr', 'bioname', 'source_type', 'source_url', 'snapshot_date', 'sha256', 'note']] \
    .to_csv(os.path.join(DATA, 'evidence_116_119.csv'), index=False)

# 의원 검색용 JSON
mem = []
for (icpsr, bio), g in panel.groupby(['icpsr', 'bioname']):
    rec = {'icpsr': int(icpsr), 'name': bio, 'party': g.party.iloc[-1], 'dim1': None if pd.isna(g.nominate_dim1.iloc[0]) else round(float(g.nominate_dim1.iloc[0]), 3),
           'terms': {}}
    for r in g.itertuples():
        rec['terms'][int(r.congress)] = {'sd': f'{r.state}-{int(r.district)}', 'c': [k for k in CAUCUS if getattr(r, k) == 1]}
    mem.append(rec)
json.dump(mem, open(os.path.join(DATA, 'members.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# ---------------- 공통 조각 ----------------
def page(title, active, body, desc=''):
    nav = [('index.html', '개요'), ('members.html', '의원 검색'), ('methods.html', '출처와 방법')]
    navh = ' '.join(f'<a href="{h}" class="{"on" if h == active else ""}">{t}</a>' for h, t in nav)
    cnav = ' '.join(f'<a href="caucus-{k}.html" class="{"on" if active == f"caucus-{k}.html" else ""}">{v[0]}</a>' for k, v in CAUCUS.items())
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap">
<link rel="stylesheet" href="assets/site.css"></head>
<body><main>
<nav class="top">{navh} <span style="color:var(--line)">|</span> {cnav}</nav>
{body}
<footer>강우창 · 고려대학교 · 데이터 기준일 2026-10-10 · 원자료와 재현 스크립트 출처는 <a href="methods.html">출처와 방법</a> 참조</footer>
</main></body></html>'''

def bars(key, w=300, h=150, big=False):
    """대별 인원 막대(106-119). 출처 없는 대는 '–'. 115|116 사이 점선 = 측정 방식 변경. 2차 출처 막대는 빗금."""
    sub = counts[counts.caucus == key].set_index('congress')
    color = f'var(--{CAUCUS[key][2]})' if key in CAUCUS else 'var(--muted)'
    vmax = max(10, sub.n_members_panel.max())
    pl, pr, pt, pb = 8, 8, 16, 22
    n = 14; bw = (w - pl - pr) / n
    out = [f'<svg class="bars" viewBox="0 0 {w} {h}" role="img" aria-label="{E(key)} 대별 인원">',
           f'<defs><pattern id="hatch-{key}" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           f'<rect width="4" height="4" fill="{color}" opacity="0.35"/><line x1="0" y1="0" x2="0" y2="4" stroke="{color}" stroke-width="2"/></pattern></defs>',
           f'<line class="gridline" x1="{pl}" x2="{w - pr}" y1="{h - pb}" y2="{h - pb}"/>']
    xdiv = pl + bw * 10
    out.append(f'<line class="divider" x1="{xdiv:.1f}" x2="{xdiv:.1f}" y1="{pt - 6}" y2="{h - pb}"><title>115대까지 Clarke(2020) 수기 코딩, 116대부터 공식 명단</title></line>')
    for i, c in enumerate(range(106, 120)):
        x = pl + bw * i
        if i % (1 if big else 2) == 0 or c == 119:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{h - 8}" text-anchor="middle">{c}</text>')
        if c not in sub.index:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{h - pb - 4}" text-anchor="middle">–</text>'); continue
        r = sub.loc[c]; v = int(r.n_members_panel)
        bh = (h - pt - pb) * v / vmax
        secondary = 'secondary' in r.source_types
        fill = f'url(#hatch-{key})' if secondary else color
        src = ', '.join(SRC_LABEL.get(s, s) for s in r.source_types.split('; '))
        out.append(f'<rect class="bar" x="{x + 1.5:.1f}" y="{h - pb - bh:.1f}" width="{bw - 3:.1f}" height="{bh:.1f}" rx="2" fill="{fill}">'
                   f'<title>{c}대 ({CONGRESS_YEARS[c]}): {v}명 · 출처: {E(src)}</title></rect>')
        if big or c in (106, 115, 116, 119) or i == 0:
            out.append(f'<text class="val" x="{x + bw / 2:.1f}" y="{h - pb - bh - 3:.1f}" text-anchor="middle">{v}</text>')
    out.append('</svg>')
    return ''.join(out)

LEGEND = ('<div class="legend"><span><span class="sw" style="background:var(--muted)"></span>막대 = 그 대에 출처에 이름이 실린 하원의원 수</span>'
          '<span>빗금 = 2차 출처(Wikipedia·WaPo)</span><span>점선 = 115|116대 사이 측정 방식 변경</span><span>– = 출처 없음</span></div>')

# ---------------- 개요 ----------------
cards = []
for k, (ko, en, col, desc) in CAUCUS.items():
    cards.append(f'<div class="card"><h3><a href="caucus-{k}.html">{ko}</a></h3><p class="sub">{en}</p>{bars(k)}</div>')
tbl = ['<div class="table-wrap"><table><tr><th>대</th><th>기간</th>' + ''.join(f'<th class="num">{v[0]}</th>' for v in CAUCUS.values()) + '</tr>']
for c in range(106, 120):
    row = [f'<td>{c}</td><td>{CONGRESS_YEARS[c]}</td>']
    for k in CAUCUS:
        s = counts[(counts.caucus == k) & (counts.congress == c)]
        row.append(f'<td class="num">{int(s.n_members_panel.iloc[0]) if len(s) else "–"}{"*" if len(s) and "secondary" in s.source_types.iloc[0] else ""}</td>')
    tbl.append(f'<tr class="{"flag" if c == 116 else ""}">' + ''.join(row) + '</tr>')
tbl.append('</table></div>')
agg = ', '.join(f'{v} {"·".join(str(c) for c in counts[counts.caucus == k].congress)}대' for k, v in AGG_ONLY.items())
body = f'''<h1>미국 의회 정당 계파</h1>
<p class="lede">미국 하원 이념 계파(코커스)의 소속 의원을 106–119대(1999–2026)에 걸쳐 추적합니다. 모든 수치는 출처 명단에서 센 값이며, 출처가 없는 칸은 비워 두었습니다.</p>
<div class="note">115대까지는 Clarke(2020)의 수기 코딩 자료, 116대부터는 각 코커스 공식 회원 페이지의 보관본(Wayback)을 씁니다. 두 구간 사이의 인원 변화에는 실제 변화와 측정 방식 차이가 섞여 있을 수 있습니다. 프리덤코커스는 공식 명단이 없어 Wikipedia 회원 목록(2차)을 씁니다.</div>
<h2>계파별 대별 인원</h2>{LEGEND}<div class="grid">{''.join(cards)}</div>
<h2>표로 보기</h2>
<p class="lede" style="font-size:0.88rem">* = 2차 출처. 116–119대 값은 그 대의 스냅샷 중 하나 이상에 이름이 실린 의원 수입니다. Clarke 자료에만 있는 계파: {agg}.</p>
{''.join(tbl)}'''
open(os.path.join(ROOT, 'index.html'), 'w').write(page('미국 의회 정당 계파', 'index.html', body, '미국 하원 이념 계파의 106–119대 소속 의원 추적'))

# ---------------- 계파별 ----------------
evg = {k: g for k, g in ev.groupby(['caucus', 'congress', 'icpsr'])}
for k, (ko, en, col, desc) in CAUCUS.items():
    s = summ[summ.caucus == k]
    t = ['<div class="table-wrap"><table><tr><th>직전 대 → 대</th><th class="num">직전</th><th class="num">이번</th>' +
         ''.join(f'<th class="num">{v}</th>' for v in STATUS.values()) + '<th>출처</th></tr>']
    for r in s.itertuples():
        t.append(f'<tr class="{"flag" if r.source_changed else ""}"><td>{r.from_congress} → {r.to_congress}</td><td class="num">{r.n_from}</td><td class="num">{r.n_to}</td>' +
                 ''.join(f'<td class="num">{getattr(r, st)}</td>' for st in STATUS) +
                 f'<td>{"출처 계열 변경" if r.source_changed else ""}</td></tr>')
    t.append('</table></div>')
    ros = []
    for c in sorted(rost[rost.caucus == k].congress.unique(), reverse=True):
        g = rost[(rost.caucus == k) & (rost.congress == c)].sort_values(['state', 'district'])
        st = trans[(trans.caucus == k) & (trans.to_congress == c)].set_index('icpsr').status.to_dict()
        left = trans[(trans.caucus == k) & (trans.to_congress == c) & trans.status.str.startswith('left')]
        rows = []
        for r in g.itertuples():
            e = evg.get((k, c, r.icpsr))
            links = ' '.join(f'<a href="{E(u)}" title="{E(str(d))}">[{i + 1}]</a>' for i, (u, d) in
                             enumerate(e[['source_url', 'snapshot_date']].drop_duplicates('source_url').itertuples(index=False))) if e is not None else ''
            stt = st.get(r.icpsr)
            rows.append(f'<tr><td>{E(r.bioname)}</td><td>{r.party}</td><td>{r.state}-{int(r.district)}</td>'
                        f'<td class="num">{"" if pd.isna(r.nominate_dim1) else f"{r.nominate_dim1:.3f}"}</td>'
                        f'<td class="st-{stt}">{STATUS.get(stt, "") if stt else ("–" if c == 116 else "")}</td><td>{links}</td></tr>')
        lefts = ''
        if len(left):
            lefts = '<p style="font-size:0.85rem;color:var(--muted)">직전 대 대비 이탈: ' + '; '.join(
                f'{E(x.bioname)} ({STATUS[x.status]})' for x in left.sort_values('bioname').itertuples()) + '</p>'
        srcs = counts[(counts.caucus == k) & (counts.congress == c)].iloc[0]
        ros.append(f'<details{" open" if c == 119 else ""}><summary>{c}대 ({CONGRESS_YEARS[c]}) · {len(g)}명</summary>'
                   f'<p style="font-size:0.85rem;color:var(--muted)">출처: {E(", ".join(SRC_LABEL.get(x, x) for x in srcs.source_types.split("; ")))}'
                   f'{" · 스냅샷 " + E(srcs.snapshot_dates) if isinstance(srcs.snapshot_dates, str) and srcs.snapshot_dates else ""}</p>{lefts}'
                   f'<div class="table-wrap"><table><tr><th>의원</th><th>정당</th><th>선거구</th><th class="num">NOMINATE 1차원</th><th>직전 대 대비</th><th>출처</th></tr>{"".join(rows)}</table></div></details>')
    extra = ''
    if k == 'rmsp':
        extra = ('<div class="note">Wikipedia RMSP 문서 2026-09-25판(oldid 1376718157)에는 "the partnership listed nine U.S. senators and all 91 members of the '
                 'Main Street Caucus as being affiliated with it"라고 적혀 있습니다. 두 조직은 이 사이트에서 별도 계열로 집계합니다.</div>')
    if k == 'hfc':
        extra = ('<div class="note">프리덤코커스는 회원 명단을 공개하지 않습니다. 116–119대 값은 Wikipedia "Freedom Caucus" 문서의 회원 목록(대마다 2개 판, oldid 고정)에 '
                 '이름이 실린 의원입니다. 문서 본문의 인원 문구와 목록 길이가 다를 수 있습니다(예: 2024-11-23판 본문 "at least 39", 목록 34명).</div>')
    if k == 'rsc':
        extra = '<div class="note">RSC는 2025-01-25 이후 공식 명단을 공개하지 않아, 119대 값은 Washington Post(2025-05-20) 기사 표(2차)입니다.</div>'
    body = f'''<h1>{ko}</h1><p class="lede">{en} — {desc}</p>{extra}
<h2>대별 인원</h2>{LEGEND}<div class="card">{bars(k, w=640, h=220, big=True)}</div>
<h2>구성원 변화 (직전 대 대비)</h2>
<p class="lede" style="font-size:0.88rem">두 대 모두 출처가 있을 때만 비교합니다. 강조된 행은 출처 계열이 바뀐 쌍이라 측정 방식 차이가 섞일 수 있습니다. 106–115대는 Clarke(2020) 자료의 집계입니다.</p>
{''.join(t)}
<h2>대별 명단 (116–119대)</h2>
<p class="lede" style="font-size:0.88rem">NOMINATE는 Voteview DW-NOMINATE 1차원(의원별 단일 값, 2026-10-10판). [1], [2]는 그 의원이 실린 원 출처(보관본·개정판) 링크입니다. 116대의 "직전 대 대비"는 115대 의원 단위 자료를 공개하지 않아 비워 둡니다.</p>
{''.join(ros)}'''
    open(os.path.join(ROOT, f'caucus-{k}.html'), 'w').write(page(f'{ko} · 미국 의회 정당 계파', f'caucus-{k}.html', body, f'{en} 대별 소속 의원'))

# ---------------- 의원 검색 ----------------
opts = ''.join(f'<option value="{k}">{v[0]}</option>' for k, v in CAUCUS.items())
body = f'''<h1>의원 검색</h1><p class="lede">116–119대 하원의원의 대별 계파 소속입니다. 이름(영문)으로 찾거나 대·계파로 거릅니다.</p>
<div class="controls"><input id="q" type="search" placeholder="이름 (예: Jayapal)" aria-label="이름 검색">
<select id="cong" aria-label="대"><option value="">모든 대</option>{''.join(f'<option value="{c}">{c}대</option>' for c in range(119, 115, -1))}</select>
<select id="cau" aria-label="계파"><option value="">모든 계파</option>{opts}</select>
<select id="party" aria-label="정당"><option value="">모든 정당</option><option value="D">민주당</option><option value="R">공화당</option></select></div>
<p id="count" style="font-size:0.85rem;color:var(--muted)"></p>
<div class="table-wrap"><table id="tbl"><thead><tr><th>의원</th><th>정당</th><th class="num">NOMINATE 1차원</th><th>116대</th><th>117대</th><th>118대</th><th>119대</th></tr></thead><tbody></tbody></table></div>
<script>window.CAUCUS_NAMES = {json.dumps({k: v[0] for k, v in CAUCUS.items()}, ensure_ascii=False)};</script>
<script src="assets/members.js"></script>'''
open(os.path.join(ROOT, 'members.html'), 'w').write(page('의원 검색 · 미국 의회 정당 계파', 'members.html', body, '116–119대 하원의원 계파 소속 검색'))

# ---------------- 출처와 방법 ----------------
body = '''<h1>출처와 방법</h1>
<h2>시기별 출처</h2>
<div class="table-wrap"><table><tr><th>대</th><th>출처</th><th>종류</th></tr>
<tr><td>106–115</td><td>Clarke, Andrew J. 2020. "Party Sub-Brands and American Party Factions." <i>American Journal of Political Science</i>. 복제 자료 <a href="https://doi.org/10.7910/DVN/SYYMJ0">doi:10.7910/DVN/SYYMJ0</a></td><td>연구자 수기 코딩</td></tr>
<tr><td>116–119</td><td>각 코커스 공식 회원 페이지의 Internet Archive(Wayback) 보관본. 대마다 최대 3개 시점</td><td>1차(보관본)</td></tr>
<tr><td>116–119</td><td>Wikipedia "Freedom Caucus", "Republican Main Street Partnership" 문서의 고정 개정판(oldid)</td><td>2차</td></tr>
<tr><td>119</td><td>RSC: Washington Post 2025-05-20 기사(Dormido &amp; Sotomayor) 표</td><td>2차</td></tr>
<tr><td>전 기간</td><td>의원 식별·이념 점수: <a href="https://voteview.com/data">Voteview</a> HSall_members.csv (2026-10-10 접근)</td><td>—</td></tr>
</table></div>
<h2>정의</h2>
<ul>
<li><b>소속</b>: 그 대에 출처 명단에 이름이 실린 하원의원. 116–119대는 그 대의 스냅샷 중 하나 이상에 실린 경우(가입·탈퇴 날짜는 담지 않음).</li>
<li><b>출처 없음</b>: 그 계파·대에 쓸 수 있는 명단이 없음. 0과 구분한다.</li>
<li><b>stale 보관본 제외</b>: 새 대 초기 보관본이 직전 대 마지막 보관본과 명단이 완전히 같으면 새 대 명단으로 보지 않는다(Blue Dog 2023-01-24 1건).</li>
<li><b>변화 분류</b>: 잔류 / 가입(신인·복귀: 직전 대에 하원의원이 아니었음) / 가입(기존 의원) / 이탈(하원 잔류) / 이탈(하원 퇴장: 은퇴·낙선·상원 이동 등).</li>
<li><b>NOMINATE</b>: Voteview DW-NOMINATE. 의원마다 경력 전체에 하나의 값이며, 현직 의원은 표결이 쌓이면 Voteview 갱신 때 값이 바뀔 수 있다.</li>
</ul>
<h2>알려진 공백과 주의</h2>
<ul>
<li>Main Street Caucus 116–117대, Problem Solvers Caucus 116–117대: 공식 페이지 보관본 없음.</li>
<li>RMSP 116대는 2019년 보관본만 있음(2020년 없음).</li>
<li>Clarke 자료에는 CPC 106대, RSC 106–107대가 없다. 114대 RSC·HFC에는 113대에만 재직한 의원 1명(icpsr 21320)이 코딩돼 있어 이 사이트 집계에서 빠진다(Clarke Table1보다 1명 적음).</li>
<li>RMSP(외부 단체 Republican Main Street Partnership)와 Main Street Caucus(하원 코커스)는 별도 계열이다.</li>
<li>출처 표기 오류 보정: RSC 2023-04-18판의 Blake Moore·Barry Moore 주 표기 뒤바뀜(이름으로 연결), "Marc Veasy"→Veasey, "Mike Haridopolis"→Haridopolos.</li>
</ul>
<h2>공개 범위</h2>
<p>Clarke(2020) 복제 자료에는 명시된 이용 라이선스가 없어(Dataverse: "limited information on how it can be used"), 106–115대는 계파별 인원·변화 집계만 싣고 의원 단위 명단은 싣지 않는다.</p>
<h2>내려받기</h2>
<ul>
<li><a href="data/caucus_counts_106_119.csv">caucus_counts_106_119.csv</a> — 계파 × 대 인원, 출처 유형, 스냅샷 날짜</li>
<li><a href="data/caucus_change_summary_106_119.csv">caucus_change_summary_106_119.csv</a> — 계파별 직전 대 대비 변화 집계</li>
<li><a href="data/members_116_119.csv">members_116_119.csv</a> — 116–119대 하원의원 × 대, 계파 소속(1/0/빈칸), NOMINATE 1·2차원</li>
<li><a href="data/caucus_change_members_117_119.csv">caucus_change_members_117_119.csv</a> — 117–119대 의원별 변화 상태</li>
<li><a href="data/evidence_116_119.csv">evidence_116_119.csv</a> — 소속 1마다 근거 출처(보관본 URL·개정판, 날짜, 원본 sha256)</li>
</ul>
<h2>재검증</h2>
<p>보관본 URL과 Wikipedia oldid는 누구나 다시 열어 확인할 수 있다. 원본 파일의 sha256이 evidence 파일에 있어, 같은 보관본을 다시 받아 동일한지 대조할 수 있다.</p>'''
open(os.path.join(ROOT, 'methods.html'), 'w').write(page('출처와 방법 · 미국 의회 정당 계파', 'methods.html', body, '자료 출처, 정의, 공백, 재검증 방법'))
print('built:', sorted(f for f in os.listdir(ROOT) if f.endswith('.html')))
print('data:', sorted(os.listdir(DATA)))
