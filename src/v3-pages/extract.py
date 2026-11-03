"""Extract structured content from the crawled old battor.com.tw pages into data.json.

Usage: python -I extract.py <old_html_dir> <old_assets_dir> <out_site_dir> <data.json>
Images referenced by migrated content are optimised into <out_site_dir>/img/m/.
"""
import sys, os, re, json, hashlib, shutil
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from PIL import Image

HTML_DIR, ASSET_DIR, SITE, OUT = sys.argv[1:5]
IMG_OUT = os.path.join(SITE, 'img', 'm')
FILE_OUT = os.path.join(SITE, 'files')
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(FILE_OUT, exist_ok=True)

IMGMAP = {}   # old path -> {src, w, h}
NOTES = []    # migration notes for the report


def soup(fn):
    return BeautifulSoup(open(os.path.join(HTML_DIR, fn), encoding='utf-8', errors='replace').read(), 'html.parser')


def img(old, maxw=1600):
    """Optimise one old-site image into img/m and return {src,w,h}."""
    old = old.strip()
    if old in IMGMAP:
        return IMGMAP[old]
    p = os.path.join(ASSET_DIR, old)
    if not os.path.exists(p):
        NOTES.append(f'missing image {old}')
        IMGMAP[old] = None
        return None
    ext = os.path.splitext(old)[1].lower()
    h = hashlib.sha1(old.encode()).hexdigest()[:10]
    im = Image.open(p)
    w0, h0 = im.size
    if ext == '.gif':
        name = h + '.gif'
        shutil.copyfile(p, os.path.join(IMG_OUT, name))
        w, hh = w0, h0
    elif ext == '.png' and im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        if w0 > maxw:
            im = im.resize((maxw, round(h0 * maxw / w0)), Image.LANCZOS)
        name = h + '.png'
        im.save(os.path.join(IMG_OUT, name), optimize=True)
        w, hh = im.size
    else:
        im = im.convert('RGB')
        if w0 > maxw:
            im = im.resize((maxw, round(h0 * maxw / w0)), Image.LANCZOS)
        name = h + '.jpg'
        im.save(os.path.join(IMG_OUT, name), quality=80, optimize=True, progressive=True)
        w, hh = im.size
    IMGMAP[old] = {'src': 'img/m/' + name, 'w': w, 'h': hh}
    return IMGMAP[old]


def copy_file(old, new):
    shutil.copyfile(os.path.join(ASSET_DIR, old), os.path.join(FILE_OUT, new))
    return 'files/' + new


# ---------------------------------------------------------------- link map (old page -> new page)
LINKMAP = {
    'index.html': 'index.html', 'about-us.html': 'about.html', 'history.html': 'milestone.html',
    'service-team.html': 'team.html', 'exhibition.html': 'gallery.html', 'news.html': 'news.html',
    'faq.html': 'faq.html', 'oil-knowledge.html': 'knowledge.html', 'oil-basic.html': 'oil-table.html',
    'water-knowledge.html': 'water-knowledge.html', 'contact.php': 'contact.html',
    'yushiro-product-oil.html': 'yushiro-plant.html', 'yushiro-product-oil-1.html': 'yushiro-plant-oil.html',
    'yushiro-product-main.html': 'yushiro.html', 'battor-product-main.html': 'battor.html',
    'formosa-product-main.html': 'formosa.html', 'cosmotech-product-main.html': 'equipment.html',
}
YU = {'1': 'water', '2': 'cutting-oil', '3': 'rust', '5': 'tempering', '6': 'cleaner', '7': 'additive'}
for k, v in YU.items():
    LINKMAP[f'yushiro-product-index-{k}.html'] = f'yushiro-{v}.html'
for i in range(1, 13):
    LINKMAP[f'battor-product-index-{i}.html'] = f'battor-{i:02d}.html'
    LINKMAP[f'formosa-product-index-{i}.html'] = f'formosa-{i:02d}.html'
for i in range(1, 7):
    LINKMAP[f'cosmotech-product-index-{i}.html'] = f'equipment-{i}.html'
    LINKMAP[f'exhibition-info-0{i}.html'] = f'album-0{i}.html'
for i in range(1, 5):
    LINKMAP[f'oil-knowledge-info-0{i}.html'] = f'knowledge-0{i}.html'


# ---------------------------------------------------------------- HTML sanitiser
KEEP = {'p', 'br', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'img', 'a', 'strong', 'b', 'em', 'sup', 'sub', 'iframe', 'video', 'source', 'div', 'figure', 'small', 'nav'}
ATTRS = {'colspan', 'rowspan', 'src', 'alt', 'href', 'title', 'class', 'id', 'poster'}
OUR_CLASSES = {'spec-h', 'grp', 'jump', 'tbl', 'vid', 'num', 'gal', 'note'}
DROP_IMG = re.compile(r'images/(team_\d+\.jpg|product/(battor|formosa|yushiro)/pd_600\.png|Icon_team\.png|Play-Icon\.png|preloader)')


