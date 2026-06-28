-- ============================================================
-- Reunion Planner — Supabase schema (code-based access version)
-- Run this in the Supabase SQL editor (Project > SQL Editor > New query)
--
-- NOTE: This version does NOT use Supabase Auth / auth.users at all.
-- Access is controlled entirely by two codes per reunion (plan_code
-- to view, edit_code to edit), checked inside the Flask app. Because
-- of that, these tables are open to the "anon" key -- there is no
-- per-person login, so there's no real row-level security to apply.
-- Treat your codes like passwords: anyone who has the edit_code can
-- change anything in that reunion.
-- ============================================================

create extension if not exists "pgcrypto";

-- Drop old auth-based tables if you previously ran the old schema version.
-- (Safe to skip if this is a brand new Supabase project.)
drop table if exists comments cascade;
drop table if exists notes cascade;
drop table if exists people cascade;
drop table if exists places cascade;
drop table if exists events cascade;
drop table if exists tasks cascade;
drop table if exists reunion_members cascade;
drop table if exists reunions cascade;

-- ---------- Reunions ----------
create table reunions (
  id uuid primary key default gen_random_uuid(),
  name text not null default 'Our reunion',
  tagline text default '',
  plan_code text not null unique,
  edit_code text not null,
  created_at timestamptz not null default now()
);

-- ---------- Tasks ----------
create table tasks (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  title text not null,
  category text not null default 'general'
    check (category in ('general', 'food', 'lodging', 'travel', 'activities', 'money')),
  notes text default '',
  created_by_name text default '',
  claimed_by_name text,
  done boolean not null default false,
  created_at timestamptz not null default now()
);

-- ---------- Events ----------
create table events (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  title text not null,
  event_date date,
  event_time time,
  location text default '',
  details text default '',
  created_by_name text default '',
  created_at timestamptz not null default now()
);

-- ---------- Notes ----------
create table notes (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  text text not null,
  author_name text default '',
  created_at timestamptz not null default now()
);

-- ---------- People (RSVP tracking) ----------
create table people (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  name text not null,
  rsvp text not null default 'unknown' check (rsvp in ('yes', 'no', 'unknown')),
  created_at timestamptz not null default now(),
  unique (reunion_id, name)
);

-- ---------- Places (lodging / venue details) ----------
create table places (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  name text not null,
  address text default '',
  check_in date,
  check_out date,
  wifi_network text default '',
  wifi_password text default '',
  host_name text default '',
  host_contact text default '',
  notes text default '',
  created_by_name text default '',
  created_at timestamptz not null default now()
);

-- ---------- Comments (polymorphic: task / event / note) ----------
create table comments (
  id uuid primary key default gen_random_uuid(),
  reunion_id uuid not null references reunions(id) on delete cascade,
  parent_type text not null check (parent_type in ('task', 'event', 'note')),
  parent_id uuid not null,
  body text not null,
  author_name text default '',
  created_at timestamptz not null default now()
);

create index idx_comments_parent on comments (parent_type, parent_id);
create index idx_tasks_reunion on tasks (reunion_id);
create index idx_events_reunion on events (reunion_id);
create index idx_notes_reunion on notes (reunion_id);
create index idx_people_reunion on people (reunion_id);
create index idx_places_reunion on places (reunion_id);
create index idx_reunions_plan_code on reunions (plan_code);

-- ============================================================
-- RLS: open to anon key, since access control happens at the
-- application layer via the plan/edit codes, not via Postgres auth.
-- ============================================================
alter table reunions enable row level security;
alter table tasks enable row level security;
alter table events enable row level security;
alter table notes enable row level security;
alter table people enable row level security;
alter table places enable row level security;
alter table comments enable row level security;

create policy "anon full access reunions" on reunions for all using (true) with check (true);
create policy "anon full access tasks" on tasks for all using (true) with check (true);
create policy "anon full access events" on events for all using (true) with check (true);
create policy "anon full access notes" on notes for all using (true) with check (true);
create policy "anon full access people" on people for all using (true) with check (true);
create policy "anon full access places" on places for all using (true) with check (true);
create policy "anon full access comments" on comments for all using (true) with check (true);
