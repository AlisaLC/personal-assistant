from .static import static_router
from .profile import profile_router
from .auth import auth_router
from .notes import notes_router

__all__ = ["static_router", "profile_router", "auth_router", "notes_router"]
