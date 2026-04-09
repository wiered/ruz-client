from .client import (
    ClientConfig,
    RuzClient,
    LecturersEndpoints,
)
from .errors import RuzAuthError, RuzClientError, RuzHttpError
from .http.endpoints import (
    GroupSearchHit,
    GroupsEndpoints,
    RuzGroupSearchItem,
    Lecturer,
    ScheduleEndpoints,
    SearchEndpoints,
    UserCreate,
    UserRead,
    UserUpdate,
    UserScheduleLesson,
    UsersEndpoints,
)

__all__ = [
    "ClientConfig",
    "RuzClient",
    "Lecturer",
    "RuzClientError",
    "RuzAuthError",
    "RuzHttpError",
    "GroupSearchHit",
    "GroupsEndpoints",
    "RuzGroupSearchItem",
    "ScheduleEndpoints",
    "SearchEndpoints",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserScheduleLesson",
    "UsersEndpoints",
]
