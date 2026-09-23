DIFFICULTY_LEVELS = {
    1: "Easy",
    2: "Medium",
    3: "Hard"
}


def next_difficulty(current_difficulty: int, correct: bool):
    """
    Adjust difficulty based on the learner's answer.
    """

    if correct:
        return min(current_difficulty + 1, 3)

    return max(current_difficulty - 1, 1)


def calculate_score(correct_answers: int, total_questions: int):
    """
    Calculate percentage score.
    """

    if total_questions <= 0:
        return 0

    return round(
        (correct_answers / total_questions) * 100
    )


def score_to_competency_level(score: int):
    """
    Convert percentage performance into
    a prototype 1-5 competency level.

    These thresholds are configurable prototype
    values, not official government standards.
    """

    if score < 20:
        return 1

    if score < 40:
        return 2

    if score < 60:
        return 3

    if score < 80:
        return 4

    return 5


def build_assessment_result(
    topic: str,
    correct_answers: int,
    total_questions: int,
    initial_level: int = 0
):
    score = calculate_score(
        correct_answers,
        total_questions
    )

    final_level = score_to_competency_level(score)

    improvement = final_level - initial_level

    return {
        "topic": topic,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "score": score,
        "initial_level": initial_level,
        "final_level": final_level,
        "improvement": improvement
    }