def mark_tables(node):
    """Old spec tables use td.table_title* for headings: turn those into th before classes are stripped."""
    for td in node.select('td'):
        cls = ' '.join(td.get('class', []))
        inner = td.select_one('.table_title00, .table_title01, .table_title02')
        if 'table_title02' in cls or (inner is not None and 'table_title02' in ' '.join(inner.get('class', []))):
            td.name = 'th'; td['class'] = ['grp']
        elif 'table_title0' in cls:
            td.name = 'th'; td['class'] = []
        elif inner is not None and td.get_text(strip=True) == inner.get_text(strip=True):
            td.name = 'th'; td['class'] = []
    # a header row in the cosmotech / knowledge tables: first row of plain cells -> th
    return node


def sanitize(node, page):
    for c in node.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for t in node.select('script,style,noscript,canvas,i.fa,form,input,button,.blog_comment,.page_post'):
        t.decompose()
    mark_tables(node)
    for t in list(node.find_all(True)):
        if t.parent is None:
            continue
        if t.name == 'h1':
            t.name = 'h3'
        if t.name not in KEEP:
            t.unwrap(); continue
        cls = [c for c in t.get('class', []) if c in OUR_CLASSES]
        for a in list(t.attrs):
            if a not in ATTRS:
                del t.attrs[a]
        if cls:
            t['class'] = cls
        elif 'class' in t.attrs:
            del t['class']
        if t.name not in ('h3', 'th', 'nav') and 'id' in t.attrs:
            del t['id']
    for t in list(node.find_all('img')):
        src = t.get('src', '')
        if DROP_IMG.search(src) or not src:
            t.decompose(); continue
        m = img(src)
        if not m:
            t.decompose(); continue
        t['src'] = m['src']; t['width'] = str(m['w']); t['height'] = str(m['h'])
        t['loading'] = 'lazy'; t['decoding'] = 'async'
        if not t.get('alt') or t['alt'] in ('img', 'Product', 'story_img'):
            t['alt'] = ''
        if 'title' in t.attrs:
            del t['title']
    for a in list(node.find_all('a')):
        href = (a.get('href') or '').strip()
        base = href.split('#')[0]
        if not href or href.startswith('#') or href.startswith('javascript'):
            a.unwrap(); continue
        if base == 'iformosa-product-index-2.html':
            base = href = 'formosa-product-index-2.html'
        if base in LINKMAP:
            a['href'] = LINKMAP[base] + (('#' + href.split('#')[1]) if '#' in href else '')
        elif href.lower().endswith('.pdf'):
            name = {'中文版': 'iso-9001-2015-zh.pdf', '英文版': 'iso-9001-2015-en.pdf'}
            new = next((v for k, v in name.items() if k in href), os.path.basename(href))
            a['href'] = copy_file(href, new); a['target'] = '_blank'; a['rel'] = 'noopener'
        elif re.search(r'\.(jpe?g|png|gif)$', href, re.I):
            # old lightbox links: keep the image only
            a.unwrap(); continue
        elif href.startswith('http'):
            a['target'] = '_blank'; a['rel'] = 'noopener'
        else:
            NOTES.append(f'{page}: unmapped link {href}')
            a.unwrap(); continue
        if 'title' in a.attrs:
            del a['title']
    for f in node.find_all('iframe'):
        src = f.get('src', '')
        f.attrs = {'src': src, 'title': '影片', 'loading': 'lazy', 'allowfullscreen': '',
                   'allow': 'accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture'}
        f.wrap(BeautifulSoup('', 'html.parser').new_tag('div', attrs={'class': 'vid'}))
    for t in node.find_all(['div', 'figure']):
        if not t.get('class'):
            t.unwrap()
    # drop empty paragraphs / headings
    for t in node.find_all(['p', 'h3', 'h4', 'li', 'strong', 'b']):
        if not t.get_text(strip=True) and not t.find(['img', 'iframe', 'video', 'table']):
            t.decompose()
    for t in node.find_all('table'):
        if not t.get('class'):
            t['class'] = ['tbl']
    return node


