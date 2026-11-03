"""Generate the C-version inner pages from data.json + the page copy in the client's docs.

Usage: python -I gen.py <data.json> <site_dir>
"""
import sys, os, re, json, html
from PIL import Image

DATA, SITE = sys.argv[1], sys.argv[2]
D = json.load(open(DATA))
E = html.escape
AC = ' aria-current="page"'
NA_CLS = ' class="na"'
PAGES = []


def dims(src):
    try:
        return Image.open(os.path.join(SITE, src)).size
    except Exception:
        return None


def im(src, alt='', cls='', lazy=True, extra=''):
    wh = dims(src)
    a = f' width="{wh[0]}" height="{wh[1]}"' if wh else ''
    l = ' loading="lazy" decoding="async"' if lazy else ''
    c = f' class="{cls}"' if cls else ''
    return f'<img src="{src}" alt="{E(alt)}"{a}{l}{c}{extra}>'


# ---------------------------------------------------------------- migrated HTML clean-up
def fix_html(h, spec_prefix='s'):
    # images: real dimensions, lazy
    def _img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        alt = re.search(r'alt="([^"]*)"', tag)
        return im(src, html.unescape(alt.group(1)) if alt else '')
    h = re.sub(r'<img\b[^>]*>', _img, h)
    h = re.sub(r'<p>\s*(?:<br/>\s*)*</p>', '', h)
    # tables: header row when the old table had none, width class, scroll wrapper
    def _tbl(m):
        t = m.group(0)
        rows = re.findall(r'<tr\b.*?</tr>', t, re.S)
        cols = 0
        for r in rows[:6]:
            n = 0
            for c in re.finditer(r'<t[hd]\b([^>]*)>', r):
                cs = re.search(r'colspan="(\d+)"', c.group(1))
                n += int(cs.group(1)) if cs else 1
            cols = max(cols, n)
        if '<th' not in t and rows:
            first = rows[0].replace('<td', '<th').replace('</td>', '</th>')
            t = t.replace(rows[0], first, 1)
        size = 'wide' if cols > 9 else ('mid' if cols > 4 else '')
        t = re.sub(r'<table class="tbl">', f'<table class="tbl {size}">'.replace(' ">', '">'), t, 1)
        hint = '<p class="scroll-hint">左右滑動查看完整表格</p>'
        return f'<div class="tbl-wrap">{t}</div>{hint}'
    h = re.sub(r'<table class="tbl">.*?</table>', _tbl, h, flags=re.S)
    # unique ids for numbered spec headings
    n = [0]
    def _sid(m):
        n[0] += 1
        return f'<h3 class="spec-h" id="{spec_prefix}{n[0]}">'
    h = re.sub(r'<h3 class="spec-h"(?: id="[^"]*")?>', _sid, h)
    h = h.replace('<p>information from cosmotech-jp.</p>', '<p class="legend">資料來源：COSMO TECH（cosmotech-jp）</p>')
    return h


def text_of(h, n=None):
    t = re.sub(r'<[^>]+>', ' ', h)
    t = html.unescape(re.sub(r'\s+', ' ', t)).strip()
    if n and len(t) > n:
        t = t[:n].rstrip('，、。:： ') + '…'
    return t


# ---------------------------------------------------------------- site chrome
NAV = [
    ('index.html', '首頁', 'Home', None, 'home'),
    ('about.html', '關於我們', 'About', [('about.html', '關於圓華油品'), ('milestone.html', '歷史沿革'), ('team.html', '服務團隊')], 'about'),
    ('products.html', '油品介紹', 'Products', [('yushiro-plant.html', 'SAN-I Yushiro 植物性油品'), ('yushiro.html', 'SAN-I Yushiro 油品系列'), ('battor.html', 'Battor 油品系列'), ('formosa.html', '台塑 潤滑油系列')], 'products'),
    ('equipment.html', '廢液(水)處理裝置', 'Equipment', None, 'equipment'),
    ('license.html', '廢油/水清運牌', 'License', None, 'license'),
    ('news.html', '最新消息', 'News', [('news.html#nexustest', '跨界合作－半導體電子設備 NEXUSTEST'), ('news.html#expo', '最新展覽'), ('news.html#launch', '新產品發表'), ('news.html#other', '其他新發布')], 'news'),
    ('gallery.html', '歷年展會/活動花絮', 'Gallery', [('gallery.html#expo', '展覽花絮'), ('gallery.html#press', '相關報導、專訪'), ('gallery.html#events', '活動、聚餐'), ('gallery.html#video', '影片')], 'gallery'),
    ('faq.html', '常見問題', 'FAQ', [('faq.html', '常見問題'), ('knowledge.html', '油品知識區'), ('oil-table.html', '油品標準用油表'), ('water-knowledge.html', '廢液(水)處理知識區')], 'faq'),
    ('contact.html', '聯絡我們', 'Contact', None, 'contact'),
]

SVG_SYMBOLS = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-drum-b" viewBox="0 0 48 64"><path d="M4 10c0-4 9-7 20-7s20 3 20 7v44c0 4-9 7-20 7S4 58 4 54z" fill="#F3C640"/><path d="M4 40c0 4 9 7 20 7s20-3 20-7v14c0 4-9 7-20 7S4 58 4 54z" fill="#1E1A10"/><ellipse cx="24" cy="10" rx="20" ry="7" fill="#fff" fill-opacity=".38"/><path d="M4 25c0 4 9 7 20 7s20-3 20-7" fill="none" stroke="#000" stroke-opacity=".2" stroke-width="2"/><ellipse cx="15" cy="9" rx="3" ry="1.4" fill="#fff" fill-opacity=".8"/></symbol>
  <symbol id="i-drop" viewBox="0 0 40 56"><path d="M20 2S4 22 4 35a16 16 0 0032 0C36 22 20 2 20 2z" fill="currentColor"/><path d="M12 36a8 8 0 006 8" stroke="#fff" stroke-opacity=".75" stroke-width="3" fill="none" stroke-linecap="round"/></symbol>
  <symbol id="i-sprout" viewBox="0 0 56 64"><path d="M28 62V30" stroke="currentColor" stroke-width="4" stroke-linecap="round"/><path d="M28 34C28 18 40 8 54 8c0 16-12 26-26 26z" fill="currentColor"/><path d="M28 40C28 28 18 20 4 20c0 12 10 20 24 20z" fill="currentColor" opacity=".72"/></symbol>
  <symbol id="i-gear" viewBox="0 0 48 48"><path d="M24 3l3.4 5.2 6-1.4 1 6.1 5.6 2.7-2.4 5.7 3.4 5.2-5.2 3.4.2 6.2-6.1.2-2.7 5.6-5.2-3.4-5.2 3.4-2.7-5.6-6.1-.2.2-6.2-5.2-3.4 3.4-5.2-2.4-5.7 5.6-2.7 1-6.1 6 1.4z" fill="currentColor"/><circle cx="24" cy="24" r="7.5" fill="#fff"/></symbol>
  <symbol id="i-pail" viewBox="0 0 44 54"><path d="M10 18C10 6 34 6 34 18" fill="none" stroke="#7C8A81" stroke-width="2.4"/><path d="M5 18h34l-3 31a4 4 0 01-4 4H12a4 4 0 01-4-4z" fill="currentColor"/><path d="M5 18c0-3 8-5 17-5s17 2 17 5-8 5-17 5S5 21 5 18z" fill="#fff" fill-opacity=".4"/><rect x="11" y="29" width="22" height="12" rx="2" fill="#fff" fill-opacity=".6"/></symbol>
  <symbol id="i-doc" viewBox="0 0 48 48"><path d="M12 4h17l9 9v29a2 2 0 01-2 2H12a2 2 0 01-2-2V6a2 2 0 012-2z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><path d="M29 4v9h9M17 22h14M17 29h14M17 36h9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
  <symbol id="i-cam" viewBox="0 0 48 48"><path d="M6 15a3 3 0 013-3h6l3-4h12l3 4h6a3 3 0 013 3v22a3 3 0 01-3 3H9a3 3 0 01-3-3z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><circle cx="24" cy="26" r="8" fill="none" stroke="currentColor" stroke-width="2.4"/></symbol>
</svg>'''


def header(section, current):
    lis = []
    for href, zh, en, subs, key in NAV:
        cur = ' class="has cur"' if subs and key == section else (' class="has"' if subs else (' class="cur"' if key == section else ''))
        ac = ' aria-current="page"' if href == current else ''
        s = f'<li{cur}><a href="{href}"{ac}>{zh}<small>{en}</small></a>'
        if subs:
            s += '\n        <ul class="sub">' + ''.join(
                f'\n          <li><a href="{h}"{AC if h == current else ""}>{t}</a></li>' for h, t in subs) + '\n        </ul>\n      '
        lis.append(s + '</li>')
    return f'''<header class="hdr" id="hdr">
  <div class="hdr-in">
    <a class="brand" href="index.html" aria-label="圓華油品 首頁">
      <span class="badge"><img src="img/mark.png" width="26" height="36" alt=""></span>
      <span><b translate="no">圓華油品</b><small>YUAN HUA OIL</small></span>
    </a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="nav" aria-label="開啟選單"><i></i><i></i><i></i></button>
    <ul class="nav" id="nav">
      {chr(10).join("      " + l if i else l for i, l in enumerate(lis))}
    </ul>
    {lang_switch(current)}
  </div>
</header>'''


def lang_switch(fn):
    # the English build (i18n.py) flips these two links; translate="no" keeps them out of the translation table
    return (f'<div class="lang-sw" translate="no" role="group" aria-label="語言 Language">'
            f'<a href="{fn}" hreflang="zh-Hant" lang="zh-Hant" aria-current="true">中文</a>'
            f'<a href="en/{fn}" hreflang="en" lang="en">EN</a></div>')


SITEMAP = '''<nav class="sitemap" data-rv="up" aria-label="網站地圖">
        <div><b>關於我們</b><a href="about.html">關於圓華油品</a><a href="milestone.html">歷史沿革</a><a href="team.html">服務團隊</a></div>
        <div><b>油品介紹</b><a href="yushiro-plant.html">SAN-I Yushiro 植物性油品</a><a href="yushiro.html">SAN-I Yushiro 油品系列</a><a href="battor.html">Battor 油品系列</a><a href="formosa.html">台塑 潤滑油系列</a></div>
        <div><b>最新消息</b><a href="news.html#nexustest">跨界合作－半導體電子設備 NEXUSTEST</a><a href="news.html#expo">最新展覽</a><a href="news.html#launch">新產品發表</a><a href="news.html#other">其他新發布</a></div>
        <div><b>歷年展會/活動花絮</b><a href="gallery.html#expo">展覽花絮</a><a href="gallery.html#press">相關報導、專訪</a><a href="gallery.html#events">活動、聚餐</a><a href="gallery.html#video">影片</a></div>
        <div><b>常見問題</b><a href="knowledge.html">油品知識區</a><a href="oil-table.html">油品標準用油表</a><a href="water-knowledge.html">廢液(水)處理知識區</a></div>
        <div><b>其他</b><a href="index.html">首頁</a><a href="equipment.html">廢液(水)處理裝置</a><a href="license.html">廢油/水清運牌</a><a href="contact.html">聯絡我們</a></div>
      </nav>'''

FOOTER = f'''<footer>
  <div class="foot-loop" aria-hidden="true"><div class="track"><span>YUAN HUA OIL</span><span>從油品開始，實踐更好的製造環境</span><span>YUAN HUA OIL</span><span>從油品開始，實踐更好的製造環境</span><span>YUAN HUA OIL</span><span>從油品開始，實踐更好的製造環境</span><span>YUAN HUA OIL</span><span>從油品開始，實踐更好的製造環境</span></div></div>
  <div class="wrap">
    <div class="top">
      <div data-rv="up">
        <a class="brand" href="index.html" aria-label="圓華油品 首頁">
          <span class="badge"><img src="img/mark.png" width="26" height="36" alt=""></span>
          <span><b translate="no">圓華油品</b><small>YUAN HUA OIL CO., LTD.</small></span>
        </a>
        <div class="partners"><a href="yushiro.html" aria-label="SAN-I Yushiro 油品系列"><img src="img/sterling-logo3.png" width="132" height="60" alt="SAN-I YUSHIRO" loading="lazy"></a><a href="equipment.html" aria-label="廢液(水)處理裝置"><img src="img/sterling-logo2.png" width="132" height="60" alt="CosmoTech" loading="lazy"></a><a href="battor.html" aria-label="Battor 油品系列"><img src="img/sterling-logo.png" width="132" height="60" alt="Battor" loading="lazy"></a></div>
      </div>
      {SITEMAP}
    </div>
    <address>台中市烏日區環中路八段 860 巷 101 號<br>服務範圍：全台皆有（以中部地區為主要服務區域）<br>切削油／切削液／金屬加工油／植物性油品／廢水處理設備</address>
    <p class="copy">© 2026 YUAN HUA OIL CO., LTD. — DEMO CONCEPT</p>
  </div>
