"""A restrained floating screen stage for source-true Sauce captures.

The UI is still the exact decoded browser frame; this module only supplies an
external neutral matte, a proper ambient shadow and clipped screen geometry.
"""
from functools import lru_cache
import cv2
import numpy as np


@lru_cache(maxsize=4)
def matte(width:int,height:int)->np.ndarray:
    yy,xx=np.mgrid[0:height,0:width].astype(np.float32)
    x=(xx-width*.5)/(width*.5)
    y=(yy-height*.44)/(height*.5)
    light=np.exp(-(x*x*.8+y*y*1.15))*12
    edge=np.clip(1-(x*x*.23+y*y*.24),.6,1.)
    bg=np.empty((height,width,3),np.float32)
    for ch,base in enumerate((39.,39.,42.)):  # BGR neutral blue-charcoal
        bg[:,:,ch]=(base+light)*edge
    grain=np.random.default_rng(903).normal(0,.42,(height,width,1))
    return np.uint8(np.clip(bg+grain,0,255))


def floating_matrix(original:np.ndarray,size:tuple[int,int],
                    framing:float=.79)->np.ndarray:
    if not .62 <= framing <= .96:raise ValueError("Unbounded floating scale")
    width,height=size
    m=original.copy()
    m[:,:2]*=framing
    m[:,2]=framing*m[:,2]+(1-framing)*np.array([width*.5,height*.5])
    return m


def rounded_coverage(matrix:np.ndarray,source_size:tuple[int,int],
                     output_size:tuple[int,int],radius_source:float=24)->np.ndarray:
    sw,sh=source_size;ow,oh=output_size
    x0=int(round(matrix[0,2]));y0=int(round(matrix[1,2]))
    x1=int(round(matrix[0,0]*sw+matrix[0,2]))
    y1=int(round(matrix[1,1]*sh+matrix[1,2]))
    r=max(4,int(round(radius_source*matrix[0,0])))
    r=min(r,max(1,(x1-x0)//3),max(1,(y1-y0)//3))
    mask=np.zeros((oh,ow),np.uint8)
    if x1<=x0 or y1<=y0:return mask
    # Real rounded window silhouette. Avoid floating browser chrome.
    cv2.rectangle(mask,(x0+r,y0),(x1-r,y1),255,-1)
    cv2.rectangle(mask,(x0,y0+r),(x1,y1-r),255,-1)
    for x in (x0+r,x1-r):
        for y in (y0+r,y1-r):
            cv2.circle(mask,(x,y),r,255,-1,lineType=cv2.LINE_AA)
    return mask


def composite_stage(warped:np.ndarray,matrix:np.ndarray,
                    source_size:tuple[int,int])->np.ndarray:
    oh,ow=warped.shape[:2]
    mask=rounded_coverage(matrix,source_size,(ow,oh))
    backdrop=matte(ow,oh).copy()
    # Soft occlusion shadow belongs OUTSIDE the screen, not over its real text.
    shadow=cv2.GaussianBlur(mask,(0,0),23).astype(np.float32)/255
    exterior=(1-mask.astype(np.float32)/255)
    shade=1.-.28*shadow*exterior
    backdrop=np.uint8(backdrop.astype(np.float32)*shade[:,:,None])
    # 1-pixel native-edge antialiasing; don't blur recorded source pixels.
    alpha=cv2.GaussianBlur(mask,(3,3),.62).astype(np.float32)[:,:,None]/255
    output=np.uint8(np.clip(backdrop*(1-alpha)+warped*alpha,0,255))
    return output
