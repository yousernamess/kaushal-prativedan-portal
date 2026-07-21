import io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ----------------------------------------------------
# Colors
# ----------------------------------------------------
BRAND_DARK   = colors.HexColor("#1a1a2e")
BRAND_BLUE   = colors.HexColor("#16213e")
BRAND_ACCENT = colors.HexColor("#0f3460")
GREEN        = colors.HexColor("#2ecc71")
RED          = colors.HexColor("#e74c3c")
GREY         = colors.HexColor("#95a5a6")
LIGHT_GREY   = colors.HexColor("#f2f2f2")
WHITE        = colors.white
DARK_TEXT    = colors.HexColor("#2c3e50")


# ----------------------------------------------------
# Spider chart
# ----------------------------------------------------
def make_spider_chart(skill_scores, class_skill_scores=None):
    """
    skill_scores       : { "Application": {"score": 4, "total": 5}, ... }
    class_skill_scores : { "Application": {"score": 3.2, "total": 5}, ... } or None

    Returns a BytesIO PNG image.
    """
    skills  = list(skill_scores.keys())
    n       = len(skills)
    angles  = [math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    angles.append(angles[0])

    student_vals = [
        skill_scores[s]["score"] / skill_scores[s]["total"]
        for s in skills
    ]
    student_vals.append(student_vals[0])

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("white")

    # Grid
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(0)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="grey")
    ax.set_xticks([math.pi / 2 + 2 * math.pi * i / n for i in range(n)])
    ax.set_xticklabels(skills, fontsize=9, fontweight="bold", color="#2c3e50")

    # Class average
    if class_skill_scores:
        class_vals = [
            class_skill_scores[s]["score"] / class_skill_scores[s]["total"]
            for s in skills
        ]
        class_vals.append(class_vals[0])
        ax.plot(
            [math.pi / 2 + 2 * math.pi * i / n for i in range(n + 1)],
            class_vals,
            color="#e74c3c", linewidth=1.5, linestyle="--", label="Class Avg"
        )
        ax.fill(
            [math.pi / 2 + 2 * math.pi * i / n for i in range(n + 1)],
            class_vals,
            color="#e74c3c", alpha=0.1
        )

    # Student
    ax.plot(
        [math.pi / 2 + 2 * math.pi * i / n for i in range(n + 1)],
        student_vals,
        color="#0f3460", linewidth=2, linestyle="-", label="Student"
    )
    ax.fill(
        [math.pi / 2 + 2 * math.pi * i / n for i in range(n + 1)],
        student_vals,
        color="#0f3460", alpha=0.2
    )

    if class_skill_scores:
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ----------------------------------------------------
# Report generator
# ----------------------------------------------------
def generate_report(
    student,
    result,
    exam_config,
    class_results,
    output_path=None
):
    """
    student      : { "name": "Rahul", "roll_number": "R001", "class": "6", "batch": "A" }
    result       : output of scorer.score()
    exam_config  : { "config_name": ..., "question_count": 15, "skill_map": {...}, "answer_key": {...} }
    class_results: list of scorer.score() outputs for all students in batch (for class stats)
    output_path  : file path string or None (returns BytesIO if None)

    Returns BytesIO or writes to output_path.
    """
    buf = io.BytesIO() if output_path is None else output_path
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles   = getSampleStyleSheet()
    elements = []

    # --------------------------------------------------
    # Styles
    # --------------------------------------------------
    title_style = ParagraphStyle(
        "title",
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=BRAND_DARK,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        fontSize=10,
        fontName="Helvetica",
        textColor=GREY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "section",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=10,
    )
    normal_style = ParagraphStyle(
        "normal_custom",
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK_TEXT,
    )
    center_style = ParagraphStyle(
        "center_custom",
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK_TEXT,
        alignment=TA_CENTER,
    )

    # --------------------------------------------------
    # Header
    # --------------------------------------------------
    elements.append(Paragraph("Vigyan Express", title_style))
    elements.append(Paragraph("Kaushal Prativedan Portal — Student Report Card", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT, spaceAfter=10))

    # --------------------------------------------------
    # Student info table
    # --------------------------------------------------
    exam_type_label = "Baseline Exam" if result.get("exam_type") == "baseline" else "Endline Exam"
    percentage      = round(result["total_score"] / result["total_marks"] * 100, 1)

    info_data = [
        [
            Paragraph(f"<b>Name:</b> {student['name']}", normal_style),
            Paragraph(f"<b>Roll No:</b> {student['roll_number']}", normal_style),
            Paragraph(f"<b>Class:</b> {student['class']}", normal_style),
        ],
        [
            Paragraph(f"<b>Batch:</b> {student['batch']}", normal_style),
            Paragraph(f"<b>Exam Type:</b> {exam_type_label}", normal_style),
            Paragraph(f"<b>Config:</b> {exam_config['config_name']}", normal_style),
        ],
    ]

    info_table = Table(info_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",        (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, GREY),
        ("PADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------
    # Score summary bar
    # --------------------------------------------------
    score_data = [[
        Paragraph(f"<b>Total Score</b><br/>{result['total_score']} / {result['total_marks']}", center_style),
        Paragraph(f"<b>Percentage</b><br/>{percentage}%", center_style),
        Paragraph(f"<b>Questions</b><br/>{result['total_marks']}", center_style),
        Paragraph(f"<b>Correct</b><br/>{result['total_score']}", center_style),
        Paragraph(f"<b>Incorrect / Unanswered</b><br/>{result['total_marks'] - result['total_score']}", center_style),
    ]]

    score_table = Table(score_data, colWidths=[3.6 * cm] * 5)
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, -1), WHITE),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",    (0, 0), (-1, -1), 10),
        ("BOX",        (0, 0), (-1, -1), 0.5, BRAND_DARK),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, BRAND_DARK),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------
    # Skill scores + Spider chart side by side
    # --------------------------------------------------

    # Compute class average skill scores
    class_skill_scores = None
    if class_results:
        class_skill_scores = {}
        for skill in result["skill_scores"]:
            total_skill_score = sum(
                r["skill_scores"][skill]["score"]
                for r in class_results
                if skill in r["skill_scores"]
            )
            total_skill_total = result["skill_scores"][skill]["total"]
            class_skill_scores[skill] = {
                "score": round(total_skill_score / len(class_results), 2),
                "total": total_skill_total,
            }

    # Skill table
    skill_header = [
        Paragraph("<b>Skill</b>", center_style),
        Paragraph("<b>Score</b>", center_style),
        Paragraph("<b>Out of</b>", center_style),
        Paragraph("<b>%</b>", center_style),
        Paragraph("<b>Class Avg</b>", center_style),
    ]
    skill_rows = [skill_header]
    for skill, data in result["skill_scores"].items():
        pct        = round(data["score"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        class_avg  = f"{round(class_skill_scores[skill]['score'], 1)}/{data['total']}" if class_skill_scores else "-"
        skill_rows.append([
            Paragraph(skill, normal_style),
            Paragraph(str(data["score"]), center_style),
            Paragraph(str(data["total"]), center_style),
            Paragraph(f"{pct}%", center_style),
            Paragraph(class_avg, center_style),
        ])

    skill_table = Table(skill_rows, colWidths=[3.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm, 2 * cm])
    skill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),  BRAND_ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, 0),  WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GREY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("BOX",        (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, GREY),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",    (0, 0), (-1, -1), 6),
    ]))

    # Spider chart
    spider_buf   = make_spider_chart(result["skill_scores"], class_skill_scores)
    spider_image = Image(spider_buf, width=7 * cm, height=7 * cm)

    combined = Table(
        [[skill_table, spider_image]],
        colWidths=[10 * cm, 8 * cm]
    )
    combined.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (1, 0), (1, 0),  "CENTER"),
    ]))
    elements.append(combined)
    elements.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------
    # Per question table
    # --------------------------------------------------
    section_bg = Table(
        [[Paragraph("  Question-wise Performance", section_style)]],
        colWidths=[18 * cm]
    )
    section_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_ACCENT),
        ("PADDING",    (0, 0), (-1, -1), 6),
    ]))
    elements.append(section_bg)
    elements.append(Spacer(1, 0.2 * cm))

    # Compute class performance per question
    class_q_correct = {}
    class_q_total   = len(class_results) if class_results else 0
    if class_results:
        for r in class_results:
            for q_key, q_data in r["per_question"].items():
                if q_data["is_correct"]:
                    class_q_correct[q_key] = class_q_correct.get(q_key, 0) + 1

    q_header = [
        Paragraph("<b>Q No</b>", center_style),
        Paragraph("<b>Skill</b>", center_style),
        Paragraph("<b>Your Answer</b>", center_style),
        Paragraph("<b>Correct Answer</b>", center_style),
        Paragraph("<b>Result</b>", center_style),
        Paragraph("<b>Class Performance</b>", center_style),
    ]

    # Build reverse skill map: question number -> skill name
    reverse_skill_map = {}
    for skill, q_nums in exam_config["skill_map"].items():
        for q_num in q_nums:
            reverse_skill_map[q_num] = skill

    q_rows = [q_header]
    for q_key, q_data in result["per_question"].items():
        q_num       = int(q_key[1:])
        is_correct  = q_data["is_correct"]
        skill_name  = reverse_skill_map.get(q_num, "-")
        detected    = q_data["detected"] or "-"
        correct     = q_data["correct"] or "-"
        result_sym  = "✓" if is_correct else "✗"
        result_color = GREEN if is_correct else RED

        if class_results:
            correct_count  = class_q_correct.get(q_key, 0)
            class_perf_str = f"{correct_count} / {class_q_total}"
        else:
            class_perf_str = "-"

        result_para = Paragraph(
            f"<b>{result_sym}</b>",
            ParagraphStyle(
                "result",
                fontSize=10,
                fontName="Helvetica-Bold",
                textColor=result_color,
                alignment=TA_CENTER,
            )
        )

        q_rows.append([
            Paragraph(q_key, center_style),
            Paragraph(skill_name, normal_style),
            Paragraph(detected, center_style),
            Paragraph(correct, center_style),
            result_para,
            Paragraph(class_perf_str, center_style),
        ])

    q_table = Table(
        q_rows,
        colWidths=[1.5 * cm, 4 * cm, 2.5 * cm, 3 * cm, 1.5 * cm, 3.5 * cm]
    )
    q_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_ACCENT),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("BOX",           (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, GREY),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",       (0, 0), (-1, -1), 6),
    ]))
    elements.append(q_table)
    elements.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------
    elements.append(HRFlowable(width="100%", thickness=1, color=GREY))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "Generated by Kaushal Prativedan Portal — Vigyan Express",
        ParagraphStyle("footer", fontSize=8, textColor=GREY, alignment=TA_CENTER)
    ))

    doc.build(elements)

    if output_path is None:
        buf.seek(0)
        return buf


