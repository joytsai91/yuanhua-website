import base64, pathlib, re
src = pathlib.Path('yuanhua.src.html').read_text()
M = {
 'hero':'opt/hero.jpg', 'about':'opt/about.jpg', 'wave':'opt/oilwave.jpg',
 'c1':'opt/c1.jpg', 'c2':'opt/c2.jpg', 'c3':'opt/c3.jpg', 'c4':'opt/c4.jpg',
 'cnc':'opt/cnc.jpg',
 'p1':'opt/sterling-logo3.png', 'p2':'opt/sterling-logo2.png', 'p3':'opt/sterling-logo.png',
}
for k,f in M.items():
    b = pathlib.Path(f).read_bytes()
    mime = 'image/png' if f.endswith('.png') else 'image/jpeg'
    src = src.replace('__IMG_%s__'%k, 'data:%s;base64,%s'%(mime, base64.b64encode(b).decode()))
left = re.findall(r'__IMG_\w+__', src)
assert not left, left
pathlib.Path('yuanhua.html').write_text(src)
print('built', round(len(src)/1024/1024,2), 'MB')