def html_of(node):
    s = ''.join(str(c) for c in node.contents) if isinstance(node, Tag) else str(node)
    s = re.sub(r'\s(style|width|height|align|valign|bgcolor|border|cellpadding|cellspacing)="[^"]*"(?=[^<]*>)', lambda m: m.group(0) if m.group(1) in ('width', 'height') and 'img/m/' in s[max(0, m.start()-200):m.start()] else '', s)
    s = s.replace('\xa0', ' ')
    s = re.sub(r'[ \t\r\f\v]+', ' ', s)
    s = re.sub(r'\s*\n\s*', '\n', s)
    s = re.sub(r'(<br/>\s*){3,}', '<br/><br/>', s)
    return s.strip()


def text(node):
    return re.sub(r'\s+', ' ', node.get_text(' ', strip=True)).strip() if node else ''


def wrap_html(items):
    holder = BeautifulSoup('<div></div>', 'html.parser').div
    for it in items:
        holder.append(it)
    return holder


# ---------------------------------------------------------------- products / equipment (shared old template)
def product_page(fn):
    s = soup(fn)
    col = s.select_one('.blog_section div.col-lg-9')
    blocks = [b for b in col.select('div.col-lg-12') if b.select_one('.base_md001 h3') and b.find_parent('div', class_='col-lg-12') is None]
    # some pages put the 2nd block outside the first row: also take direct col-lg-12 siblings
    title = text(blocks[0].select_one('.base_md001 h3'))
    pl = blocks[0].select_one('.product-list')
    hero = None
    hi = pl.select_one('.image img') if pl else None
    if hi is not None and not DROP_IMG.search(hi.get('src', '')):
        hero = img(hi['src'])
    overview, apps = [], []
    if pl:
        nd = pl.select_one('.name-desc')
        label = None
        for c in nd.children if nd else []:
            if not isinstance(c, Tag):
                continue
            cls = c.get('class', [])
            if 'namex' in cls:
                label = text(c).rstrip(':： ')
                continue
            if 'description' in cls and label and '應用範圍' in label:
                apps = [i['src'] for i in c.select('img')]
                label = None
                continue
            node = sanitize(c, fn)
            node.attrs = {}
            h = html_of(node) if 'description' in cls else html_of(wrap_html([node]))
            if text(BeautifulSoup(h, 'html.parser')):
                overview.append({'label': label or '', 'html': h})
            label = None
    sections = []
    for b in blocks[1:]:
        head = text(b.select_one('.base_md001 h3'))
        if '相關系列' in head:
            continue
        b.select_one('.base_md001').decompose()
        for ab in b.select('.abt_heading_wrapper'):
            ab.decompose()
        # numbered sub-headings
        for sm in b.select('.series_md001'):
            num = text(sm.select_one('.series_md001_l_in'))
            r = sm.select_one('.series_md001_r')
            sub = r.find('span')
            subt = text(sub) if sub else ''
            if sub: sub.extract()
            for br in r.find_all('br'): br.replace_with(' ')
            main = text(r)
            h = s.new_tag('h3', attrs={'class': 'spec-h'})
            if sm.get('id'): h['id'] = sm['id']
            n = s.new_tag('em', attrs={'class': 'num'}); n.string = num; h.append(n)
            h.append(main)
            if subt:
                sm2 = s.new_tag('small'); sm2.string = subt; h.append(sm2)
            sm.replace_with(h)
        for t in b.select('table'):
            t.attrs.pop('id', None)
        node = sanitize(b, fn)
        sections.append({'title': head, 'html': html_of(node)})
    # in-page jump list (yushiro "block_ui")
    jumps = []
    for a in col.select('ul.block_ui a'):
        jumps.append({'href': a.get('href'), 'label': text(a)})
    # the cosmotech LE page keeps a free-form entry-content block after the overview
    return {'old': fn, 'title': title, 'hero': hero, 'overview': overview,
            'apps': [img(a) for a in apps if a and not re.search(r'team_\d', a)],
            'apps_generic': bool([a for a in apps if re.search(r'team_\d', a)]),
            'sections': sections, 'jumps': jumps}


def menu_names(fn):
    """Sidebar names for Battor / Formosa / Yushiro items (short names)."""
    s = soup(fn)
    out = {}
    for a in s.select('.right_blog_category_list_wrapper a'):
        out[a['href']] = text(a)
    return out


def series_main(fn):
    s = soup(fn)
    col = s.select_one('.blog_section div.col-lg-9')
    node = sanitize(col, fn)
    return html_of(node)


def series_listing(fn):
    """Battor/Formosa main pages list each product with its model line and blurb."""
    s = soup(fn)
    col = s.select_one('.blog_section div.col-lg-9')
    out = {}
    for blk in col.select('.blog_about, .product-list, .gray_bg'):
        a = blk.select_one('h1 a, .namex a, h2 a, h3 a')
        if not a or not a.get('href'):
            continue
        out.setdefault(a['href'], {'name': text(a), 'blurb': text(blk.select_one('p, .description'))})
    return out


