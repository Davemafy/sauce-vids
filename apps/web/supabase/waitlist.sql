-- Run once in the Supabase SQL editor. The service-role key stays server-side.
create extension if not exists pgcrypto;

create table if not exists public.waitlist_signups (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  source text not null default 'hero'
    check (source in ('hero', 'footer')),
  created_at timestamptz not null default now()
);

create index if not exists waitlist_signups_created_at_idx
  on public.waitlist_signups (created_at desc);

alter table public.waitlist_signups enable row level security;

revoke all on public.waitlist_signups from anon, authenticated;
-- No public select/insert policies. Server uses the service-role key.
