"""Analytics service — computes assessment, school, student, and question analytics.

All functions accept a SQLAlchemy Session and return plain dicts/pydantic-ready
data. No FastAPI dependency injection here — the router calls these functions.

Key design decisions:
- Only COMPLETED AssessmentAttempt records are included.
- Competition ranking for ties (1, 2, 2, 4).
- Percentile = (count scoring strictly lower / total in scope) * 100.
- All aggregation is done in-memory after fetching the relevant rows.
- Student section is matched via current_class + current_section strings.
- Question identity is based on normalized (question_text, option_a-d) fingerprint.
"""

from decimal import Decimal
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Assessment,
    AssessmentAttempt,
    AttemptQuestion,
    AttemptStatus,
    Question,
    School,
    Student,
)


# ── Helpers ────────────────────────────────────────────────────────


def _to_float(val) -> float:
    """Convert Decimal/int/float to plain float."""
    if val is None:
        return 0.0
    return float(val)


def _competition_rank(percentages: list[float]) -> dict[float, int]:
    """Return {percentage -> rank} using competition ranking.

    Example: [82, 76, 76, 61] -> {82: 1, 76: 2, 61: 4}
    """
    sorted_unique = sorted(set(percentages), reverse=True)
    rank_map: dict[float, int] = {}
    rank = 1
    for pct in sorted_unique:
        rank_map[pct] = rank
        rank += 1
    return rank_map


def _percentile(target_pct: float, all_pcts: list[float]) -> float:
    """Percentile: (count scoring strictly lower / total) * 100.

    Students with equal percentages get the same percentile.
    """
    total = len(all_pcts)
    if total <= 1:
        return 0.0
    lower = sum(1 for p in all_pcts if p < target_pct)
    return round(lower / total * 100, 2)


def _normalize(text: str | None) -> str:
    """Normalize text for question identity comparison.

    Rules: None -> "", lowercase, strip, collapse whitespace.
    Does NOT remove punctuation.
    """
    if text is None:
        return ""
    return " ".join(text.lower().split())


def question_fingerprint(q: Question) -> tuple[str, str, str, str, str]:
    """Compute the five-field normalized fingerprint for a question.

    Returns (normalized_text, normalized_a, normalized_b, normalized_c, normalized_d).
    """
    return (
        _normalize(q.question_text),
        _normalize(q.option_a),
        _normalize(q.option_b),
        _normalize(q.option_c),
        _normalize(q.option_d),
    )


def _is_valid_fingerprint(fp: tuple[str, str, str, str, str]) -> bool:
    """A fingerprint is valid only if at least one field is non-empty."""
    return any(field != "" for field in fp)


def _domain_breakdown_from_attempts(
    attempts: list[AssessmentAttempt],
    school_id: int | None = None,
    class_number: int | None = None,
    section: str | None = None,
) -> list[dict]:
    """Compute domain breakdown across multiple attempts.

    If school/class/section filters are provided, attempts are pre-filtered
    before calling this function, so we just aggregate AttemptQuestion rows.
    """
    # Collect all AttemptQuestion rows from the given attempts
    domain_stats: dict[str, dict] = {}  # domain -> {correct, total}

    for att in attempts:
        for aq in att.questions:
            d = aq.domain
            if d not in domain_stats:
                domain_stats[d] = {"correct": 0, "total": 0}
            domain_stats[d]["total"] += 1
            if aq.is_correct:
                domain_stats[d]["correct"] += 1

    result = []
    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        total = stats["total"]
        correct = stats["correct"]
        pct = round(correct / total * 100, 2) if total > 0 else 0.0
        result.append({
            "domain": domain,
            "correct": correct,
            "total": total,
            "percentage": pct,
        })
    return result


# ── Core query helpers ─────────────────────────────────────────────


def _get_completed_attempts(
    db: Session,
    assessment_id: int,
    school_id: int | None = None,
    class_number: int | None = None,
    section: str | None = None,
) -> list[AssessmentAttempt]:
    """Fetch all COMPLETED attempts for an assessment, with optional filters.

    Eagerly loads: student (with school), questions (AttemptQuestion).
    """
    query = (
        db.query(AssessmentAttempt)
        .options(
            selectinload(AssessmentAttempt.student)
            .selectinload(Student.school),
            selectinload(AssessmentAttempt.questions),
        )
        .filter(
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
        )
    )

    if school_id is not None or class_number is not None or section is not None:
        query = query.join(Student, AssessmentAttempt.student_id == Student.id)
        if school_id is not None:
            query = query.filter(Student.school_id == school_id)
        if class_number is not None:
            query = query.filter(Student.current_class == class_number)
        if section is not None:
            query = query.filter(Student.current_section == section)

    return query.all()


