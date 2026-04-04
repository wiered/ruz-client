from __future__ import annotations

from .groups import GroupSearchHit, GroupsEndpoints, RuzGroupSearchItem
from .lecturers import Lecturer
from .schedule import ScheduleEndpoints, UserScheduleLesson
from .search import SearchEndpoints, search_group_filters
from .users import UserCreate, UserRead, UserUpdate, UsersEndpoints

__all__ = [
    "GroupSearchHit",
    "GroupsEndpoints",
    "RuzGroupSearchItem",
    "Lecturer",
    "ScheduleEndpoints",
    "SearchEndpoints",
    "search_group_filters",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserScheduleLesson",
    "UsersEndpoints",
]
