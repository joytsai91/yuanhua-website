"""Helpers for the translation hand-off.

  python -I i18n_tools.py chunk <units.json> <chunk_dir>         # split units into translation batches
  python -I i18n_tools.py check <chunk.json> <out.json>          # validate one translated batch
  python -I i18n_tools.py merge <chunk_dir> <out_dir> <en.json>  # merge batches into the translation table
"""
import sys, os, re, json, glob

BAD = re.compile(r'[　-〿゠-ヿ㐀-鿿豈-﫿＀-￯]')
GROUPS = [  # (batch name, page-name prefixes) in hand-off order
    ('home', ['index.html']),
    ('about', ['about.html', 'milestone.html', 'team.html']),
    ('products', ['products.html', 'yushiro-plant', 'yushiro.html', 'battor.html', 'formosa.html']),
    ('yushiro', ['yushiro-']),
    ('battor', ['battor-']),
    ('formosa', ['formosa-']),
    ('equipment', ['equipment.html', 'eq-', 'license.html']),
    ('faq', ['faq.html', 'knowledge', 'oil-table.html', 'water-knowledge.html']),
    ('gallery', ['gallery.html', 'album-']),
    ('contact', ['contact.html', 'news']),
]
LIMIT = 3200


def group_of(page):
    for i, (_, prefixes) in enumerate(GROUPS):
        if any(page == p or (p.endswith('-') and page.startswith(p)) or (not p.endswith('.html') and page.startswith(p)) for p in prefixes):
            return i
    return len(GROUPS)


def cmd_chunk(units_path, chunk_dir):
    units = json.load(open(units_path))
    shared = [u for u in units if len(u['pages']) >= 4]
    rest = [u for u in units if len(u['pages']) < 4]
    batches = [('shared', shared)]
    by = {}
    for u in rest:
        by.setdefault(group_of(u['pages'][0]), []).append(u)
    for gi in sorted(by):
        name = GROUPS[gi][0] if gi < len(GROUPS) else 'misc'
        parts, cur, size = [], [], 0
        for u in by[gi]:
            if cur and size + len(u['key']) > LIMIT:
                parts.append(cur); cur, size = [], 0
            cur.append(u); size += len(u['key'])
        if cur:
            if parts and size < 1200:   # a short tail rides along with the previous batch
                parts[-1] += cur
            else:
                parts.append(cur)
        for k, part in enumerate(parts, 1):
            batches.append((f'{name}-{k}' if len(parts) > 1 else name, part))
    for f in glob.glob(os.path.join(chunk_dir, '*.json')):
        os.remove(f)
    for i, (name, us) in enumerate(batches):
        fn = os.path.join(chunk_dir, f'c{i:02d}-{name}.json')
        json.dump(us, open(fn, 'w'), ensure_ascii=False, indent=1)
        print(f'{os.path.basename(fn)}: {len(us)} units, {sum(len(u["key"]) for u in us)} chars')


TAG = re.compile(r'<(/?)(\d+)(/?)>')


def tag_problems(zh, en):
    want = sorted((m[2], bool(m[3])) for m in TAG.finditer(zh) if not m[1])
    got = sorted((m[2], bool(m[3])) for m in TAG.finditer(en) if not m[1])
    if want != got:
        return f'numbered tags differ: source {[w[0] + ("/" if w[1] else "") for w in want]} vs translation {[g[0] + ("/" if g[1] else "") for g in got]}'
    stack = []
    for m in TAG.finditer(en):
        if m[3]:
            continue
        if not m[1]:
            stack.append(m[2])
        elif not stack or stack.pop() != m[2]:
            return 'numbered tags are not properly nested/closed'
    if stack:
        return 'numbered tags left open'
    rest = TAG.sub('', en)
    rest = re.sub(r'<(br|wbr)\s*/?>', '', rest)
    if '<' in rest or '>' in rest:
        return 'stray "<" or ">" (escape as &lt; &gt;; only numbered tags and <br> are allowed)'
    return None


def cmd_check(chunk_path, out_path):
    units = json.load(open(chunk_path))
    try:
        out = json.load(open(out_path))
    except Exception as e:
        print(f'FAIL cannot read {out_path}: {e}'); return 1
    errs, warns = [], []
    ids = {u['id'] for u in units}
    for u in units:
        en = out.get(u['id'])
        if not isinstance(en, str) or not en.strip():
            errs.append(f'{u["id"]}: missing'); continue
        if BAD.search(en):
            errs.append(f'{u["id"]}: contains CJK/full-width characters: {"".join(sorted(set(BAD.findall(en))))}')
        if u['kind'] == 'html':
            p = tag_problems(u['key'], en)
            if p:
                errs.append(f'{u["id"]}: {p}')
        elif TAG.search(en) or '<' in en:
            errs.append(f'{u["id"]}: attribute/plain-text unit must not contain tags')
        nums = set(re.findall(r'\d+(?:\.\d+)?', TAG.sub('', u['key'])))
        miss = [n for n in nums if n not in en]
        if miss:
            warns.append(f'{u["id"]}: numbers not found in translation: {miss}')
        for a in '→←↓':
            if u['key'].count(a) != en.count(a):
                warns.append(f'{u["id"]}: arrow {a} count differs')
        zh_len = len(re.sub(r'<[^>]+>', '', u['key']))
        if zh_len >= 25 and len(re.sub(r'<[^>]+>', '', en)) < zh_len:
            warns.append(f'{u["id"]}: translation looks short for the source (possible omission)')
    extra = set(out) - ids
    if extra:
        errs.append(f'unknown ids: {sorted(extra)[:10]}')
    for e in errs:
        print('ERROR', e)
    for w in warns:
        print('WARN ', w)
    print(f'{"FAIL" if errs else "PASS"}: {len(units)} units, {len(errs)} errors, {len(warns)} warnings')
    return 1 if errs else 0


def cmd_merge(chunk_dir, out_dir, table_path):
    table = json.load(open(table_path)) if os.path.exists(table_path) else {}
    n = 0
    for cp in sorted(glob.glob(os.path.join(chunk_dir, '*.json'))):
        op = os.path.join(out_dir, os.path.basename(cp))
        if not os.path.exists(op):
            print('no output for', os.path.basename(cp)); continue
        out = json.load(open(op))
        for u in json.load(open(cp)):
            if u['id'] in out:
                table[u['key']] = out[u['id']]; n += 1
    json.dump(table, open(table_path, 'w'), ensure_ascii=False, indent=1, sort_keys=True)
    print(f'merged {n} -> {table_path} ({len(table)} entries)')


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'chunk':
        cmd_chunk(*sys.argv[2:4])
    elif c == 'check':
        sys.exit(cmd_check(*sys.argv[2:4]))
    elif c == 'merge':
        cmd_merge(*sys.argv[2:5])