def _verify_assessment(db: Session, assessment_id: int) -> Assessment:
    """Return assessment or raise ValueError."""
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.is_deleted.is_(False),
    ).first()
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")
    return assessment


def _verify_school(db: Session, school_id: int) -> School:
    """Return school or raise ValueError."""
    school = db.get(School, school_id)
    if not school:
        raise ValueError(f"School {school_id} not found")
    return school


def _verify_student_attempt(
    db: Session, assessment_id: int, student_id: int
) -> AssessmentAttempt:
    """Return the COMPLETED attempt for a student in an assessment, or raise."""
    att = (
        db.query(AssessmentAttempt)
        .options(
            selectinload(AssessmentAttempt.student)
            .selectinload(Student.school),
            selectinload(AssessmentAttempt.questions),
        )
        .filter(
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.student_id == student_id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
        )
        .first()
    )
    if not att:
        raise ValueError(
            f"No completed attempt found for student {student_id} "
            f"in assessment {assessment_id}"
        )
    return att


# ── Analytics functions ────────────────────────────────────────────


def assessment_overview(
    db: Session,
    assessment_id: int,
    school_id: int | None = None,
    class_number: int | None = None,
    section: str | None = None,
) -> dict:
    """Assessment-wide analytics with optional filters.

    Returns summary stats, domain breakdown, and school summaries.
    """
    _verify_assessment(db, assessment_id)

    attempts = _get_completed_attempts(
        db, assessment_id, school_id=school_id,
        class_number=class_number, section=section,
    )

    if not attempts:
        return {
            "assessment_id": assessment_id,
            "total_students_assessed": 0,
            "average_score": 0.0,
            "average_percentage": 0.0,
            "highest_percentage": 0.0,
            "lowest_percentage": 0.0,
            "domains": [],
            "schools": [],
        }

    percentages = [_to_float(a.percentage) for a in attempts]
    scores = [a.score for a in attempts]

    # Domain breakdown (across all filtered attempts)
    domains = _domain_breakdown_from_attempts(attempts)

    # School summaries: group attempts by school
    school_groups: dict[int, list[AssessmentAttempt]] = {}
    for att in attempts:
        sid = att.student.school_id
        school_groups.setdefault(sid, []).append(att)

    school_summaries = []
    for sid, school_atts in school_groups.items():
        school_pct = [_to_float(a.percentage) for a in school_atts]
        school_scores = [a.score for a in school_atts]
        school_domains = _domain_breakdown_from_attempts(school_atts)
        school_summaries.append({
            "school_id": sid,
            "school_name": school_atts[0].student.school.name,
            "students_assessed": len(school_atts),
            "average_score": round(sum(school_scores) / len(school_scores), 2),
            "average_percentage": round(sum(school_pct) / len(school_pct), 2),
            "highest_percentage": max(school_pct),
            "lowest_percentage": min(school_pct),
            "domains": school_domains,
        })

    # Rank schools by average percentage
    school_avgs = {s["school_id"]: s["average_percentage"] for s in school_summaries}
    school_rank_map = _competition_rank(list(school_avgs.values()))
    # Map rank back by value (not by school_id)
    avg_to_rank = _competition_rank([s["average_percentage"] for s in school_summaries])
    for s in school_summaries:
        s["school_rank"] = avg_to_rank.get(s["average_percentage"], 1)

    # Sort by rank then name
    school_summaries.sort(key=lambda s: (s["school_rank"], s["school_name"]))

    return {
        "assessment_id": assessment_id,
        "total_students_assessed": len(attempts),
        "average_score": round(sum(scores) / len(scores), 2),
        "average_percentage": round(sum(percentages) / len(percentages), 2),
        "highest_percentage": max(percentages),
        "lowest_percentage": min(percentages),
        "domains": domains,
        "schools": school_summaries,
    }


