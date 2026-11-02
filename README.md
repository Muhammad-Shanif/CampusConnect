# CampusConnect — Student Club & Event Management System

A full-stack DBMS mini project for UVCE. The app centralises students, clubs, club memberships, venues, events, event registrations and feedback in a normalized MySQL 8.0 database.

## Stack
- **Database:** MySQL 8.0 (7 relational tables, constraints, indexes, triggers, stored procedures, views and a scheduled event)
- **Backend:** FastAPI + `aiomysql`, parameterized raw SQL (no ORM)
- **Frontend:** React 18, TypeScript, Vite, Tailwind-ready styling, TanStack Query, Axios and Recharts/Lucide dependencies
- **Packaging:** Docker Compose + Nginx

## Run with Docker (recommended)
1. Install Docker Desktop and start Docker.
2. In this folder, copy `.env.example` to `.env` (the defaults are for local demonstration only).
3. Run:
   ```bash
   docker compose up --build
   ```
4. Open:
   - Frontend: http://localhost:3000
   - API docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

The first MySQL startup initializes the schema, triggers, procedures, views, scheduler and demo data. Initialization scripts run only when the MySQL data volume is empty. To rebuild from a clean database, run `docker compose down -v` and then `docker compose up --build` (this permanently deletes the local database volume).

## Run without Docker
### Database
Run the SQL files in this order in MySQL Workbench or the MySQL CLI:
`database/schema/01_schema.sql` → `02_triggers.sql` → `03_procedures.sql` → `04_views.sql` → `05_scheduler.sql` → `database/seeds/seed_data.sql`.

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
uvicorn app.main:app --reload --port 8000
```
### Frontend
```bash
cd frontend
npm install
# optional: create .env with VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev
```
Open http://localhost:5173.

## Main features
- Student directory: create, search, update and delete student records; view club and event activity through API routes.
- Clubs: CRUD, membership join/leave/status, officer assignment and club events.
- Venues: CRUD and venue event listing.
- Events: CRUD, registration and waitlisting, cancellation/promotion, attendance marking, completion/cancellation, event summary and feedback.
- Reports: dashboard totals, club membership/activity, officers, event popularity/attendance, feedback, student activity, department participation and venue utilisation.

## API
All application endpoints use `/api/v1`. Interactive OpenAPI docs are at `/docs`.

## Important notes
- This is a local academic demo. Authentication/authorization is not implemented; do not expose it publicly.
- Demo DB credentials are intentionally simple. Change them before any non-local deployment.
- SQL triggers and procedures are the source of truth for business rules such as registration deadlines, capacity checks, waitlist promotion and attendance-gated feedback.
- The SQL scheduler requires MySQL event-scheduler support and appropriate privileges. If your MySQL account cannot enable it, start the server with `event_scheduler=ON` or omit `05_scheduler.sql` for the demo; the rest of the app works.
- Database initialization files are idempotent only for fresh initialization. For schema changes to an existing volume, apply the relevant SQL migration manually.

## Project structure
```text
campusconnect/
├── backend/                 # FastAPI service
├── database/                # schema, procedures, views, seeds and tests
├── frontend/                # React + TypeScript UI
├── docs/                    # viva and design notes
├── docker-compose.yml
└── README.md
```
