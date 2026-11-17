# Sauce — Bounded production-safe stress gate

Date: 2026-11-17
Status: **burst-read and isolated admission tests passed after fixing a real socket backlog failure**. NOT a paid self-service launch signoff.
Source: \`Davemafy/sauce-vids\`, GitHub \`main\` only.

## Scope and safety

The tests intentionally did **not** submit jobs to the live capture/AI engine, trigger Gemini inference, navigate third-party product sites, perform purchases, expose bearer credentials, or disrupt real queued work.

The existing private pilot is running on Vultr with three services: \`sauce-url2video.service\`, \`sauce-studio.service\`, \`sauce-steward.service\`. No reset or replacement of the existing dirty production checkout. A separate clean main checkout hosted the tests.

Automated production burst covered GET-only localhost health + actual Unix status + stored, SHA/source-verified continuous preview MP4. The isolated queue test used only synthetic content in a temporary localhost server and a fake executor that never calls a model or visits the internet. This is **not** a benchmark of real simultaneous production rendering or general 4G video experience.

## Confirmed baseline failure and correction

An actual baseline at 12 concurrent local clients, before changes, issued 100 health requests, 120 job status reads, and 24 existing-video reads (244 total). Health passed 100/100. Unix reads failed **13/144 connections**: six status and seven media; error \`BlockingIOError\` during local socket connect. Latency for successful calls was low; the issue was admission under burst, not a slow renderer.

Root cause in Python standard-library server configuration: the private \`ThreadingMixIn + UnixStreamServer\` was inheriting a connection backlog of **5**. \`backend/sauce_api.py\` now explicitly sets \`PrivateUnixServer.request_queue_size=64\` and \`LocalTCPServer.request_queue_size=64\` (still bound to loopback, no new public endpoint). Existing service restarted only after checking there were no active paid jobs. The previous \`sauce_api.py\` was backed up in \`/var/lib/sauce-steward/deploy-backups/stress-20261117/\`.

## Post-fix actual worker load: 0 failures

| Concurrent clients | GET calls (health + status + video) | Errors | Status p95 | Video p95 |
|---|---:|---:|---:|---:|
| 12 | 244 (100 + 120 + 24) | 0 | 9.17 ms | 15.43 ms |
| 24 | 320 (100 + 180 + 40) | 0 | 15.80 ms | 28.94 ms |
| 32 | 348 (100 + 200 + 48) | 0 | 21.17 ms | 32.54 ms |

These measurements are within the same VM and include only existing jobs and previews (largest actual sample 1,339,826 bytes). **They are not network round trips from end-user mobile devices**, nor evidence of 32 simultaneous video renders.

Private machine-readable aggregate receipts:
- \`/var/lib/sauce-steward/stress-12.json\`
- \`/var/lib/sauce-steward/stress-24.json\`
- \`/var/lib/sauce-steward/stress-32.json\`

The bounded read-only harness is \`ops/stress_sauce_pilot.py\`, max 32 clients and 600 calls per invocation. Run only on the authorized host; never treat its diagnostic traffic as user activity.

After the load, \`sauce-url2video.service\` had \`MemoryCurrent=26,943,488\` bytes (~25.7 MiB), \`TasksCurrent=2\`. All 3 Sauce services remained active. Public Studio HTTPS returned 200; unauthenticated job POST remained forbidden (403).

## Job-admission load — isolated fake worker only

\`tests/test_sauce_api_load.py\` starts a temporary localhost API and patches only the test server's worker with a deterministic non-network fake. At 24 simultaneous authenticated submissions it returned **2 accepted (202) / 22 rejected (429)** per the current bounded queue policy. Both fake jobs completed on release; 200 concurrent GET status reads and 40 synthetic-media reads passed; two unauthorized status/media requests returned 401. There were zero AI calls, browser interactions, or generated real product claims.

The test does **not** demonstrate processing capacity for two concurrent 1080p video renders: the production executor has one render worker, and the isolated runner is a stub.

## Public HTTPS authentication and edge behavior

A plain Python HTTP client was rejected by the upstream edge with \`HTTP 403 / error 1010\`. A real Chromium pilot login and an authenticated Playwright browser-context test were accepted. In a bounded 8-client authenticated browser test, **40 status requests and 10 stored-video requests received HTTP 200**, with measured p95 around 107 ms status and 85 ms media. The test script incorrectly checked \`status\` at the JSON top level instead of inside the web proxy's \`job\` wrapper; therefore those 40 cannot count as fully body-validated passing assertions. The 10 media bodies passed their length check. Do not reclassify that client harness mistake as a server fault or claim a complete authenticated-web load gate.

Do not attempt to circumvent edge security using deceptive headers; use permitted browser-based testing in future controlled tests.

## Existing product bottlenecks and pending gates

1. **Media byte ranges / streaming:** Current web \`apps/web/app/api/studio/url/[...parts]/route.ts\` buffers a complete MP4 response and emits \`Accept-Ranges: none\`; the private API also serves full files without 206 ranges. This is fine for small samples but a significant memory/bandwidth and seekability risk under larger clips and Nigerian 4G. Implement true authenticated byte-range streaming with backpressure and prove 206/416, browser seek, interruption and parallel downloads.
2. **Full real-pipeline load:** This test did not measure multiple simultaneous expensive Chromium captures, 1080p re-renders, Gemini rate limiting, queue wait/p95, per-job CPU/RAM/disk peak or job recovery through a forced failure mid-render. Do so in a controlled staging fixture with strict caps before self-service demand, and obtain separate owner authorization for actual paid inference.
3. **Identity and quotas:** The private pilot shared access code plus opaque job IDs are not production multi-tenant ownership/authorization. Add scoped customer accounts, per-user job quotas, storage expiration/cleanup, rate limiting, content length constraints, and cost accounting before broad public access. Test malicious and repeated submissions.
4. **Real slow networks:** Test the actual web video at 4G and flaky/mobile network conditions, Android resume/background, partial downloads, time-to-first-frame and cross-device account recovery.
5. **Quality:** Quantitative uptime/tests are necessary but insufficient. Existing Phase 2 Brimble modal occlusion/cropped payoff and lower-fidelity 720p-to-1080p public URL capture remain. Three distinct real, visually accepted cinematic product films and actual buyer reviews are needed before claiming "premium".
6. **No commercial proof:** The previously recorded four continuous output clips come from development/pilot trials, with no submitted external customer ratings or verified payments. This stress test adds **zero customer demand evidence**.

## Repeatable commands

On the Vultr host, source clone lives at \`/var/lib/sauce-steward/source-main\`:

\`\`\`sh
cd /var/lib/sauce-steward/source-main
/opt/sauce-vids/.venv/bin/python -m pytest -q \\
  tests/test_sauce_api_load.py tests/test_sauce_pilot_stress.py \\
  tests/test_job_store.py tests/test_sauce_value_report.py \\
  tests/test_sauce_steward.py tests/test_product_explorer.py \\
  tests/test_url2video_api.py

# bounded, read-only, NO job POSTs or inference
sudo -u devmcp /opt/sauce-vids/.venv/bin/python \\
  ops/stress_sauce_pilot.py --clients 32 \\
  --health 100 --status 200 --media 48
\`\`\`

Combined targeted regression result on 2026-11-17: **40 tests passed, 24 nested subtests passed**, ~0.95 seconds. Source changes committed on main, service verified active. The next meaningful performance release gate is authenticated streaming/seek and real bounded render workload, not endlessly repeating 1 MB cached-video GETs.

## Launch decision

**Safe to continue the invite-only pilot. Not stress-certified for unrestricted public production or paid unattended traffic.**

The load failure is corrected and verified; further scaling claims must wait for byte-range delivery, tenant isolation, quota/cost controls, and a genuine full-render capacity test. Preserve the film's source-truth/creative quality standard independently of this infrastructure work.