</footer>'''

LINE = 'https://line.me/R/ti/p/%40wmz2174k'


def cta_band(title=('有現場問題，', '不確定該從哪裡開始？'), qs=None, lede=None, item=None):
    qs = qs or ['不確定該使用哪一款油品？', '正在處理切削液壽命、異味、生鏽或廢水問題？']
    lede = lede or '告訴我們目前的加工條件與使用情況，由圓華團隊協助了解需求並評估適合的產品與服務方式。'
    ask = 'contact.html#form' if not item else f'contact.html?item={item}#form'
    return f'''<section class="sec contact cta-sec">
  <div class="wrap">
    <div class="contact-panel" data-rv="rise">
      <span class="glow" aria-hidden="true"></span>
      <div class="props" data-rv="kids" style="--d:400ms" aria-hidden="true">
        <svg width="38" viewBox="0 0 48 64" style="--n:0"><use href="#i-drum-b"/></svg>
        <svg width="30" viewBox="0 0 44 54" style="--n:1;color:#1E8A49"><use href="#i-pail"/></svg>
        <svg width="34" viewBox="0 0 48 48" style="--n:2;color:#0B4A2C"><g class="spin" style="transform-origin:24px 24px"><use href="#i-gear"/></g></svg>
        <svg width="30" viewBox="0 0 56 64" style="--n:3;color:#1E8A49"><use href="#i-sprout"/></svg>
      </div>
      <div class="contact-text">
        <span class="chip w" data-rv="pop">Contact ／ 聯絡我們</span>
        <h2 class="sec-title" data-rv="mask"><span class="ln" style="--k:0"><span>{title[0]}</span></span><span class="ln" style="--k:1"><span>{title[1]}</span></span></h2>
        <ul class="qs" data-rv="up">{''.join(f'<li>{q}</li>' for q in qs)}</ul>
        <p class="lede" data-rv="up">{lede}</p>
      </div>
      <div class="info" data-rv="pop" style="--d:200ms">
        <h3>圓華油品股份有限公司</h3>
        <dl>
          <div class="row"><dt>Tel</dt><dd><a href="tel:+886423355559">04-2335-5559</a></dd></div>
          <div class="row"><dt>Fax</dt><dd>04-2335-8886</dd></div>
          <div class="row"><dt>Mail</dt><dd><a href="mailto:battor.oil@gmail.com">battor.oil@<wbr>gmail.com</a></dd></div>
          <div class="row"><dt>Hours</dt><dd>週一至週五 08:00 – 17:00</dd></div>
        </dl>
        <div class="btns">
          <a class="btn y" href="{ask}">留下需求 <i>→</i></a>
          <a class="btn g ping" href="{LINE}" target="_blank" rel="noopener" aria-label="LINE 詢問（LINE ID：@wmz2174k，另開新視窗）">LINE 詢問 <i>→</i></a>
        </div>
      </div>
    </div>
  </div>
</section>'''


def crumbs(items):
    out = ['<a href="index.html">首頁</a>']
    for i, (href, t) in enumerate(items):
        out.append('<i>/</i>')
        out.append(f'<b aria-current="page">{E(t)}</b>' if i == len(items) - 1 or not href else f'<a href="{href}">{E(t)}</a>')
    return '<nav class="crumbs" aria-label="麵包屑" data-h style="--d:0ms">' + ''.join(out) + '</nav>'


def hero(crumb, chip, lines, lede='', sub='', cta='', img='img/hero-3.jpg', pos='50% 50%', small=False, art='', art_card=False):
    tapes = ''.join(f'<span class="tape{" y" if i % 2 else ""}" style="--n:{i}">{E(l)}</span>' for i, l in enumerate(lines))
    cls = 'phero' + (' sm' if small else '') + (' has-art' if art else '')
    art_html = ''
    if art:
        art_html = f'<div class="phero-art{" card-art" if art_card else ""}" aria-hidden="true">{im(art, "", lazy=False)}</div>'
    return f'''<section class="{cls}" data-sc>
  <div class="phero-bg">{im(img, "", lazy=False, extra=f' style="--pos:{pos}" fetchpriority="high"')}</div>
  <div class="phero-shade" aria-hidden="true"></div>
  {art_html}
  <div class="wrap phero-in">
    {crumbs(crumb)}
    <span class="chip w" data-h style="--d:120ms">{chip}</span>
    <h1 class="pcatch">{tapes}</h1>
    {f'<p class="phero-sub" data-h style="--d:520ms">{sub}</p>' if sub else ''}
    {f'<p class="phero-lede" data-h style="--d:640ms">{lede}</p>' if lede else ''}
    {f'<div class="phero-cta" data-h style="--d:780ms">{cta}</div>' if cta else ''}
  </div>
</section>'''


def lnav(items, current, label):
    lis = ''.join(f'<li><a href="{h}"{AC if h == current else ""}>{t}</a></li>' for h, t in items)
    return f'<nav class="lnav" aria-label="{label}"><div class="wrap"><ul>{lis}</ul></div></nav>'


def sec_title(lines, tag='h2'):
    return f'<{tag} class="sec-title" data-rv="mask">' + ''.join(f'<span class="ln" style="--k:{i}"><span>{l}</span></span>' for i, l in enumerate(lines)) + f'</{tag}>'


def page(fn, title, desc, section, body, preload=None, lightbox=False):
    pre = f'\n<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ''
    lb = '''
<dialog class="lb" aria-label="照片檢視">
  <figure><img src="" alt=""><figcaption></figcaption></figure>
  <button class="x" type="button" aria-label="關閉">✕</button>
  <button class="pv" type="button" aria-label="上一張">←</button>
  <button class="nx" type="button" aria-label="下一張">→</button>
</dialog>''' if lightbox else ''
    out = f'''<!doctype html>
