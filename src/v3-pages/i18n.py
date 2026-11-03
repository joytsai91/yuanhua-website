"""English edition of the C-version site, built from the Chinese pages + a translation table.

Every translatable piece of a Chinese page becomes one "unit":
  * a run of inline content (text + inline tags) inside a block element. Tags are masked as <1>…</1>
    (void tags as <1/>) so the translation never touches attributes; br/wbr stay literal.
  * a translatable attribute value (alt, aria-label, title, placeholder, meta content, option value…).
The table (i18n/en.json) maps the masked Chinese unit to its English text.

Usage:
  python -I i18n.py extract <site_dir> <en.json> <out.json>   # units still missing a translation (with context)
  python -I i18n.py build   <site_dir> <en.json>              # write <site_dir>/en/*.html, report gaps
"""
import sys, os, re, json, glob, html
from urllib.parse import quote, unquote, parse_qsl, urlencode
from bs4 import BeautifulSoup, NavigableString, Comment, Tag
from bs4.formatter import HTMLFormatter
from bs4.dammit import EntitySubstitution

CJK = re.compile(r'[　-〿㐀-鿿豈-﫿＀-￯]')
INLINE = {'a', 'abbr', 'b', 'bdi', 'bdo', 'br', 'cite', 'code', 'data', 'dfn', 'em', 'i', 'kbd', 'mark', 'q', 's',
          'samp', 'small', 'span', 'strong', 'sub', 'sup', 'time', 'u', 'var', 'wbr'}
VOID = {'br', 'wbr'}
OPAQUE = {'script', 'style', 'svg', 'noscript', 'template', 'iframe', 'video', 'canvas', 'math'}
NO_ATTR = {'script', 'style', 'svg', 'noscript', 'template', 'math'}   # attributes of video/iframe are still translated
ATTRS = ['alt', 'aria-label', 'title', 'placeholder', 'data-alt', 'value']
WS = re.compile(r'\s+')

# news stays in Chinese for now (client request): these parts of the news pages are left as they are
SKIP = {
    'news.html': ['.ngrid h3', '.ngrid p'],
    'news-detail': ['.phero h1', '.article .cover', '.article .prose', '.article .gal', '.pager b'],
}
SKIP_ATTR = 'data-i18n-skip'

# repeated attribute patterns, translated by rule instead of one table entry per number
PATTERNS = [
    (re.compile(r'^放大第 (\d+) 張照片$'), lambda m, t: f'Enlarge photo {m[1]}'),
    (re.compile(r'^第 (\d+) 張$'), lambda m, t: f'Slide {m[1]}'),
    (re.compile(r'^(.+) 照片 (\d+)$'), lambda m, t: f'{t(m[1])} – photo {m[2]}'),
]

class KeepOrder(HTMLFormatter):
    # keep attribute order and HTML5-style void/boolean attributes, so en/ pages diff cleanly against the Chinese ones
    def attributes(self, tag):
        return tag.attrs.items()


FMT = KeepOrder(entity_substitution=EntitySubstitution.substitute_xml, void_element_close_prefix=None, empty_attributes_are_booleans=True)

TITLE_SUFFIX = '｜圓華油品 YUAN HUA OIL'
EN_TITLE_SUFFIX = ' | Yuan Hua Oil'
NEWS_NOTE = 'News articles are currently published in Traditional Chinese only.'
ARTICLE_NOTE = 'This article is currently available in Traditional Chinese only.'
# strings set from inline scripts on the home page (site.js picks its own strings by <html lang>)
SCRIPT_STRINGS = {"'開啟選單'": "'Open menu'", "'關閉選單'": "'Close menu'"}


def has_cjk(s):
    return bool(CJK.search(s or ''))


def norm(s):
    return WS.sub(' ', s).strip()


def is_inline(node):
    if isinstance(node, Comment):
        return True
    if isinstance(node, NavigableString):
        return True
    if not isinstance(node, Tag) or node.name not in INLINE or node.has_attr(SKIP_ATTR) or node.get('translate') == 'no':
        return False
    return all(is_inline(c) for c in node.children)


def mask(nodes):
    """Serialize a run of inline nodes with every non-void tag (and attributed void tag) replaced by <k>…</k>."""
    tags = []

    def ser(n):
        if isinstance(n, Comment):
            return ''
        if isinstance(n, NavigableString):
            return str(n).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        if n.name in VOID and not n.attrs:
            return f'<{n.name}>'
        tags.append(n)
        k = len(tags)
        if n.name in VOID:
            return f'<{k}/>'
        return f'<{k}>' + ''.join(ser(c) for c in n.children) + f'</{k}>'

    s = ''.join(ser(n) for n in nodes)
    lead = re.match(r'\s*', s).group(0)
    trail = re.search(r'\s*$', s).group(0)
    return norm(s), tags, (' ' if lead else ''), (' ' if trail else '')


