# -*- coding: utf-8 -*-
"""生成 matching.html（岗位匹配分析页）"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'matching_data.json'), encoding='utf-8'))
data_js = json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>岗位匹配分析 · 杨钧凇</title>
<meta name="description" content="113 份按岗位定制的简历索引：每一条收藏职位对应一份匹配其招聘要求与职责的简历，可搜索、可筛选、可查看 PDF。">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231f3a5f'/%3E%3Ctext x='16' y='22' font-size='16' font-family='Georgia' fill='%23faf9f6' text-anchor='middle'%3E%E6%9D%A8%3C/text%3E%3C/svg%3E">
<style>
:root{--ink:#191b1f;--ink-2:#44474e;--ink-3:#7d818a;--paper:#faf9f6;--card:#fff;--line:#e6e3dc;--accent:#1f3a5f;--accent-soft:#eef1f6;--gold:#9a7b4f;--serif:Georgia,"Source Han Serif SC","Noto Serif SC","Songti SC",serif;--sans:-apple-system,"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif;--mono:"SF Mono",Consolas,monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);font-size:15px;line-height:1.7;-webkit-font-smoothing:antialiased}
::selection{background:#1f3a5f;color:#faf9f6}
nav{position:sticky;top:0;z-index:50;background:rgba(250,249,246,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav-inner{max-width:1180px;margin:0 auto;padding:16px 30px;display:flex;justify-content:space-between;align-items:center}
.nav-logo{font-family:var(--serif);font-size:16px;font-weight:700;letter-spacing:2px;text-decoration:none;color:var(--ink)}
.nav-logo span{color:var(--accent)}
.nav-right{display:flex;gap:24px;font-size:13px}
.nav-right a{color:var(--ink-2);text-decoration:none;letter-spacing:1px}
.nav-right a:hover{color:var(--accent)}
.wrap{max-width:1180px;margin:0 auto;padding:54px 30px 80px}
.hero-tag{font-family:var(--mono);font-size:11.5px;color:var(--gold);letter-spacing:3px;margin-bottom:13px}
h1{font-family:var(--serif);font-size:clamp(28px,4vw,40px);font-weight:700;letter-spacing:1px;margin-bottom:14px}
.sub{color:var(--ink-2);font-size:14.5px;max-width:780px;line-height:1.9}
.sub b{color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:32px 0 26px}
.stat{background:var(--paper);padding:18px 22px}
.stat b{font-family:var(--serif);font-size:24px;color:var(--accent)}
.stat span{display:block;font-size:11.5px;color:var(--ink-3);letter-spacing:1.5px;margin-top:4px}
.filterbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
input[type=text],select{
  border:1px solid var(--line);background:var(--card);padding:10px 14px;font-size:13.5px;
  font-family:inherit;color:var(--ink);border-radius:2px;outline:none;transition:border-color .2s}
input[type=text]:focus,select:focus{border-color:var(--accent)}
input[type=text]{flex:1;min-width:220px}
.count{font-size:12.5px;color:var(--ink-3);margin-bottom:14px;letter-spacing:.5px}
.count b{color:var(--accent)}
.tbl-wrap{background:var(--card);border:1px solid var(--line);overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:880px}
th{background:#f4f2ed;color:var(--ink-2);text-align:left;padding:11px 14px;font-weight:600;font-size:11.5px;letter-spacing:1px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid #f0eee9;color:var(--ink-2);vertical-align:top}
tbody tr{transition:background .15s}
tbody tr:hover{background:#f7f5f0}
td .t{font-weight:600;color:var(--ink);font-size:13px}
.num{font-family:var(--mono);color:var(--ink-3);font-size:11.5px}
.arch{display:inline-block;background:var(--accent-soft);color:var(--accent);padding:1px 8px;font-size:11px;border-radius:2px;white-space:nowrap}
.pdflink{display:inline-block;color:var(--accent);text-decoration:none;font-size:12px;font-weight:600;border-bottom:1px solid rgba(31,58,95,.3);white-space:nowrap}
.pdflink:hover{border-bottom-color:var(--accent)}
.empty{padding:60px 20px;text-align:center;color:var(--ink-3);font-size:13.5px}
footer{border-top:1px solid var(--line)}
.foot-inner{max-width:1180px;margin:0 auto;padding:28px 30px;font-size:12px;color:var(--ink-3);display:flex;justify-content:space-between;letter-spacing:1px;flex-wrap:wrap;gap:8px}
@media(max-width:760px){.stats{grid-template-columns:1fr 1fr}.wrap{padding:40px 20px 60px}}
</style>
</head>
<body>
<nav><div class="nav-inner">
  <a class="nav-logo" href="index.html">杨钧凇<span>.</span></a>
  <div class="nav-right"><a href="index.html">← 返回主页</a></div>
</div></nav>

<div class="wrap">
  <div class="hero-tag">JOB — RESUME MATCHING</div>
  <h1>岗位匹配分析</h1>
  <p class="sub">
    三大招聘平台（Boss直聘 / 智联 / 猎聘）收藏的 <b>116 个岗位</b>，每一个都有一份
    <b>按其招聘要求与职责定制的工作经验与项目经验描述</b>——共 <b>113 份简历</b>（Word + PDF 双格式）。
    支持按职位、公司搜索，按平台、方向、城市筛选；点击行内「PDF」可查看该岗位对应的定制简历全文。
  </p>

  <div class="stats">
    <div class="stat"><b>113</b><span>定制简历（docx+PDF）</span></div>
    <div class="stat"><b>56</b><span>长春岗位</span></div>
    <div class="stat"><b>40</b><span>战略规划方向</span></div>
    <div class="stat"><b>18+</b><span>AI 应用 / AI 产品方向</span></div>
  </div>

  <div class="filterbar">
    <input type="text" id="q" placeholder="搜索职位或公司，如：战略 / 芯源微 / AI">
    <select id="fSrc"><option value="">全部平台</option></select>
    <select id="fArch"><option value="">全部方向</option></select>
    <select id="fCity"><option value="">全部城市</option></select>
    <select id="fSort">
      <option value="no">按编号</option>
      <option value="salary">按薪资（高→低）</option>
    </select>
  </div>
  <div class="count">当前显示 <b id="cnt">0</b> / __TOTAL__ 条</div>

  <div class="tbl-wrap">
  <table>
    <thead><tr><th>#</th><th>职位</th><th>公司</th><th>薪资</th><th>地点</th><th>平台</th><th>定制方向</th><th>简历</th></tr></thead>
    <tbody id="tb"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none">没有匹配的结果，试试清空筛选条件</div>
  </div>
</div>

<footer><div class="foot-inner">
  <span>© 2026 杨钧凇 · <a href="index.html" style="color:inherit">个人作品集</a></span>
  <span>数据来源：三平台收藏列表 · 更新于 2026-10-29</span>
</div></footer>

<script>
const DATA = __DATA__;
const q = document.getElementById('q'), fSrc = document.getElementById('fSrc'),
      fArch = document.getElementById('fArch'), fCity = document.getElementById('fCity'),
      fSort = document.getElementById('fSort'), tb = document.getElementById('tb'),
      cnt = document.getElementById('cnt'), emptyEl = document.getElementById('empty');

function cityOf(c){ for (const k of ['长春','沈阳','大连']) if (c.includes(k)) return k; return '其他'; }
function salNum(s){
  s = (s||'').replace(/K/g,'k');
  if (s.includes('/')) s = s.split('/').pop() || s;
  let m = s.match(/([\d.]+)\s*[-~]\s*([\d.]+)\s*k/i);
  if (m) return parseFloat(m[2]);
  m = s.match(/([\d.]+)\s*k/i); if (m) return parseFloat(m[1]);
  m = s.match(/([\d.]+)\s*[-~]\s*([\d.]+)\s*万/);
  if (m) return parseFloat(m[2]) * 10;
  m = s.match(/([\d.]+)\s*万/); if (m) return parseFloat(m[1]) * 10;
  m = s.match(/([\d.]+)/); return m ? parseFloat(m[1]) : 0;
}
const srcs = [...new Set(DATA.map(d=>d.src))].sort();
srcs.forEach(s=>fSrc.insertAdjacentHTML('beforeend',`<option>${s}</option>`));
const archs = [...new Set(DATA.map(d=>d.arch))].sort();
archs.forEach(s=>fArch.insertAdjacentHTML('beforeend',`<option>${s}</option>`));
const cities = [...new Set(DATA.map(d=>cityOf(d.city)))].sort();
cities.forEach(s=>fCity.insertAdjacentHTML('beforeend',`<option>${s}</option>`));

let cur = DATA.slice();
function apply(){
  const kw = q.value.trim().toLowerCase();
  const fs = fSrc.value, fa = fArch.value, fc = fCity.value;
  cur = DATA.filter(d =>
    (!kw || (d.title + ' ' + d.company).toLowerCase().includes(kw)) &&
    (!fs || d.src === fs) && (!fa || d.arch === fa) && (!fc || cityOf(d.city) === fc));
  if (fSort.value === 'salary') cur = cur.slice().sort((a,b)=>salNum(b.salary)-salNum(a.salary));
  else cur = cur.slice().sort((a,b)=>a.no-b.no);
  render();
}
function render(){
  cnt.textContent = cur.length;
  emptyEl.style.display = cur.length ? 'none' : 'block';
  tb.innerHTML = cur.map(d => '<tr>'
    + '<td class="num">' + String(d.no).padStart(2,'0') + '</td>'
    + '<td><div class="t">' + d.title + '</div></td>'
    + '<td><div>' + d.company + '</div></td>'
    + '<td style="white-space:nowrap">' + d.salary + '</td>'
    + '<td style="font-size:12px">' + d.city + '</td>'
    + '<td style="font-size:12px;white-space:nowrap">' + d.src + '</td>'
    + '<td><span class="arch">' + d.arch + '</span></td>'
    + '<td>' + (d.pdf ? '<a class="pdflink" href="' + d.pdf + '" target="_blank">PDF ↗</a>' : '—') + '</td>'
    + '</tr>').join('');
}
[q,fSrc,fArch,fCity].forEach(el => el.addEventListener('input', apply));
fSort.addEventListener('change', apply);
apply();
</script>
</body>
</html>"""

html = TPL.replace('__DATA__', data_js).replace('__TOTAL__', str(len(rows)))
out = os.path.join(BASE, 'matching.html')
open(out, 'w', encoding='utf-8').write(html)
print('matching.html 生成:', round(len(html)/1024), 'KB，行数', len(rows))
