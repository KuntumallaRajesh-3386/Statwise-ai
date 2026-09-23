import sqlite3
from pathlib import Path
from datetime import datetime
from datetime import datetime, timezone
from .auth import hash_password, verify_password
import os
# --------------------------------
# Database location
# --------------------------------

DB_PATH = Path(__file__).parent / "statwise.db"


# --------------------------------
# Default competency levels
# --------------------------------

DEFAULT_COMPETENCY_LEVEL = 3

DEFAULT_COMPETENCIES = {
    "Statistical Methods": 3,
    "Sampling": 3,
    "Python": 3,
    "SQL": 3,
    "Data Visualization": 3,
    "GIS": 3,
    "AI and Machine Learning": 3,
    "Cybersecurity": 3,
    "Leadership": 3,
    "Communication": 3,
}


# --------------------------------
# Database connection
# --------------------------------

def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------
# Initialize database
# --------------------------------

def initialize_database():

    connection = get_connection()

    # --------------------------------
    # Current competency levels
    # --------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS competencies (
            topic TEXT PRIMARY KEY,
            level INTEGER NOT NULL
        )
        """
    )

    # --------------------------------
    # Competency assessment history
    # --------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS assessment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            previous_level INTEGER,
            new_level INTEGER NOT NULL,
            assessment_score REAL,
            assessed_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Statistical Officer',
            account_type TEXT NOT NULL DEFAULT 'user',
            google_id TEXT UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------
    # Insert default competencies
    # only when they don't already exist
    # --------------------------------

    for topic, level in DEFAULT_COMPETENCIES.items():

        connection.execute(
            """
            INSERT OR IGNORE INTO competencies (
                topic,
                level
            )
            VALUES (?, ?)
            """,
            (
                topic,
                level
            )
        )

    connection.commit()
    ensure_admin_user()

    connection.close()


# --------------------------------
# Update competency
# --------------------------------

def update_competency(
    topic: str,
    level: int,
    assessment_score=None
):

    connection = get_connection()

    try:

        # --------------------------------
        # Validate level
        # --------------------------------

        level = int(level)

        if level < 1 or level > 5:

            raise ValueError(
                "Competency level must be between 1 and 5."
            )

        # --------------------------------
        # Get previous level
        # --------------------------------

        existing_row = connection.execute(
            """
            SELECT level
            FROM competencies
            WHERE topic = ?
            """,
            (topic,)
        ).fetchone()

        if existing_row is not None:

            previous_level = int(
                existing_row["level"]
            )

        else:

            # First assessment for this competency.
            # Use the same default level as the dashboard.
            previous_level = DEFAULT_COMPETENCY_LEVEL

        # --------------------------------
        # Update current competency
        # --------------------------------

        connection.execute(
            """
            INSERT INTO competencies (
                topic,
                level
            )
            VALUES (?, ?)

            ON CONFLICT(topic)
            DO UPDATE SET
                level = excluded.level
            """,
            (
                topic,
                level
            )
        )

        # --------------------------------
        # Save assessment history
        # --------------------------------

        connection.execute(
            """
            INSERT INTO assessment_history (
                topic,
                previous_level,
                new_level,
                assessment_score,
                assessed_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                topic,
                previous_level,
                level,
                assessment_score,
                datetime.now().isoformat()
            )
        )

        connection.commit()

        return {
            "success": True,
            "topic": topic,
            "previous_level": previous_level,
            "updated_level": level,
            "assessment_score": assessment_score
        }

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# --------------------------------
# Get current competency
# --------------------------------

def get_competency(topic: str):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            topic,
            level
        FROM competencies
        WHERE topic = ?
        """,
        (topic,)
    ).fetchone()

    connection.close()

    if row is None:

        return {
            "topic": topic,
            "level": DEFAULT_COMPETENCY_LEVEL
        }

    return {
        "topic": row["topic"],
        "level": row["level"]
    }


# --------------------------------
# Get all current competencies
# --------------------------------

def get_all_competencies():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            topic,
            level
        FROM competencies
        ORDER BY topic
        """
    ).fetchall()

    connection.close()

    result = {
        topic: level
        for topic, level in DEFAULT_COMPETENCIES.items()
    }

    for row in rows:

        result[row["topic"]] = row["level"]

    return result


# --------------------------------
# Get assessment history
# --------------------------------

