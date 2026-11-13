'use client';

import { useState, type FormEvent } from 'react';
import { ArrowRightIcon, CheckCircleIcon, EnvelopeSimpleIcon } from '@phosphor-icons/react';

type FormStatus = 'idle' | 'pending' | 'success' | 'error';

export function WaitlistForm({
  source = 'hero',
  theme = 'light',
}: {
  source?: 'hero' | 'footer';
  theme?: 'light' | 'dark';
}) {
  const [email, setEmail] = useState('');
  const [website, setWebsite] = useState('');
  const [status, setStatus] = useState<FormStatus>('idle');
  const [message, setMessage] = useState('');
  const isDark = theme === 'dark';

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === 'pending') return;
    setStatus('pending');
    setMessage('');
    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, website, source }),
      });
      const data: { ok?: boolean; message?: string } = await response.json();
      if (!response.ok || !data.ok) {
        setStatus('error');
        setMessage(data.message ?? 'Could not save your email. Please try again.');
        return;
      }
      setStatus('success');
      setMessage(data.message ?? "You're on the list.");
      setEmail('');
    } catch {
      setStatus('error');
      setMessage('Connection problem. Please try again.');
    }
  }

  return (
    <div className="w-full max-w-[570px]">
      <form
        onSubmit={submit}
        aria-label="Join the Sauce early-access waitlist"
        className="flex min-h-[63px] w-full flex-col gap-2 rounded-[22px] bg-sauce-cream p-[5px] shadow-[0_6px_0_#8c0c1410,0_14px_30px_#66150422] sm:min-h-[66px] sm:flex-row sm:items-center sm:gap-1 sm:rounded-full"
      >
        <label className="flex min-w-0 flex-1 items-center gap-3 px-4 py-2 text-sauce-ink/60 sm:py-0">
          <EnvelopeSimpleIcon aria-hidden="true" size={22} weight="bold" className="shrink-0 text-sauce-red-deep" />
          <span className="sr-only">Email address</span>
          <input
            type="email"
            name="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (status === 'error') setStatus('idle');
            }}
            autoComplete="email"
            inputMode="email"
            autoCapitalize="off"
            spellCheck={false}
            maxLength={254}
            placeholder="Your email address"
            required
            disabled={status === 'pending'}
            aria-describedby={message ? `waitlist-message-${source}` : undefined}
            className="w-full min-w-0 bg-transparent text-[16px] font-medium text-sauce-ink outline-none placeholder:text-sauce-ink/55 disabled:opacity-60"
          />
        </label>
        <label aria-hidden="true" className="absolute -left-[10000px] h-px w-px overflow-hidden">
          Your website
          <input name="website" type="text" value={website} onChange={(event) => setWebsite(event.target.value)} tabIndex={-1} autoComplete="off" />
        </label>
        <button
          type="submit"
          disabled={status === 'pending'}
          className="inline-flex min-h-[50px] shrink-0 items-center justify-center gap-3 rounded-[17px] bg-sauce-red px-6 text-[17px] font-bold text-sauce-cream transition-colors duration-150 hover:bg-sauce-red-deep focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-sauce-ink disabled:cursor-wait disabled:opacity-70 sm:rounded-full"
        >
          {status === 'pending' ? 'Joining...' : 'Join the waitlist'}
          <ArrowRightIcon size={21} weight="bold" aria-hidden="true" />
        </button>
      </form>
      <div
        id={`waitlist-message-${source}`}
        role={status === 'error' ? 'alert' : 'status'}
        aria-live="polite"
        className={`mt-3 flex min-h-[24px] items-start gap-2 text-sm font-semibold ${status === 'error' ? 'text-sauce-red-deep' : isDark ? 'text-sauce-cream' : 'text-sauce-ink'}`}
      >
        {status === 'success' && <CheckCircleIcon size={20} weight="fill" className="shrink-0" aria-hidden="true" />}
        {message || 'Early access updates only. No spam.'}
      </div>
    </div>
  );
}
