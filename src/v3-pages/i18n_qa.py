"""QA for the English pages: leftover Chinese, broken relative links/anchors.

Usage: python -I i18n_qa.py <site_dir>
"""
import sys, os, re, glob
from urllib.parse import unquote
from bs4 import BeautifulSoup, NavigableString, Comment

CJK = re.compile(r'[　-〿゠-ヿ㐀-鿿豈-﫿＀-￯]')
ATTRS = ['alt', 'aria-label', 'title', 'placeholder', 'content', 'value', 'data-alt']
site = sys.argv[1]
en = os.path.join(site, 'en')
ids = {}


def zh_ok(el):
    for p in [el] + list(el.parents):
        if getattr(p, 'attrs', None) is None:
            continue
        if p.get('lang', '').startswith('zh') or p.get('translate') == 'no':
            return True
    return False


left, links = [], []
pages = sorted(glob.glob(os.path.join(en, '*.html')))
soups = {}
for path in pages:
    soups[path] = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    ids[path] = {e['id'] for e in soups[path].find_all(id=True)}
for path in pages:
    fn = os.path.basename(path)
    soup = soups[path]
    for s in soup.find_all(string=True):
        if isinstance(s, Comment) or s.parent.name in ('script', 'style'):
            continue
        if fn.startswith('news-detail') and s.parent.name == 'title':
            continue   # news titles stay in Chinese
        if CJK.search(s) and not zh_ok(s.parent):
            left.append(f'{fn}: text "{s.strip()[:60]}"')
    for el in soup.find_all(True):
        for a in ATTRS:
            v = el.get(a)
            if fn.startswith('news-detail') and el.name == 'meta':
                continue
            if isinstance(v, str) and CJK.search(v) and not zh_ok(el):
                left.append(f'{fn}: {a} on <{el.name}> "{v[:60]}"')
        for a in ('href', 'src', 'data-full'):
            u = el.get(a)
            if not u or re.match(r'^([a-z][a-z0-9+.-]*:|//)', u):
                continue
            base, _, frag = u.partition('#')
            base = base.split('?')[0]
            target = os.path.normpath(os.path.join(en, unquote(base))) if base else path
            if not os.path.exists(target):
                links.append(f'{fn}: {a}="{u}" -> missing {os.path.relpath(target, site)}')
            elif frag and target.endswith('.html'):
                tid = ids.get(target)
                if tid is None:
                    tid = {e['id'] for e in BeautifulSoup(open(target, encoding='utf-8').read(), 'html.parser').find_all(id=True)}
                    ids[target] = tid
                if frag not in tid and not re.match(r'^(nexustest|expo|launch|other|press|events|video|all)$', frag):
                    links.append(f'{fn}: {a}="{u}" -> no #{frag}')
print(f'{len(pages)} English pages checked')
print(f'leftover Chinese outside zh regions: {len(left)}')
for x in left[:80]:
    print('  ', x)
print(f'broken links: {len(links)}')
for x in links[:60]:
    print('  ', x)
sys.exit(1 if left or links else 0)
