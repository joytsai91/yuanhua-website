import base64, pathlib, re
src = pathlib.Path('v3.src.html').read_text()
M = {'logo':'opt3/logo.png','heroworker':'opt3/hero-worker.jpg','policy':'opt3/policy.jpg','teamwide':'opt3/team-wide.jpg','team':'opt3/team.jpg','booth':'opt3/booth.jpg',
     'posters':'opt3/posters.jpg','c1':'opt3/c1.jpg','c2':'opt3/c2.jpg','c4':'opt3/c4.jpg','cnc':'opt3/cnc.jpg',
     'p1':'opt3/sterling-logo3.png','p2':'opt3/sterling-logo2.png','p3':'opt3/sterling-logo.png'}
for k,f in M.items():
    b=pathlib.Path(f).read_bytes()
    mime='image/png' if f.endswith('.png') else 'image/jpeg'
    src=src.replace('__IMG_%s__'%k,'data:%s;base64,%s'%(mime,base64.b64encode(b).decode()))
left=re.findall(r'__IMG_\w+__',src); assert not left, left
pathlib.Path('v3.html').write_text(src)
print('built', round(len(src)/1024/1024,2),'MB')
