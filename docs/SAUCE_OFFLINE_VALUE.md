# Sauce — unattended customer-value loop (private pilot)

Date: 2026-11-17
Status: **deployed and browser-verified as a bounded private pilot**, not a self-serve paid launch.

## What "works while the owner is away" means

A customer with access to the private pilot can submit a safe public HTTP(S) website URL, close their tab, and return to a real generated MP4 without the owner operating ChatGPT or the Vultr console. Production happens server-side; authentication and file access remain gated. The user can review the result and optionally leave a 1–5 quality rating. The system never pretends to demonstrate a private/authenticated product feature.

This is a **customer job execution/delivery loop**, not autonomous customer acquisition, billing, model-powered code writing, or a guarantee of film quality or recurring revenue.

## Verified implementation

### Production engine
- Service: \`sauce-url2video.service\` on Vultr, running as unprivileged devmcp at \`/opt/sauce-vids\`. It was already serving the continuous-browser pilot; no renderer rewrite was performed.
- New \`backend/job_store.py\` provides atomic, fsync-backed status writes (mode 0600), loads existing completed jobs after backend restart, resumes only jobs that were still untouched in \`queued\`, and classifies interrupted in-progress jobs as failed **without repeating an AI direction call**.
- Recovered legacy successful jobs are re-labeled as continuous source footage **only if** their existing \`release.json\` records actual \`continuous_motion=true\`, \`source_verified=true\` and an existing nonempty preview. No nonexistent source integrity claim.
- Real output is still Playwright Chromium WebM → H.264 preview/master with source SHA; the URL master is **upscaled** from a 1280×720 recorder and frame rate resampled to 60fps. Do not misrepresent as native 1080p/60fps.

### Customer return experience
- Studio includes \`apps/web/app/studio/film-library.tsx\` and its CSS. It stores at most 12 random job IDs in same-browser \`localStorage\`, **not** URLs, source screenshots or private video bytes.
- Revisiting Studio after a tab has been closed retrieves job status and finished media from the authenticated server; a direct authorized \`?job=\` review link is remembered on the device.
- The new UI says that server processing continues when the tab closes and explains that history is device-local, not a real account library.
- Existing 6-hour private pilot cookie/same-origin validation remains. Customers may need to re-enter the access code after expiration. Shared pilot access is NOT a production multi-tenant security design.

### Actual deployed paths
- Web service: \`sauce-studio.service\`. Existing \`/etc/systemd/system/sauce-studio.service.d/30-offline-value.conf\` points to the versioned release \`/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-studio-offline-value-v2-20261117/apps/web\`. The previous releases remain as rollback candidates.
- Backend updated only \`/opt/sauce-vids/backend/sauce_api.py\` and \`backend/job_store.py\`. Backups under \`/var/lib/sauce-steward/deploy-backups/offline-value-20261117\`; the existing dirty production checkout was not reset, rebased or cleaned.
- \`sauce-steward.service\` remains separately active as a read-only supervisor. It now runs an hourly \`value-report\` job from \`ops/sauce_value_report.py\`. Private receipts: \`/var/lib/sauce-steward/value-report.json\` and \`/var/lib/sauce-steward/status.json\`. No new public data endpoint.
- Status/logs:
  \`systemctl status sauce-studio.service sauce-url2video.service sauce-steward.service --no-pager\`
  \`journalctl -u sauce-url2video.service -n 40 --no-pager\`

## Independent acceptance performed on production

- \`python -m pytest -q\` across \`tests/test_job_store.py\`, \`tests/test_sauce_value_report.py\`, \`tests/test_sauce_steward.py\`, \`tests/test_product_explorer.py\`, \`tests/test_url2video_api.py\`: **35 passed, 17 nested subtests**.
- Staged web \`npm run typecheck\`, Next.js production \`npm run build\`, \`npm run test\`: 13 Vitest tests. \`npm run test:e2e -- tests/url-flow.spec.ts\`: **6 Playwright browser tests**, including closing the tab, opening a new tab, recovering a completed film, and reopening the download link. Note a first browser test attempt failed from an *incorrect executable directory path* and passed after pointing to the actual executable.
- After live backend and web restarts: \`sauce-studio.service\`, \`sauce-url2video.service\`, \`sauce-steward.service\` all \`active\`. Public HTTPS Studio and samples returned HTTP 200. Unauthenticated POST to the protected URL-job route returned HTTP 403.
- Private Unix backend recovered an existing completed genuine continuous film: status HTTP 200, preview \`video/mp4\` HTTP 200. A legacy source-verified continuous film originally missing its mode label was correctly recovered; **all four** existing source-verified continuous-film records now show continuous mode.
- Real HTTPS Playwright journey (no new AI render): pilot login → existing finished job → actual video and device history at 1280×720 and 390×844, with no horizontal overflow. Protected media HTTP 200; \`video.readyState=4\`, \`HTMLMediaElement.play()\` succeeds and \`video.error=0\` in desktop and mobile Chromium. Private QA screenshots kept under \`/var/lib/sauce-steward/qa-logs/public-return-20261117\`, not publicly posted.
- No new arbitrary-URL production render was triggered in the deployment QA, avoiding an unapproved paid model call; existing verified customer-style outputs established the return/retrieval proof.
- A full VM reboot was deliberately NOT performed. Service persistence is systemd-enabled, not reboot-stress-tested.

## Actual operational value indicators

The first private hourly report, from existing accumulated pilot/developer jobs on 2026-11-17 UTC, found:
- 28 total job records, 15 marked ready-for-review, 9 failed and 4 requiring private-site access.
- Of the 15 ready jobs, **4** have continuous-source verified receipts and actual playable videos. Other ready jobs include older workflows and should not be counted as equivalent saleable continuous films.
- 28.3 seconds of verified continuous footage in those four files.
- **0 recorded customer ratings**, **0 verified paying customers**, payment data unavailable / no billing integration.

These records include testing and development usage; they are NOT evidence of 28 external users or paid conversions. "Output delivered" is a weaker signal than "customer found value".

## Important remaining blockers before an unattended paid launch

1. Make actual generated films consistently premium: prior Brimble modal-entrance rectangle and overly cropped close-up remain creative defects. URL footage still needs native high-density capture, credible cinematic direction, reference-level readability, and three distinct successful product flows.
2. Genuine account/tenant isolation. Current private pilot code is shared; random job IDs plus gate do not constitute customer authorization. Add per-user identity and access to each film before self-serve scale or email delivery.
3. Real retention/quotas/cost controls, user-specific storage lifecycle, download authorization, abuse throttling, queue limits and restart integration. No account-wide recent-film library across devices yet.
4. Customer acquisition and pricing are not implemented. No checkout, invoices or automated email notification exists. Avoid collecting payments or widening public access without explicit authorization and a validated price/proposition.
5. Interview at least 5 real prospective buyers, including 2 motion designers; validate willingness to pay for fewer retakes and usable source-true footage. Review count/paid conversion and repeat usage, not green CI or render count, drive release decisions.

**Operating rule:** Sauce can continue processing authorized customer requests while the owner is offline, but it does not create revenue from an empty queue. The next compounding step is **a better customer result plus actual demand**, not another recursive self-modifying AI agent.
