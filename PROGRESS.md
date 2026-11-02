# CampusConnect — Build Progress Tracker

> **HOW TO RESUME:** Upload this whole `campusconnect/` folder (or at least this file + the
> synopsis PDF) to a new chat and say: *"Continue the CampusConnect build from PROGRESS.md."*
> Pick up at the first unchecked `[ ]` item. Do NOT redo checked items. Follow the
> "Contract" section so new files stay consistent with existing ones.

Last updated: 2026-11-02 · Status: IN PROGRESS

## Source material
- Synopsis: `DBMS_lab_mini_project_synopsis.pdf` (CampusConnect: Student Club & Event Management System,
  UVCE Bengaluru, MySQL 8.0, 3NF, triggers, stored procedures, views, 7 tables per ER diagram).
- Reference: classmate's "netops" repo (txt). Used ONLY for architecture/stack, not domain.
  Mirrored: docker-compose (mysql+backend+frontend), FastAPI + raw aiomysql (no ORM, all SQL in
  `db/queries.py`), Pydantic models, routers, React 18 + TS + Vite + Tailwind + react-query + axios,
  nginx frontend image, database/ folder with README + explanation.
  Dropped (not relevant): collector, simulator, RAG/LLM, 3D topology, alembic.

## Contract (decisions — keep consistent!)
**Tables (7, per ER):** students, clubs, club_memberships, venues, events, event_registrations, event_feedback
- PKs: `student_id, club_id, membership_id, venue_id, event_id, registration_id, feedback_id` (INT UNSIGNED AI)
- Enums: club.category/status, membership_role(MEMBER,PRESIDENT,VICE_PRESIDENT,SECRETARY,TREASURER),
  membership_status(ACTIVE,INACTIVE,LEFT), event_status(UPCOMING,ONGOING,COMPLETED,CANCELLED),
  registration_status(REGISTERED,WAITLISTED,CANCELLED), attendance_status(PENDING,PRESENT,ABSENT)
- DB name/user/pass default: `campusconnect` / `campusconnect` / `campusconnect`
- Custom SQLSTATE 45000 errnos from triggers/procs: **51001 not found→404, 51002 conflict→409, 51003 rule violation→422**
- Seed mode: `SET @cc_seed_mode = 1;` bypasses time-based checks (used only in seed file)
- Waitlist promotion happens in stored proc `sp_cancel_registration` (MySQL triggers can't update their own table)
- API prefix `/api/v1`; backend :8000, frontend nginx :3000 (dev vite :5173), mysql :3306
- Project root: `campusconnect/`

## Phases
### P0 Analysis
- [x] P0.1 Read synopsis + reference repo, decide architecture
- [x] P0.2 Create PROGRESS.md

### P1 Database (database/schema)
- [x] P1.1 `01_schema.sql` — tables, constraints, indexes
- [x] P1.2 `02_triggers.sql`
- [x] P1.3 `03_procedures.sql` (+ functions)
- [x] P1.4 `04_views.sql`
- [x] P1.5 `05_scheduler.sql` (MySQL EVENT to auto-sync event status)
- [x] P1.6 `seeds/generate_seed.py` + `seeds/seed_data.sql`
- [x] P1.7 `queries/reports.sql` (report queries)
- [x] P1.8 `tests/selftest.sql` (trigger/constraint self-test procedure)

### P2 Backend (FastAPI + aiomysql)
- [x] P2.1 config, core (errors w/ MySQL errno mapping, logging), db (pool, helpers incl. call_proc)
- [x] P2.2 models (pydantic)
- [x] P2.3 db/queries.py
- [ ] P2.4 routers: health, students, clubs, venues, events, registrations/feedback, reports
- [ ] P2.5 main.py, requirements, Dockerfile, tests (pure-pydantic/unit)

### P3 Frontend (React + TS + Vite + Tailwind)
- [ ] P3.1 config files (package.json, vite, tailwind, tsconfig, nginx, Dockerfile, index.html)
- [ ] P3.2 types, api services, hooks, utils
- [ ] P3.3 common components + layout
- [ ] P3.4 pages: Dashboard, Students, Clubs(+detail), Events(+detail), Venues, Reports

### P4 Packaging & docs
- [ ] P4.1 docker-compose.yml, .env.example, .gitignore
- [ ] P4.2 root README.md (run instructions)
- [ ] P4.3 database/README.md + database/explanation.md (ER→tables, 3NF proof, design choices)
- [ ] P4.4 docs/VIVA_QA.md (likely viva questions)

### P5 Final QA
- [ ] P5.1 python py_compile all backend files; grep consistency of table/column names across SQL/queries/models/TS types
- [ ] P5.2 zip deliverable + final summary

## Notes / known limitations
- Tooling gotcha: the sandbox shell is `sh` (no `{a,b}` brace expansion) — create dirs one by one. `create_file` auto-creates parents.
- Phase 1 (database) is COMPLETE: 7 tables, 3 helper procs, 6 triggers (+1 after-update cascade), 3 functions,
  9 procs, 10 views, 1 scheduler EVENT, seed (generated), 20 report queries, selftest + demo scripts.
- Views available to the backend: v_club_membership_counts, v_club_officers, v_event_overview (master),
  v_upcoming_events, v_event_popularity, v_event_attendance, v_event_feedback_summary, v_club_activity_report,
  v_student_activity, v_event_roster.
- Procs (all return a result set on success): sp_register_for_event(student,event), sp_cancel_registration(reg),
  sp_mark_attendance(reg,'PRESENT|ABSENT|PENDING'), sp_complete_event(event), sp_cancel_event(event),
  sp_event_summary(event), sp_join_club(student,club), sp_leave_club(membership), sp_assign_officer(club,student,role),
  sp_submit_feedback(student,event,rating,comments).
- Sandbox had no MySQL, no network → SQL & app code could not be executed here. Run the self-test
  (`database/tests/selftest.sql`) and `docker compose up --build` on your machine; report any error text
  back and it will be fixed.
