# CampusConnect frontend

React 18 + TypeScript + Vite interface. `npm install && npm run dev` starts the local development server at `http://localhost:5173`. Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` in a local `.env` file when running the API separately. In Docker, Nginx proxies `/api/` to the backend service.

The interface includes a dashboard, student/club/event/venue management tables with create/edit/delete forms, upcoming events and a database-view-backed reports explorer.
