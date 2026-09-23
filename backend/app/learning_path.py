COMPETENCY_PREREQUISITES = {

    "AI and Machine Learning": [
        "Python",
        "Statistical Methods"
    ],

    "Data Visualization": [
        "Statistical Methods"
    ],

    "GIS": [
        "Data Visualization"
    ],

    "Advanced Python": [
        "Python"
    ],

    "SQL": [],

    "Sampling": [
        "Statistical Methods"
    ],

    "Statistical Methods": [],

    "Python": [],

    "Cybersecurity": [],

    "Leadership": [],

    "Communication": []
}


def find_missing_prerequisites(
    competency_gaps
):

    gaps = {
        item["competency"]: item["gap"]
        for item in competency_gaps
    }

    missing = []

    for competency, gap in gaps.items():

        if gap <= 0:
            continue

        prerequisites = (
            COMPETENCY_PREREQUISITES
            .get(competency, [])
        )

        for prerequisite in prerequisites:

            prerequisite_gap = gaps.get(
                prerequisite,
                0
            )

            if prerequisite_gap > 0:

                missing.append({
                    "competency": prerequisite,
                    "required_for": competency,
                    "gap": prerequisite_gap
                })

    return missing

def build_learning_path(
    competency_gaps,
    recommendations
):

    missing_prerequisites = (
        find_missing_prerequisites(
            competency_gaps
        )
    )

    path = []

    added_competencies = set()

    # --------------------------------
    # STEP 1 — Prerequisites
    # --------------------------------

    for item in missing_prerequisites:

        competency = item["competency"]

        if competency in added_competencies:
            continue

        matching_courses = [
            course
            for course in recommendations
            if course["competency"]
            == competency
        ]

        if matching_courses:

            best_course = max(
                matching_courses,
                key=lambda x:
                x["match_score"]
            )

            path.append({
                "step": len(path) + 1,
                "type": "Prerequisite",
                "competency": competency,
                "course": best_course["title"],
                "provider": best_course["provider"],
                "match_score": best_course[
                    "match_score"
                ],
                "reason": (
                    f"Build {competency} first "
                    f"because it is a prerequisite "
                    f"for another identified gap."
                )
            })

            added_competencies.add(
                competency
            )

    # --------------------------------
    # STEP 2 — Main skill gaps
    # --------------------------------

    sorted_gaps = sorted(
        competency_gaps,
        key=lambda x: x["gap"],
        reverse=True
    )

    for gap in sorted_gaps:

        competency = gap["competency"]

        if gap["gap"] <= 0:
            continue

        if competency in added_competencies:
            continue

        matching_courses = [
            course
            for course in recommendations
            if course["competency"]
            == competency
        ]

        if not matching_courses:
            continue

        best_course = max(
            matching_courses,
            key=lambda x:
            x["match_score"]
        )

        path.append({
            "step": len(path) + 1,
            "type": "Core Skill",
            "competency": competency,
            "course": best_course["title"],
            "provider": best_course["provider"],
            "match_score": best_course[
                "match_score"
            ],
            "reason": (
                f"This course addresses "
                f"your {competency} skill gap."
            )
        })

        added_competencies.add(
            competency
        )

    return path