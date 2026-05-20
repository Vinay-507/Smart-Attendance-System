from dataclasses import dataclass


@dataclass
class AttendanceDraftRow:
    """Editable attendance status for one registered student."""

    student_id: int
    roll_number: str
    full_name: str
    class_name: str | None
    section: str | None
    predicted_present: bool
    confidence: float | None
