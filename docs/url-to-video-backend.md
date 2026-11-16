# Sauce URL-to-video backend (private alpha)

The backend is a thin orchestrator, not a replacement renderer:
public URL -> Playwright inspection -> ONE Gemini vision call ->
validated shot plan -> recorded browser states/interaction trace ->
existing Sauce cinematic renderer -> private MP4 -> human review ->
next director call improved by earlier reviews.

No keyless heuristic pretends to be an AI director. A marketing-only homepage
behind a login must be rejected as needs_access, not sold as a demo.

## Location

- Source: backend/url2video.py, backend/sauce_api.py
- Service: sauce-url2video.service on the Vultr VM, loopback only.
- API: http://127.0.0.1:8767
- Job artifacts: /var/lib/sauce-url2video/jobs/<id>
- Credential file: /etc/sauce-url2video.env (root-only, never commit)
- No public video or raw capture paths are automatically published.

## API secret and Gemini key

The access token is generated on the host and never appears in Git.

    sudoedit /etc/sauce-url2video.env
    # Append GEMINI_API_KEY=<your Google AI Studio key>
    sudo systemctl restart sauce-url2video
    curl http://127.0.0.1:8767/health

Use a Google AI Studio key for a vision-capable Gemini model. Default
SAUCE_DIRECTOR_MODEL=gemini-3.5-flash-lite can be changed in the env file.
Gemini receives a screenshot and page outline. On a free tier, use
public web pages only; paid and free data-use terms differ.

## API examples (from the VM; no token printed)

    TOKEN="$(sudo sed -n 's/^SAUCE_API_TOKEN=//p' /etc/sauce-url2video.env)"
    curl -sS http://127.0.0.1:8767/health
    curl -sS -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d '{"url":"https://paldey.com/"}' http://127.0.0.1:8767/v1/inspect
    curl -sS -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d '{"url":"https://example.com/"}' http://127.0.0.1:8767/v1/jobs

A successful POST returns job_id and status_url. Poll:

    curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8767/v1/jobs/JOB_ID
    curl -H "Authorization: Bearer $TOKEN" \
      http://127.0.0.1:8767/v1/jobs/JOB_ID/preview.mp4 -o preview.mp4

Feedback (1–5, 4+ approved and not rerendered automatically):

    curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d '{"rating":2,"notes":"The UI is too small and the product action is invisible"}' \
      http://127.0.0.1:8767/v1/jobs/JOB_ID/feedback

The last six notes are included as untrusted observations in the NEXT
single director call. Human approval does not automatically submit forms,
publish anything, or generate an expensive second render.

## Safeguards and present limitations

- Public HTTP(S) only, standard ports, global DNS addresses.
- Browser reconnaissance and safe capture block non-GET traffic and
  local/private requests; redirects are rechecked.
- Automatic workflow currently supports scroll/hover only, not account
  login, purchases, application submission or other form mutations.
- Exactly one Gemini director call per job with no generation retry.
- Two queued jobs maximum, one renderer at a time.
- Raw HAR, screenshots and source remain private.
- Existing 1080p60 render can be CPU-intensive; jobs are bounded.
- Passing deterministic technical tests is NOT a visual quality score:
  output requires human review.
- Verified: API authentication, public Paldey inspection, missing-key
  guard, six unit tests.
- Not yet verified: end-to-end Gemini-directed film (no key configured).
