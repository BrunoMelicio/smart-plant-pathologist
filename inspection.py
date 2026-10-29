"""Deterministic image measurements, deliberately separate from model claims."""
from collections import deque
from PIL import Image, ImageOps


def measure_image(image):
    thumb = image.copy().convert('RGB')
    thumb.thumbnail((256, 256))
    w, h = thumb.size
    hsv_image = thumb.convert('HSV')
    hsv = list(hsv_image.get_flattened_data() if hasattr(hsv_image, 'get_flattened_data') else hsv_image.getdata())
    # Hue/saturation thresholds locate COLOR CANDIDATES, not confirmed lesions.
    yellow = [20 <= H <= 49 and S > 65 and V > 85 for H, S, V in hsv]
    brown = [5 <= H <= 33 and S > 65 and 25 < V < 150 for H, S, V in hsv]
    masks = [('Yellow / pale areas', yellow), ('Brown / dark areas', brown)]
    regions = []
    for label, mask in masks:
        seen = set()
        components = []
        for idx, active in enumerate(mask):
            if not active or idx in seen:
                continue
            seen.add(idx)
            todo = deque([idx]); points = []
            while todo:
                cur = todo.popleft(); points.append(cur)
                x, y = cur % w, cur // w
                for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    nxt = ny*w+nx
                    if 0 <= nx < w and 0 <= ny < h and nxt not in seen and mask[nxt]:
                        seen.add(nxt); todo.append(nxt)
            if len(points) >= max(18, w*h*.001):
                components.append(points)
        for pts in sorted(components, key=len, reverse=True)[:3]:
            xs = [p % w for p in pts]; ys = [p // w for p in pts]
            regions.append(dict(label=label, x=min(xs)/w, y=min(ys)/h,
                                width=(max(xs)-min(xs)+1)/w, height=(max(ys)-min(ys)+1)/h,
                                coverage=round(100*len(pts)/(w*h), 2)))
    regions = sorted(regions, key=lambda r:r['coverage'], reverse=True)[:5]
    return dict(regions=regions, metrics=[dict(label=label, coverage=round(100*sum(mask)/(w*h), 1)) for label,mask in masks],
                method='HSV color thresholding on a resized image. Coverage is a percentage of the entire photo, including background; boxes are color candidates, not disease detections.',
                analysis_resolution=[w,h])
