from __future__ import annotations

from .disciplines import Discipline, DisciplinesEndpoints
from .groups import (
    GroupCreate,
    GroupRead,
    GroupSearchHit,
    GroupsEndpoints,
    GroupUpdate,
    RuzGroupSearchItem,
)
from .lecturers import Lecturer
from .schedule import ScheduleEndpoints, UserScheduleLesson
from .search import SearchEndpoints, search_group_filters
from .users import UNSET, UserCreate, UserRead, UsersEndpoints, UserUpdate

__all__ = [
    "GroupCreate",
    "GroupRead",
    "GroupSearchHit",
    "GroupUpdate",
    "GroupsEndpoints",
    "RuzGroupSearchItem",
    "Lecturer",
    "ScheduleEndpoints",
    "SearchEndpoints",
    "search_group_filters",
    "UNSET",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserScheduleLesson",
    "UsersEndpoints",
    "DisciplinesEndpoints",
    "Discipline",
]
