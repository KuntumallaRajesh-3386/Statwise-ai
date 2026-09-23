import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)


def generate_mcq(passage: str):
    prompt = f"""
Generate ONE multiple-choice question using ONLY the provided passage.

Do not use outside knowledge.
Do not invent facts.
The correct answer must be directly supported by the passage.

Return ONLY valid JSON in this format:

{{
  "question": "string",
  "options": [
    "string",
    "string",
    "string",
    "string"
  ],
  "answer": 1,
  "difficulty": "Easy",
  "explanation": "string"
}}

The answer must be the zero-based option index:
0, 1, 2, or 3.

PASSAGE:
{passage}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    text = response.text.strip()

    # Remove Markdown code fences if Gemini adds them
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1)
        text = text.strip()

    return json.loads(text)