<html lang="zh-Hant" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}｜圓華油品 YUAN HUA OIL</title>
<meta name="description" content="{E(desc)}">
<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="img/favicon-64.png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="alternate" hreflang="zh-Hant" href="{fn}">
<link rel="alternate" hreflang="en" href="en/{fn}">{pre}
<script>document.documentElement.classList.add('js')</script>
<noscript><style>.hdr{{background:rgba(255,255,255,.94)}} .hdr .brand b{{color:#0E663B}} .hdr .brand b,.hdr .brand small,.hdr .nav>li>a{{color:#17251D;text-shadow:none}}</style></noscript>
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
{SVG_SYMBOLS}
{header(section, fn)}

<main id="main">
{body}
</main>

{FOOTER}
{lb}
<script src="assets/site.js" defer></script>
</body>
</html>
'''
    out = re.sub(r'\n\s*\n\s*\n+', '\n\n', out)
    # old equipment pages were renumbered to model slugs
    for o, n in EQ_FILE.items():
        out = out.replace(f'href="{o}.html"', f'href="{n}"')
    # brief: every mention of Yushiro must read "SAN-I Yushiro" (text only; file names are lower-case)
    out = re.sub(r'San-I Yushiro|SAN-I YUSHIRO(?= 化學)', 'SAN-I Yushiro', out)
    out = re.sub(r'(?<!SAN-I )(?<!SAN-I\u00a0)(?<![-/\w])Yushiro\b', 'SAN-I Yushiro', out)
    out = out.replace('ENVIROMENTAL', 'ENVIRONMENTAL')   # old-site typo
    open(os.path.join(SITE, fn), 'w').write(out)
    PAGES.append(fn)


def gal(images, alt):
    lis = []
    for i, g in enumerate(images):
        if not g:
            continue
        lis.append(f'<li><button type="button" data-full="{g["src"]}" data-alt="{E(alt)}" aria-label="放大第 {i + 1} 張照片">{im(g["src"], f"{alt} 照片 {i + 1}")}</button></li>')
    return '<ul class="gal" data-rv="up">' + ''.join(lis) + '</ul>'


# ---------------------------------------------------------------- about section
ABOUT_NAV = [('about.html', '關於圓華油品'), ('milestone.html', '歷史沿革'), ('team.html', '服務團隊')]
CP = D['company_photos']


def about():
    body = hero([('about.html', '關於我們'), (None, '關於圓華油品')], 'About ／ 關於我們',
                ['從金屬加工油品出發，', '持續走進加工現場'],
                lede='圓華油品長期投入金屬加工與工業用油領域，從油品供應出發，逐步累積產品應用、現場服務與製程問題處理經驗。隨著客戶需求從「選擇適合的油品」，延伸到使用管理、換液、廢水處理與後續清運，圓華也持續拓展服務內容，希望以更完整的方式，回應製造現場實際面對的問題。',
                sub='產品只是起點，真正重要的是能不能符合您的現場加工需求。',
                cta='<a class="btn y" href="milestone.html">查看圓華歷史沿革 <i>→</i></a><a class="btn glass" href="team.html">認識服務團隊 <i>→</i></a>',
                img='img/hero-3.jpg', pos='50% 36%')
    body += lnav(ABOUT_NAV, 'about.html', '關於我們')
    body += f'''
<section class="sec first" data-sc>
  <div class="wrap split">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Understanding ／ 理解現場</span>
      {sec_title(['從油品開始，', '理解加工與製造現場真正的需求'])}
      <div class="copy" data-rv="up">
        <p>金屬加工現場面對的問題，往往不只是一款油品是否符合規格。</p>
        <p>加工材質、機台設備、刀具、加工方式、水質、使用濃度與日常管理，都可能影響切削液使用狀況、加工品質與後續廢液處理。</p>
        <p>因此，圓華在提供產品之外，也重視實際使用條件與現場狀況。從了解加工需求、產品使用，到後續處理方式，希望讓每一次產品選擇，都更貼近客戶真正面對的問題。</p>
      </div>
      <ul class="tags" data-rv="up" aria-label="影響使用狀況的現場條件"><li>加工材質</li><li>機台設備</li><li>刀具</li><li>加工方式</li><li>水質</li><li>使用濃度</li><li>日常管理</li></ul>
    </div>
    <div class="photo-wrap" data-rv="right">
      <span class="sun" aria-hidden="true"></span>
      <figure class="photo r-big ar-54">{im(CP[7]["src"], "圓華油品實驗室，研究人員檢測油品")}</figure>
      <div class="vcatch" aria-hidden="true" data-rv="vwipe"><span style="--n:0">先理解</span><span class="y" style="--n:1">再建議</span></div>
    </div>
  </div>
</section>

<section class="stage-slab round-l" data-sc>
  <span class="slab-glow" aria-hidden="true"></span>
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Service Path ／ 服務延伸</span>
      {sec_title(['客戶的需求延伸到哪裡，', '我們的服務就持續往前跟進'])}
      <p class="lede" data-rv="up">圓華最初從金屬加工油品出發，但在長期服務過程中逐漸發現，客戶真正面對的問題不會只停留在產品交付。油品導入之後，仍可能涉及使用狀況、濃度管理、換油換水、廢液處理，以及後續清運等不同環節。</p>
      <p class="lede" data-rv="up">因此，圓華逐步從產品供應延伸至現場服務、廢水處理設備與後續處理，希望減少客戶面對不同供應商時的溝通成本，也讓油品使用與後端處理之間有更完整的銜接。</p>
    </div>
    <ol class="stages">
      <li data-rv="up"><span class="n">01</span><h3>油品與產品應用</h3><p>從切削液、切削油到各類工業用油，依實際使用需求協助評估。</p></li>
      <li data-rv="up"><span class="n">02</span><h3>現場使用與技術支援</h3><p>依產品導入與使用狀況，提供後續服務與相關支援。</p></li>
      <li data-rv="up"><span class="n">03</span><h3>設備與後續處理</h3><p>依需求延伸至廢水處理設備、換油換水與廢油／廢水清運。</p></li>
    </ol>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Brands ／ 品牌與技術</span>
      {sec_title(['以產品與技術為基礎，', '持續擴充服務能力'])}
      <p class="lede" data-rv="up">圓華長期投入金屬加工與工業用油市場，並持續透過不同品牌、產品與設備，建立更完整的服務能力。以 SAN-I Yushiro 日本技術與金屬加工液為核心，搭配 Battor、Formosa 等不同油品選擇，並延伸至 CosmoTech 廢水處理設備，讓服務範圍能從製程用油進一步銜接至後端處理需求。</p>
    </div>
    <div class="brands">
      <a class="brand-card" href="yushiro.html" data-rv="up"><span class="logo"><img src="img/sterling-logo3.png" width="132" height="60" alt="SAN-I YUSHIRO" loading="lazy"></span><h3>SAN-I Yushiro</h3><p>日本金屬加工液與相關油品技術</p><i class="go">→</i></a>
      <a class="brand-card" href="battor.html" data-rv="up"><span class="logo"><img src="img/sterling-logo.png" width="132" height="60" alt="Battor" loading="lazy"></span><h3>Battor</h3><p>金屬加工與工業用油產品</p><i class="go">→</i></a>
      <a class="brand-card" href="formosa.html" data-rv="up"><span class="logo"><span class="wordmark">台塑<small>FORMOSA LUBRICANTS</small></span></span><h3>Formosa</h3><p>工業潤滑油相關產品</p><i class="go">→</i></a>
      <a class="brand-card" href="equipment.html" data-rv="up"><span class="chip y sm role">總代理</span><span class="logo"><img src="img/sterling-logo2.png" width="132" height="60" alt="CosmoTech" loading="lazy"></span><h3>CosmoTech</h3><p>廢水處理設備</p><i class="go">→</i></a>
    </div>
  </div>
</section>

<section class="sec values round-r" data-sc>
  <span class="blob" aria-hidden="true"></span>
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Principles ／ 我們重視的三件事</span>
      {sec_title(['我們重視的，', '不僅僅只是把產品交出去'])}
    </div>
    <ol class="principles">
      <li data-rv="up"><div class="principle"><span class="n">01</span><h3>先理解現場</h3><p>每一個加工條件與使用環境都不同。比起先推薦產品，我們更重視了解目前使用狀況與實際問題。</p></div></li>
      <li data-rv="up"><div class="principle"><span class="n">02</span><h3>持續追蹤使用狀況</h3><p>產品導入不是合作的終點。實際使用後的狀況，才是判斷方案是否真正適合的重要依據。</p></div></li>
      <li data-rv="up"><div class="principle"><span class="n">03</span><h3>把不同環節串起來</h3><p>從油品、換液到廢水處理與後續清運，依實際需求協助串聯服務，降低不同環節之間的溝通落差。</p></div></li>
    </ol>
  </div>
</section>

<section class="sec" data-sc>
  <div class="wrap statement">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Our Role ／ 圓華的角色</span>
      <blockquote data-rv="up">我們是您加工現場遇到問題時，可以一起討論並協助調整的夥伴</blockquote>
      <div class="copy" data-rv="up">
        <p>圓華不會僅是在客戶需要採購油品時出現。</p>
        <p>從產品選擇、油品調整、實際使用，到製程後端的處理需求，我們希望透過持續累積的產品與現場經驗，和客戶一起找到更合適的處理方式。</p>
        <p>面對不同加工條件與製造需求，我們不預設唯一答案，而是從現場實際狀況開始討論。</p>
      </div>
    </div>
    <figure class="photo r-big-l ar-43 plx" data-rv="left"><div class="plx-l">{im("img/hero-4.jpg", "圓華油品倉儲，整齊排列的油桶")}</div></figure>
  </div>
</section>

<section class="sec tight band">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">More ／ 延伸閱讀</span>
      {sec_title(['從過去的累積，', '到每一次現場合作'])}
    </div>
    <div class="next">
      <a class="next-card" href="milestone.html" data-rv="up">{im(CP[8]["src"], "")}<small>History ／ 歷史沿革</small><b>了解圓華一路走來的發展歷程</b><p>從油品、品牌合作到設備與服務，了解圓華如何逐步形成今天的服務內容。</p><span class="more">查看歷史沿革 <i>→</i></span></a>
      <a class="next-card" href="team.html" data-rv="up">{im("img/field.jpg", "")}<small>Team ／ 服務團隊</small><b>認識實際與客戶合作的服務方式</b><p>從需求溝通、產品評估到現場與後續支援，了解圓華如何陪伴客戶處理不同階段的問題。</p><span class="more">認識服務團隊 <i>→</i></span></a>
    </div>
  </div>
</section>
''' + cta_band()
    page('about.html', '關於我們', '圓華油品從金屬加工油品出發，延伸至技術支援、廢水處理設備與後續清運，以理解現場為起點，與客戶一起找到合適的處理方式。', 'about', body, 'img/hero-3.jpg')


def milestone():
    items = [
        ('2010', '建置二廠', ['隨著市場需求與業務成長，圓華完成二廠建置，進一步強化公司營運與售後服務能力。']),
        ('2013', '取得台塑潤滑油品經銷權', ['圓華取得台塑潤滑油品經銷權，擴充工業潤滑油產品線，讓產品選擇更加多元。']),
        ('2015', '建置三廠，成立環保事業部', ['圓華增設三廠並成立環保事業部，服務範圍開始從工業用油進一步延伸至工業廢液處理。', '這個階段也代表圓華開始將環境保護與後端處理需求納入服務體系。']),
        ('2018', '拓展廢水處理設備服務', ['與日本環保設備廠商建立合作，並成立水溶性廢液處理設備展示中心。', '圓華進一步將服務從油品與廢液問題，延伸至廢水處理設備與實際導入。']),
        ('2019', '取得 ISO 9001:2015 品質管理系統認證', ['圓華持續完善品質管理制度，並取得 ISO 9001:2015 品質管理系統認證，進一步建立公司內部管理與服務品質的制度基礎。']),
    ]
    tl = ''.join(f'<li><span class="yr">{y}</span><span class="dot" aria-hidden="true"></span><div class="tcard"><h3>{t}</h3>{"".join(f"<p>{p}</p>" for p in ps)}</div></li>' for y, t, ps in items)
    body = hero([('about.html', '關於我們'), (None, '歷史沿革')], 'History ／ 歷史沿革',
                ['從油品出發，', '持續拓展製造現場的服務能力'],
                lede='圓華一路從金屬加工與工業用油市場出發，隨著客戶需求與產業環境持續變化，逐步拓展產品、廠務、環保設備與後續服務。每一個發展階段，不只是公司規模的成長，也代表圓華持續增加回應製造現場需求的能力。',
                sub='每一次拓展，都是為了回應下一個現場需求。', img='img/hero-4.jpg', pos='50% 60%')
    body += lnav(ABOUT_NAV, 'milestone.html', '關於我們')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">History ／ 發展歷程</span>
      {sec_title(['一步一步，', '形成今天的圓華'])}
    </div>
    <ol class="tl" data-sc>{tl}</ol>
  </div>
</section>

<section class="sec band-y round-l" data-sc>
  <div class="wrap statement">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Today ／ 從油品到更完整的服務</span>
      <blockquote data-rv="up">改變的是服務範圍，不變的是從現場需求出發</blockquote>
      <div class="copy" data-rv="up">
        <p>從工業用油、產品線擴充，到環保事業、廢液與廢水處理設備，圓華的服務範圍隨著客戶需求持續延伸。</p>
        <p>今天所提供的產品、技術與後續服務，都是多年合作經驗逐步累積的結果。</p>
        <p>未來，圓華也將持續從實際製造需求出發，尋找更適合現場的產品與解決方式。</p>
      </div>
    </div>
    <div class="photo-wrap" data-rv="left"><span class="sun" aria-hidden="true"></span><figure class="photo r-big ar-43">{im(CP[8]["src"], "圓華油品廠區儲油槽")}</figure></div>
  </div>
</section>

<section class="sec tight">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">More ／ 延伸閱讀</span>
      {sec_title(['了解圓華，', '也了解我們如何服務現場'])}
    </div>
    <div class="next">
      <a class="next-card" href="about.html" data-rv="up">{im("img/hero-3.jpg", "")}<small>About ／ 關於我們</small><b>認識圓華的企業定位與服務理念</b><p>了解圓華如何從油品出發，逐步形成今天的服務方式。</p><span class="more">關於圓華 <i>→</i></span></a>
      <a class="next-card" href="team.html" data-rv="up">{im("img/field.jpg", "")}<small>Team ／ 服務團隊</small><b>認識實際與客戶合作的服務方式</b><p>從需求溝通、產品評估到現場支援，了解圓華團隊如何參與每一個合作階段。</p><span class="more">認識服務團隊 <i>→</i></span></a>
    </div>
  </div>
</section>
''' + cta_band()
    page('milestone.html', '歷史沿革', '圓華油品發展歷程：2010 建置二廠、2013 取得台塑潤滑油品經銷權、2015 成立環保事業部、2018 拓展廢水處理設備服務、2019 取得 ISO 9001:2015 認證。', 'about', body, 'img/hero-4.jpg')


def team():
    body = hero([('about.html', '關於我們'), (None, '服務團隊')], 'Team ／ 服務團隊',
                ['從了解問題開始，', '陪客戶把產品發揮到最大效能'],
                lede='好的產品只是合作的開始。圓華團隊從加工方式、材質、設備、油品問題與實際使用狀況開始了解，依據現場條件協助產品與方案評估，並在導入後持續關注實際使用需求。當問題進一步延伸到換油換水、廢液處理或設備需求，也能依實際情況協助串聯後續服務。',
                sub='先了解現場，再一起找到最適合的處理方式。',
                cta=f'<a class="btn y" href="contact.html#form">與我們討論現場問題 <i>→</i></a><a class="btn glass" href="contact.html">聯絡圓華 <i>→</i></a>',
                img='img/field.jpg', pos='50% 40%')
    body += lnav(ABOUT_NAV, 'team.html', '關於我們')
    body += f'''
<section class="sec first" data-sc>
  <div class="wrap split rev">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Listen First ／ 從了解需求開始</span>
      {sec_title(['每一間的加工條件和現場狀況皆不同，', '適合的做法也不會只有一種'])}
      <div class="copy" data-rv="up">
        <p>加工材質、機台、刀具、加工方式、水質與日常管理條件……都可能影響油品實際使用狀況。</p>
        <p>因此，在推薦產品之前，圓華團隊會先了解目前使用的產品、加工條件，以及現場實際遇到的問題，再進一步討論適合的產品或處理方式。</p>
        <p>我們希望處理的不是單一規格需求，而是讓產品能真正在實際製程中發揮最佳作用。</p>
      </div>
    </div>
    <div class="photo-wrap" data-rv="left"><span class="sun" aria-hidden="true"></span><figure class="photo r-big ar-54">{im(CP[10]["src"], "圓華油品實驗室同仁進行油品檢測")}</figure>
      <div class="vcatch" aria-hidden="true" data-rv="vwipe"><span style="--n:0">先了解</span><span class="y" style="--n:1">再評估</span></div></div>
  </div>
</section>

<section class="sec flow band round-r" data-sc>
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Process ／ 從需求到後續服務</span>
      {sec_title(['從第一次討論，', '到產品真正進入現場'])}
    </div>
    <div class="flow-track" aria-hidden="true"></div>
    <ol class="steps">
      <li data-rv="up"><div class="step"><span class="n">01</span><h3>了解現場需求</h3><p>從加工方式、設備、加工材質、現用油品與目前問題開始了解，掌握實際使用條件。</p></div></li>
      <li data-rv="up"><div class="step"><span class="n">02</span><h3>產品與方案評估</h3><p>依據性能需求、使用條件與預算，協助評估適合的油品、設備或處理方式。</p></div></li>
      <li data-rv="up"><div class="step"><span class="n">03</span><h3>現場導入與使用支援</h3><p>產品導入後，依實際使用狀況提供後續支援，持續了解產品在現場的使用情形。</p></div></li>
      <li data-rv="up"><div class="step"><span class="n">04</span><h3>延伸後續服務</h3><p>當需求延伸至換油、換水、廢水處理設備或廢油／廢水清運時，依實際需求協助串聯相關服務。</p></div></li>
    </ol>
  </div>
</section>

<section class="sec" data-sc>
  <div class="wrap split">
    <div class="split-text">
      <span class="chip g" data-rv="pop">After Delivery ／ 交付之後</span>
      {sec_title(['產品交付之後，', '才真正開始看見服務的重要性'])}
      <div class="copy" data-rv="up">
        <p>油品是否適合，不只取決於產品本身，也需要回到實際加工條件與使用管理。</p>
        <p>因此，圓華重視產品導入後的實際狀況。當現場出現下列問題時，團隊會從目前條件重新了解原因與需求，再一起討論並調整至最佳的處理方式。</p>
      </div>
      <ul class="tags warn" data-rv="up" aria-label="常見的現場問題"><li>使用壽命</li><li>異味</li><li>生鏽</li><li>加工效果</li><li>廢液處理</li></ul>
      <p class="lead-big" data-rv="up">對圓華而言，服務不是僅完成交貨，而是讓產品與使用者能更穩定地銜接實際製造需求。</p>
    </div>
    <figure class="photo r-big-l ar-11 plx" data-rv="right"><div class="plx-l">{im("img/lab.jpg", "檢測切削液樣品")}</div></figure>
  </div>
</section>

<section class="stage-slab round-l" data-sc>
  <span class="slab-glow" aria-hidden="true"></span>
  <div class="wrap statement">
    <div class="split-text">
      <span class="chip g" data-rv="pop">One Window ／ 一個服務窗口</span>
      {sec_title(['服務多元化並統一窗口，', '串聯加工現場不同階段的需求'])}
      <p class="lede" data-rv="up">加工現場遇到的問題，往往會跨越不同環節。從油品選擇、環境與加工條件、使用狀況、換液、設備與後續廢液處理，圓華希望透過持續累積的產品與服務經驗，協助客戶減少不同環節之間的溝通落差。</p>
      <p class="lede" data-rv="up">不論需求從哪一個階段開始，我們都希望先了解實際問題，再一起確認下一步最適合的處理方式。</p>
    </div>
    <figure class="photo ar-43" data-rv="left">{im(CP[14]["src"], "圓華油品辦公室與服務團隊")}</figure>
  </div>
</section>
''' + cta_band(qs=['不論是油品選擇、切削液使用狀況，', '或廢水與後續處理需求，都可以先告訴我們。'],
               lede='告訴我們目前的加工條件與實際問題，由圓華團隊協助了解需求，再一起討論適合的產品與服務方式。')
    page('team.html', '服務團隊', '圓華服務團隊從了解現場需求開始，協助產品與方案評估、現場導入與使用支援，並串聯換油換水、廢水處理設備與清運等後續服務。', 'about', body, 'img/field.jpg')


# ---------------------------------------------------------------- products
P = D['products']
DR = D['drums']
SERIES = [
    {'key': 'yushiro-plant', 'page': 'yushiro-plant.html', 'name': 'SAN-I Yushiro 植物性油品', 'short': '植物性油品', 'en': 'Plant-based',
     'items': ['yushiro-plant-oil'], 'drum': DR['yushiro']['src'], 'bg': 'img/c1.jpg', 'pos': '50% 46%',
     'lines': ['SAN-I Yushiro', '植物性油品'], 'old': 'yushiro-product-oil.html',
     'lede': '植物酯由植物油中萃取，油膜層不易破裂、潤滑性高，不需添加氯化石蠟極壓劑，也能滿足高精度及嚴苛條件下的加工。'},
    {'key': 'yushiro', 'page': 'yushiro.html', 'name': 'SAN-I Yushiro 油品系列', 'short': 'SAN-I Yushiro', 'en': 'SAN-I Yushiro',
     'items': ['yushiro-water', 'yushiro-cutting-oil', 'yushiro-rust', 'yushiro-tempering', 'yushiro-cleaner', 'yushiro-additive'],
     'drum': DR['yushiro']['src'], 'bg': 'img/hero-2.jpg', 'pos': '60% 50%', 'lines': ['SAN-I Yushiro', '金屬加工油品系列'], 'old': 'yushiro-product-main.html',
     'lede': 'SAN-I YUSHIRO 化學工業株式會社之金屬加工油與切削液，提供各類 CNC 與機械產業的金屬切削加工用途油品。'},
    {'key': 'battor', 'page': 'battor.html', 'name': 'Battor 油品系列', 'short': 'Battor', 'en': 'Battor',
     'items': [f'battor-{i:02d}' for i in range(1, 13)], 'drum': 'img/drum-battor.png', 'bg': 'img/hero-1.jpg', 'pos': '50% 40%',
     'lines': ['Battor', '金屬機械加工油'], 'old': 'battor-product-main.html',
     'lede': '液壓油、主軸油、滑道油、齒輪油、空壓機油、熱媒油、放電加工油與淬火油等工業用油，依機台與使用條件選擇。'},
    {'key': 'formosa', 'page': 'formosa.html', 'name': '台塑 潤滑油系列', 'short': '台塑潤滑油', 'en': 'Formosa',
     'items': [f'formosa-{i:02d}' for i in range(1, 13)], 'drum': DR['formosa']['src'], 'bg': 'img/hero-4.jpg', 'pos': '50% 55%',
     'lines': ['台塑', '工業潤滑油系列'], 'old': 'formosa-product-main.html',
     'lede': '採用符合 API Group II 標準之高精煉基礎油，涵蓋潤滑脂、空壓機油、渦輪機油、齒輪油、錠子油、熱媒油、滑道油、液壓油與循環油。'},
]
SKEY = {s['key']: s for s in SERIES}
for s in SERIES:
    for k in s['items']:
        P[k]['series'] = s['key']

# display names and model lines (the old pages mix model codes into titles)
BATTOR = {
    'battor-01': ('省能源液壓油', ''), 'battor-02': ('耐磨耗液壓油', 'HIVIS AW HLPSO:32-680'), 'battor-03': ('防火液壓油', 'HIVIS Fluid DU 系列'),
    'battor-04': ('高速主軸油', 'HIVIS HV ISO:5 10 22'), 'battor-05': ('滑道油', 'SIDEWAY BW ISO:32 68 220'), 'battor-06': ('齒輪油', 'ISO: 32-680'),
    'battor-07': ('空壓機油', 'GIREX SW NG ISO: 32-680'), 'battor-08': ('熱媒油', 'HEAT BRANFER ISO: 32 46 68'), 'battor-09': ('冷凍機油', 'Refigerator KM SP 系列'),
    'battor-10': ('放電加工油', 'EMD Fluid E.S 系列'), 'battor-11': ('高溫淬火油', 'Quench oils X.Y.Z 系列'), 'battor-12': ('二硫化鉬油脂', 'Moly GREASE EP-2'),
}
YUSHIRO = {
    'yushiro-plant-oil': ('植物性切削油／切削液', 'Plant-based Ester'), 'yushiro-water': ('水溶性切削油', '合成・半合成／乳化型／化學型'),
    'yushiro-cutting-oil': ('油性切削油', '油性・氯系・硫系・氯硫磷系'), 'yushiro-rust': ('防鏽油', '溶劑稀釋型／礦油型／樹脂型／水溶性'),
    'yushiro-tempering': ('調質油', '水溶性乳化型／分散型／預塗油'), 'yushiro-cleaner': ('清洗劑', '水溶性／不水溶性'), 'yushiro-additive': ('添加劑', '水溶性／不水溶性'),
}
for k, p in P.items():
    if k in BATTOR:
        p['name'], p['model'] = BATTOR[k]
    elif k in YUSHIRO:
        p['name'], p['model'] = YUSHIRO[k]
    elif k.startswith('formosa'):
        m = re.match(r'(.*?)\s*((?:SC|RC|TB|AW)?\s*GII)$', p['title'])
        p['name'] = p['title']
        p['model'] = 'API Group II' if 'GII' in p['title'] else '潤滑脂'
    else:
        p['name'], p['model'] = p['title'], ''
    p['blurb'] = text_of(' '.join(o['html'] for o in p['overview']), 76)


def pcard(k, i):
    p = P[k]
    s = SKEY[p['series']]
    return f'''<li data-rv="up"><a class="pcard" href="{k}.html"><span class="ph"><span class="idx">{i:02d}</span>{im(s["drum"], "")}</span><span class="bd"><span class="model">{E(p["model"])}</span><h3>{E(p["name"])}</h3><p>{E(p["blurb"])}</p><span class="more">查看產品資訊 <i>→</i></span></span></a></li>'''


PROD_NAV = [('products.html', '全部油品'), ('yushiro-plant.html', '植物性油品'), ('yushiro.html', 'SAN-I Yushiro'), ('battor.html', 'Battor'), ('formosa.html', '台塑潤滑油'), ('oil-table.html', '標準用油表')]


def products_hub():
    body = hero([(None, '油品介紹')], 'Products ／ 油品介紹', ['依加工條件，', '找到合適的油品'],
                lede='從 SAN-I Yushiro 植物性油品與金屬加工液，到 Battor、台塑工業潤滑油，圓華依加工材質、機台設備與使用條件，協助評估適合的產品。',
                cta='<a class="btn y" href="oil-table.html">查看標準用油表 <i>→</i></a><a class="btn glass" href="contact.html#form">不確定型號？直接詢問 <i>→</i></a>',
                img='img/drums-aisle.jpg', pos='50% 50%')
    body += lnav(PROD_NAV, 'products.html', '油品介紹')
    cards = []
    tints = ['rgba(30,138,73,.18)', 'rgba(30,138,73,.14)', 'rgba(243,198,64,.3)', 'rgba(31,95,168,.14)']
    for i, s in enumerate(SERIES):
        n = len(s['items'])
        cards.append(f'''<a class="hub-card{" dark" if i == 0 else ""}" href="{s["page"]}" style="--tint:{tints[i]}" data-rv="up"><span class="txt"><span class="chip {"y" if i == 0 else "g"} sm">{i + 1:02d} ／ {s["en"]}</span><h3>{s["name"]}</h3><p>{s["lede"]}</p><span class="count">{n} 項產品分類 →</span></span>{im(s["drum"], "")}</a>''')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Series ／ 油品系列</span>
      {sec_title(['四大油品系列，', '對應不同的加工與設備需求'])}
      <p class="lede" data-rv="up">不知道產品型號也沒關係，可以先從加工方式或設備類型開始找；也歡迎直接告訴我們目前遇到的問題。</p>
    </div>
    <div class="hub">{''.join(cards)}</div>
    <div class="mini-links">
      <a class="spec-card" href="oil-table.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4zM4 10h16M10 5v14"/></svg></span><div><b>Oil Chart</b><span>油品標準用油表</span></div><i class="go">→</i></a>
      <a class="spec-card" href="knowledge.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h10l4 4v12H5zM15 4v4h4M8 12h8M8 16h6"/></svg></span><div><b>Knowledge</b><span>油品知識區</span></div><i class="go">→</i></a>
      <a class="spec-card" href="equipment.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3s-6 7-6 11a6 6 0 0012 0c0-4-6-11-6-11zM9 15a3 3 0 003 3"/></svg></span><div><b>Equipment</b><span>廢液(水)處理裝置</span></div><i class="go">→</i></a>
    </div>
  </div>
</section>
''' + cta_band()
    page('products.html', '油品介紹', '圓華油品產品總覽：SAN-I Yushiro 植物性油品、SAN-I Yushiro 金屬加工油品、Battor 工業用油與台塑潤滑油系列。', 'products', body, 'img/drums-aisle.jpg')


def series_page(s):
    intro = fix_html(D['series_html'][s['old']])
    # the old listing already becomes our card grid: keep only the intro copy blocks
    intro = re.split(r'<a href="[a-z0-9-]+\.html">', intro)[0]
    intro = re.sub(r'<h3>(.*?)</h3>', r'<p class="lead-big">\1</p>', intro, flags=re.S)
    intro = re.sub(r'<h2>\s*(.*?)\s*</h2>', r'<p class="lead-big">\1</p>', intro, flags=re.S)
    photos = re.findall(r'<img [^>]+>', intro)
    intro_txt = re.sub(r'<p>\s*<img [^>]+>\s*</p>|<img [^>]+>', '', intro)
    banner = photos[0] if photos else ''
    side = ''
    if s['key'] == 'battor':
        side = f'<figure class="photo ar-43" data-rv="right">{banner}</figure>'
    elif s['key'] == 'formosa':
        side = f'<figure class="photo" data-rv="right" style="background:#fff">{banner}</figure>'
    elif s['key'] == 'yushiro-plant':
        side = f'<figure class="photo ar-11 plx" data-rv="right"><div class="plx-l">{im("img/c1.jpg", "切削油沖刷刀具與工件的加工特寫")}</div></figure>'
    else:
        side = f'<figure class="photo ar-43 plx" data-rv="right"><div class="plx-l">{im("img/hero-2.jpg", "SAN-I 與 Yushiro 油桶")}</div></figure>'
    grid = ''.join(pcard(k, i + 1) for i, k in enumerate(s['items']))
    body = hero([('products.html', '油品介紹'), (None, s['name'])], f'Products ／ {s["en"]}', s['lines'], lede=s['lede'],
                cta=f'<a class="btn y" href="#list">查看產品 <i>↓</i></a><a class="btn glass" href="contact.html?item={s["name"]}#form">詢問此系列 <i>→</i></a>',
                img=s['bg'], pos=s['pos'], art=s['drum'])
    body += lnav(PROD_NAV, s['page'], '油品介紹')
    body += f'''
<section class="sec first">
  <div class="wrap series-intro">
    <div class="split-text">
      <span class="chip g" data-rv="pop">About ／ 系列介紹</span>
      <div class="prose" data-rv="up">{intro_txt}</div>
    </div>
    {side}
  </div>
</section>

<section class="sec tight band round-r" id="list">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Line-up ／ 產品列表</span>
      {sec_title([s['name']])}
    </div>
    <ul class="pgrid">{grid}</ul>
  </div>
</section>
''' + cta_band(item=s['name'])
    page(s['page'], s['name'], f'{s["name"]}：{s["lede"]}', 'products', body, s['bg'])


def side_nav(cur):
    out = []
    for s in SERIES:
        open_ = ' open' if P[cur].get('series') == s['key'] else ''
        lis = ''.join(f'<li><a href="{k}.html"{AC if k == cur else ""}>{E(P[k]["name"])}</a></li>' for k in s['items'])
        out.append(f'<details class="side-nav"{open_}><summary>{s["name"]}</summary><ul>{lis}</ul></details>')
    return ''.join(out)


def product_page(k):
    p = P[k]
    s = SKEY[p['series']]
    ov = ''
    for o in p['overview']:
        lab = o['label'].rstrip(':：').replace('(金屬加工油)', '').strip()
        ov += (f'<p class="eyebrow">{E(lab)}</p>' if lab else '') + f'<div class="prose">{fix_html(o["html"])}</div>'
    secs = ''
    jumps = ''
    for j, sec in enumerate(p['sections']):
        h = fix_html(sec['html'], spec_prefix=f's{j + 1}-')
        heads = re.findall(r'<h3 class="spec-h" id="([^"]+)"><em class="num">[^<]*</em>(.*?)(?:<small>|</h3>)', h)
        if len(heads) >= 3:
            jumps = '<nav class="jump" aria-label="規格分類">' + ''.join(f'<a href="#{i}">{text_of(t)}</a>' for i, t in heads) + '</nav>'
        secs += f'<section class="pd-sec" id="spec{j + 1}" data-rv="up"><h2>{E(sec["title"])}</h2>{jumps if j == 0 else ""}<div class="prose">{h}</div></section>'
    legend = ''
    if k.startswith('yushiro') and k != 'yushiro-plant-oil':
        legend = '<p class="legend">表內符號依原廠資料標示；實際適用條件請以圓華團隊評估為準。</p>'
    apps = ''
    if p.get('apps_generic'):
        apps = '<section class="pd-sec" data-rv="up"><h2>應用範圍</h2><div class="apps">' + ''.join(im(a['src'], '') for a in D['apps_generic']) + '</div><p class="legend">各類 CNC 機械設備與工業用機械之金屬加工、潤滑與冷卻應用。</p></section>'
    sibs = [x for x in s['items'] if x != k][:3]
    rel = ''
    if sibs:
        rel = f'<section class="pd-sec" data-rv="up"><h2>同系列產品</h2><ul class="pgrid">{"".join(pcard(x, s["items"].index(x) + 1) for x in sibs)}</ul></section>'
    body = hero([('products.html', '油品介紹'), (s['page'], s['name']), (None, p['name'])], f'{s["en"]} ／ {s["short"]}',
                [p['name']] + ([p['model']] if p['model'] and p['model'] != 'API Group II' else []), small=True,
                img=s['bg'], pos=s['pos'], art=s['drum'])
    body += f'''
<section class="sec first">
  <div class="wrap pd">
    <aside class="pd-side" aria-label="油品系列">
      {side_nav(k)}
      <div class="side-cta"><b>需要協助選油？</b><p>告訴我們加工材質、機台與目前問題，由圓華團隊協助評估。</p><a class="btn g" href="contact.html?item={E(p["name"])}#form">詢問這項產品 <i>→</i></a></div>
    </aside>
    <div class="pd-main">
      <div class="pd-over" data-rv="up">
        <div class="pic"><span class="ring" aria-hidden="true"></span>{im(s["drum"], "")}</div>
        <div class="txt">
          <span class="chip g sm">{s["name"]}</span>
          <h2>{E(p["name"])}</h2>
          {f'<span class="model">{E(p["model"])}</span>' if p["model"] else ''}
          {ov}
          <div class="btns-row"><a class="btn y" href="contact.html?item={E(p["name"])}#form">詢問這項產品 <i>→</i></a><a class="btn g" href="{LINE}" target="_blank" rel="noopener">LINE 詢問 <i>→</i></a></div>
        </div>
      </div>
      {secs}{legend}
      {apps}
      {rel}
    </div>
  </div>
</section>
''' + cta_band(item=p['name'])
    page(f'{k}.html', f'{p["name"]}｜{s["name"]}', f'{s["name"]}－{p["name"]}：{p["blurb"]}', 'products', body, s['bg'])


# ---------------------------------------------------------------- equipment
# Order and line-up follow 資訊提供-20260720.pdf: the five models 圓華 represents, CT-AQ25H first (most popular).
# Copy for the three models that were not on the old site is translated from cosmotech-jp.com (allowed by the brief).
FRIENDLY_SPEC = '''<div class="tbl-wrap"><table class="tbl mid"><thead><tr><th>型式</th><th>CT-AQ10H</th><th>CT-AQ25H</th><th>CT-AQ100H</th><th>CT-AQ125H</th></tr></thead><tbody>
<tr><th>處理能力（每小時）</th><td>10 L</td><td>25 L</td><td>100 L</td><td>125–150 L</td></tr>
<tr><th>對象廢液</th><td colspan="4">水溶性廢液</td></tr>
<tr><th>控制方式</th><td colspan="4">間接熱泵型</td></tr>
<tr><th>電源</th><td colspan="4">3 相 200V 50/60Hz</td></tr>
<tr><th>電氣容量／電流</th><td>約 5.2KVA／14.8A</td><td>約 13.8KVA／40A</td><td>約 34.7KVA／100A</td><td>約 55.6KVA／160A</td></tr>
<tr><th>輸入斷路器</th><td>30A</td><td>75A</td><td>125A</td><td>175A</td></tr>
<tr><th>產品重量（運轉時）</th><td>約 260 kg（約 320 kg）</td><td>約 585 kg（約 825 kg）</td><td>約 1,660 kg（約 2,070 kg）</td><td>約 1,800 kg（約 2,105 kg）</td></tr>
<tr><th>尺寸（mm）</th><td>W800×D1000×H1430</td><td>W1500×D1052×H1900</td><td>W3100×D1600×H1900<br>〈2 Units〉W1800／W1300</td><td>W3100×D1600×H1940<br>〈2 Units〉W1800／W1300</td></tr>
</tbody></table></div><p class="scroll-hint">左右滑動查看完整表格</p>'''
FRIENDLY_FAQ = [
    ('哪些廢液可以處理？', '切削廢液、洗淨廢液、電鍍製程廢液等，以水為主成分的水溶性廢液。依廢液種類與濃度，適用性會有所不同，建議先進行處理測試確認。'),
    ('採用什麼處理方式？', '將裝置內的濃縮槽減壓，以 40℃ 以下的低溫將廢液蒸餾分離的「減壓蒸餾方式」。並採用冷凍機的熱泵方式，耗電量低，也不需要鍋爐、冷卻水設備、壓縮空氣等附帶設備，有助降低導入與運轉成本。'),
    ('蒸餾分離出的再生水如何處理？', '從廢液蒸餾分離出的再生水，可依現場需求再利用於洗淨或稀釋；若符合當地排放標準，也可排入下水道。'),
]
FRIENDLY_FEAT = ['160 台以上導入實績', '最大 1/20 的廢液削減實績（約削減 95%）', '減壓蒸餾 × 熱泵控制的節能設計',
                 '依處理量提供 4 種機型（每小時 10L／25L／100L／125L）', '不需附帶設備（鍋爐・冷卻水設備・壓縮空氣等）', '24 小時連續運轉／自動釜洗淨功能']
COMMON_BEN = ['降低產業廢棄物處理成本（委託・運搬）', '因應處理費上漲與環境法規趨嚴', '廢液處理內製化，成本更穩定', '減少廢液保管量與保管空間']

EQ_MAIN = [
    {'slug': 'eq-friendly-aq25h', 'old': 'equipment-2', 'name': 'FRIENDLY CT-AQ25H', 'kind': '水溶性廢液處理裝置', 'badge': '熱門機型',
     'cap': ('處理能力', '25 L/h'), 'target': ('對象', '水溶性廢液'),
     'tag': '廢液「自行處理」，降低產業廢棄物處理成本', 'feat': FRIENDLY_FEAT, 'ben': COMMON_BEN, 'faq': FRIENDLY_FAQ, 'spec': FRIENDLY_SPEC,
     'drop_old': ('規格',)},
    {'slug': 'eq-friendly-aq100h', 'old': 'equipment-3', 'name': 'FRIENDLY CT-AQ100H／125H', 'kind': '水溶性廢液處理裝置',
     'cap': ('處理能力', '100–150 L/h'), 'target': ('對象', '水溶性廢液'),
     'tag': '大處理量機型，滿足排廢量多的工廠需求', 'feat': FRIENDLY_FEAT, 'ben': COMMON_BEN, 'faq': FRIENDLY_FAQ, 'spec': FRIENDLY_SPEC,
     'drop_old': ('規格',)},
    {'slug': 'eq-master-line', 'old': 'equipment-6', 'name': 'MASTER Line', 'kind': 'MVR 型大型廢液處理裝置', 'img': 'img/eq/master-line.jpg',
     'cap': ('處理能力', '最大 3,850 L/h'), 'target': ('對象', '水溶性廢液全般'),
     'tag': '德國 KMU-LOFT 製造，最大每小時 3,850 L 的處理能力',
     'feat': ['德國製造商 KMU-LOFT 製，實績豐富', 'MVR 方式蒸發器／減壓蒸餾處理', '24 小時連續運轉／自動釜洗淨功能', '可透過網路確認運轉狀況'],
     'ben': ['降低廢液處理成本（委託・運搬）', '廢液處理內製化，成本更穩定', '減少廢液保管量與保管空間', '因應處理費上漲與法規趨嚴'],
     'faq': [('哪些廢液可以處理？', '切削廢液、洗淨廢液、電鍍廢液等，以水為主成分的水溶性廢液。依廢液種類與濃度，適用性會有所不同，建議先進行處理測試確認。'),
             ('採用什麼處理方式？', '將裝置內的濃縮槽減壓，以 40℃ 以下的低溫蒸餾分離廢液的「減壓蒸餾方式」。並採用 MVR 方式：將蒸發的蒸氣以壓縮機壓縮、再加熱後作為熱源再利用，幾乎不需外部加熱，可大幅降低耗電；也不需要鍋爐、冷卻水設備、壓縮空氣等附帶設備。'),
             ('分離出的再生水如何處理？', '分離出的再生水可依現場需求再利用於洗淨或稀釋；若符合當地排放標準，也可排入下水道。')],
     'flow': ['水溶性廢液', '帶式過濾機', '蒸發器本體（搭配酸性／鹼性洗淨劑）', '濃縮液 ／ 油水分離機', '再生水（蒸餾水）'],
     'old_title': 'DESTIMAT® LE 系列（舊站資料）'},
    {'slug': 'eq-dr-1', 'name': 'DR-1', 'kind': '蒸餾式廢液回收再利用裝置', 'img': 'img/eq/dr-1.jpg',
     'cap': ('處理能力', '最大 10.5 L/h'), 'target': ('對象', '電鍍廢液'),
     'tag': '以蒸餾把廢液變成「資源」',
     'feat': ['低溫減壓蒸餾方式濃縮處理', '同時回收可再利用的濃縮液與再生水', '不需附帶設備的自給式系統', '節能設計（熱泵控制）', '觸控面板・自動控制'],
     'ben': ['減少產業廢棄物與處理費用', '降低原物料成本', '減少用水量與環境成本', '減輕現場作業負擔', '強化法規與品質因應'],
     'note': '電鍍液處理範例：鎳（Ni）、錫（Sn）、鋅（Zn）等劣化溶液，經處理後分離為「水」與「濃縮液」。',
     'spec': '''<div class="tbl-wrap"><table class="tbl kvt"><tbody>
<tr><th>處理能力</th><td>最大蒸發量 10.5 L/hr（60Hz）（精製水處理時）</td></tr>
<tr><th>控制方式</th><td>熱泵循環控制</td></tr>
<tr><th>電源</th><td>三相 AC200V 50/60Hz</td></tr>
<tr><th>消耗電力／電流（50/60Hz）</th><td>3.1／3.4 kW ／ 9.8／10.7 A</td></tr>
<tr><th>本體尺寸</th><td>W1320×D940×H1900 mm</td></tr>
<tr><th>重量</th><td>約 320 kg（運轉重量約 380 kg）</td></tr>
</tbody></table></div>'''},
    {'slug': 'eq-for-3', 'name': 'FOR-III', 'kind': '浮上油回收裝置', 'img': 'img/eq/for-3.png',
     'cap': ('槽容量', '約 22 L'), 'target': ('用途', '浮上油回收・油水分離'),
     'tag': '回收浮上油，延長切削液壽命',
     'feat': ['不需電源・氣動驅動', '浮上油回收＆油水分離', 'SUS 不鏽鋼高耐久構造', '附液面調整機構', '增加溶氧量，抑制厭氧菌'],
     'ben': ['大幅減少廢液處理的工時', '改善作業環境並提升安全性', '最佳化廢棄成本', '降低設備與保養成本'],
     'points': [('延長液體壽命', '透過裝置內的過濾球增加液中溶氧量，防止厭氧菌增殖，延長切削液壽命。'),
                ('高品質不鏽鋼規格', '本體接液部與吸引浮球皆採用不鏽鋼，防止溶液造成生鏽與劣化，長時間維持品質。'),
                ('可 mm 單位調整液面', '依浮上油量以液面調整器調整液面高度，避免乳化油未被回收或排出過多水分。')],
     'spec': '''<div class="tbl-wrap"><table class="tbl kvt"><tbody>
<tr><th>構造</th><td>分離槽、浮球及接液部 SUS 製；內建液用過濾網（SUS 製 100 mesh）</td></tr>
<tr><th>吸引部</th><td>浮球 Φ60 球型（3 個）</td></tr>
<tr><th>分離槽容量</th><td>約 22 L</td></tr>
<tr><th>吸引量</th><td>最大 18 L/min</td></tr>
<tr><th>驅動源</th><td>空氣（標準設定壓力 0.3 MPa）</td></tr>
<tr><th>本體尺寸</th><td>W420×D300×H980 mm</td></tr>
<tr><th>重量</th><td>約 35 kg</td></tr>
</tbody></table></div>'''},
]
EQ_MORE = [
    {'slug': 'eq-friendly', 'old': 'equipment-1', 'name': 'FRIENDLY 系列（CT-AQ5／CT-AQ10）', 'kind': '水溶性廢液（水）處理裝置'},
    {'slug': 'eq-friendly-plus', 'old': 'equipment-4', 'name': 'FRIENDLY PLUS', 'kind': '複合型水溶性廢液處理裝置'},
    {'slug': 'eq-friendly-uf', 'old': 'equipment-5', 'name': 'FRIENDLY UF', 'kind': '水溶性含油廢液膜處理裝置'},
]
for e in EQ_MAIN + EQ_MORE:
    if e.get('old') and not e.get('img'):
        h = P[e['old']]['hero']
        e['img'] = h['src'] if h else 'img/cosmotech.jpg'
EQ_ALL = EQ_MAIN + EQ_MORE
EQ_FILE = {e['old']: e['slug'] + '.html' for e in EQ_ALL if e.get('old')}
EQ_CTA = dict(title=('想評估廢液減量？', '先告訴我們目前的廢液狀況'), qs=['每月廢液量大約多少？', '廢液種類：切削液、清洗廢水、電鍍廢液或其他？'],
              lede='提供目前的廢液種類、產生量與處理方式，圓華團隊會協助評估適合的設備與導入方式。')
CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'


def eq_card(e, i, small=False):
    badge = f'<span class="chip y sm hot">{e["badge"]}</span>' if e.get('badge') else ''
    kv = '' if small else f'<dl class="kv"><div><dt>{e["cap"][0]}</dt><dd>{e["cap"][1]}</dd></div><div><dt>{e["target"][0]}</dt><dd>{e["target"][1]}</dd></div></dl>'
    return f'''<li data-rv="up"><a class="pcard eq" href="{e["slug"]}.html"><span class="ph white">{im(e["img"], "")}<span class="idx">{i:02d}</span>{badge}</span><span class="bd"><span class="model">{E(e["kind"])}</span><h3>{E(e["name"])}</h3>{kv}<span class="more">查看設備資訊 <i>→</i></span></span></a></li>'''


def equipment_hub():
    intro = fix_html(D['series_html']['cosmotech-product-main.html'])
    m = re.search(r'<h3>.*?</h3>\s*<p>(.*?)</p>', intro, re.S) or re.search(r'<p>(.*?)</p>', intro, re.S)
    lead_lines = [l.strip() for l in re.split(r'\n', m.group(1) if m else '') if l.strip()]
    main = ''.join(eq_card(e, i + 1) for i, e in enumerate(EQ_MAIN))
    more = ''.join(eq_card(e, i + 1, small=True) for i, e in enumerate(EQ_MORE))
    ben = ''.join(f'<li data-rv="up"><span class="ic">{CHECK}</span><b>{b}</b></li>' for b in COMMON_BEN)
    body = hero([(None, '廢液(水)處理裝置')], 'Equipment ／ 廢水處理機', ['COSMO TECH', '廢液（水）處理裝置'],
                lede='圓華為 CosmoTech 廢水處理機總代理。導入日本減壓蒸餾技術與 24 小時自動化設備，協助處理切削廢液、洗淨廢液、電鍍廢液等水溶性工業廢液，從源頭減少廢液量與處理成本。',
                cta='<a class="btn y" href="#list">查看代理機型 <i>↓</i></a><a class="btn glass" href="contact.html?item=廢水處理設備&topic=廢水處理設備#form">詢問設備導入 <i>→</i></a>',
                img='img/policy.jpg', pos='50% 50%', art=EQ_MAIN[0]['img'], art_card=True)
    body += f'''
<section class="sec first" id="list">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Line-up ／ 代理機型</span>
      {sec_title(['依處理量與廢液性質，', '選擇適合的設備'])}
      <p class="lede" data-rv="up">從每小時 25 L 的熱門機型 FRIENDLY CT-AQ25H，到每小時最大 3,850 L 的大型 MASTER Line，以及電鍍廢液回收與浮上油回收裝置。</p>
    </div>
    <ul class="pgrid eq-grid">{main}</ul>
  </div>
</section>

<section class="stage-slab round-l" data-sc>
  <span class="slab-glow" aria-hidden="true"></span>
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Why ／ 為什麼自行處理廢液</span>
      {sec_title(['廢液減量，', '從源頭降低處理成本'])}
      <p class="lede" data-rv="up">{''.join(lead_lines[:2])}</p>
    </div>
    <ul class="bens">{ben}</ul>
    <ol class="stages" style="margin-top:clamp(40px,5vw,60px)">
      <li data-rv="up"><span class="n">01</span><h3>減壓</h3><p>將裝置內的濃縮槽減壓，讓廢液在低溫下就能沸騰。</p></li>
      <li data-rv="up"><span class="n">02</span><h3>低溫蒸餾</h3><p>以 40℃ 以下的低溫蒸餾分離，熱泵或 MVR 方式回收熱能，耗電低。</p></li>
      <li data-rv="up"><span class="n">03</span><h3>再生水＋濃縮液</h3><p>再生水可再利用於洗淨或稀釋，濃縮後的廢液大幅減量再委外處理。</p></li>
    </ol>
  </div>
</section>

<section class="sec">
  <div class="wrap split">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Video ／ 設備影片</span>
      {sec_title(['FRIENDLY', '運轉實況'])}
      <div class="copy" data-rv="up">{''.join(f'<p>{l}</p>' for l in lead_lines[2:])}</div>
      <ul class="tags" data-rv="up" aria-label="適用廢液"><li>切削廢液（油）</li><li>洗淨廢液</li><li>電鍍廢液</li><li>印刷廠廢液</li><li>烤漆廢液</li></ul>
    </div>
    <div class="vcard" data-rv="right">
      <div class="vid"><video controls preload="none" playsinline poster="{P['equipment-1']['hero']['src']}" aria-label="COSMOTECH FRIENDLY 廢水處理設備影片"><source src="{D['cosmo_video']}" type="video/mp4"></video></div>
      <b>COSMOTECH FRIENDLY 廢水處理設備影片</b>
      <p>設備運轉實況與處理流程介紹。</p>
    </div>
  </div>
</section>

<section class="sec tight band round-r">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">More ／ 其他機型</span>
      {sec_title(['其他 COSMO TECH 機型'])}
      <p class="lede" data-rv="up">以下機型資料來自舊網站，是否繼續刊登待圓華確認。</p>
    </div>
    <ul class="pgrid eq-grid sm">{more}</ul>
  </div>
</section>
''' + cta_band(item='廢水處理設備', **EQ_CTA)
    page('equipment.html', '廢液(水)處理裝置', 'CosmoTech 廢液（水）處理裝置：FRIENDLY CT-AQ25H、CT-AQ100H／125H、MASTER Line、DR-1 與 FOR-III 浮上油回收裝置。', 'equipment', body, 'img/policy.jpg')


def equipment_page(e):
    old = P.get(e.get('old')) if e.get('old') else None
    secs = ''
    n = 0
    def sec(title, inner, sid=None):
        nonlocal n
        n += 1
        return f'<section class="pd-sec" id="{sid or f"part{n}"}" data-rv="up"><h2>{title}</h2>{inner}</section>'
    if e.get('feat'):
        secs += sec('產品特色', '<ul class="feat">' + ''.join(f'<li><span class="ic">{CHECK}</span>{f}</li>' for f in e['feat']) + '</ul>')
    if e.get('points'):
        secs += sec('設計重點', '<ol class="principles three">' + ''.join(f'<li><div class="principle"><span class="n">{i + 1:02d}</span><h3>{t}</h3><p>{d}</p></div></li>' for i, (t, d) in enumerate(e['points'])) + '</ol>')
    if e.get('ben'):
        secs += sec('導入效果', '<ul class="bens light">' + ''.join(f'<li><span class="ic">{CHECK}</span><b>{b}</b></li>' for b in e['ben']) + '</ul>')
    if e.get('note'):
        secs += f'<p class="notice" data-rv="up">{e["note"]}</p>'
    if e.get('flow'):
        secs += sec('處理流程（參考）', '<ol class="flowline">' + ''.join(f'<li><span>{i + 1:02d}</span>{f}</li>' for i, f in enumerate(e['flow'])) + '</ol>')
    if e.get('faq'):
        secs += sec('常見問題', '<div class="qa-list" style="margin-top:0">' + ''.join(f'<details class="qa"{" open" if i == 0 else ""}><summary><span class="q">Q{i + 1}</span>{q}</summary><div class="a"><div class="prose"><p>{a}</p></div></div></details>' for i, (q, a) in enumerate(e['faq'])) + '</div>')
    if e.get('spec'):
        secs += sec('規格', e['spec'] + '<p class="legend">※ 規格・外觀可能因改良而變更，恕不另行通知；其他規格請洽圓華。</p>', 'spec')
    if old:
        ov = ''.join(f'<div class="prose">{fix_html(o["html"])}</div>' for o in old['overview'])
        olds = ''.join(f'<h3 class="sub-h">{E(s_["title"])}</h3><div class="prose">{fix_html(s_["html"], f"o{j + 1}-")}</div>'
                       for j, s_ in enumerate(old['sections']) if s_['title'] not in e.get('drop_old', ()))
        label = e.get('old_title') or ('設備介紹' if not e.get('feat') else '更多介紹')
        secs += sec(label, ov + olds)
    sib = [x for x in EQ_MAIN if x is not e][:3]
    secs += sec('其他代理機型', '<ul class="pgrid eq-grid">' + ''.join(eq_card(x, EQ_MAIN.index(x) + 1) for x in sib) + '</ul>')
    side = ('<details class="side-nav" open><summary>代理機型</summary><ul>' + ''.join(f'<li><a href="{x["slug"]}.html"{AC if x is e else ""}>{E(x["name"])}</a></li>' for x in EQ_MAIN) + '</ul></details>'
            + f'<details class="side-nav"{" open" if e in EQ_MORE else ""}><summary>其他機型</summary><ul>' + ''.join(f'<li><a href="{x["slug"]}.html"{AC if x is e else ""}>{E(x["name"])}</a></li>' for x in EQ_MORE) + '</ul></details>')
    kv = f'<dl class="kv"><div><dt>{e["cap"][0]}</dt><dd>{e["cap"][1]}</dd></div><div><dt>{e["target"][0]}</dt><dd>{e["target"][1]}</dd></div></dl>' if e.get('cap') else ''
    badge = f'<span class="chip y sm">{e["badge"]}</span>' if e.get('badge') else ''
    more_note = '<p class="notice">此機型資料來自舊網站，是否繼續刊登待圓華確認。</p>' if e in EQ_MORE else ''
    body = hero([('equipment.html', '廢液(水)處理裝置'), (None, e['name'])], 'Equipment ／ CosmoTech', [e['name'], e['kind']], small=True,
                img='img/policy.jpg', pos='50% 50%', art=e['img'], art_card=True)
    body += f'''
<section class="sec first">
  <div class="wrap pd">
    <aside class="pd-side" aria-label="設備列表">
      {side}
      <div class="side-cta"><b>評估設備導入？</b><p>提供廢液種類與產生量，由圓華團隊協助評估適合的機型。</p><a class="btn g" href="contact.html?item={E(e["name"])}&topic=廢水處理設備#form">詢問這台設備 <i>→</i></a></div>
    </aside>
    <div class="pd-main">
      <div class="pd-over" data-rv="up">
        <div class="pic photo-pic">{im(e["img"], f'{e["name"]} 設備外觀')}</div>
        <div class="txt">
          <span class="btns-row" style="gap:8px"><span class="chip g sm">COSMO TECH</span>{badge}</span>
          <h2>{E(e["name"])}</h2>
          <span class="model">{E(e["kind"])}</span>
          {f'<p class="lead-big">{e["tag"]}</p>' if e.get("tag") else ''}
          {kv}{more_note}
          <div class="btns-row"><a class="btn y" href="contact.html?item={E(e["name"])}&topic=廢水處理設備#form">詢問這台設備 <i>→</i></a><a class="btn g" href="{LINE}" target="_blank" rel="noopener">LINE 詢問 <i>→</i></a></div>
        </div>
      </div>
      {secs}
    </div>
  </div>
</section>
''' + cta_band(item=e['name'], **EQ_CTA)
    page(f'{e["slug"]}.html', f'{e["name"]}｜廢液(水)處理裝置', f'CosmoTech {e["kind"]} {e["name"]}：{e.get("tag", "")}', 'equipment', body, 'img/policy.jpg')


# ---------------------------------------------------------------- license
def license_page():
    iso = D['iso_imgs']
    todo = '<svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg>'
    body = hero([(None, '廢油/水清運牌')], 'License ／ 廢油・廢水清運', ['廢油／水清運牌', '證照資訊'],
                lede='從換油、換水、設備需求到後續廢油／廢水清運，協助客戶減少不同廠商之間的溝通與管理成本。清運相關許可證照將公開於本頁，方便客戶查核。',
                cta='<a class="btn y" href="contact.html?item=廢油・廢水清運&topic=廢油・廢水清運#form">詢問清運服務 <i>→</i></a>',
                img='img/drums-aisle.jpg', pos='50% 45%')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Permits ／ 清運許可</span>
      {sec_title(['廢油／廢水清運', '許可證照'])}
      <p class="lede" data-rv="up">清運服務相關之許可文件，將依主管機關核發內容公告。</p>
    </div>
    <ul class="certs">
      <li data-rv="up"><div class="cert"><div class="ph todo">{todo}證照圖檔<br>待圓華提供</div><b>廢油清運許可</b><p>許可字號、有效期限與核准項目待確認後公告。</p></div></li>
      <li data-rv="up"><div class="cert"><div class="ph todo">{todo}證照圖檔<br>待圓華提供</div><b>廢水（廢液）清運許可</b><p>許可字號、有效期限與核准項目待確認後公告。</p></div></li>
      <li data-rv="up"><div class="cert"><div class="ph todo">{todo}證照圖檔<br>待圓華提供</div><b>其他相關證照</b><p>如有車輛、處理機構或其他相關文件，可一併於此呈現。</p></div></li>
    </ul>
    <p class="notice" data-rv="up" style="margin-top:28px">此區為版面示意：清運許可證照目前尚未取得檔案，正式上線前需由圓華提供並確認內容。</p>
  </div>
</section>

<section class="sec tight band round-r">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Quality ／ 品質管理認證</span>
      {sec_title(['ISO 9001:2015', '品質管理系統認證'])}
      <p class="lede" data-rv="up">圓華油品於 2019 年取得 ISO 9001:2015 國際品質管理系統認證；產品並檢附國內檢驗 SGS 認證資料，以及歐盟 REACH、RoHS、COA 認證資料表。（品質管理認證，非清運許可證。）</p>
    </div>
    <ul class="certs">
      <li data-rv="up"><div class="cert"><div class="ph">{im(iso['ISO-9001-2015-國際品質管理系統認證-圓華油品-中文版.jpg']['src'], 'ISO 9001:2015 認證證書（中文版）')}</div><b>ISO 9001:2015 證書（中文版）</b><div class="links"><a href="{D['iso']['zh']}" target="_blank" rel="noopener">開啟 PDF</a></div></div></li>
      <li data-rv="up"><div class="cert"><div class="ph">{im(iso['ISO-9001-2015-國際品質管理系統認證-圓華油品-英文版.jpg']['src'], 'ISO 9001:2015 Certificate (English)')}</div><b>ISO 9001:2015 證書（英文版）</b><div class="links"><a href="{D['iso']['en']}" target="_blank" rel="noopener">開啟 PDF</a></div></div></li>
      <li data-rv="up"><div class="cert"><div class="ph" style="aspect-ratio:auto;padding:16px;gap:12px;display:grid;grid-template-columns:1fr 1fr 1fr;background:#fff">{im(iso['sgs.jpg']['src'], 'SGS')}{im(iso['reach.jpg']['src'], 'REACH')}{im(iso['rohs.jpg']['src'], 'RoHS')}</div><b>SGS ／ REACH ／ RoHS</b><p>產品檢驗與歐盟相關認證資料，可向圓華索取。</p><div class="links"><a href="news-detail14.html">閱讀認證公告</a></div></div></li>
    </ul>
  </div>
</section>
''' + cta_band(title=('需要換油、換水', '或廢油／廢水清運？'), qs=['目前的廢油、廢水量與清運頻率？', '是否同時需要換液或設備評估？'],
               lede='告訴我們現場狀況，圓華團隊會協助串聯換液、設備與後續清運。', item='廢油・廢水清運')
    page('license.html', '廢油/水清運牌', '圓華油品廢油／廢水清運服務與相關證照資訊，以及 ISO 9001:2015 品質管理系統認證。', 'license', body, 'img/drums-aisle.jpg')


# ---------------------------------------------------------------- news
NEWS = D['news']
NEWS_ORDER = ['news-detail17.html', 'news-detail15.html', 'news-detail14.html', 'news-detail13.html', 'news-detail12.html',
              'news-detail9.html', 'news-detail8.html', 'news-detail7.html', 'news-detail6.html', 'news-detail4.html', 'news-detail3.html',
              'news-detail2.html', 'news-detail1.html', 'news-detail.html']
NEWS_CAT = {k: 'expo' for k in NEWS_ORDER}
NEWS_CAT['news-detail14.html'] = 'other'
CAT_NAME = {'nexustest': '跨界合作', 'expo': '最新展覽', 'launch': '新產品發表', 'other': '其他新發布'}


def clean_title(t):
    return re.sub(r'\s*[～~]?\s*\|\s*', '｜', t).strip()


def news_pages():
    lis = []
    lis.append(f'''<li data-cat="nexustest"><div class="ncard pending"><span class="ph empty"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg><span class="chip y sm">跨界合作</span></span><span class="bd"><span class="date">即將發布</span><h3>跨界合作－半導體電子設備 聯資儀器 NEXUSTEST</h3><p>合作內容與圖片整理中，將由圓華提供後發布。</p></span></div></li>''')
    lis.append(f'''<li data-cat="launch"><div class="ncard pending"><span class="ph empty"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg><span class="chip y sm">新產品發表</span></span><span class="bd"><span class="date">即將發布</span><h3>Qualichem 油品</h3><p>Qualichem 相關油品資訊整理中，確認後將於此發布；未來可能移至「油品介紹」分類。</p></span></div></li>''')
    for fn in NEWS_ORDER:
        n = NEWS[fn]
        thumb = n['thumb']['src'] if n.get('thumb') else None
        ph = f'<span class="ph">{im(thumb, "")}<span class="chip y sm">{CAT_NAME[NEWS_CAT[fn]]}</span></span>' if thumb else f'<span class="ph empty"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg><span class="chip y sm">{CAT_NAME[NEWS_CAT[fn]]}</span></span>'
        ex = n['excerpt'] or text_of(n['html'], 70)
        lis.append(f'''<li data-cat="{NEWS_CAT[fn]}"><a class="ncard" href="{fn}">{ph}<span class="bd"><time datetime="{n["date"]}">{n["date"].replace("-", ".")}</time><h3>{E(clean_title(n["title"]))}</h3><p>{E(text_of(ex, 80))}</p><span class="foot">閱讀更多 <span aria-hidden="true">→</span></span></span></a></li>''')
    counts = {c: sum(1 for x in NEWS_CAT.values() if x == c) for c in CAT_NAME}
    counts['nexustest'] = 1
    counts['launch'] = 1
    tabs = ''.join(f'<button role="tab" type="button" data-key="{k}" data-hash="{k if k != "all" else ""}" aria-selected="false">{t}<span class="c">{c}</span></button>'
                   for k, t, c in [('all', '全部', len(NEWS_ORDER) + 2)] + [(k, v if k != 'nexustest' else '跨界合作－NEXUSTEST', counts[k]) for k, v in CAT_NAME.items()])
    body = hero([(None, '最新消息')], 'News ／ 最新消息', ['展覽、合作與', '圓華的最新動態'],
                lede='圓華參與的工具機展、自動化展與產業合作消息，以及品質認證等公告。',
                img=NEWS['news-detail15.html']['cover']['src'] if NEWS['news-detail15.html'].get('cover') else 'img/hero-1.jpg', pos='50% 40%')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Latest ／ 消息列表</span>
      {sec_title(['最新消息'])}
    </div>
    <div class="tabs" role="tablist" aria-label="消息分類" data-tabs="filter">{tabs}</div>
    <ul class="ngrid" data-filter-grid>{''.join(lis)}</ul>
    <div class="empty-state" data-empty hidden>
      <svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg>
      <b>目前尚無消息</b>
      <p data-for="launch">新產品發表內容整理中，將由圓華提供後發布。</p>
    </div>
  </div>
</section>
''' + cta_band()
    page('news.html', '最新消息', '圓華油品最新消息：展覽參展資訊、跨界合作、新產品發表與 ISO 9001:2015 認證公告。', 'news', body)
    # detail pages
    order = NEWS_ORDER
    for i, fn in enumerate(order):
        n = NEWS[fn]
        prev_ = order[i + 1] if i + 1 < len(order) else None
        next_ = order[i - 1] if i > 0 else None
        h = fix_html(n['html'])
        h = re.sub(r'(<p>(?:(?!</p>).)*</p>\s*)\1+', r'\1', h, flags=re.S)  # collapse repeated captions
        cover = f'<figure class="cover" data-rv="up">{im(n["cover"]["src"], clean_title(n["title"]))}</figure>' if n.get('cover') else ''
        g = f'<section class="pd-sec" data-rv="up"><h2>活動照片</h2>{gal(n["gallery"], clean_title(n["title"]))}</section>' if n.get('gallery') else ''
        pager = '<nav class="pager" aria-label="上一則／下一則">'
        pager += f'<a href="{prev_}"><small>← 較早</small><b>{E(clean_title(NEWS[prev_]["title"]))}</b></a>' if prev_ else '<span></span>'
        pager += f'<a class="nx" href="{next_}"><small>較新 →</small><b>{E(clean_title(NEWS[next_]["title"]))}</b></a>' if next_ else '<span></span>'
        pager += '</nav>'
        title = clean_title(n['title'])
        body = hero([('news.html', '最新消息'), (None, CAT_NAME[NEWS_CAT[fn]])], f'News ／ {CAT_NAME[NEWS_CAT[fn]]}', [title], small=True,
                    img=n['cover']['src'] if n.get('cover') and (n['cover']['w'] or 0) >= 700 else 'img/hero-1.jpg', pos='50% 40%')
        body += f'''
<section class="sec first">
  <div class="wrap">
    <article class="article">
      <div class="meta" data-rv="up"><span class="chip g sm">{CAT_NAME[NEWS_CAT[fn]]}</span><time datetime="{n["date"]}">{n["date"].replace("-", ".")}</time></div>
      {cover}
      <div class="prose" data-rv="up">{h}</div>
      {g}
      <a class="back" href="news.html">← 回到最新消息</a>
      {pager}
    </article>
  </div>
</section>
''' + cta_band()
        page(fn, title, text_of(n['excerpt'] or n['html'], 110), 'news', body, lightbox=bool(n.get('gallery')))


# ---------------------------------------------------------------- gallery
ALBUM_EXTRA = {'exhibition-info-03.html': 'news-detail10.html', 'exhibition-info-04.html': 'news-detail11.html', 'exhibition-info-06.html': 'news-detail16.html'}
ALBUM_TITLE = {
    'exhibition-info-01.html': '2018 台灣國際工具機展', 'exhibition-info-02.html': '2019 台南工具機大展',
    'exhibition-info-03.html': '2019 中國國際工業博覽會', 'exhibition-info-04.html': '2019 台中工具機展',
    'exhibition-info-05.html': '2020 高雄自動化工業展', 'exhibition-info-06.html': '2020 TIAE 台中工具機展',
}


def gallery_pages():
    albums = list(reversed(D['albums']))
    for a in albums:
        extra = ALBUM_EXTRA.get(a['old'])
        imgs = list(a['images'])
        seen = {x['src'] for x in imgs if x}
        txt = ''
        if extra:
            n = NEWS_EXTRA = D['news'][extra]
            for g in n['gallery']:
                if g and g['src'] not in seen:
                    imgs.append(g); seen.add(g['src'])
            txt = n['excerpt'] or ''
        a['all'] = [x for x in imgs if x]
        a['txt'] = txt
        a['slug'] = 'album-' + a['old'][-7:-5]
        a['name'] = ALBUM_TITLE[a['old']]
    cards = ''.join(f'''<li data-cat="expo"><a class="ncard" href="{a["slug"]}.html"><span class="ph">{im((a["cover"] or a["all"][0])["src"], "")}<span class="chip y sm">{len(a["all"])} 張照片</span></span><span class="bd"><span class="date">EXHIBITION</span><h3>{E(a["name"])}</h3><p>{E(text_of(a["txt"], 60) or "展覽現場花絮照片。")}</p><span class="foot">觀看相簿 <span aria-hidden="true">→</span></span></span></a></li>''' for a in albums)
    press = [o for o in D['news_orphans'] if '工商時報' in o['title']]
    press_html = ''
    if press:
        o = press[0]
        press_html = f'''<ul class="ngrid"><li><div class="ncard"><span class="ph">{im(o["thumb"]["src"], "") if o.get("thumb") else ""}<span class="chip y sm">媒體報導</span></span><span class="bd"><time datetime="{o["date"]}">{o["date"].replace("-", ".")}</time><h3>{E(clean_title(o["title"]))}</h3><p>{E(text_of(o["excerpt"], 120))}</p><span class="foot" style="color:var(--ink-soft)">完整報導內容待確認</span></span></div></li></ul>'''
    vids = [('LELFrQztGWM', '圓華油品介紹影片', '關於圓華油品的介紹影片。', D['company_photos'][9]['src']),
            ('iLwythbC3N4', 'COSMOTECH LE 設備介紹', 'DESTIMAT® LE 減壓蒸發設備運轉介紹。', P['equipment-6']['hero']['src'] if P['equipment-6']['hero'] else 'img/cosmotech.jpg')]
    vhtml = ''.join(f'''<div class="vcard" data-rv="up"><div class="vid"><button class="poster" type="button" data-yt="{v}" aria-label="播放：{t}">{im(p, "")}<span aria-hidden="true">▶</span></button></div><b>{t}</b><p>{d}</p></div>''' for v, t, d, p in vids)
    vhtml += f'''<div class="vcard" data-rv="up"><div class="vid"><video controls preload="none" playsinline poster="{P['equipment-1']['hero']['src']}" aria-label="COSMOTECH FRIENDLY 廢水處理設備影片"><source src="{D['cosmo_video']}" type="video/mp4"></video></div><b>COSMOTECH FRIENDLY 廢水處理設備</b><p>水溶性廢液處理裝置 FRIENDLY 運轉影片。</p></div>'''
    empty = lambda t, p: f'<div class="empty-state"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-cam"/></svg><b>{t}</b><p>{p}</p></div>'
    panels = [('expo', '展覽花絮', f'<ul class="ngrid">{cards}</ul>'),
              ('press', '相關報導、專訪', press_html + empty('更多報導整理中', '相關報導與專訪內容將由圓華提供後發布。')),
              ('events', '活動、聚餐', empty('活動照片整理中', '公司活動、聚餐等照片將由圓華提供後發布。')),
              ('video', '影片', f'<div class="vgrid">{vhtml}</div>')]
    tabs = ''.join(f'<button role="tab" type="button" id="tab-{k}" aria-controls="panel-{k}" data-hash="{k}" aria-selected="false">{t}</button>' for k, t, _ in panels)
    pan = ''.join(f'<div class="panel" role="tabpanel" id="panel-{k}" aria-labelledby="tab-{k}" hidden>{h}</div>' for k, _, h in panels)
    cover = albums[0]['cover']['src'] if albums[0].get('cover') else 'img/hero-1.jpg'
    body = hero([(None, '歷年展會/活動花絮')], 'Gallery ／ 歷年展會/活動花絮', ['歷年展會', '與活動花絮'],
                lede='圓華歷年參與工具機展、自動化展與產業博覽會的現場紀錄，以及設備與公司介紹影片。', img=cover, pos='50% 45%')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Gallery ／ 花絮</span>
      {sec_title(['現場紀錄'])}
    </div>
    <div class="tabs" role="tablist" aria-label="花絮分類" data-tabs="panels">{tabs}</div>
    {pan}
  </div>
</section>
''' + cta_band()
    page('gallery.html', '歷年展會/活動花絮', '圓華油品歷年展會花絮、相關報導、活動照片與影片。', 'gallery', body)
    for i, a in enumerate(albums):
        prev_ = albums[i + 1] if i + 1 < len(albums) else None
        next_ = albums[i - 1] if i > 0 else None
        pager = '<nav class="pager" aria-label="上一本／下一本相簿">'
        pager += f'<a href="{prev_["slug"]}.html"><small>← 較早</small><b>{E(prev_["name"])}</b></a>' if prev_ else '<span></span>'
        pager += f'<a class="nx" href="{next_["slug"]}.html"><small>較新 →</small><b>{E(next_["name"])}</b></a>' if next_ else '<span></span>'
        pager += '</nav>'
        body = hero([('gallery.html', '歷年展會/活動花絮'), (None, a['name'])], 'Gallery ／ 展覽花絮', [a['name'], '展覽花絮'], small=True,
                    img=(a['cover'] or a['all'][0])['src'], pos='50% 45%')
        body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="article" style="max-width:none">
      <div class="meta" data-rv="up"><span class="chip g sm">展覽花絮</span><span>{len(a["all"])} 張照片</span></div>
      {f'<p class="lead-big" data-rv="up">{E(a["txt"])}</p>' if a['txt'] else ''}
      {gal(a['all'], a['name'])}
      <a class="back" href="gallery.html">← 回到歷年展會/活動花絮</a>
      {pager}
    </div>
  </div>
</section>
''' + cta_band()
        page(f'{a["slug"]}.html', f'{a["name"]}｜展覽花絮', f'圓華油品參與{a["name"]}的現場花絮照片。', 'gallery', body, lightbox=True)


# ---------------------------------------------------------------- FAQ + knowledge
FAQ_NAV = [('faq.html', '常見問題'), ('knowledge.html', '油品知識區'), ('oil-table.html', '油品標準用油表'), ('water-knowledge.html', '廢液(水)處理知識區')]
KN_TITLE = ['切削油劑之使用管理 Part-1', '水溶性切削液之更液過程（Part-2）', '新切削液添加：五大要項嚴守（Part-3）', '切削液日常管理（Part-4）']


def faq_page():
    items = D['faq']['items']
    qa = ''.join(f'<details class="qa" data-rv="up"{" open" if i == 0 else ""}><summary><span class="q">Q{i + 1}</span>{E(it["q"])}</summary><div class="a"><div class="prose">{fix_html(it["a"])}</div></div></details>' for i, it in enumerate(items))
    body = hero([(None, '常見問題')], 'FAQ ／ 常見問題', ['切削液使用', '常見問題'], lede=E(D['faq']['intro']), img='img/policy.jpg', pos='50% 40%')
    body += lnav(FAQ_NAV, 'faq.html', '常見問題')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Q&amp;A ／ 油品使用常見問題</span>
      {sec_title(['變質、起泡、分離、生鏽……', '先從原因開始了解'])}
    </div>
    <div class="qa-list">{qa}</div>
    <div class="mini-links" style="margin-top:clamp(36px,4vw,56px)">
      <a class="spec-card" href="knowledge.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h10l4 4v12H5zM15 4v4h4M8 12h8M8 16h6"/></svg></span><div><b>Knowledge</b><span>油品知識區：切削油劑之使用管理</span></div><i class="go">→</i></a>
      <a class="spec-card" href="oil-table.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4zM4 10h16M10 5v14"/></svg></span><div><b>Oil Chart</b><span>依機台與材質查詢標準用油</span></div><i class="go">→</i></a>
      <a class="spec-card" href="water-knowledge.html" data-rv="up"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3s-6 7-6 11a6 6 0 0012 0c0-4-6-11-6-11zM9 15a3 3 0 003 3"/></svg></span><div><b>Wastewater</b><span>廢液（水）處理知識區</span></div><i class="go">→</i></a>
    </div>
  </div>
</section>
''' + cta_band(title=('沒有找到您的問題？', '直接問圓華團隊'))
    page('faq.html', '常見問題', '切削液為何變質發臭、起泡、分離、乳化、變色、生鏽與機台清潔性等常見問題解答。', 'faq', body, 'img/policy.jpg')


def knowledge_pages():
    ks = D['knowledge']
    cards = ''.join(f'''<li><a class="ncard" href="knowledge-0{i + 1}.html"><span class="ph empty"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg><span class="chip y sm">Part {i + 1}</span></span><span class="bd"><time datetime="{k["date"]}">{k["date"].replace("-", ".")}</time><h3>{E(KN_TITLE[i])}</h3><p>{E(text_of(k["excerpt"], 80))}</p><span class="foot">閱讀文章 <span aria-hidden="true">→</span></span></span></a></li>''' for i, k in enumerate(ks))
    body = hero([('faq.html', '常見問題'), (None, '油品知識區')], 'Knowledge ／ 油品知識區', ['切削油劑之', '使用管理'],
                lede='從更液、添加到日常管理，整理切削液在現場使用時需要注意的重點。', img='img/lab.jpg', pos='50% 50%')
    body += lnav(FAQ_NAV, 'knowledge.html', '常見問題')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Articles ／ 文章列表</span>
      {sec_title(['油品知識區'])}
    </div>
    <ul class="ngrid" data-rv="up">{cards}</ul>
  </div>
</section>
''' + cta_band()
    page('knowledge.html', '油品知識區', '切削油劑之使用管理系列文章：更液過程、新切削液添加、日常管理。', 'faq', body, 'img/lab.jpg')
    for i, k in enumerate(ks):
        prev_ = i - 1 if i > 0 else None
        next_ = i + 1 if i + 1 < len(ks) else None
        pager = '<nav class="pager" aria-label="上一篇／下一篇">'
        pager += f'<a href="knowledge-0{prev_ + 1}.html"><small>← 上一篇</small><b>{E(KN_TITLE[prev_])}</b></a>' if prev_ is not None else '<span></span>'
        pager += f'<a class="nx" href="knowledge-0{next_ + 1}.html"><small>下一篇 →</small><b>{E(KN_TITLE[next_])}</b></a>' if next_ is not None else '<span></span>'
        pager += '</nav>'
        body = hero([('faq.html', '常見問題'), ('knowledge.html', '油品知識區'), (None, f'Part {i + 1}')], f'Knowledge ／ Part {i + 1}', [KN_TITLE[i]], small=True, img='img/lab.jpg')
        body += lnav(FAQ_NAV, 'knowledge.html', '常見問題')
        body += f'''
<section class="sec first">
  <div class="wrap">
    <article class="article">
      <div class="meta" data-rv="up"><span class="chip g sm">油品知識區</span><time datetime="{k["date"]}">{k["date"].replace("-", ".")}</time></div>
      <div class="prose" data-rv="up">{fix_html(k["html"])}</div>
      <a class="back" href="knowledge.html">← 回到油品知識區</a>
      {pager}
    </article>
  </div>
</section>
''' + cta_band()
        page(f'knowledge-0{i + 1}.html', KN_TITLE[i], text_of(k['excerpt'] or k['html'], 110), 'faq', body)


def fmt_oil(v):
    if v in (None, 'N/A', ''):
        return '—'
    return re.sub(r'\s*,\s*|\s+', '、', v.strip())


def oil_table_page():
    rows = D['oil_table']
    mats = [m for m, _ in rows[0]['rows']]
    head = '<tr><th scope="col">加工機種＼材質</th>' + ''.join(f'<th scope="col" data-col="{j}">{E(m)}</th>' for j, m in enumerate(mats)) + '</tr>'
    body_rows = ''
    for r in rows:
        vals = dict(r['rows'])
        body_rows += f'<tr><th scope="row">{E(r["machine"])}</th>' + ''.join(
            f'<td data-col="{j}"{NA_CLS if vals.get(m, "N/A") in ("N/A", "") else ""}>{E(fmt_oil(vals.get(m)))}</td>' for j, m in enumerate(mats)) + '</tr>'
    filt = '<button class="btn-chip" type="button" data-col="all" aria-pressed="true">全部</button>' + ''.join(f'<button class="btn-chip" type="button" data-col="{j}" aria-pressed="false">{E(m)}</button>' for j, m in enumerate(mats))
    body = hero([('faq.html', '常見問題'), (None, '油品標準用油表')], 'Oil Chart ／ 標準用油表', ['依機台與材質，', '查詢標準用油'],
                lede='依加工機種與工件材質整理的 SAN-I Yushiro 標準用油建議。實際選用仍需依加工條件、水質與設備狀況評估。',
                cta='<a class="btn y" href="contact.html?item=標準用油表諮詢#form">請圓華協助選油 <i>→</i></a>', img='img/hero-1.jpg', pos='50% 50%')
    body += lnav(FAQ_NAV, 'oil-table.html', '常見問題')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Standard ／ 標準用油表</span>
      {sec_title(['加工機種 × 工件材質'])}
      <p class="lede" data-rv="up">點選材質可以只看該欄的建議油品；表格可左右滑動。</p>
    </div>
    <div class="mat-filter tabs" role="group" aria-label="依材質篩選"><span>MATERIAL</span>{filt.replace('class="btn-chip"', '')}</div>
    <div class="tbl-wrap" style="margin-top:18px" data-rv="up"><table class="tbl otable"><thead>{head}</thead><tbody>{body_rows}</tbody></table></div>
    <p class="scroll-hint">左右滑動查看完整表格</p>
    <p class="legend" style="margin-top:14px">表中為產品型號（如 EC-202、UX-11）；「—」表示原表標示 N/A。</p>
  </div>
</section>
''' + cta_band(title=('找不到對應的機台？', '告訴我們加工條件'))
    body = body.replace('<button type="button" data-col', '<button type="button" data-col')
    page('oil-table.html', '油品標準用油表', '依加工機種與工件材質查詢 SAN-I Yushiro 標準用油建議。', 'faq', body, 'img/hero-1.jpg')


def water_knowledge_page():
    body = hero([('faq.html', '常見問題'), (None, '廢液(水)處理知識區')], 'Wastewater ／ 廢液處理知識區', ['廢液（水）', '處理知識區'],
                lede='整理工業廢水處理、廢水處理機與廢水設備相關知識。', img='img/policy.jpg', pos='50% 50%')
    body += lnav(FAQ_NAV, 'water-knowledge.html', '常見問題')
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Articles ／ 文章列表</span>
      {sec_title(['廢液（水）處理知識區'])}
    </div>
    <div class="empty-state" data-rv="up"><svg viewBox="0 0 48 48" aria-hidden="true"><use href="#i-doc"/></svg><b>文章整理中</b><p>舊站此分類目前沒有文章內容，將由圓華提供後發布。想先了解廢液減量方式，可以參考 COSMO TECH 設備介紹。</p><div class="btns-row" style="justify-content:center"><a class="btn g" href="equipment.html">查看廢水處理設備 <i>→</i></a></div></div>
  </div>
</section>
''' + cta_band(title=('想評估廢液減量？', '先告訴我們目前的廢液狀況'), qs=['每月廢液量大約多少？', '廢液種類：切削液、清洗廢水或其他？'],
               lede='提供目前的廢液種類、產生量與處理方式，圓華團隊會協助評估適合的設備與導入方式。')
    page('water-knowledge.html', '廢液(水)處理知識區', '工業廢水處理、廢水處理機與廢水設備相關知識。', 'faq', body, 'img/policy.jpg')


# ---------------------------------------------------------------- contact
def contact_page():
    ico = {
        'tel': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2"/></svg>',
        'mail': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v12H3zM3 7l9 6 9-6"/></svg>',
        'line': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4c5 0 9 3.1 9 7s-4 7-9 7c-.8 0-1.6-.1-2.3-.2L5 20l1-3.6C4.2 15.1 3 13.2 3 11c0-3.9 4-7 9-7z"/></svg>',
    }
    topics = ['SAN-I Yushiro 植物性油品', '金屬加工油品', '工業潤滑油', '廢水處理設備', '廢油・廢水清運', '其他']
    addr = '台中市烏日區環中路八段 860 巷 101 號'
    q = 'https://www.google.com/maps/search/?api=1&query=' + '%E5%8F%B0%E4%B8%AD%E5%B8%82%E7%83%8F%E6%97%A5%E5%8D%80%E7%92%B0%E4%B8%AD%E8%B7%AF%E5%85%AB%E6%AE%B5860%E5%B7%B7101%E8%99%9F'
    embed = 'https://maps.google.com/maps?q=%E5%8F%B0%E4%B8%AD%E5%B8%82%E7%83%8F%E6%97%A5%E5%8D%80%E7%92%B0%E4%B8%AD%E8%B7%AF%E5%85%AB%E6%AE%B5860%E5%B7%B7101%E8%99%9F&z=16&output=embed'
    body = hero([(None, '聯絡我們')], 'Contact ／ 聯絡我們', ['有油品、加工或廢水問題？', '直接找我們討論'],
                lede='不確定該使用哪一款油品，或正在處理切削液、廢水與後續清運問題？簡單告訴我們目前遇到的狀況，圓華團隊會先協助了解需求，再一起確認適合的處理方式。',
                sub='不知道產品型號也沒關係，先告訴我們目前遇到的問題即可。',
                cta=f'<a class="btn y" href="tel:+886423355559">電話聯絡 04-2335-5559 <i>→</i></a><a class="btn glass" href="{LINE}" target="_blank" rel="noopener">LINE 詢問 <i>→</i></a><a class="btn glass" href="#form">留下需求，我們與您聯絡 <i>↓</i></a>',
                img='img/hero-3.jpg', pos='50% 40%')
    opts = ''.join(f'<option value="{t}">{t}</option>' for t in topics)
    body += f'''
<section class="sec first">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Quick Contact ／ 快速聯絡</span>
      {sec_title(['請選擇您最方便的方式', '與我們聯絡'])}
    </div>
    <div class="quick">
      <a class="qbtn main" href="tel:+886423355559" data-rv="up"><span class="ic">{ico['tel']}</span><span><small>電話聯絡</small><b>04-2335-5559</b><em>週一至週五 08:00 – 17:00</em></span><i>→</i></a>
      <a class="qbtn main" href="mailto:battor.oil@gmail.com" data-rv="up"><span class="ic">{ico['mail']}</span><span><small>Email</small><b>battor.oil@<wbr>gmail.com</b><em>來信請留下聯絡電話</em></span><i>→</i></a>
      <a class="qbtn" href="{LINE}" target="_blank" rel="noopener" data-rv="up" aria-label="LINE 詢問（LINE ID：@wmz2174k，另開新視窗）"><span class="ic">{ico['line']}</span><span><small>LINE</small><b>@wmz2174k</b><em>加入好友後直接傳訊息</em></span><i>→</i></a>
    </div>
  </div>
</section>

<section class="sec tight band round-r" id="form">
  <div class="wrap form-wrap">
    <div class="split-text">
      <span class="chip g" data-rv="pop">Inquiry ／ 需求表單</span>
      {sec_title(['請留下您的需求，', '我們將與您聯繫'])}
      <p class="lede" data-rv="up">不用準備完整資料，簡單留下目前想詢問的項目與遇到的問題即可。</p>
      <ul class="qs" data-rv="up" style="--q:var(--green)"><li>想了解更符合貴司加工用的油品</li><li>切削液容易產生異味、工件生鏽、油品起泡</li><li>需要處理製程廢水</li></ul>
    </div>
    <form class="form" id="ask" novalidate data-rv="up">
      <div class="field"><label for="f-name">姓名<span class="req" aria-hidden="true">＊</span></label><input id="f-name" name="name" autocomplete="name" required aria-describedby="e-name"><span class="err" id="e-name" aria-live="polite"></span></div>
      <div class="field"><label for="f-co">公司名稱<span class="req" aria-hidden="true">＊</span></label><input id="f-co" name="company" autocomplete="organization" required aria-describedby="e-co"><span class="err" id="e-co" aria-live="polite"></span></div>
      <div class="field"><label for="f-tel">聯絡電話<span class="req" aria-hidden="true">＊</span></label><input id="f-tel" name="tel" type="tel" autocomplete="tel" inputmode="tel" required aria-describedby="e-tel"><span class="err" id="e-tel" aria-live="polite"></span></div>
      <div class="field"><label for="f-topic">想詢問的項目<span class="req" aria-hidden="true">＊</span></label><select id="f-topic" name="topic" required aria-describedby="e-topic"><option value="">請選擇</option>{opts}</select><span class="err" id="e-topic" aria-live="polite"></span></div>
      <div class="field full"><label for="f-msg">簡單描述您的需求<span class="req" aria-hidden="true">＊</span></label><textarea id="f-msg" name="message" required aria-describedby="e-msg h-msg" placeholder="例如：想了解更符合貴司加工用的油品、切削液容易產生異味、工件生銹、油品起泡問題、需要處理製程廢水等。"></textarea><span class="err" id="e-msg" aria-live="polite"></span><span class="hint" id="h-msg">不知道產品型號也沒關係，描述現場狀況即可。</span></div>
      <div class="actions"><button class="btn g" type="submit">送出需求 <i>→</i></button><small>送出即表示同意圓華以您留下的資料與您聯繫。</small></div>
      <div class="form-done" id="ask-done" hidden role="status"><b>已收到您的需求（展示版）</b><p>此為網站展示版本，表單尚未串接寄送；正式上線後會直接寄到圓華信箱。如需立即聯絡，請來電 04-2335-5559 或使用 LINE。</p></div>
    </form>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="chip g" data-rv="pop">Company ／ 公司資訊</span>
      {sec_title(['圓華油品'])}
    </div>
    <div class="info-grid" style="margin-top:clamp(28px,3vw,40px)">
      <div class="info flat" data-rv="up">
        <h3>圓華油品股份有限公司</h3>
        <dl>
          <div class="row"><dt>Tel</dt><dd><a href="tel:+886423355559">04-2335-5559</a></dd></div>
          <div class="row"><dt>Fax</dt><dd>04-2335-8886</dd></div>
          <div class="row"><dt>Mail</dt><dd><a href="mailto:battor.oil@gmail.com">battor.oil@<wbr>gmail.com</a></dd></div>
          <div class="row"><dt>Hours</dt><dd>週一至週五 08:00 – 17:00</dd></div>
          <div class="row"><dt>Address</dt><dd>{addr}</dd></div>
          <div class="row"><dt>Area</dt><dd>服務範圍：全台皆有（以中部地區為主要服務區域）</dd></div>
        </dl>
        <div class="btns"><a class="btn y" href="{q}" target="_blank" rel="noopener">開啟 Google 地圖 <i>→</i></a></div>
      </div>
      <div class="map" data-rv="up"><iframe src="{embed}" title="圓華油品位置地圖：{addr}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
    </div>
  </div>
</section>

<section class="sec contact cta-sec">
  <div class="wrap">
    <div class="contact-panel" data-rv="rise">
      <span class="glow" aria-hidden="true"></span>
      <div class="contact-text">
        <span class="chip w" data-rv="pop">Ask Us ／ 歡迎詢問</span>
        {sec_title(['若不知道該從哪一個產品開始，', '也歡迎直接詢問我們'])}
        <p class="lede" data-rv="up">告訴我們現在遇到的問題，圓華團隊會先協助了解現況，再一起確認下一步。</p>
      </div>
      <div class="btns" data-rv="pop"><a class="btn g" href="tel:+886423355559">電話聯絡 <i>→</i></a><a class="btn g ping" href="{LINE}" target="_blank" rel="noopener">LINE 詢問 <i>→</i></a></div>
    </div>
  </div>
</section>
'''
    page('contact.html', '聯絡我們', '聯絡圓華油品：電話 04-2335-5559、Email battor.oil@gmail.com、LINE @wmz2174k，或留下需求表單，地址台中市烏日區環中路八段 860 巷 101 號。', 'contact', body, 'img/hero-3.jpg')


# ---------------------------------------------------------------- run
about(); milestone(); team()
products_hub()
for s in SERIES:
    series_page(s)
    for k in s['items']:
        product_page(k)
equipment_hub()
for e in EQ_ALL:
    equipment_page(e)
license_page()
news_pages()
gallery_pages()
faq_page(); knowledge_pages(); oil_table_page(); water_knowledge_page()
contact_page()
print(len(PAGES), 'pages')
json.dump(PAGES, open(os.path.join(os.path.dirname(DATA), 'pages.json'), 'w'))
