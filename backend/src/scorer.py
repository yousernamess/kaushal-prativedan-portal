# ----------------------------------------------------
# scorer.py
# ----------------------------------------------------

def score(detected_answers, exam_config):
    """
    detected_answers : { "Q1": "B", "Q2": None, ... }
    exam_config      : {
        "question_count": 15,
        "answer_key": { "Q1": "B", "Q2": "C", ... },
        "skill_map": { "Application": [1,2,3,4,5], ... }
    }

    Returns:
    {
        "total_score": 12,
        "total_marks": 15,
        "per_question": {
            "Q1": { "detected": "B", "correct": "B", "is_correct": True },
            "Q2": { "detected": None, "correct": "C", "is_correct": False },
            ...
        },
        "skill_scores": {
            "Application": { "score": 4, "total": 5 },
            ...
        }
    }
    """
    question_count = exam_config["question_count"]
    answer_key     = exam_config["answer_key"]
    skill_map      = exam_config["skill_map"]

    per_question = {}
    total_score  = 0

    for i in range(1, question_count + 1):
        q_key   = f"Q{i}"
        correct = answer_key.get(q_key)
        detected = detected_answers.get(q_key)

        is_correct = detected is not None and detected == correct

        if is_correct:
            total_score += 1

        per_question[q_key] = {
            "detected":   detected,
            "correct":    correct,
            "is_correct": is_correct,
        }

    # Per skill scores
    skill_scores = {}
    for skill, question_numbers in skill_map.items():
        skill_score = 0
        skill_total = 0

        for q_num in question_numbers:
            if q_num <= question_count:
                skill_total += 1
                if per_question[f"Q{q_num}"]["is_correct"]:
                    skill_score += 1

        skill_scores[skill] = {
            "score": skill_score,
            "total": skill_total,
        }

    return {
        "total_score":   total_score,
        "total_marks":   question_count,
        "per_question":  per_question,
        "skill_scores":  skill_scores,
    }


# ----------------------------------------------------
# Standalone test
# ----------------------------------------------------
if __name__ == "__main__":
    detected_answers = {
        "Q1":  "B",
        "Q2":  None,
        "Q3":  "B",
        "Q4":  "D",
        "Q5":  "A",
        "Q6":  "B",
        "Q7":  "C",
        "Q8":  "B",
        "Q9":  "C",
        "Q10": "D",
        "Q11": "B",
        "Q12": "B",
        "Q13": "C",
        "Q14": "A",
        "Q15": "B",
    }

    exam_config = {
        "question_count": 15,
        "answer_key": {
            "Q1":  "B", "Q2":  "C", "Q3":  "B", "Q4":  "D", "Q5":  "B",
            "Q6":  "B", "Q7":  "C", "Q8":  "B", "Q9":  "C", "Q10": "D",
            "Q11": "B", "Q12": "B", "Q13": "A", "Q14": "A", "Q15": "B",
        },
        "skill_map": {
            "Application":   [1, 2, 3, 4, 5],
            "Understanding":  [6, 7, 8, 9, 10],
            "HOTS":          [11, 12, 13],
            "Knowledge":     [14, 15],
        }
    }

    result = score(detected_answers, exam_config)

    print(f"Total: {result['total_score']} / {result['total_marks']}")
    print()
    print("Per Question:")
    for q_key, data in result["per_question"].items():
        status = "✓" if data["is_correct"] else "✗"
        print(f"  {q_key}: detected={data['detected']} correct={data['correct']} {status}")
    print()
    print("Skill Scores:")
    for skill, data in result["skill_scores"].items():
        print(f"  {skill}: {data['score']} / {data['total']}")