import json
from pathlib import Path


COURSE_FILE = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "courses.json"
)


def load_courses():

    with open(COURSE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_course_score(
    course,
    competency,
    gap,
    current_level
):

    # 1. Does the course address the skill?
    skill_match = (
        1.0
        if competency in course["competencies"]
        else 0.0
    )

    if skill_match == 0:
        return 0

    # 2. Difficulty fit
    course_level = course["difficulty"]

    difference = abs(
        course_level - current_level
    )

    difficulty_fit = max(
        0,
        1 - (difference / 5)
    )

    # 3. Gap priority
    gap_priority = min(gap / 5, 1)

    # Weighted score
    score = (
        0.50 * skill_match
        + 0.30 * gap_priority
        + 0.20 * difficulty_fit
    )

    return round(score * 100, 2)


def generate_recommendations(
    competency_gaps
):

    courses = load_courses()

    recommendations = []

    # -----------------------------------------
    # Normalize input
    # -----------------------------------------

    normalized_gaps = []

    # Case 1:
    # Assessment result already contains
    # a list of gap dictionaries.
    #
    # Example:
    #
    # [
    #   {
    #     "competency": "Python",
    #     "gap": 2,
    #     "current_level": 2
    #   }
    # ]

    if isinstance(competency_gaps, list):

        normalized_gaps = competency_gaps

    # Case 2:
    # A dictionary was supplied.
    #
    # Example:
    #
    # {
    #   "Python": 2,
    #   "SQL": 3
    # }
    #
    # We only convert entries that already
    # contain gap information.
    elif isinstance(
        competency_gaps,
        dict
    ):

        for competency, value in competency_gaps.items():

            if isinstance(value, dict):

                normalized_gaps.append({
                    "competency":
                        value.get(
                            "competency",
                            competency
                        ),

                    "gap":
                        value.get(
                            "gap",
                            0
                        ),

                    "current_level":
                        value.get(
                            "current_level",
                            value.get(
                                "level",
                                0
                            )
                        )
                })

            else:

                # A plain competency level does
                # not contain enough information
                # to calculate a gap.
                #
                # Do not treat the competency
                # name as a dictionary.

                continue

    # -----------------------------------------
    # Generate recommendations
    # -----------------------------------------

    for gap_data in normalized_gaps:

        if not isinstance(
            gap_data,
            dict
        ):
            continue

        competency = gap_data.get(
            "competency"
        )

        gap = gap_data.get(
            "gap",
            0
        )

        current_level = gap_data.get(
            "current_level",
            0
        )

        if not competency:
            continue

        try:
            gap = float(gap)
        except (
            TypeError,
            ValueError
        ):
            continue

        try:
            current_level = float(
                current_level
            )
        except (
            TypeError,
            ValueError
        ):
            current_level = 0

        if gap <= 0:
            continue

        # -------------------------------------
        # Compare against available courses
        # -------------------------------------

        for course in courses:

            score = calculate_course_score(
                course,
                competency,
                gap,
                current_level
            )

            if score <= 0:
                continue

            recommendations.append({

                "course_id":
                    course["id"],

                "title":
                    course["title"],

                "provider":
                    course["provider"],

                "competency":
                    competency,

                "match_score":
                    score,

                "difficulty":
                    course["difficulty"],

                "duration_hours":
                    course[
                        "duration_hours"
                    ],

                "why": [

                    f"Your current "
                    f"{competency} level is "
                    f"{current_level}/5.",

                    f"You have a competency "
                    f"gap of {gap} level(s).",

                    f"This course directly "
                    f"addresses {competency}.",

                    "Course difficulty was "
                    "considered when calculating "
                    "the recommendation."
                ]
            })

    # -----------------------------------------
    # Sort recommendations
    # -----------------------------------------

    recommendations.sort(
        key=lambda x: x[
            "match_score"
        ],
        reverse=True
    )

    return recommendations[:10]