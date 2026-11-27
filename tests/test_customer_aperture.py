import copy,json,subprocess
from pathlib import Path
import pytest
from backend.customer_aperture import aperture,translate,derive,validate_binding,frame_hashes

def fixture():
    box={"x":800,"y":342,"width":2240,"height":1476}
    m={"capture_rect":{"width":3840,"height":2160},"duration":.1,"cursorless":True,
       "events":[{"targetRect":{"x":1500,"y":650,"width":160,"height":68},
                  "resultRect":{"x":820,"y":836,"width":2208,"height":966}}],
       "pointer_samples":[{"x":960,"y":432,"t":.01},{"x":1580,"y":680,"t":.05}]}
    return box,m

def test_aperture_fits_native_product_and_every_point():
    r,m=fixture();a=aperture([r,r],m)
    assert a and a[2]<3200 and a[3]>=1080 and a[2]*9==a[3]*16
    d=translate(m,a)
    assert d["events"][0]["targetRect"]["x"]+a[0]==m["events"][0]["targetRect"]["x"]
    assert d["pointer_samples"][1]["x"]+a[0]==m["pointer_samples"][1]["x"]
    assert m["capture_rect"]["width"]==3840
    assert aperture([r,{**r,"y":r["y"]+12}],m) is None
    far=copy.deepcopy(m);far["pointer_samples"].append({"x":3830,"y":50,"t":.09})
    assert aperture([r,r],far) is None
    with pytest.raises(ValueError):translate(m,[1200,400,1920,1080])

def test_real_lossless_native_crop_hash_binding(tmp_path):
    r,m=fixture();src=tmp_path/"source.mp4";mf=tmp_path/"manifest.json"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","testsrc2=size=3840x2160:rate=60",
                    "-frames:v","6","-c:v","libx264","-preset","ultrafast","-threads","2","-pix_fmt","yuv420p",str(src)],check=True)
    mf.write_text(json.dumps(m))
    cropped,manifest=derive(src,mf,[r,r]);assert cropped!=src
    validate_binding(cropped,manifest)
    d=json.loads(manifest.read_text());assert d["nativeCrop"]["frames"]==6
    assert d["nativeCrop"]["originalSourceSha256"]
    d["pointer_samples"][0]["x"]+=1;manifest.write_text(json.dumps(d))
    with pytest.raises(ValueError,match="geometry"):validate_binding(cropped,manifest)

def test_state_dependent_action_needs_predecessor():
    from backend.customer_story import validated_selection
    a={"id":"a","kind":"option","group":"one","label":"First"}
    b={"id":"b","kind":"option","group":"two","label":"Second","requires":"a"}
    c={"id":"c","kind":"option","group":"three","label":"Other"}
    rows=[a,b,c]
    def select(ids):return validated_selection(json.dumps({"ids":ids,"hero_action_id":"b","story":"Connected proof"}),rows)
    assert select(["a","b"])
    assert select(["b","a"]) is None
    assert select(["c","b"]) is None
    assert select(["a","c","b"]) is None