# ---------------------------------------------------------------- news / albums / knowledge
def news_list():
    s = soup('news.html')
    col = s.select_one('.blog_section div.col-lg-9')
    items = []
    for h in col.select('h1'):
        a = h.find('a')
        if not a: continue
        box = h.find_parent(class_='blog_index_post_wrapper') or h.parent.parent
        im = box.select_one('img')
        lis = [text(li) for li in box.select('.blog_txt_info li')]
        date = next((x for x in lis if re.match(r'\d{4}-\d{2}-\d{2}', x)), '')
        p = box.select_one('.blog_txt p')
        items.append({'old': a['href'], 'title': text(a), 'date': date, 'thumb': im['src'] if im else None,
                      'excerpt': text(p)})
    return items


def news_detail(fn):
    s = soup(fn)
    col = s.select_one('.blog_section div.col-lg-9')
    h = col.find('h1')
    title = text(h)
    lis = [text(li) for li in col.select('.blog_txt_info li')]
    date = next((x for x in lis if re.match(r'\d{4}-\d{2}-\d{2}', x)), '')
    first_img = col.select_one('img')
    cover = first_img['src'] if first_img else None
    if first_img is not None:
        first_img.decompose()
    if h: h.decompose()
    for u in col.select('.blog_txt_info'): u.decompose()
    gallery = []
    # albums inside news: <a href=img><img></a><p>caption</p> sequences
    for a in col.select('a[href]'):
        if re.search(r'\.(jpe?g|png)$', a['href'], re.I) and a.find('img'):
            gallery.append(a['href'])
    if len(gallery) >= 4:
        for a in col.select('a[href]'):
            if re.search(r'\.(jpe?g|png)$', a['href'], re.I):
                nxt = a.find_next_sibling()
                if nxt is not None and nxt.name == 'p' and len(text(nxt)) < 40:
                    nxt.decompose()
                a.decompose()
    node = sanitize(col, fn)
    return {'old': fn, 'title': title, 'date': date, 'cover': img(cover) if cover else None,
            'html': html_of(node), 'gallery': [img(g) for g in gallery] if len(gallery) >= 4 else []}


def album(fn):
    s = soup(fn)
    title = text(s.select_one('h1.whitetxt'))
    imgs = [i['src'] for i in s.select('#gridWrapper .port_img_wrapper img')]
    return {'old': fn, 'title': title, 'images': [img(i) for i in imgs]}


def knowledge(fn):
    s = soup(fn)
    col = s.select_one('.blog_section div.col-lg-9')
    h = col.find(['h2', 'h1'])
    title = text(h).strip('【】 ')
    lis = [text(li) for li in col.select('ul li')[:3]]
    date = next((re.sub(r'.*?(\d{4}-\d{2}-\d{2}).*', r'\1', x) for x in lis if re.search(r'\d{4}-\d{2}-\d{2}', x)), '')
    if h: h.decompose()
    u = col.find('ul')
    if u is not None and '分類標籤' in text(u): u.decompose()
    node = sanitize(col, fn)
    return {'old': fn, 'title': title, 'date': date, 'html': html_of(node)}


def knowledge_list():
    s = soup('oil-knowledge.html')
    col = s.select_one('.blog_section div.col-lg-9')
    out = {}
    for h in col.select('h2'):
        a = h.find('a')
        p = h.find_next('p')
        out[a['href']] = text(p)
    return out


def faq():
    s = soup('faq.html')
    out = []
    for p in s.select('.sidebar_wrapper .panel'):
        q = text(p.select_one('.panel-title')).lstrip('-– \t')
        body = p.select_one('.panel_cont') or p.select_one('.panel-body')
        out.append({'q': q, 'a': html_of(sanitize(body, 'faq.html'))})
    intro = text(s.select_one('.choose_heading_wrapper p'))
    return {'intro': intro, 'items': out}


def oil_table():
    s = soup('oil-basic.html')
    out = []
    for b in s.select('.blog_wrapper .blog_about'):
        name = text(b.select_one('h1'))
        rows = []
        for li in b.select('li'):
            t = text(li)
            if ':' in t or '：' in t:
                k, v = re.split(r'[:：]', t, 1)
                rows.append([k.strip(), v.strip()])
        out.append({'machine': name, 'rows': rows})
    return out


def about_old():
    s = soup('about-us.html')
    w = s.select_one('.about_us_wrapper')
    photos = [img(i['src']) for i in w.select('img') if 'company_use' in i.get('src', '')]
    vids = [f.get('src') for f in s.select('iframe') if 'youtube' in f.get('src', '')]
    return {'photos': photos, 'videos': vids}


