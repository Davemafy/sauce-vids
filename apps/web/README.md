# Sauce waitlist website

A static-first, editorial Sauce landing page built on the existing Next.js 15 / React 19 application. The Hermes plugin, capture pipeline, Remotion Studio, and FFmpeg renderer are unchanged.

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

The conceptual example frame in the purple section is explicitly **illustrative**, not real captured footage or a playable export. Replace it with a verified Sauce render when available.

## Production gates

- Inspect the real browser at 390x844, 768x1024, 1440x900.
- The RECORD / POLISH cutouts must remain sharp, transparent, and not obscure the form or headline.
- All links must have real destinations; no fake sign-in, price table, testimonials, or fabricated videos.
- Test a real production database insert, including duplicates and network failure.
