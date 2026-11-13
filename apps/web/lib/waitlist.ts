export type WaitlistValidation =
  | { ok: true; email: string }
  | { ok: false; message: string };

export function validateWaitlistEmail(input: unknown): WaitlistValidation {
  if (typeof input !== 'string') {
    return { ok: false, message: 'Enter a valid email address.' };
  }

  const email = input.trim().toLowerCase();
  if (email.length < 3 || email.length > 254 || /\s/.test(email)) {
    return { ok: false, message: 'Enter a valid email address.' };
  }

  // Disallow invalid punctuation and consecutive dots, without pretending to
  // implement the entire RFC 5322 grammar.
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(email) || email.includes('..')) {
    return { ok: false, message: 'Enter a valid email address.' };
  }

  return { ok: true, email };
}
