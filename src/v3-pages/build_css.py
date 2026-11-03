import re, sys
src, sub, out = sys.argv[1:4]
h = open(src, encoding='utf-8').read()
css = h[h.index('<style>\n:root') + 8:h.index('</style>\n</head>')]
parts = re.split(r'(?m)^(?=/\* ---------- )', css)
keep = [p for p in parts if not re.match(r'/\* ---------- (loader|hero) ', p)]
banner = '/* 圓華油品 C 版：內頁共用樣式（共用區塊取自 index.html，內頁元件在後段） */\n'
open(out, 'w', encoding='utf-8').write(banner + ''.join(keep) + open(sub, encoding='utf-8').read())
print(len(css), '->', sum(len(p) for p in keep), 'kept blocks:', [re.match(r'/\* ---------- ([^ ]+)', p).group(1) if p.startswith('/*') else 'root' for p in keep])
