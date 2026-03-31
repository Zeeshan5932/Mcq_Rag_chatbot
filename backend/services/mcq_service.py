import json
import re
from groq import Groq

from config import GROQ_API_KEY


def _get_groq_client() -> Groq:
    """Create Groq client lazily so module import never fails on startup."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Set it in backend/.env or environment variables."
        )
    return Groq(api_key=GROQ_API_KEY)


def _extract_json_array(raw_text: str) -> str:
    """Extract the first balanced JSON array from model output."""
    if not raw_text:
        raise ValueError("Empty LLM response")

    text = raw_text.strip()

    # Handle markdown fenced output like ```json ... ```
    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1).strip()

    # Fast path: response already looks like a pure JSON array
    if text.startswith("[") and text.endswith("]"):
        return text

    # Balanced bracket scan to avoid fragile non-greedy regex extraction.
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array start '[' found in LLM response")

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(text)):
        ch = text[idx]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]

    raise ValueError("No balanced JSON array end ']' found in LLM response")

def generate_mcqs(text, topic, num_questions):
    """
    Generate MCQs with explanations from the given text.
    Returns a list of questions with proper structure.
    """
    prompt = f"""
    From the following text, generate exactly {num_questions} multiple choice questions.
    Topic focus: {topic}

    Make questions CONCEPTUAL and application-oriented:
    1. Prefer "why/how" and scenario-based reasoning questions.
    2. Avoid simple one-line factual recall unless absolutely necessary.
    3. Include plausible distractors that test understanding, not memorization.
    4. Keep language clear and exam-friendly.

    For each question, provide:
    1. A clear question text
    2. Exactly 4 options (A, B, C, D)
    3. The correct answer (one of the options)
    4. A short explanation of why the answer is correct

    Return ONLY a valid JSON array with no additional text. Use this exact format:
    [
      {{
        "id": 1,
        "question": "What is the time complexity of binary search?",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "correct_answer": "O(log n)",
        "explanation": "Binary search divides the sorted array into halves in each step, resulting in logarithmic time complexity."
      }}
    ]

    Text:
    {text[:5000]}
    """

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate conceptual MCQs in strict JSON format only. "
                        "Do not include any text outside JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()

        json_str = _extract_json_array(content)
        mcqs = json.loads(json_str)
        
        # Validate and ensure proper structure
        validated_mcqs = []
        for idx, mcq in enumerate(mcqs, 1):
            validated_mcq = {
                "id": mcq.get("id", idx),
                "question": mcq.get("question", ""),
                "options": mcq.get("options", []),
                "correct_answer": mcq.get("correct_answer", ""),
                "explanation": mcq.get("explanation", "")
            }
            if all([validated_mcq["question"], validated_mcq["options"], 
                    validated_mcq["correct_answer"], validated_mcq["explanation"]]):
                validated_mcqs.append(validated_mcq)
        
        return validated_mcqs if validated_mcqs else []
    
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return empty list
        print(f"Error parsing MCQ response: {e}")
        return []
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return []