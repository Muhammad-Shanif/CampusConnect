# CampusConnect API

FastAPI application using `aiomysql` and parameterized SQL (no ORM). Start with `uvicorn app.main:app --reload --port 8000` after setting the MySQL environment variables. Open `/docs` for the interactive API reference.

The service exposes `/health` and `/api/v1/*`. Database routines are invoked for membership, officer, registration, attendance, completion/cancellation and feedback workflows; list and CRUD operations use parameterized SQL against the seven project tables and reporting views.
