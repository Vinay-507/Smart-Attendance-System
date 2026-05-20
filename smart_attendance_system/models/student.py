from dataclasses import dataclass


@dataclass
class Student:
    """Simple student data object used between routes and repositories."""

    roll_number: str
    full_name: str
    email: str | None = None
    class_name: str | None = None
    section: str | None = None