def school_analytics(
    db: Session,
    assessment_id: int,
    school_id: int,
) -> dict:
    """Analytics for a specific school in a specific assessment."""
    _verify_assessment(db, assessment_id)
    school = _verify_school(db, school_id)

    attempts = _get_completed_attempts(db, assessment_id, school_id=school_id)

    # Get all-school attempts for ranking context
    all_attempts = _get_completed_attempts(db, assessment_id)

    if not attempts:
        return {
            "assessment_id": assessment_id,
            "school_id": school_id,
            "school_name": school.name,
            "students_assessed": 0,
            "average_score": 0.0,
            "average_percentage": 0.0,
            "highest_percentage": 0.0,
            "lowest_percentage": 0.0,
            "domains": [],
            "school_rank": None,
            "students": [],
        }

    percentages = [_to_float(a.percentage) for a in attempts]
    scores = [a.score for a in attempts]
    domains = _domain_breakdown_from_attempts(attempts)

    # School rank among all schools
    all_school_groups: dict[int, list[float]] = {}
    for att in all_attempts:
        sid = att.student.school_id
        all_school_groups.setdefault(sid, []).append(_to_float(att.percentage))

    all_school_avgs = [
        round(sum(pcts) / len(pcts), 2) for pcts in all_school_groups.values()
    ]
    avg_to_rank = _competition_rank(all_school_avgs)
    school_avg = round(sum(percentages) / len(percentages), 2)
    school_rank = avg_to_rank.get(school_avg, 1)

    # Student list
    students = []
    for att in attempts:
        students.append({
            "student_id": att.student_id,
            "student_name": att.student.student_name,
            "roll_number": att.student.roll_number,
            "score": att.score,
            "total_questions": att.total_questions,
            "percentage": _to_float(att.percentage),
        })
    students.sort(key=lambda s: s["percentage"], reverse=True)

    return {
        "assessment_id": assessment_id,
        "school_id": school_id,
        "school_name": school.name,
        "students_assessed": len(attempts),
        "average_score": round(sum(scores) / len(scores), 2),
        "average_percentage": school_avg,
        "highest_percentage": max(percentages),
        "lowest_percentage": min(percentages),
        "domains": domains,
        "school_rank": school_rank,
        "students": students,
    }


def student_analytics(
    db: Session,
    assessment_id: int,
    student_id: int,
) -> dict:
    """Analytics for a specific student in a specific assessment."""
    assessment = _verify_assessment(db, assessment_id)

    # Verify student exists
    student = db.get(Student, student_id)
    if not student:
        raise ValueError(f"Student {student_id} not found")

    att = _verify_student_attempt(db, assessment_id, student_id)

    # Domain breakdown for this student
    domain_stats: dict[str, dict] = {}
    for aq in att.questions:
        d = aq.domain
        if d not in domain_stats:
            domain_stats[d] = {"correct": 0, "total": 0}
        domain_stats[d]["total"] += 1
        if aq.is_correct:
            domain_stats[d]["correct"] += 1

    domains = []
    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        total = stats["total"]
        correct = stats["correct"]
        pct = round(correct / total * 100, 2) if total > 0 else 0.0
        domains.append({
            "domain": domain,
            "correct": correct,
            "total": total,
            "percentage": pct,
        })

    # All attempts in this assessment for ranking/percentile
    all_attempts = _get_completed_attempts(db, assessment_id)
    all_percentages = [_to_float(a.percentage) for a in all_attempts]

    # School attempts for school ranking
    school_attempts = [
        a for a in all_attempts if a.student.school_id == student.school_id
    ]
    school_percentages = [_to_float(a.percentage) for a in school_attempts]

    # School average
    school_avg = (
        round(sum(school_percentages) / len(school_percentages), 2)
        if school_percentages else 0.0
    )

    # Overall average
    overall_avg = (
        round(sum(all_percentages) / len(all_percentages), 2)
        if all_percentages else 0.0
    )

    # Competition ranking — within school (student vs schoolmates)
    school_rank_map = _competition_rank(school_percentages)
    school_rank = school_rank_map.get(_to_float(att.percentage), 1)

    # Competition ranking — overall (student vs all)
    overall_rank_map = _competition_rank(all_percentages)
    overall_rank = overall_rank_map.get(_to_float(att.percentage), 1)

    # Percentile — school
    school_pct = _percentile(_to_float(att.percentage), school_percentages)

    # Percentile — overall
    overall_pct = _percentile(_to_float(att.percentage), all_percentages)

    # School domain averages (across all school students in this assessment)
    school_domain_breakdown = _domain_breakdown_from_attempts(school_attempts)

    # Overall domain averages (across all students in this assessment)
    overall_domain_breakdown = _domain_breakdown_from_attempts(all_attempts)

    return {
        "assessment_id": assessment_id,
        "student_id": student_id,
        "student_name": student.student_name,
        "roll_number": student.roll_number,
        "school_id": student.school_id,
        "school_name": student.school.name,
        "current_class": student.current_class,
        "current_section": student.current_section,
        "score": att.score,
        "total_questions": att.total_questions,
        "wrong": att.total_questions - att.score,
        "percentage": _to_float(att.percentage),
        "domains": domains,
        "school_domains": school_domain_breakdown,
        "overall_domains": overall_domain_breakdown,
        "school_average": school_avg,
        "overall_average": overall_avg,
        "school_rank": school_rank,
        "overall_rank": overall_rank,
        "school_percentile": school_pct,
        "overall_percentile": overall_pct,
        "assessment_name": assessment.name,
        "assessment_type": assessment.assessment_type.value,
        "academic_year_name": assessment.academic_year.name if assessment.academic_year else "",
    }


