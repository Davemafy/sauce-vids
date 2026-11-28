# Sauce product site and private Studio

An editorial Sauce landing page and responsive one-click Studio on Next.js 15 / React 19. The Studio triggers a bounded set of real Python/Chromium/FFmpeg render jobs while preserving the existing verified rendering pipeline.

## Install and run

```bash
cd apps/web
npm install
npm run dev
```

## Website stack

- Tailwind CSS v4 exclusively for layout and component styling (the global stylesheet contains only the Tailwind import, theme tokens, and minimal base typography/selection rules).
- Big Shoulders, Instrument Sans, Lobster brand wordmark via Next.js font optimization.
- Phosphor icons (SSR import for server components, client import only for the interactive form).
- Independently positioned RECORD and POLISH photography assets at `public/art/record.webp` and `public/art/polish.webp`.
- Native HTML controls and accessible labels, no animation runtime.

## Waitlist setup (required before publishing)

1. Create or use a Supabase project.
2. Execute `supabase/waitlist.sql` in its SQL editor.
3. In the Vercel project rooted at `apps/web`, set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` as **server-side** environment variables.
4. Deploy and submit a test email. Verify the row in `public.waitlist_signups`.
5. Submit the same address twice; the table's unique constraint ensures no duplicate row.
6. Remove only your test email in Supabase afterward.

The server responds with HTTP 503 when no database is configured. **It never pretends a signup succeeded.** Empty/invalid addresses are rejected; a honeypot field provides basic spam friction. Add managed rate limiting / bot protection before larger-scale traffic.

Do not commit `.env.local`. Never set `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY`.

## Verify

```bash
npm run typecheck
npm test
npm run build
```

The **AFTER: A demo with Sauce** film is a real Phase 2 3D Launch H.264/AAC export, hosted on the existing Vultr HTTPS origin. The Studio UI at `/studio` supports two verified recordings, three presets and a Foley toggle. The worker requires explicit server configuration; without it, rendering fails closed while the reference film remains viewable. See `docs/sauce-studio-phase3.md` for the full API contract, verification and service setup.

## Production gates

- Inspect the real browser at 390x844, 768x1024, 1440x900.
- The RECORD / POLISH cutouts must remain sharp, transparent, and not obscure the form or headline.
- All links must have real destinations; no fake sign-in, price table, testimonials, or fabricated videos.
- Test a real production database insert, including duplicates and network failure.

## The product journey (November 2026)

- `/`: editorial condiment campaign, genuine short technique sample, real waitlist, and URL entry.
- Homepage URL entry validates public HTTP(S) format, removes potentially sensitive query/fragment data, and routes to `/studio?url=<encoded>`. This is **prefill, not submission**.
- `/studio`: real private-pilot form, proof-oriented progress, existing jobs, downloadable previews, reviews, and saved-film recovery.
- Auto PR is shown as **in development** only. The stylized PR card is a labeled concept, not product footage.
- The three-second sample is **not** a quality-approved autonomous product film; do not market it as one.
- Public rendering is not open; a real pilot code and configured backend are required. Waitlist storage is real Supabase or HTTP 503, never fake success.

Verified separately in development with TypeScript, build, Vitest and Playwright desktop/mobile; see `docs/SAUCE_HANDOFF.md` for latest receipts.
