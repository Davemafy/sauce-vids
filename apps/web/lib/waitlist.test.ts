import { describe, expect, it } from 'vitest';
import { validateWaitlistEmail } from './waitlist';

describe('waitlist validation', () => {
  it('normalizes valid email addresses', () => {
    expect(validateWaitlistEmail('  TEST+demo@Example.COM  ')).toEqual({
      ok: true,
      email: 'test+demo@example.com',
    });
  });

  it.each([
    '',
    'not-an-email',
    'a@b',
    'a@x..com',
    'a @example.com',
    'hello@@example.com',
    'x'.repeat(255) + '@example.com',
  ])('rejects invalid address %s', (value) => {
    expect(validateWaitlistEmail(value).ok).toBe(false);
  });

  it('rejects non-string payloads', () => {
    expect(validateWaitlistEmail({ email: 'a@b.com' }).ok).toBe(false);
    expect(validateWaitlistEmail(null).ok).toBe(false);
  });
});
