import re

IDENTIFIER_MAX_LENGTH = 100


def normalize_identifier(student_name: str) -> str:
    """Reduce a student name to the identifier part of a student code."""
    return re.sub(r"[^a-z0-9]", "", student_name.lower())[:IDENTIFIER_MAX_LENGTH]


def build_student_code(school_number: int, class_number: int, student_name: str) -> str:
    """Build the structured student code: [school number][class number][identifier].

    Example: school 6, class 7, "Harsh Khatri" -> "0607harshkhatri".
    """
    identifier = normalize_identifier(student_name)
    if not identifier:
        raise ValueError("Student name must contain letters or digits to build a student code")
    return f"{school_number:02d}{class_number:02d}{identifier}"
