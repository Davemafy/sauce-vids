import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { validateWaitlistEmail } from '../../../lib/waitlist';

export const runtime = 'nodejs';

const success = () =>
  NextResponse.json(
    { ok: true, message: "You're on the list. We'll email you when early access opens." },
    { status: 200, headers: { 'Cache-Control': 'no-store' } },
  );

export async function POST(request: NextRequest) {
  const origin = request.headers.get('origin');
  const requestHost = request.headers.get('x-forwarded-host') ?? request.headers.get('host');
  if (origin && requestHost) {
    try {
      if (new URL(origin).host.toLowerCase() !== requestHost.toLowerCase()) {
        return NextResponse.json({ ok: false, message: 'Invalid request origin.' }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ ok: false, message: 'Invalid request origin.' }, { status: 403 });
    }
  }

  if (Number(request.headers.get('content-length') ?? 0) > 4096) {
    return NextResponse.json({ ok: false, message: 'Request too large.' }, { status: 413 });
  }

  let payload: { email?: unknown; website?: unknown; source?: unknown };
  try {
    payload = await request.json();
    if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
      return NextResponse.json({ ok: false, message: 'Invalid submission.' }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ ok: false, message: 'Invalid submission.' }, { status: 400 });
  }

  const parsed = validateWaitlistEmail(payload.email);
  if (!parsed.ok) {
    return NextResponse.json({ ok: false, message: parsed.message }, { status: 400 });
  }

  // Invisible field: silently acknowledge obvious automated submissions.
  if (typeof payload.website === 'string' && payload.website.trim()) return success();

  const url = process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceKey) {
    console.error('[waitlist] Persistence has not been configured.');
    return NextResponse.json(
      { ok: false, message: 'Signups are temporarily unavailable. Please try again later.' },
      { status: 503 },
    );
  }

  try {
    const supabase = createClient(url, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    const source = payload.source === 'footer' ? 'footer' : 'hero';
    const { error } = await supabase
      .from('waitlist_signups')
      .upsert({ email: parsed.email, source }, { onConflict: 'email', ignoreDuplicates: true });

    if (error) {
      console.error('[waitlist] Write failed:', error.code);
      return NextResponse.json(
        { ok: false, message: 'Could not save your email. Please try again.' },
        { status: 503 },
      );
    }
    return success();
  } catch {
    console.error('[waitlist] Connection failure.');
    return NextResponse.json(
      { ok: false, message: 'Could not save your email. Please try again.' },
      { status: 503 },
    );
  }
}

export async function GET() {
  return NextResponse.json({ message: 'Method not allowed.' }, { status: 405 });
}
