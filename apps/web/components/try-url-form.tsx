'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRightIcon, LinkSimpleIcon } from '@phosphor-icons/react';
import s from '../app/landing.module.css';

export function TryUrlForm() {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const candidate = value.trim();
    if (!candidate) return;
    try {
      const full = /^https?:\/\//i.test(candidate) ? candidate : 'https://' + candidate;
      const parsed = new URL(full);
      if (!['https:', 'http:'].includes(parsed.protocol) || !parsed.hostname.includes('.') ||
          parsed.username || parsed.password || parsed.hostname === 'localhost') {
        throw new Error('Enter a public website address.');
      }
      // Credentials and tracking tokens copied from a product URL do not belong in previews.
      parsed.search = '';
      parsed.hash = '';
      setError('');
      router.push('/studio?url=' + encodeURIComponent(parsed.toString()));
    } catch {
      setError('Enter a public website address, like example.com.');
    }
  }

  return (
    <form onSubmit={submit} className={s.tryForm} aria-label="Try Sauce with your product URL">
      <label htmlFor="try-url" className={s.tryLabel}>Got a product? Start here.</label>
      <div className={s.tryInputGroup}>
        <LinkSimpleIcon size={22} weight="bold" aria-hidden="true" />
        <input
          id="try-url"
          type="text"
          inputMode="url"
          autoComplete="url"
          autoCapitalize="off"
          spellCheck={false}
          value={value}
          onChange={event => { setValue(event.target.value); if (error) setError(''); }}
          placeholder="yourproduct.com"
          aria-describedby={error ? 'try-url-error' : 'try-url-note'}
          required
          maxLength={2048}
        />
        <button type="submit">Take a look <ArrowRightIcon size={21} weight="bold" aria-hidden="true"/></button>
      </div>
      {error ? <p role="alert" id="try-url-error" className={s.tryError}>{error}</p> :
        <p id="try-url-note" className={s.tryNote}>Opens the real Sauce Studio. Rendering is currently invite-only.</p>}
    </form>
  );
}
