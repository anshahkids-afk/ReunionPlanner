# Reunion Planner (Flask + Supabase, code-based access)

A shared reunion-planning app: tasks people can claim, an events schedule
with a calendar view, group notes, RSVPs, and comments on tasks/events/notes.

**No accounts, no email/password.** Instead, each reunion has two codes:
- a **plan code** — anyone with this can open the board and look around
- an **edit code** — anyone with this can also add/change/claim/delete things

People just type their name once per visit so their tasks, comments, and
RSVPs show up under that name.

## Stack
- **Backend:** Flask (Python), server-rendered Jinja templates
- **Database:** Supabase (Postgres) — used as a plain database here, not for login
- **Frontend:** plain HTML/CSS + a little vanilla JS (for comment toggles)

---

## 1. Create your Supabase project

1. Go to https://supabase.com and create a free project.
2. Open **SQL Editor → New query**, paste in the contents of
   `supabase_schema.sql` from this project, and run it. This creates the
   tables (`reunions`, `tasks`, `events`, `notes`, `people`, `comments`).
   - Note: since there's no login, these tables are open to anyone holding
     your Supabase `anon` key. The plan/edit codes are checked inside the
     Flask app, not by Supabase. Don't expose your Supabase project to
     people you don't want touching the raw database directly.
3. Go to **Settings → API** and copy:
   - `Project URL` → this is your `SUPABASE_URL`
   - `anon public` key → this is your `SUPABASE_ANON_KEY`

## 2. Configure the app

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
FLASK_SECRET_KEY=some-long-random-string
```

(`FLASK_SECRET_KEY` isn't from Supabase — make up any random string yourself;
it's used to sign session cookies.)

## 3. Install and run locally

```bash
python -m pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## 4. Try it out

1. Type your **name**.
2. **Create a reunion** — give it a name. You'll land on the Overview page,
   which shows your new **plan code** and **edit code**.
3. Share the **plan code** with everyone (so they can view the board) and
   the **edit code** only with people you want to be able to make changes.
4. Anyone who wants to view: go to the home page, type their name, enter
   the plan code under "Enter an existing reunion."
5. Anyone who wants to *edit*: once on the board, there's a bar near the
   top — "Enter the edit code to make changes" — typing the correct code
   unlocks claiming tasks, adding events, posting notes/comments, etc. for
   that visit.

## How access control works

There's no database-level row security tied to a login (there's no login).
Instead, every write route in `board_routes.py` checks
`can_edit(reunion_id)`, which just checks whether this browser session
entered the right edit code for that specific reunion. Read-only routes
only require a name. Keep in mind: anyone holding a code can act as
"anyone" under whatever name they type — there's no verification tying a
name to a person.

## Project structure

```
app.py                 — Flask entry point, registers blueprints
config.py              — Supabase client setup, reads .env
access_helpers.py      — code generation, lookups, can_edit(), name_required
access_routes.py       — home (name entry), create/enter reunion, unlock editing
board_routes.py        — overview, tasks, events, calendar, notes, people, comments
templates/             — Jinja HTML templates
static/css/style.css   — all styling
supabase_schema.sql    — run this once in the Supabase SQL editor
.env.example           — copy to .env and fill in your keys
requirements.txt
```

## Deploying for real (so people can use it from anywhere)

Deploy to any host that runs a Python web app, e.g.:

- **Render** (render.com) — "New Web App" → connect repo → set the three
  env vars from `.env` → start command: `gunicorn app:app`
- **Railway** (railway.app) — similar one-click flow
- **Fly.io** — more control, still simple for Flask apps

Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `FLASK_SECRET_KEY` as
environment variables on that platform (don't commit your real `.env`).

## Limitations / things you may want to add next

- No real identity verification — anyone with a code can claim to be
  anyone by typing a different name.
- No real-time push updates — pages refresh on navigation, not live.
- No email invites — sharing is by giving out the plan/edit codes directly.
- No file/photo uploads yet (Supabase Storage could be added for this).
