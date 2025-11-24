from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.activities import router as activities_router

__all__ = ["auth_router", "clients_router", "activities_router"]