from .admin import admin_router
from .getlogs import router as getlogs_router
from .gettickets import router as gettickets_router
from .start import router as start_router
from .status import router as status_router

__all__ = ["start_router", "status_router", "getlogs_router", "gettickets_router", "admin_router"]