def get_assessment_history(topic=None):

    connection = get_connection()

    try:

        if topic:

            rows = connection.execute(
                """
                SELECT
                    id,
                    topic,
                    previous_level,
                    new_level,
                    assessment_score,
                    assessed_at
                FROM assessment_history
                WHERE topic = ?
                ORDER BY assessed_at DESC
                """,
                (topic,)
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT
                    id,
                    topic,
                    previous_level,
                    new_level,
                    assessment_score,
                    assessed_at
                FROM assessment_history
                ORDER BY assessed_at DESC
                """
            ).fetchall()

        return [
            {
                "id": row["id"],
                "topic": row["topic"],
                "previous_level": (
                    row["previous_level"]
                ),
                "new_level": row["new_level"],
                "assessment_score": (
                    row["assessment_score"]
                ),
                "assessed_at": (
                    row["assessed_at"]
                )
            }
            for row in rows
        ]

    finally:

        connection.close()


# --------------------------------
# Delete assessment history
# --------------------------------


def delete_assessment_history(history_id: int):

    connection = get_connection()

    try:

        connection.execute(
            """
            DELETE FROM assessment_history
            WHERE id = ?
            """,
            (history_id,)
        )

        connection.commit()

        return {
            "success": True,
            "history_id": history_id
        }

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()

# --------------------------------
# Reset current competency level
# Used for development/test cleanup
# --------------------------------
# ============================================================
# USER AUTHENTICATION
# ============================================================

def create_user(
    email: str,
    password: str,
    name: str,
    role: str = "Statistical Officer",
    account_type: str = "user",
):
    email = email.strip().lower()
    name = name.strip()
    role = role.strip()

    if not email:
        raise ValueError("Email is required.")

    if not password:
        raise ValueError("Password is required.")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    if not name:
        raise ValueError("Name is required.")

    if account_type not in {"user", "admin"}:
        raise ValueError(
            "Invalid account type."
        )

    connection = get_connection()

    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = connection.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                name,
                role,
                account_type,
                is_active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                email,
                hash_password(password),
                name,
                role,
                account_type,
                now,
                now,
            ),
        )

        connection.commit()

        return get_user_by_id(cursor.lastrowid)

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError(
            "An account with this email already exists."
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_by_email(email: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                name,
                role,
                account_type,
                google_id,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_user_by_id(user_id: int):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                email,
                name,
                role,
                account_type,
                google_id,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def authenticate_user(
    email: str,
    password: str,
):
    user = get_user_by_email(email)

    if not user:
        return None

    if not user["is_active"]:
        return None

    if not user["password_hash"]:
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "account_type": user["account_type"],
        "is_active": user["is_active"],
    }


def get_all_users():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                email,
                name,
                role,
                account_type,
                google_id,
                is_active,
                created_at,
                updated_at
            FROM users
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
def ensure_admin_user():
    """
    Create the initial administrator from environment variables
    if an administrator account does not already exist.
    """
    admin_email = os.getenv("STATWISE_ADMIN_EMAIL")
    admin_password = os.getenv("STATWISE_ADMIN_PASSWORD")
    admin_name = os.getenv(
        "STATWISE_ADMIN_NAME",
        "STATWISE Administrator",
    )

    if not admin_email or not admin_password:
        return

    existing_admin = get_user_by_email(admin_email)

    if existing_admin:
        return

    create_user(
        email=admin_email,
        password=admin_password,
        name=admin_name,
        role="Administrator",
        account_type="admin",
    )
def update_user(
    user_id: int,
    name: str | None = None,
    role: str | None = None,
    account_type: str | None = None,
    is_active: int | None = None,
):
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id, email, name, role, account_type, is_active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if not existing:
            return None

        current = dict(existing)

        new_name = (
            name.strip()
            if name is not None
            else current["name"]
        )

        new_role = (
            role.strip()
            if role is not None
            else current["role"]
        )

        new_account_type = (
            account_type
            if account_type is not None
            else current["account_type"]
        )

        new_is_active = (
            int(is_active)
            if is_active is not None
            else current["is_active"]
        )

        if not new_name:
            raise ValueError("Name is required.")

        if not new_role:
            raise ValueError("Role is required.")

        if new_account_type not in {"user", "admin"}:
            raise ValueError("Invalid account type.")

        if new_is_active not in {0, 1}:
            raise ValueError("Invalid active status.")

        now = datetime.now(timezone.utc).isoformat()

        connection.execute(
            """
            UPDATE users
            SET
                name = ?,
                role = ?,
                account_type = ?,
                is_active = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                new_name,
                new_role,
                new_account_type,
                new_is_active,
                now,
                user_id,
            ),
        )

        connection.commit()

        return get_user_by_id(user_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def deactivate_user(user_id: int):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE users
            SET
                is_active = 0,
                updated_at = ?
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                user_id,
            ),
        )

        connection.commit()

        if cursor.rowcount == 0:
            return None

        return get_user_by_id(user_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_user(user_id: int):
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if not existing:
            return False

        connection.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,),
        )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()