def tag_hint(tags):
    out = []
    for k, t in enumerate(tags, 1):
        cls = '.'.join(t.get('class', []))
        out.append(f'{k}={t.name}{"." + cls if cls else ""}')
    return ' '.join(out)


def start_tag(t):
    a = ''.join(f' {k}' if v == '' else f' {k}="' + (' '.join(v) if isinstance(v, list) else str(v)).replace('&', '&amp;').replace('"', '&quot;') + '"'
                for k, v in t.attrs.items())
    return f'<{t.name}{a}>'


def unmask(en, tags):
    """Rebuild HTML from a masked translation; raises ValueError when the tag set does not match."""
    seen = []

    def rep(m):
        close, k, void = m.group(1), int(m.group(2)), m.group(3)
        if k < 1 or k > len(tags):
            raise ValueError(f'unknown tag <{k}>')
        t = tags[k - 1]
        if void:
            seen.append(k)
            return start_tag(t)
        if close:
            return f'</{t.name}>'
        seen.append(k)
        return start_tag(t)

    out = re.sub(r'<(/?)(\d+)(/?)>', rep, en)
    if sorted(seen) != list(range(1, len(tags) + 1)):
        raise ValueError(f'tags {sorted(seen)} != 1..{len(tags)}')
    return out


def page_skips(fn):
    if fn == 'news.html':
        return SKIP['news.html']
    if fn.startswith('news-detail'):
        return SKIP['news-detail']
    return []


SVG = re.compile(r'<svg\b.*?</svg>', re.S)


def load(path, keep=None):
    # inline SVG is parked verbatim (html.parser would lower-case viewBox/linearGradient and expand <path/>)
    src = open(path, encoding='utf-8').read()
    if keep is not None:
        src = SVG.sub(lambda m: keep.append(m.group(0)) or f'<x-svg data-n="{len(keep) - 1}"></x-svg>', src)
    return BeautifulSoup(src, 'html.parser')


def mark_skips(soup, fn):
    for sel in page_skips(fn):
        for el in soup.select(sel):
            el[SKIP_ATTR] = ''


def in_skip(el):
    return any(p.has_attr(SKIP_ATTR) or p.get('translate') == 'no' for p in [el] + list(el.parents) if isinstance(p, Tag))


def walk(el, found):
    """Yield (kind, payload) units under el.  kind 'run': (parent, nodes)."""
    if not isinstance(el, Tag) or el.name in OPAQUE or el.has_attr(SKIP_ATTR) or el.get('translate') == 'no':
        return
    run = []
    group = el.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') or 'vcatch' in el.get('class', [])

    def flush():
        if run and any(has_cjk(str(n)) for n in run if not isinstance(n, Comment)):
            loose = any(isinstance(n, NavigableString) and not isinstance(n, Comment) and n.strip() for n in run)
            if loose or group:
                found.append((el, list(run)))
            else:   # only elements side by side (chip + date, two buttons…): translate each one on its own
                for n in run:
                    if isinstance(n, Tag):
                        walk(n, found)
        run.clear()

    for c in list(el.children):
        if is_inline(c):
            run.append(c)
        else:
            flush()
            walk(c, found)
    flush()


def page_units(soup, fn):
    """All units of a page: list of dicts {key, kind, ...}."""
    units = []
    found = []
    walk(soup.body, found)
    for parent, nodes in found:
        key, tags, _, _ = mask(nodes)
        units.append(dict(kind='html', key=key, ctx=f'<{parent.name}{"." + ".".join(parent.get("class", [])) if parent.get("class") else ""}>', tags=tag_hint(tags)))
    for el in soup.find_all(True):
        if el.name in NO_ATTR:
            continue
        for a in ATTRS:
            v = el.get(a)
            if isinstance(v, str) and has_cjk(v):
                if a == 'value' and el.name != 'option' and not (el.name == 'input' and el.get('type') in ('submit', 'button')):
                    continue
                for pat, _ in PATTERNS:
                    m = pat.match(v)
                    if m:
                        if pat.pattern.startswith('^(.+)') and not in_skip(el):
                            units.append(dict(kind='attr', key=norm(m[1]), ctx=f'{a} on <{el.name}>'))
                        break
                else:
                    if not in_skip(el):
                        units.append(dict(kind='attr', key=norm(v), ctx=f'{a} on <{el.name}>'))
        href = el.get('href') if el.name == 'a' else None
        if href and '?' in href:
            for k, v in parse_qsl(href.split('?', 1)[1].split('#')[0]):
                if k in ('item', 'topic') and has_cjk(v):
                    units.append(dict(kind='attr', key=norm(v), ctx='contact-form prefill (item = product name, topic = option value)'))
    t = soup.title.string if soup.title else ''
    if t and has_cjk(t) and not fn.startswith('news-detail'):
        t = t.replace(TITLE_SUFFIX, '')
        units.append(dict(kind='attr', key=norm(t), ctx='<title> (page title, " | Yuan Hua Oil" is appended)'))
    for m in soup.find_all('meta'):
        if m.get('name') in ('description',) or (m.get('property') or '').startswith('og:'):
            v = m.get('content', '')
            if has_cjk(v) and not fn.startswith('news-detail'):
                units.append(dict(kind='attr', key=norm(v), ctx='<meta name=description>'))
    return units