# ── Question Analytics (M6B) ──────────────────────────────────────


def question_analytics(
    db: Session,
    assessment_id: int,
    school_id: int | None = None,
    class_number: int | None = None,
    section: str | None = None,
) -> dict:
    """Per-question analytics for an assessment with optional scope filters.

    Returns a list of question stats: assessed, correct, wrong, percentage.
    """
    assessment = _verify_assessment(db, assessment_id)

    attempts = _get_completed_attempts(
        db, assessment_id,
        school_id=school_id, class_number=class_number, section=section,
    )

    # Build question stats from the AttemptQuestion rows
    q_stats: dict[int, dict] = {}  # question_id -> {correct, total, ...}
    for att in attempts:
        for aq in att.questions:
            qid = aq.question_id
            if qid not in q_stats:
                q_stats[qid] = {"correct": 0, "total": 0}
            q_stats[qid]["total"] += 1
            if aq.is_correct:
                q_stats[qid]["correct"] += 1

    # Build ordered list from assessment questions
    questions = sorted(assessment.questions, key=lambda q: q.question_number)
    result_questions = []
    for q in questions:
        stats = q_stats.get(q.id, {"correct": 0, "total": 0})
        assessed = stats["total"]
        correct = stats["correct"]
        wrong = assessed - correct
        pct = round(correct / assessed * 100, 2) if assessed > 0 else 0.0
        result_questions.append({
            "question_id": q.id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "domain": q.domain,
            "assessed": assessed,
            "correct": correct,
            "wrong": wrong,
            "percentage": pct,
        })

    return {
        "assessment_id": assessment_id,
        "total_students_assessed": len(attempts),
        "scope": {
            "school_id": school_id,
            "class_number": class_number,
            "section": section,
        },
        "questions": result_questions,
    }


