-- Allied Forces Mod Shop: licence requests + site access to the whitelist.
-- Run after af_server_whitelist.sql. Safe to run more than once.
-- Uses the site's existing is_admin() function (the public.admins table).

alter table public.af_server_whitelist add column if not exists owner_id uuid references auth.users(id) on delete set null;
alter table public.af_server_whitelist add column if not exists product text not null default 'af_weapons_pack';

create table if not exists public.af_license_requests (
  id          bigint generated always as identity primary key,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  product     text not null default 'af_weapons_pack',
  server_name text not null check (char_length(server_name) between 2 and 60),
  ip          text not null check (ip ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$'),
  port        integer not null check (port between 1 and 65535),
  note        text check (note is null or char_length(note) <= 500),
  status      text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  staff_note  text,
  created_at  timestamptz not null default now(),
  decided_at  timestamptz
);
create unique index if not exists af_license_requests_one_pending
  on public.af_license_requests (user_id, ip, port) where status = 'pending';

alter table public.af_license_requests enable row level security;

-- Buyers: see, create and cancel their own requests. Staff: everything.
drop policy if exists "af requests read" on public.af_license_requests;
create policy "af requests read" on public.af_license_requests
  for select using (user_id = auth.uid() or is_admin());
drop policy if exists "af requests create" on public.af_license_requests;
create policy "af requests create" on public.af_license_requests
  for insert with check (user_id = auth.uid() and status = 'pending' and staff_note is null and decided_at is null);
drop policy if exists "af requests cancel" on public.af_license_requests;
create policy "af requests cancel" on public.af_license_requests
  for delete using (user_id = auth.uid() and status = 'pending');
drop policy if exists "af requests staff" on public.af_license_requests;
create policy "af requests staff" on public.af_license_requests
  for all using (is_admin()) with check (is_admin());

-- Whitelist: staff manage it, an owner can see their own servers. The licence check
-- itself runs in the af-license edge function with the service role and ignores these.
drop policy if exists "af whitelist staff" on public.af_server_whitelist;
create policy "af whitelist staff" on public.af_server_whitelist
  for all using (is_admin()) with check (is_admin());
drop policy if exists "af whitelist owner read" on public.af_server_whitelist;
create policy "af whitelist owner read" on public.af_server_whitelist
  for select using (owner_id = auth.uid());

-- Check log: staff only.
drop policy if exists "af checks staff read" on public.af_license_checks;
create policy "af checks staff read" on public.af_license_checks
  for select using (is_admin());
