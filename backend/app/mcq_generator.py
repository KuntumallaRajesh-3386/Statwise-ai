import json
import os

from google import genai

from .vector_store import vector_store


def build_context(topic: str, num_questions: int = 5):
    passages = vector_store.search(topic, k=5)

    if not passages:
        return "", []

    context_parts = []

    for i, passage in enumerate(passages):
        context_parts.append(
            f"""
SOURCE {i + 1}
PAGE: {passage["page"]}

CONTENT:
{passage["text"]}
"""
        )

    return "\n".join(context_parts), passages

def fallback_mcqs(topic, passages, num_questions=5):
    """
    Document-grounded fallback MCQ generator.

    Used when the AI model is temporarily unavailable.
    """

    questions = []

    for i, passage in enumerate(passages[:num_questions]):

        text = passage.get("text", "").strip()

        if len(text) < 50:
            continue

        # Normalize whitespace
        clean_text = " ".join(text.split())

        # Find useful sentences
        sentences = [
            sentence.strip()
            for sentence in clean_text.split(".")
            if len(sentence.strip()) >= 50
        ]

        if not sentences:
            continue

        evidence = sentences[0]

        # -----------------------------------------
        # Python module-specific fallback
        # -----------------------------------------
        if "module" in evidence.lower():

            question = (
                "What is the purpose of modules in Python "
                "as described in the learning material?"
            )

            options = [
                "They provide reusable functions and data types that can be imported when needed.",
                "They require every Python program to contain all available capabilities.",
                "They prevent Python programs from using functions defined outside the main program.",
                "They automatically convert Python programs into Java bytecode."
            ]

            answer = 0

            explanation = (
                "The material explains that Python modules are "
                "self-contained programs that define functions "
                "and data types which can be called when needed."
            )

        # -----------------------------------------
        # Generic fallback
        # -----------------------------------------
        else:

            question = (
                f"Which statement about {topic} "
                "is supported by the learning material?"
            )

            options = [
                evidence[:180],
                "It requires every available capability to be included in every program.",
                "It prevents programs from using reusable components.",
                "It automatically converts every program into another programming language."
            ]

            answer = 0

            explanation = (
                "The selected answer is directly supported "
                "by the retrieved learning material."
            )

        questions.append({
            "id": i + 1,
            "topic": topic,
            "question": question,
            "options": options,
            "answer": answer,
            "difficulty": "Medium",
            "source_page": passage["page"],
            "evidence": evidence[:300],
            "explanation": explanation
        })

    if not questions:
        return {
            "error": (
                f"Not enough relevant material was found "
                f"to generate a {topic} assessment."
            )
        }

    return questions
def generate_mcqs(topic: str, num_questions: int = 5):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "error": "GEMINI_API_KEY is not configured."
        }

    context, passages = build_context(topic, num_questions)

    if not context:
        return {
            "error": "No relevant content found in the uploaded document."
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an assessment-generation engine for STATWISE AI.

Generate {num_questions} multiple-choice questions about:

TOPIC:
{topic}

IMPORTANT RULES:

1. Use ONLY the information contained in the supplied SOURCE CONTENT.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Each question must have exactly four options.
5. Exactly one option must be correct.
6. Questions should test understanding, not merely copy sentences.
7. Use a mixture of conceptual and applied questions when the source supports it.
8. Assign difficulty as Easy, Medium, or Hard.
9. Provide a short explanation for the correct answer.
10. Return valid JSON only.
11. Generate competency-oriented questions, not trivia questions.
12. Prefer questions that test understanding, application, reasoning, code interpretation, or problem solving.
13. Avoid historical trivia, creator/founder facts, naming trivia, or incidental facts unless they are directly relevant to the requested competency.
14. Do not begin questions with phrases such as "According to the source text" or "According to the passage".
15. Every question must be understandable on its own and must test the learner's knowledge of the requested topic.
16. Use only information supported by the retrieved source content.
17. For Python questions, prioritize:
    - Python syntax and language concepts
    - variables and data types
    - control flow
    - functions
    - lists, tuples, sets, and dictionaries
    - code interpretation
    - error identification
    - practical data-analysis applications

18. For Statistical Methods questions, prioritize:
    - statistical concepts
    - interpretation of statistical results
    - practical statistical applications
    - appropriate method selection
    - reasoning about data

19. For Sampling questions, prioritize:
    - sampling concepts
    - sampling methods
    - sample selection
    - sampling errors
    - practical survey scenarios
    - choosing an appropriate sampling method

20. Match question difficulty to the requested level:
    - Easy: fundamental concepts and direct understanding
    - Medium: interpretation and practical application
    - Hard: multi-step reasoning and complex practical scenarios

21. Avoid questions where the correct answer can be guessed simply because it repeats distinctive wording from the source.

22. Make distractors plausible and related to the same topic. Do not use obviously unrelated options.

23. Before returning a question, verify that exactly one of the four options is correct.

24. If the retrieved source material is insufficient to create a valid competency question, do not invent information. Return fewer questions rather than unsupported questions.

25. Preserve source grounding by including the relevant source page and evidence for every generated question.
26. Do not strengthen, reinterpret, or extend a claim beyond what the source explicitly supports.

27. When asking about a cause, benefit, effect, or mechanism, ensure that the source explicitly supports that relationship.

28. Prefer questions that use the same technical meaning as the source rather than introducing a stronger technical interpretation.

29. Distractors must represent plausible misconceptions or alternative interpretations of the same topic.

30. Avoid obviously unrelated distractors that a learner could eliminate without knowing the subject.

31. Do not make the correct answer noticeably more detailed, precise, or technically sophisticated than the distractors.

32. Before generating the final question, verify that the question, correct answer, explanation, and evidence all describe the same concept.

33. If the source supports only a limited claim, ask about that limited claim instead of expanding it into a broader technical claim.

SOURCE CONTENT:
{context}

Return this exact JSON structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": 0,
            "difficulty": "Medium",
            "explanation": "Why the correct answer is correct.",
            "source_page": 1,
            "evidence": "Short supporting passage from the source."
        }}
    ]
}}

The answer field must be:
0 for Option A
1 for Option B
2 for Option C
3 for Option D
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )

        data = json.loads(response.text)

        questions = data.get("questions", [])

        for index, question in enumerate(questions, start=1):
            question["id"] = index
            question["topic"] = topic

        return questions

    except Exception as error:

     error_text = str(error)

    print("Gemini generation failed:", error_text)

    # Gemini temporarily unavailable.
    # Use retrieved document content so the demo continues.
    if "503" in error_text or "UNAVAILABLE" in error_text:

        print("Using document-grounded fallback MCQs.")

        return fallback_mcqs(
            topic,
            passages,
            num_questions
        )

    return {
        "error": f"AI generation failed: {error_text}"
    }