def site_pages(site):
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(site, '*.html')))


def cmd_extract(site, table_path, out):
    table = json.load(open(table_path)) if os.path.exists(table_path) else {}
    agg = {}
    for fn in site_pages(site):
        soup = load(os.path.join(site, fn))
        mark_skips(soup, fn)
        for u in page_units(soup, fn):
            if u['key'] in table:
                continue
            a = agg.setdefault(u['key'], dict(key=u['key'], kind=u['kind'], ctx=u['ctx'], tags=u.get('tags', ''), pages=[]))
            if fn not in a['pages']:
                a['pages'].append(fn)
    units = sorted(agg.values(), key=lambda u: (u['pages'][0], u['key']))
    for i, u in enumerate(units):
        u['id'] = f'u{i:04d}'
    json.dump(units, open(out, 'w'), ensure_ascii=False, indent=1)
    chars = sum(len(u['key']) for u in units)
    print(f'{len(units)} missing units, {chars} chars -> {out}')


# ---------------------------------------------------------------- build
ASSET_RE = re.compile(r'^(?![a-z][a-z0-9+.-]*:|//|#|/)')


def rel_en(url, pages):
    """Rewrite a URL from a Chinese page so it works from en/<page>."""
    if not url or not ASSET_RE.match(url):
        return url
    path = url.split('#')[0].split('?')[0]
    if path == '' or path in pages:        # page links stay inside en/
        return url
    return '../' + url


