ROLE_REQUIREMENTS = {
    "Statistical Officer": {
        "Statistical Methods": 5,
        "Sampling": 5,
        "Python": 4,
        "SQL": 3,
        "Data Visualization": 4,
        "GIS": 3,
        "AI and Machine Learning": 3,
        "Cybersecurity": 2,
        "Leadership": 4,
        "Communication": 4
    },

    "Data Analyst": {
        "Statistical Methods": 4,
        "Sampling": 3,
        "Python": 5,
        "SQL": 5,
        "Data Visualization": 5,
        "GIS": 3,
        "AI and Machine Learning": 4,
        "Cybersecurity": 2,
        "Leadership": 2,
        "Communication": 3
    }
}


def classify_gap(gap: int) -> str:

    if gap >= 4:
        return "Critical"

    if gap == 3:
        return "High"

    if gap == 2:
        return "Medium"

    if gap == 1:
        return "Low"

    return "No Gap"


def calculate_competency(role: str, scores: dict):

    if role not in ROLE_REQUIREMENTS:
        return {
            "error": f"Unknown role: {role}"
        }

    requirements = ROLE_REQUIREMENTS[role]

    result = []

    for competency, required in requirements.items():

        current = scores.get(competency, 0)

        current = max(0, min(current, 5))

        gap = max(required - current, 0)

        result.append({
            "competency": competency,
            "required_level": required,
            "current_level": current,
            "gap": gap,
            "status": classify_gap(gap)
        })

    result.sort(
        key=lambda x: x["gap"],
        reverse=True
    )

    return {
        "role": role,
        "competencies": result
    }