# ---------------------------------------------------------------- run
data = {}

# products
names = menu_names('battor-product-index-1.html')
data['menu'] = names
data['products'] = {}
for old, new in LINKMAP.items():
    m = re.match(r'(yushiro-product-(index-\d|oil-1)|battor-product-index-\d+|formosa-product-index-\d+|cosmotech-product-index-\d)\.html$', old)
    if not m:
        continue
    d = product_page(old)
    d['slug'] = new[:-5]
    d['menu'] = names.get(old, '')
    data['products'][d['slug']] = d

data['series_html'] = {fn: series_main(fn) for fn in ('battor-product-main.html', 'formosa-product-main.html', 'yushiro-product-main.html', 'cosmotech-product-main.html', 'yushiro-product-oil.html')}

# news + albums
data['news_list'] = news_list()
data['news'] = {}
for fn in ['news-detail.html'] + [f'news-detail{i}.html' for i in range(1, 18)]:
    d = news_detail(fn)
    # the old list links several items to the wrong detail page: only trust a list row whose title matches
    row = next((it for it in data['news_list'] if it['old'] == fn and it['title'][:8] == d['title'][:8]), None)
    d['thumb'] = img(row['thumb']) if row and row['thumb'] else d['cover']
    d['excerpt'] = row['excerpt'] if row else ''
    data['news'][fn] = d
# list rows that point at a page with a different title (e.g. the 工商時報 report) are kept for review
data['news_orphans'] = [dict(it, thumb=img(it['thumb']) if it['thumb'] else None) for it in data['news_list']
                        if data['news'].get(it['old']) and data['news'][it['old']]['title'][:8] != it['title'][:8]]
data['albums'] = [album(f'exhibition-info-0{i}.html') for i in range(1, 7)]
s = soup('exhibition.html')
covers = {}
for a in s.select('a[href^="exhibition-info"]'):
    im = a.find('img') or (a.find_parent().find('img') if a.find_parent() else None)
    if im is not None:
        covers.setdefault(a['href'], im['src'])
for al in data['albums']:
    c = covers.get(al['old'])
    al['cover'] = img(c) if c else (al['images'][0] if al['images'] else None)

# knowledge, faq, oil table, about
kl = knowledge_list()
data['knowledge'] = []
for i in range(1, 5):
    d = knowledge(f'oil-knowledge-info-0{i}.html')
    d['excerpt'] = kl.get(f'oil-knowledge-info-0{i}.html', '')
    data['knowledge'].append(d)
data['faq'] = faq()
data['oil_table'] = oil_table()
data['about_old'] = about_old()
data['cosmo_video'] = copy_file('videos/COSMOTECH-Friendly-廢水處理設備影片.mp4', 'cosmotech-friendly.mp4')
data['iso'] = {'zh': 'files/iso-9001-2015-zh.pdf', 'en': 'files/iso-9001-2015-en.pdf'}
for k in ('images/news/ISO-9001-2015-國際品質管理系統認證-圓華油品-中文版.pdf', 'images/news/ISO-9001-2015-國際品質管理系統認證-圓華油品-英文版.pdf'):
    copy_file(k, 'iso-9001-2015-zh.pdf' if '中文' in k else 'iso-9001-2015-en.pdf')
for k in ('images/news/ISO-9001-2015-國際品質管理系統認證-圓華油品-中文版.jpg', 'images/news/ISO-9001-2015-國際品質管理系統認證-圓華油品-英文版.jpg',
          'images/news/sgs.jpg', 'images/news/reach.jpg', 'images/news/rohs.jpg', 'images/news/ISO-9001-2015.jpg'):
    data.setdefault('iso_imgs', {})[os.path.basename(k)] = img(k)
data['company_photos'] = [img('images/company_use/' + f) for f in sorted(os.listdir(os.path.join(ASSET_DIR, 'images/company_use')))]
data['drums'] = {k: img(f'images/product/{k}/pd_600.png', 900) for k in ('battor', 'formosa', 'yushiro')}
data['apps_generic'] = [img(f'images/team_{n}.jpg') for n in (4, 11, 6, 2)]
data['notes'] = NOTES
json.dump(data, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('products', len(data['products']), 'news', len(data['news']), 'albums', len(data['albums']),
      'knowledge', len(data['knowledge']), 'faq', len(data['faq']['items']), 'oil', len(data['oil_table']),
      'images', len([v for v in IMGMAP.values() if v]))
print('\n'.join(NOTES[:40]))
