# Sauce Steward: persistent read-only quality supervisor

**Scope:** Runs independently of ChatGPT login. Separate from existing Sauce production workers. Does **not** autonomously code, commit, call an AI provider, or launch a product. Those require a bounded coding-agent runtime, explicit inference budget, and owner-approved write policy.

Entry: ops/sauce_steward.py, service unit: ops/systemd/sauce-steward.service.

## Operational behavior

- systemd daemon under the unprivileged devmcp user, auto-restarts and starts at boot.
- SQLite task journal persisted in /var/lib/sauce-steward/jobs.sqlite3; interrupted jobs resume once (max two attempts) after service restart.
- Every 10 minutes probes remote GitHub main; changes trigger **safe fast-forward** of a separate checkout in /var/lib/sauce-steward/source-main. It will never reset a dirty checkout or modify /opt/sauce-vids.
- Hourly checks public Studio and proof page HTTP reachability.
- Daily downloads and checks the bounded, known source-true Phase 2 reference MP4 and full-decodes it. Keeps private frame 48 as a visual inspection aid; does not claim quality approval.
- Only four fixed task types: sync-main, smoke-web, audit-proof, test-main. The test job is manual to avoid expensive continuous CI.
- /var/lib/sauce-steward/status.json and journalctl hold receipts and errors. No new public network endpoint or secret/key provisioning.
- No AI calls or authenticated browser actions; no uncontrolled spending.

## Install on existing Vultr

Only after testing and safe ownership checks:

    sudo install -d -m 0755 /usr/local/lib/sauce-steward
    sudo install -m 0755 ops/sauce_steward.py /usr/local/lib/sauce-steward/sauce_steward.py
    sudo install -m 0644 ops/systemd/sauce-steward.service /etc/systemd/system/sauce-steward.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now sauce-steward.service

The user can close the ChatGPT app; systemd continues on Vultr. The worker is separate from sauce-url2video.service and sauce-studio.service.

## Status and manually triggered jobs

    sudo systemctl status sauce-steward.service --no-pager
    sudo journalctl -u sauce-steward.service -n 80 --no-pager
    sudo -u devmcp env SAUCE_STEWARD_STATE=/var/lib/sauce-steward \
      python3 /usr/local/lib/sauce-steward/sauce_steward.py status
    sudo -u devmcp env SAUCE_STEWARD_STATE=/var/lib/sauce-steward \
      python3 /usr/local/lib/sauce-steward/sauce_steward.py enqueue test-main

Do not enqueue a test on production checkout. test-main uses isolated source-main, verifies clean git status and runs URL pilot tests in a bounded process.

## Deliberate separation from an autonomous builder

A CLI coding agent with authenticated model access is **not installed** on the host as of the initial audit. No model expenditure or permission for unattended commits was authorized. The service deliberately performs safe useful work without tokens.

To extend: add a separate sandboxed writer service with independent clean working tree, explicit per-job limits (inference cost/time, file scope, test requirement), mandatory visual QA and owner-gated releases. The supervising worker can ingest its verifiable receipts later. Never permit model-generated arbitrary systemd commands or host-root control.

All previously tracked project rules in AGENTS.md and docs/SAUCE_STANDARDS.md still apply, especially main-only development, source truth and honest visual acceptance.