def question_history(
    db: Session,
    assessment_id: int,
    question_id: int,
    school_id: int | None = None,
    class_number: int | None = None,
    section: str | None = None,
) -> dict:
    """Historical performance for a specific question across assessments.

    Finds questions with identical normalized fingerprints in other assessments.
    For each historical appearance, computes scoped stats.
    """
    assessment = _verify_assessment(db, assessment_id)

    # Verify question belongs to this assessment
    target_q = None
    for q in assessment.questions:
        if q.id == question_id:
            target_q = q
            break
    if target_q is None:
        raise ValueError(
            f"Question {question_id} not found in assessment {assessment_id}"
        )

    fp = question_fingerprint(target_q)
    if not _is_valid_fingerprint(fp):
        return {
            "question_id": question_id,
            "question_number": target_q.question_number,
            "question_text": target_q.question_text,
            "domain": target_q.domain,
            "fingerprint_valid": False,
            "fingerprint_match_count": 0,
            "current": {
                "assessment_id": assessment_id,
                "assessment_name": assessment.name,
                "academic_year": assessment.academic_year.name
                if assessment.academic_year else "",
                "assessment_type": assessment.assessment_type.value,
                "question_number": target_q.question_number,
                "assessed": 0,
                "correct": 0,
                "percentage": 0.0,
            },
            "history": [],
        }

    # Find all questions with matching fingerprint across non-deleted assessments
    all_questions = (
        db.query(Question)
        .join(Assessment, Question.assessment_id == Assessment.id)
        .filter(Assessment.is_deleted.is_(False))
        .all()
    )
    matching_questions = [
        q for q in all_questions
        if q.id != question_id and question_fingerprint(q) == fp
    ]

    # Get current assessment stats for this question
    current_attempts = _get_completed_attempts(
        db, assessment_id,
        school_id=school_id, class_number=class_number, section=section,
    )
    current_correct = 0
    current_assessed = 0
    for att in current_attempts:
        for aq in att.questions:
            if aq.question_id == question_id:
                current_assessed += 1
                if aq.is_correct:
                    current_correct += 1
    current_pct = (
        round(current_correct / current_assessed * 100, 2)
        if current_assessed > 0 else 0.0
    )

    # Build history from matching questions
    history = []
    for mq in matching_questions:
        hist_attempts = _get_completed_attempts(
            db, mq.assessment_id,
            school_id=school_id, class_number=class_number, section=section,
        )
        if not hist_attempts:
            continue  # No students in scope — omit this appearance

        h_correct = 0
        h_assessed = 0
        for att in hist_attempts:
            for aq in att.questions:
                if aq.question_id == mq.id:
                    h_assessed += 1
                    if aq.is_correct:
                        h_correct += 1

        if h_assessed == 0:
            continue

        h_pct = round(h_correct / h_assessed * 100, 2)
        hist_assessment = mq.assessment
        history.append({
            "assessment_id": hist_assessment.id,
            "assessment_name": hist_assessment.name,
            "academic_year": hist_assessment.academic_year.name
            if hist_assessment.academic_year else "",
            "assessment_type": hist_assessment.assessment_type.value,
            "question_number": mq.question_number,
            "assessed": h_assessed,
            "correct": h_correct,
            "percentage": h_pct,
        })

    # Sort history by academic year descending, then assessment type
    history.sort(key=lambda h: (h["academic_year"], h["assessment_type"]), reverse=True)

    return {
        "question_id": question_id,
        "question_number": target_q.question_number,
        "question_text": target_q.question_text,
        "domain": target_q.domain,
        "fingerprint_valid": True,
        "fingerprint_match_count": len(matching_questions),
        "current": {
            "assessment_id": assessment_id,
            "assessment_name": assessment.name,
            "academic_year": assessment.academic_year.name
            if assessment.academic_year else "",
            "assessment_type": assessment.assessment_type.value,
            "question_number": target_q.question_number,
            "assessed": current_assessed,
            "correct": current_correct,
            "percentage": current_pct,
        },
        "history": history,
    }


# ── M7: Student Report Questions ──────────────────────────────────


def student_report_questions(
    db: Session,
    assessment_id: int,
    student_id: int,
) -> dict:
    """Per-question breakdown for a single student's attempt.

    Returns the AttemptQuestion rows joined with Question data for the
    student report's question analysis table. Includes option text and
    school-level "% got right" for each question.
    """
    _verify_assessment(db, assessment_id)

    student = db.get(Student, student_id)
    if not student:
        raise ValueError(f"Student {student_id} not found")

    att = _verify_student_attempt(db, assessment_id, student_id)

    # Fetch all questions for this assessment
    from app.models import Question
    questions = (
        db.query(Question)
        .filter(Question.assessment_id == assessment_id)
        .all()
    )
    q_by_id = {q.id: q for q in questions}

    # Get all school-level attempts for "% got right" calculation
    school_attempts = _get_completed_attempts(db, assessment_id, school_id=student.school_id)

    # Build per-question correct counts from school attempts
    q_correct_counts: dict[int, int] = {}  # question_id -> correct count
    q_total_counts: dict[int, int] = {}    # question_id -> total count
    for sa in school_attempts:
        for saq in sa.questions:
            qid = saq.question_id
            q_total_counts[qid] = q_total_counts.get(qid, 0) + 1
            if saq.is_correct:
                q_correct_counts[qid] = q_correct_counts.get(qid, 0) + 1

    items = []
    for aq in sorted(att.questions, key=lambda a: q_by_id.get(a.question_id, a).question_number):
        q = q_by_id.get(aq.question_id)
        total = q_total_counts.get(aq.question_id, 0)
        correct = q_correct_counts.get(aq.question_id, 0)
        pct_right = round(correct / total * 100, 1) if total > 0 else 0.0
        items.append({
            "question_number": q.question_number if q else 0,
            "question_text": q.question_text if q else None,
            "domain": aq.domain,
            "detected_answer": aq.detected_answer,
            "correct_answer": aq.correct_answer,
            "is_correct": aq.is_correct,
            "option_a": q.option_a if q else None,
            "option_b": q.option_b if q else None,
            "option_c": q.option_c if q else None,
            "option_d": q.option_d if q else None,
            "percent_correct": pct_right,
        })

    return {
        "assessment_id": assessment_id,
        "student_id": student_id,
        "questions": items,
    }
