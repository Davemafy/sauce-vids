"""Loopback-only authenticated Sauce URL-to-video API.

POST /v1/inspect {"url": "..."} -> grounded public site scan (no AI key)
POST /v1/jobs {"url": "..."} -> one-call direction + capture + render
GET  /v1/jobs/{id} -> stage, outcome, review requirement
GET  /v1/jobs/{id}/preview.mp4 -> private, authenticated preview
POST /v1/jobs/{id}/feedback {"rating":1..5,"notes":"..."} -> review ledger
GET /health -> readiness; no secrets or raw browser recordings.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import hmac,json,os,re,secrets,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from .url2video import execute,inspect_url,validate_public_url,NeedsKey,NeedsAccess

HOST="127.0.0.1"
PORT=int(os.getenv("SAUCE_API_PORT","8767"))
OUT=Path(os.getenv("SAUCE_JOBS_DIR","/var/lib/sauce-url2video/jobs"))
TOKEN=os.getenv("SAUCE_API_TOKEN","")
if len(TOKEN)<32:
    raise RuntimeError("SAUCE_API_TOKEN is required (32+ characters)")
OUT.mkdir(parents=True,exist_ok=True)
os.chmod(OUT,0o700)
POOL=ThreadPoolExecutor(max_workers=1)
LOCK=threading.Lock()
JOBS={}

def save(job_id):
    j=JOBS[job_id]
    folder=OUT/job_id
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"status.json").write_text(json.dumps(j,indent=2))

def worker(job_id):
    folder=OUT/job_id
    def stage(value):
        with LOCK:
            JOBS[job_id]["stage"]=value
            JOBS[job_id]["updated_at"]=time.time()
            save(job_id)
    try:
        result=execute(JOBS[job_id]["url"],folder,progress=stage)
        with LOCK:
            JOBS[job_id].update(result)
            JOBS[job_id]["updated_at"]=time.time()
            save(job_id)
    except NeedsKey:
        with LOCK:
            JOBS[job_id].update(status="needs_key",stage="needs_key",
                                error="Configure GEMINI_API_KEY server-side")
            save(job_id)
    except NeedsAccess as err:
        with LOCK:
            JOBS[job_id].update(status="needs_access",stage="needs_access",error=str(err)[:250])
            save(job_id)
    except Exception as err:
        # Avoid returning provider payload or private page data in HTTP errors.
        category=type(err).__name__
        with LOCK:
            JOBS[job_id].update(status="failed",stage="failed",error=category)
            save(job_id)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        return # no bearer tokens, URLs, personal traces or HAR in access logs
    def send_json(self,code,data):
        body=json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def authorized(self):
        supplied=self.headers.get("Authorization","")
        return hmac.compare_digest(supplied,"Bearer "+TOKEN)
    def require_auth(self):
        if not self.authorized():
            self.send_json(401,{"error":"Unauthorized"})
            return False
        return True
    def body(self):
        size=int(self.headers.get("Content-Length","0"))
        if not 0<size<=4096: raise ValueError("Invalid request size")
        value=json.loads(self.rfile.read(size))
        if not isinstance(value,dict): raise ValueError("JSON object required")
        return value
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/health":
            return self.send_json(200,{"service":"Sauce URL-to-video",
                "status":"ready","director_key_configured":bool(os.getenv("GEMINI_API_KEY")),
                "one_ai_call":True,"export_requires_review":True})
        if not self.require_auth(): return
        match=re.fullmatch(r"/v1/jobs/([a-f0-9]{24})(/preview\.mp4)?",path)
        if not match: return self.send_json(404,{"error":"Not found"})
        job_id,video=match.group(1),match.group(2)
        with LOCK: job=JOBS.get(job_id)
        if job is None:
            path=OUT/job_id/"status.json"
            if path.exists(): job=json.loads(path.read_text())
        if job is None: return self.send_json(404,{"error":"Job unknown"})
        if not video:
            return self.send_json(200,job)
        video_path=OUT/job_id/"export"/"preview.mp4"
        if job.get("status")!="needs_review" or not video_path.is_file():
            return self.send_json(404,{"error":"Preview unavailable"})
        self.send_response(200)
        self.send_header("Content-Type","video/mp4")
        self.send_header("Cache-Control","private, no-store")
        self.send_header("Content-Length",str(video_path.stat().st_size))
        self.end_headers()
        with video_path.open("rb") as src:
            while True:
                block=src.read(1024*1024)
                if not block: break
                self.wfile.write(block)
    def do_POST(self):
        if not self.require_auth(): return
        path=urlsplit(self.path).path
        try: body=self.body()
        except (ValueError,UnicodeError):
            return self.send_json(400,{"error":"Malformed request"})
        if path=="/v1/inspect":
            try:
                url=validate_public_url(body.get("url",""))
                folder=OUT/("inspect-"+secrets.token_hex(12))
                report=inspect_url(url,folder/"private")
                return self.send_json(200,{"title":report["title"],
                    "heading":report["heading"],"actions":report["actions"],
                    "scrollHeight":report["scrollHeight"]})
            except Exception as exc:
                return self.send_json(422,{"error":type(exc).__name__})
        if path=="/v1/jobs":
            if not os.getenv("GEMINI_API_KEY"):
                return self.send_json(412,{"error":"GEMINI_API_KEY not configured; /v1/inspect remains available"})
            try: url=validate_public_url(body.get("url",""))
            except ValueError as exc: return self.send_json(422,{"error":str(exc)})
            with LOCK:
                if sum(x.get("status")=="queued" or x.get("stage") in
                       ("inspecting","directing","capturing","rendering")
                       for x in JOBS.values())>=2:
                    return self.send_json(429,{"error":"Sauce queue full"})
                job_id=secrets.token_hex(12)
                JOBS[job_id]={"id":job_id,"url":url,"stage":"queued",
                              "status":"queued","created_at":time.time()}
                save(job_id)
                POOL.submit(worker,job_id)
            return self.send_json(202,{"job_id":job_id,
                "status_url":"/v1/jobs/"+job_id})
        match=re.fullmatch(r"/v1/jobs/([a-f0-9]{24})/feedback",path)
        if match:
            job_id=match.group(1)
            with LOCK:
                j=JOBS.get(job_id)
                if j is None and (OUT/job_id/"status.json").is_file():
                    j=json.loads((OUT/job_id/"status.json").read_text())
                    JOBS[job_id]=j
            if not j: return self.send_json(404,{"error":"Job unknown"})
            rating=body.get("rating")
            note=body.get("notes","")
            if type(rating)!=int or rating not in (1,2,3,4,5) or \
                  not isinstance(note,str) or len(note)>2000:
                return self.send_json(422,{"error":"rating 1-5 and notes under 2000 characters"})
            feedback={"rating":rating,"notes":note,"created_at":time.time()}
            with LOCK:
                j["feedback"]=feedback
                save(job_id)
            return self.send_json(200,{"saved":True,"status":"review_recorded"})
        return self.send_json(404,{"error":"Not found"})

if __name__=="__main__":
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