# ----------------------------------------------------
# Standalone test
# ----------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path
    from scorer import score

    BASE_DIR = Path(__file__).resolve().parent.parent

    student = {
        "name":        "Rahul Sharma",
        "roll_number": "R001",
        "class":       "6",
        "batch":       "A",
    }

    exam_config = {
        "config_name":   "Science Grade 6 Baseline",
        "question_count": 15,
        "answer_key": {
            "Q1": "B", "Q2": "C", "Q3": "B", "Q4": "B", "Q5": "B",
            "Q6": "B", "Q7": "C", "Q8": "B", "Q9": "C", "Q10": "D",
            "Q11": "B", "Q12": "B", "Q13": "A", "Q14": "C", "Q15": "B",
        },
        "skill_map": {
            "Application":   [1, 2, 3, 4, 5],
            "Understanding": [6, 7, 8, 9, 10],
            "HOTS":          [11, 12, 13],
            "Knowledge":     [14, 15],
        }
    }

    detected_answers = {
        "Q1": "B", "Q2": "A",  "Q3": "B", "Q4": "D", "Q5": "B",
        "Q6": "B", "Q7": "C",  "Q8": "B", "Q9": "C", "Q10": "A",
        "Q11": "B", "Q12": "B", "Q13": "C", "Q14": "C", "Q15": "B",
    }

    result = score(detected_answers, exam_config)
    result["exam_type"] = "baseline"

    # Simulate class results (3 students)
    class_results = [result, result, result]

    out = BASE_DIR / "output" / "test_report.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    generate_report(student, result, exam_config, class_results, output_path=str(out))
    print(f"Report saved to: {out}")