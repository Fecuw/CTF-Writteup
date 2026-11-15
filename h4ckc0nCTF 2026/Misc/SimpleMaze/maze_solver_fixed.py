#!/usr/bin/env python3
import argparse
from collections import deque
from PIL import Image, ImageDraw

p = argparse.ArgumentParser()
p.add_argument('image')
p.add_argument('-s','--start',nargs=2,type=int,required=True,metavar=('X','Y'))
p.add_argument('-g','--goal',nargs=2,type=int,required=True,metavar=('X','Y'))
p.add_argument('-o','--output',default='solve_fixed.png')
p.add_argument('--threshold',type=int,default=180)
p.add_argument('--bounds',nargs=4,type=int,metavar=('LEFT','TOP','RIGHT','BOTTOM'),help='Restrict search to maze interior')
a=p.parse_args()
im=Image.open(a.image).convert('RGB')
w,h=im.size
pix=im.convert('L').load()
left,top,right,bottom=a.bounds if a.bounds else (0,0,w-1,h-1)
left=max(0,left);top=max(0,top);right=min(w-1,right);bottom=min(h-1,bottom)
start=tuple(a.start);goal=tuple(a.goal)

def allowed(x,y):
    return left<=x<=right and top<=y<=bottom and pix[x,y]>=a.threshold

for label,(x,y) in [('start',start),('goal',goal)]:
    if not (0<=x<w and 0<=y<h):p.error(f'{label} outside image: {(x,y)}; size={w}x{h}')
    if not allowed(x,y):p.error(f'{label} is a wall or outside bounds: {(x,y)}; grayscale={pix[x,y]}')

prev={start:None}
queue=deque([start])
while queue:
    x,y=queue.popleft()
    if (x,y)==goal:break
    for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if (nx,ny) not in prev and allowed(nx,ny):
            prev[(nx,ny)]=(x,y)
            queue.append((nx,ny))
if goal not in prev:
    raise SystemExit(f'No route within bounds {left,top,right,bottom}. Check start/goal, threshold and bounds.')
path=[]
p=goal
while p is not None:
    path.append(p);p=prev[p]
path.reverse()
d=ImageDraw.Draw(im)
d.line(path,fill=(255,0,0),width=2)
d.ellipse((start[0]-3,start[1]-3,start[0]+3,start[1]+3),fill=(0,180,0))
d.ellipse((goal[0]-3,goal[1]-3,goal[0]+3,goal[1]+3),fill=(0,0,255))
im.save(a.output)
print(f'Path found: {len(path)} pixels; saved {a.output}')
