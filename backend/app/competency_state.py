# Temporary in-memory competency store.
# Later this can be replaced with PostgreSQL.

COMPETENCY_STATE = {}


def update_competency(topic: str, level: int):
    COMPETENCY_STATE[topic] = level

    return {
        "success": True,
        "topic": topic,
        "updated_level": level
    }


def get_competency(topic: str):
    level = COMPETENCY_STATE.get(topic)

    if level is None:
        return {
            "topic": topic,
            "level": None
        }

    return {
        "topic": topic,
        "level": level
    }


def get_all_competencies():
    return COMPETENCY_STATE