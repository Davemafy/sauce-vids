"""Isolated concurrent Sauce API admission/stream tests; no real AI calls.

Uses an in-process localhost HTTP server and a temp storage directory.
The production worker, queue, public endpoint and billing are never touched.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


class ConcurrentApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="sauce-api-stress-")
        cls.test_token = "LocalOnlyUnpaidStressToken" * 2
        with patch.dict(os.environ, {
            "SAUCE_API_TOKEN": cls.test_token,
            "SAUCE_JOBS_DIR": cls.tmp.name,
            "SAUCE_API_PORT": "0",
        }):
            from backend import sauce_api
            cls.api=sauce_api
        from http.server import ThreadingHTTPServer
        class TestServer(ThreadingHTTPServer):
            request_queue_size=64
            daemon_threads=True
        cls.server=TestServer(("127.0.0.1",0),cls.api.Handler)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.api.POOL.shutdown(wait=True, cancel_futures=True)
        cls.tmp.cleanup()

    @classmethod
    def request(cls, method, route, body=None, *, auth=True):
        conn=http.client.HTTPConnection("127.0.0.1",cls.port,timeout=10)
        headers={}
        if auth: headers["Authorization"]="Bearer "+cls.test_token
        if body is not None: headers["Content-Type"]="application/json"
        try:
            conn.request(method,route,
                body=json.dumps(body).encode() if body is not None else None,
                headers=headers)
            resp=conn.getresponse()
            data=resp.read()
            return resp.status,data,dict(resp.getheaders())
        finally:
            conn.close()

    def test_parallel_queue_cap_poll_and_media(self):
        api=self.api
        api.JOBS.clear()
        started=threading.Event()
        finish=threading.Event()

        def unpaid_worker(job_id):
            with api.LOCK:
                api.JOBS[job_id]["stage"]="capturing"
                api.save(job_id)
            started.set()
            if not finish.wait(12):
                raise RuntimeError("Test fixture release timed out")
            with api.LOCK:
                api.JOBS[job_id].update(stage="needs_review",status="needs_review")
                api.save(job_id)

        def only_test_url(raw):
            if raw != "https://example.com/":
                raise ValueError("Fixture URL only")
            return raw

        with patch.object(api,"worker",unpaid_worker),patch.object(
             api,"validate_public_url",only_test_url):
            # No product page is opened; only the admission/locking logic runs.
            with ThreadPoolExecutor(max_workers=24) as pool:
                statuses=list(pool.map(
                    lambda _:self.request("POST","/v1/jobs",
                                          {"url":"https://example.com/"})[0],
                    range(24)))
            self.assertEqual(statuses.count(202),2)
            self.assertEqual(statuses.count(429),22)
            self.assertEqual(len(api.JOBS),2)
            self.assertTrue(started.wait(3))
            finish.set()
            end=time.monotonic()+10
            while time.monotonic()<end:
                if all(job.get("status")=="needs_review"
                       for job in api.JOBS.values()):break
                time.sleep(.025)
            self.assertTrue(all(job.get("status")=="needs_review"
                                for job in api.JOBS.values()))

            target_id=next(iter(api.JOBS))
            media=Path(self.tmp.name)/target_id/"export"/"preview.mp4"
            media.parent.mkdir(parents=True,exist_ok=True)
            fake_bytes=(b"\x00\x00\x00\x18ftypisom"+b"x"*1024)*640
            media.write_bytes(fake_bytes)
            # Isolated simulated bytes test streaming mechanics ONLY; this
            # file is never represented as genuine product-footage evidence.
            def verify_status(_):
                code,data,_=self.request("GET",f"/v1/jobs/{target_id}")
                return code==200 and json.loads(data)["status"]=="needs_review"

            def verify_media(_):
                code,data,headers=self.request(
                    "GET",f"/v1/jobs/{target_id}/preview.mp4")
                return code==200 and data==fake_bytes and (
                    headers.get("Content-Type")=="video/mp4")

            with ThreadPoolExecutor(max_workers=24) as pool:
                status_reads=list(pool.map(verify_status,range(200)))
                media_reads=list(pool.map(verify_media,range(40)))
            self.assertTrue(all(status_reads))
            self.assertTrue(all(media_reads))
            code,_,_=self.request("GET",f"/v1/jobs/{target_id}",auth=False)
            self.assertEqual(code,401)
            code,_,_=self.request("GET",f"/v1/jobs/{target_id}/preview.mp4",auth=False)
            self.assertEqual(code,401)
            self.assertTrue(all((Path(self.tmp.name)/jid/"status.json").is_file()
                                for jid in api.JOBS))
            print("ISOLATED_API_STRESS: 24 parallel admissions (2 accepted / 22 throttled), "
                  "200 status polls, 40 media reads, 2 unauthorized requests rejected; "
                  "0 external browser actions / 0 AI calls")


if __name__=="__main__":
    unittest.main()