def cmd_build(site, table_path):
    table = json.load(open(table_path))
    pages = set(site_pages(site))
    out_dir = os.path.join(site, 'en')
    os.makedirs(out_dir, exist_ok=True)
    missing, bad = {}, {}

    def tr(key, fn, ctx=None):
        # "option|其他" style entries override the plain key where one Chinese word needs two English ones
        if ctx and f'{ctx}|{key}' in table:
            return table[f'{ctx}|{key}']
        if key in table:
            return table[key]
        missing.setdefault(key, set()).add(fn)
        return None

    for fn in sorted(pages):
        svgs = []
        soup = load(os.path.join(site, fn), svgs)
        mark_skips(soup, fn)

        def t_text(v, ctx=None):
            # plain-text contexts (attributes, <title>, URLs): table values written for HTML may carry entities
            en = tr(norm(v), fn, ctx)
            return html.unescape(en) if en is not None else v

        # text runs
        found = []
        walk(soup.body, found)
        for parent, nodes in found:
            key, tags, lead, trail = mask(nodes)
            en = tr(key, fn, parent.name)
            if en is None:
                continue
            try:
                h = unmask(en, tags)
            except ValueError as e:
                bad[key] = f'{e} :: {en}'
                continue
            frag = BeautifulSoup(lead + h + trail, 'html.parser')
            anchor = nodes[0]
            for n in list(frag.contents):
                anchor.insert_before(n)
            for n in nodes:
                n.extract()
        # attributes
        for el in soup.find_all(True):
            if el.name in NO_ATTR:
                continue
            for a in ATTRS:
                v = el.get(a)
                if not (isinstance(v, str) and has_cjk(v)):
                    continue
                if a == 'value' and el.name != 'option' and not (el.name == 'input' and el.get('type') in ('submit', 'button')):
                    continue
                skip = in_skip(el)
                for pat, fx in PATTERNS:
                    m = pat.match(v)
                    if m:
                        el[a] = fx(m, (lambda s: s) if skip else (lambda s: t_text(s)))
                        break
                else:
                    if not skip:
                        el[a] = t_text(v, el.name)
            if el.name == 'a' and '?' in el.get('href', '') and has_cjk(unquote(el['href'])):
                base, rest = el['href'].split('?', 1)
                q, _, frag = rest.partition('#')
                q = [(k, t_text(v, 'option' if k == 'topic' else None) if k in ('item', 'topic') and has_cjk(v) else v) for k, v in parse_qsl(q)]
                el['href'] = f'{base}?{urlencode(q, quote_via=quote)}' + (f'#{frag}' if frag else '')
        # head
        if soup.title and soup.title.string and has_cjk(soup.title.string) and not fn.startswith('news-detail'):
            t = soup.title.string
            if t.endswith(TITLE_SUFFIX):
                soup.title.string = t_text(t[:-len(TITLE_SUFFIX)]) + EN_TITLE_SUFFIX
            else:
                soup.title.string = t_text(t)
        elif soup.title and soup.title.string:
            soup.title.string = soup.title.string.replace(TITLE_SUFFIX, EN_TITLE_SUFFIX)
        for m in soup.find_all('meta'):
            if (m.get('name') == 'description' or (m.get('property') or '').startswith('og:')) and has_cjk(m.get('content', '')) and not fn.startswith('news-detail'):
                m['content'] = t_text(m['content'])
        soup.html['lang'] = 'en'
        # relative URLs: assets one level up, pages stay in en/
        for el in soup.find_all(True):
            for a in ('href', 'src', 'poster', 'data-full', 'data-src'):
                if el.has_attr(a) and not (a == 'href' and el.name == 'a' and el.get('hreflang')):
                    el[a] = rel_en(el[a], pages)
            if el.has_attr('srcset'):
                el['srcset'] = ', '.join(' '.join([rel_en(p.split()[0], pages)] + p.split()[1:]) for p in el['srcset'].split(','))
            if el.has_attr('style') and 'url(' in el['style']:
                el['style'] = re.sub(r'url\((["\']?)([^)"\']+)\1\)', lambda m: f'url({m[1]}{rel_en(m[2], pages)}{m[1]})', el['style'])
            if el.name == 'iframe' and 'maps.google.com' in el.get('src', ''):
                el['src'] += '&hl=en'
        # language switch + alternates point back to the Chinese page
        for sw in soup.select('.lang-sw a'):
            if sw.get('hreflang') == 'en':
                sw['href'] = fn
                sw['aria-current'] = 'true'
            else:
                sw['href'] = '../' + fn
                if sw.has_attr('aria-current'):
                    del sw['aria-current']
        for ln in soup.select('link[rel=alternate][hreflang]'):
            ln['href'] = ('../' if ln['hreflang'] != 'en' else '') + fn
        for s in soup.find_all('script'):
            if s.string:
                txt = s.string
                for zh, en in SCRIPT_STRINGS.items():
                    txt = txt.replace(zh, en)
                if txt != s.string:
                    s.string.replace_with(txt)
        for t in soup.find_all(string=lambda x: '\u3000' in x):   # stray ideographic spaces (old-site copy)
            if t.parent.name not in ('script', 'style') and not in_skip(t.parent):
                t.replace_with(t.replace('\u3000', ' '))
        for el in soup.find_all(attrs={SKIP_ATTR: True}):
            del el[SKIP_ATTR]
            el['lang'] = 'zh-Hant'
        for el in soup.select('[translate=no]'):
            if not el.has_attr('lang') and 'lang-sw' not in el.get('class', []) and has_cjk(el.get_text()):
                el['lang'] = 'zh-Hant'
        # news is not translated yet: say so where the Chinese starts
        note = None
        if fn == 'news.html':
            note, where = NEWS_NOTE, soup.select_one('.sec.first .sec-head')
        elif fn.startswith('news-detail'):
            note, where = ARTICLE_NOTE, soup.select_one('.article .meta')
        if note and where:
            p = soup.new_tag('p', attrs={'class': 'lang-note'})
            p.string = note
            if fn == 'news.html':
                where.insert_after(p)
            else:
                where.insert_before(p)
        out = soup.decode(formatter=FMT)
        out = re.sub(r'<x-svg data-n="(\d+)"></x-svg>', lambda m: svgs[int(m[1])], out)
        out = re.sub(r'^<!DOCTYPE html>\s*', '<!doctype html>\n', out)
        open(os.path.join(out_dir, fn), 'w', encoding='utf-8').write(out)

    print(f'built {len(pages)} pages -> {out_dir}')
    if missing:
        print(f'MISSING {len(missing)} units')
        for k, v in list(missing.items())[:40]:
            print('  ', k[:90], '|', ','.join(sorted(v))[:60])
    if bad:
        print(f'BAD {len(bad)} units')
        for k, v in list(bad.items())[:40]:
            print('  ', k[:70], '=>', v[:120])
    return 0 if not missing and not bad else 1


if __name__ == '__main__':
    cmd, site, table = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == 'extract':
        cmd_extract(site, table, sys.argv[4])
    else:
        sys.exit(cmd_build(site, table))
