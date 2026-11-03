"""Make the white backdrop of the old drum product shots transparent (flood fill from the border)."""
import sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
for p in sys.argv[1:]:
    im = Image.open(p).convert('RGBA')
    w, h = im.size
    rgb = im.convert('RGB')
    mask = Image.new('L', (w, h), 0)
    # flood fill on a copy, marking near-white pixels reachable from the edges
    work = rgb.copy()
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (0, h // 2), (w - 1, h // 2)]:
        if sum(work.getpixel((x, y))) > 700:
            ImageDraw.floodfill(work, (x, y), (255, 0, 255), thresh=38)
    a = np.array(work)
    bg = (a[:, :, 0] == 255) & (a[:, :, 1] == 0) & (a[:, :, 2] == 255)
    alpha = np.array(im)[:, :, 3].copy()
    alpha[bg] = 0
    al = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))
    im.putalpha(al)
    bbox = im.getbbox()
    im = im.crop(bbox)
    im.save(p, optimize=True)
    print(p, (w, h), '->', im.size, 'transparent %.0f%%' % (bg.mean() * 100))
