-- Allied Forces Weapons Pack - server whitelist.
-- Run once in the Supabase SQL editor (or as a migration).

create table if not exists public.af_server_whitelist (
  id         bigint generated always as identity primary key,
  name       text not null,                 -- e.g. 'AF Test Server'
  ip         text not null,                 -- public IP the server calls out from
  port       integer not null check (port between 1 and 65535),   -- DayZ game port
  enabled    boolean not null default true,
  created_at timestamptz not null default now(),
  unique (ip, port)
);

create table if not exists public.af_license_checks (
  id         bigint generated always as identity primary key,
  ip         text not null,
  port       integer not null,
  allowed    boolean not null,
  checked_at timestamptz not null default now()
);

-- Only the edge function (service role) reads or writes these; nothing is exposed to the public API.
alter table public.af_server_whitelist enable row level security;
alter table public.af_license_checks enable row level security;

-- Add a server (example):
-- insert into public.af_server_whitelist (name, ip, port) values ('AF Test Server', '203.0.113.10', 2302);
