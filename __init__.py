"""API routers."""
from app.routers.clubs import memberships_router
from app.routers.clubs import router as clubs_router
from app.routers.events import feedback_router, registrations_router
from app.routers.events import router as events_router
from app.routers.health import router as health_router
from app.routers.reports import router as reports_router
from app.routers.students import router as students_router
from app.routers.venues import router as venues_router

__all__ = [
    "clubs_router", "memberships_router", "events_router", "registrations_router",
    "feedback_router", "health_router", "reports_router", "students_router", "venues_router",
]
