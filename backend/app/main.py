from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
)
from .auth import (
    create_access_token,
    get_current_user,
    require_admin,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .competency_database import (
    update_competency,
    get_competency,
    get_all_competencies,
    get_assessment_history,
    initialize_database,
    delete_assessment_history,
    create_user,
    get_user_by_id,
    authenticate_user,
    get_all_users,
)

import os
import tempfile

from .competency import calculate_competency
from .questions import QUESTIONS
from .recommendation import generate_recommendations
from .learning_path import build_learning_path
from .vector_store import vector_store
from .mcq_generator import generate_mcqs
from app.ai_generator import generate_mcq
from .adaptive import build_assessment_result

from .document import extract_pdf_text, chunk_pages

from .competency_database import (
    update_competency,
    get_competency,
    get_all_competencies,
    get_assessment_history,
    initialize_database,
    delete_assessment_history,
)


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="STATWISE AI",
    description="Competency Intelligence Platform",
    version="0.1.0",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# CORS
# ============================================================

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================


class AssessmentRequest(BaseModel):
    role: str
    scores: dict[str, int]


class AnswerSubmission(BaseModel):
    question_id: int
    answer: int
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "Statistical Officer"


class LoginRequest(BaseModel):
    email: str
    password: str
class AdminUserUpdateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    account_type: str | None = None
    is_active: int | None = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def calculate_assessment_score(
    correct_answers: int,
    total_questions: int,
) -> int:
    """
    Convert correct answers into a percentage score.
    """

    if total_questions <= 0:
        return 0

    correct_answers = max(
        0,
        min(correct_answers, total_questions),
    )

    return round(
        (correct_answers / total_questions) * 100
    )


def score_to_level(score: int) -> int:
    """
    Convert assessment percentage into competency level.
    """

    score = max(0, min(int(score), 100))

    if score < 20:
        return 1

    if score < 40:
        return 2

    if score < 60:
        return 3

    if score < 80:
        return 4

    return 5


# ============================================================
# ROOT / HEALTH
# ============================================================


@app.get("/")
def root():
    return {
        "name": "STATWISE AI",
        "message": "Competency Intelligence API is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# COMPETENCY ENDPOINTS
# ============================================================


@app.get("/competencies")
def competencies():
    """
    Return all saved competency levels.
    """

    return {
        "competencies": get_all_competencies(),
    }


@app.get("/competency/{topic}")
def competency(topic: str):
    """
    Return the saved competency for one topic.
    """

    result = get_competency(topic)

    if result is None:
        return {
            "topic": topic,
            "level": None,
        }

    return result


@app.post("/competency/update")
def update_competency_endpoint(data: dict):
    """
    Update a competency after an assessment.

    The database layer is responsible for recording
    the assessment history.
    """

    topic = data.get("topic")

    if not topic:
        return {
            "error": "Topic is required.",
        }

    try:
        new_level = int(data.get("level", 0))
    except (TypeError, ValueError):
        return {
            "error": "Competency level must be a number.",
        }

    if new_level < 1 or new_level > 5:
        return {
            "error": "Competency level must be between 1 and 5.",
        }

    assessment_score = data.get(
        "assessment_score"
    )

    if assessment_score is not None:
        try:
            assessment_score = int(
                assessment_score
            )
        except (TypeError, ValueError):
            assessment_score = None

    try:
        result = update_competency(
            topic,
            new_level,
            assessment_score,
        )

        return {
            **result,
            "message": (
                f"{topic} competency updated successfully."
            ),
        }

    except Exception as error:
        print(
            "Competency update error:",
            error,
        )

        return {
            "error": (
                "Could not update competency."
            ),
            "detail": str(error),
        }


# ============================================================
# COMPETENCY HISTORY
# ============================================================


@app.get("/competency-history")
def competency_history(
    topic: str | None = None,
):
    """
    Return competency assessment history.

    Optional:
        ?topic=Python
    """

    try:
        history = get_assessment_history(topic)

        return {
            "history": history or [],
        }

    except Exception as error:
        print(
            "Competency history error:",
            error,
        )

        return {
            "history": [],
            "error": str(error),
        }


# ============================================================
# DASHBOARD ASSESSMENT
# ============================================================


@app.post("/assessment")
def assessment(
    request: AssessmentRequest,
):
    """
    Calculate the dashboard competency analysis.
    """

    result = calculate_competency(
        request.role,
        request.scores,
    )

    return result


# ============================================================
# ADAPTIVE ASSESSMENT RESULT
# ============================================================


@app.post("/adaptive/result")
def adaptive_result(data: dict):
    """
    Calculate the final competency level after
    completing an AI assessment.
    """

    topic = str(
        data.get("topic", "")
    ).strip()

    if not topic:
        return {
            "error": "Topic is required.",
        }

    try:
        correct_answers = int(
            data.get(
                "correct_answers",
                0,
            )
        )

        total_questions = int(
            data.get(
                "total_questions",
                0,
            )
        )

        initial_level = int(
            data.get(
                "initial_level",
                0,
            )
        )

    except (TypeError, ValueError):
        return {
            "error": (
                "Assessment result values "
                "must be numeric."
            ),
        }

    if total_questions <= 0:
        return {
            "error": (
                "Total questions must be greater than zero."
            ),
        }

    # Keep values within valid boundaries.
    correct_answers = max(
        0,
        min(
            correct_answers,
            total_questions,
        ),
    )

    initial_level = max(
        1,
        min(initial_level, 5),
    )

    assessment_score = calculate_assessment_score(
        correct_answers,
        total_questions,
    )

    print(
        "Adaptive assessment:",
        {
            "topic": topic,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "score": assessment_score,
            "initial_level": initial_level,
        },
    )

    result = build_assessment_result(
        topic=topic,
        correct_answers=correct_answers,
        total_questions=total_questions,
        initial_level=initial_level,
    )

    return result


# ============================================================
# MCQ GENERATION
# ============================================================

# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/auth/register")
def register(data: RegisterRequest):
    try:
        user = create_user(
            email=data.email,
            password=data.password,
            name=data.name,
            role=data.role,
            account_type="user",
        )

        return {
            "success": True,
            "message": "Account created successfully.",
            "user": user,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/auth/login")
def login(data: LoginRequest):
    user = authenticate_user(
        email=data.email,
        password=data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        account_type=user["account_type"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me")
def current_user(
    current_user: dict = Depends(get_current_user),
):
    user = get_user_by_id(
        current_user["user_id"]
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User account not found.",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive.",
        )

    return {
        "user": user,
    }
@app.get("/mcqs")
def mcqs(topic: str):
    """
    Generate AI assessment questions for a topic.
    """

    if not topic:
        return {
            "error": "Topic is required.",
        }

    result = generate_mcqs(topic)

    if (
        isinstance(result, dict)
        and "error" in result
    ):
        return result

    return {
        "topic": topic,
        "questions": result,
    }


@app.post("/generate-mcq")
def generate_mcq_endpoint(data: dict):
    """
    Generate an MCQ from supplied passage text.
    """

    passage = data.get(
        "passage",
        "",
    )

    if not passage:
        return {
            "error": "Passage is required.",
        }

    return generate_mcq(passage)


# ============================================================
# STATIC QUESTION BANK
# ============================================================


@app.get("/questions/{competency}")
def get_questions(
    competency: str,
):
    """
    Return questions for a competency without
    exposing the correct answers.
    """

    questions = [
        question
        for question in QUESTIONS
        if question["competency"].lower()
        == competency.lower()
    ]

    safe_questions = []

    for question in questions:
        safe_questions.append(
            {
                "id": question["id"],
                "competency": question[
                    "competency"
                ],
                "difficulty": question[
                    "difficulty"
                ],
                "question": question[
                    "question"
                ],
                "options": question[
                    "options"
                ],
            }
        )

    return safe_questions


@app.post("/evaluate")
def evaluate_answer(
    submission: AnswerSubmission,
):
    """
    Evaluate one static question-bank answer.
    """

    question = next(
        (
            question
            for question in QUESTIONS
            if question["id"]
            == submission.question_id
        ),
        None,
    )

    if question is None:
        return {
            "error": "Question not found",
        }

    correct = (
        submission.answer
        == question["answer"]
    )

    return {
        "correct": correct,
        "correct_answer": question[
            "answer"
        ],
    }


# ============================================================
# RECOMMENDATIONS
# ============================================================


@app.post("/recommendations")
def recommendations(
    data: dict,
):
    """
    Generate recommended learning resources
    based on competency gaps.
    """

    competencies = data.get(
        "competencies",
        [],
    )

    result = generate_recommendations(
        competencies
    )

    return {
        "recommendations": result,
    }


# ============================================================
# PERSONALIZED LEARNING PATH
# ============================================================


@app.post("/learning-path")
def learning_path(
    data: dict,
):
    """
    Build a personalized learning path.
    """

    competencies = data.get(
        "competencies",
        [],
    )

    recommendations = data.get(
        "recommendations",
        [],
    )

    path = build_learning_path(
        competencies,
        recommendations,
    )

    return {
        "learning_path": path,
    }


# ============================================================
# DOCUMENT SEARCH
# ============================================================


@app.get("/documents/search")
def search_document(
    query: str,
):
    """
    Search uploaded learning material
    using the vector store.
    """

    if not query:
        return {
            "query": query,
            "results": [],
        }

    results = vector_store.search(
        query
    )

    return {
        "query": query,
        "results": results,
    }


# ============================================================
# DOCUMENT UPLOAD
# ============================================================


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Process an uploaded PDF and add its
    content to the vector store.
    """

    if not file.filename:
        return {
            "error": "No file selected.",
        }

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        return {
            "error": (
                "Only PDF files are supported "
                "in this version."
            ),
        }

    file_bytes = await file.read()

    if not file_bytes:
        return {
            "error": "The uploaded PDF is empty.",
        }

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:

            temp_file.write(
                file_bytes
            )

            temp_path = temp_file.name

        pages = extract_pdf_text(
            temp_path
        )

        chunks = chunk_pages(
            pages
        )

        vector_store.add_chunks(
            chunks
        )

        return {
            "filename": file.filename,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "pages": pages,
            "chunks": chunks,
        }

    except Exception as error:
        print(
            "Document processing error:",
            error,
        )

        return {
            "error": (
                "Failed to process document."
            ),
            "detail": str(error),
        }

    finally:
        if (
            temp_path
            and os.path.exists(temp_path)
        ):
            os.remove(temp_path)

@app.delete("/competency-history/{history_id}")
def delete_history(history_id: int):
    try:
        delete_assessment_history(history_id)

        return {
            "success": True,
            "message": f"Assessment history {history_id} deleted"
        }

    except Exception as e:
        raise  HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.get("/admin/test")
def admin_test(
    current_user: dict = Depends(require_admin),
):
    return {
        "success": True,
        "message": "Administrator access confirmed.",
        "user_id": current_user["user_id"],
        "email": current_user["email"],
    }
@app.get("/admin/users")
def admin_get_users(
    current_user: dict = Depends(require_admin),
):
    return {
        "users": get_all_users()
    }


@app.put("/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    data: AdminUserUpdateRequest,
    current_user: dict = Depends(require_admin),
):
    try:
        user = update_user(
            user_id=user_id,
            name=data.name,
            role=data.role,
            account_type=data.account_type,
            is_active=data.is_active,
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User account not found.",
            )

        return {
            "success": True,
            "message": "User updated successfully.",
            "user": user,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/admin/users")
def admin_create_user(
    data: RegisterRequest,
    current_user: dict = Depends(require_admin),
):
    try:
        user = create_user(
            email=data.email,
            password=data.password,
            name=data.name,
            role=data.role,
            account_type="user",
        )

        return {
            "success": True,
            "message": "User created successfully.",
            "user": user,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/admin/users/{user_id}/deactivate")
def admin_deactivate_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
):
    user = deactivate_user(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User account not found.",
        )

    return {
        "success": True,
        "message": "User deactivated successfully.",
        "user": user,
    }


@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
):
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=400,
            detail="Administrator cannot delete their own account.",
        )

    deleted = delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User account not found.",
        )

    return {
        "success": True,
        "message": "User deleted successfully.",
    }

