from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.mcq_service import generate_mcqs
from services.pdf_reader import extract_text_from_pdf

app = FastAPI()

# Add CORS middleware to allow requests from Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-mcqs/")
async def generate(
    file: UploadFile = File(...),
    topic: str = Form(...),
    num_questions: int = Form(...)
):
    """
    Generate MCQs from uploaded PDF.
    
    Returns:
    {
        "success": bool,
        "questions": [
            {
                "id": int,
                "question": str,
                "options": list,
                "correct_answer": str,
                "explanation": str
            }
        ],
        "error": str (if any)
    }
    """
    try:
        text = extract_text_from_pdf(file.file)
        if not text:
            return {
                "success": False,
                "questions": [],
                "error": "Could not extract text from PDF"
            }
        
        mcqs = generate_mcqs(text, topic, num_questions)
        
        if not mcqs:
            return {
                "success": False,
                "questions": [],
                "error": "Failed to generate MCQs from the provided text"
            }
        
        return {
            "success": True,
            "questions": mcqs,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "questions": [],
            "error": str(e)
        }


def evaluate_answers(
    questions: List[Dict[str, Any]],
    user_answers: Dict[int, str]
) -> List[Dict[str, Any]]:
    """Compare user answers against backend-provided correct answers."""
    evaluation_results: List[Dict[str, Any]] = []

    for idx, question in enumerate(questions):
        user_answer = user_answers.get(idx)
        correct_answer = question.get("correct_answer", "")

        evaluation_results.append(
            {
                "id": question.get("id", idx + 1),
                "question": question.get("question", ""),
                "options": question.get("options", []),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": user_answer == correct_answer,
                "explanation": question.get("explanation", "No explanation provided."),
            }
        )

    return evaluation_results


def calculate_statistics(evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute score summary for the submitted quiz."""
    total_questions = len(evaluation_results)
    correct_answers = sum(1 for result in evaluation_results if result["is_correct"])
    wrong_answers = total_questions - correct_answers
    percentage = (correct_answers / total_questions * 100) if total_questions else 0.0

    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "percentage": round(percentage, 2),
    }


def _validate_questions(questions: Any) -> bool:
    """Validate backend response payload before rendering quiz."""
    if not isinstance(questions, list) or not questions:
        return False

    required_fields = {"id", "question", "options", "correct_answer", "explanation"}
    for item in questions:
        if not isinstance(item, dict):
            return False
        if not required_fields.issubset(item.keys()):
            return False
        if not isinstance(item.get("options"), list) or len(item["options"]) < 2:
            return False
        if item.get("correct_answer") not in item.get("options", []):
            return False
    return True


def _fetch_mcqs_from_api(
    uploaded_file: Any,
    topic: str,
    num_questions: int,
    backend_url: str,
) -> List[Dict[str, Any]]:
    """Call backend endpoint and return validated questions list."""
    import requests

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    data = {"topic": topic, "num_questions": num_questions}

    response = requests.post(
        f"{backend_url.rstrip('/')}/generate-mcqs/",
        files=files,
        data=data,
        timeout=90,
    )
    response.raise_for_status()

    payload = response.json()
    if not payload.get("success"):
        error_message = payload.get("error") or "Backend returned an unknown error"
        raise ValueError(error_message)

    questions = payload.get("questions", [])
    if not _validate_questions(questions):
        raise ValueError("Invalid backend response: expected questions with answer and explanation")

    return questions


def run_streamlit_app() -> None:
    """Run Streamlit UI for quiz generation, submission, and evaluation."""
    import os

    import streamlit as st

    st.set_page_config(page_title="MCQ Quiz App", page_icon="MCQ", layout="wide")

    st.title("MCQ Quiz Application")
    st.caption("Generate MCQs from PDF, submit quiz, and review detailed results")

    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = []

    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    with st.sidebar:
        st.header("Quiz Setup")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        topic = st.selectbox(
            "Select Topic",
            options=[
                "Data Structures",
                "Algorithms",
                "Database",
                "Web Development",
                "Python",
                "Machine Learning",
                "Other",
            ],
        )
        num_questions = st.slider("Number of MCQs", min_value=2, max_value=25, value=5)

        generate_clicked = st.button("Generate MCQs", type="primary", use_container_width=True)
        reset_clicked = st.button("Reset Quiz", use_container_width=True)

    if reset_clicked:
        st.session_state.questions = []
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.evaluation_results = []
        st.rerun()

    if generate_clicked:
        if uploaded_file is None:
            st.error("Please upload a PDF before generating questions.")
        else:
            with st.spinner("Generating MCQs from backend API..."):
                try:
                    questions = _fetch_mcqs_from_api(
                        uploaded_file=uploaded_file,
                        topic=topic,
                        num_questions=num_questions,
                        backend_url=backend_url,
                    )
                    if not questions:
                        st.error("Backend returned an empty MCQ list.")
                    else:
                        st.session_state.questions = questions
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.evaluation_results = []
                        st.success(f"Loaded {len(questions)} questions.")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Failed to generate MCQs: {exc}")

    if not st.session_state.questions:
        st.info("Upload a PDF and click Generate MCQs to start the quiz.")
        return

    if not st.session_state.quiz_submitted:
        st.subheader("Answer Questions")
        with st.form("quiz_form"):
            answers: Dict[int, str] = {}
            for idx, question in enumerate(st.session_state.questions):
                st.markdown(f"### Q{idx + 1}. {question['question']}")
                selected = st.radio(
                    "Options",
                    options=question["options"],
                    key=f"question_{idx}",
                    index=None,
                )
                answers[idx] = selected

            submitted = st.form_submit_button("Submit Quiz", use_container_width=True)

        if submitted:
            unanswered = [idx + 1 for idx, value in answers.items() if value is None]
            if unanswered:
                st.error("Please answer all questions before submitting.")
            else:
                st.session_state.user_answers = answers
                st.session_state.evaluation_results = evaluate_answers(
                    st.session_state.questions,
                    st.session_state.user_answers,
                )
                st.session_state.quiz_submitted = True
                st.rerun()
        return

    stats = calculate_statistics(st.session_state.evaluation_results)
    st.subheader("Result Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Questions", stats["total_questions"])
    c2.metric("Correct", stats["correct_answers"])
    c3.metric("Wrong", stats["wrong_answers"])
    c4.metric("Percentage", f"{stats['percentage']}%")

    st.markdown("---")
    st.subheader("Detailed Review")

    for idx, result in enumerate(st.session_state.evaluation_results, start=1):
        is_correct = result["is_correct"]
        status_text = "Correct" if is_correct else "Wrong"
        status_color = "#eaf8ef" if is_correct else "#fbeaea"
        border_color = "#1f8f3a" if is_correct else "#c0392b"

        st.markdown(
            (
                f"<div style='border-left:5px solid {border_color}; background:{status_color};"
                " padding:12px; border-radius:8px; margin-bottom:10px;'>"
                f"<b>Q{idx}.</b> {result['question']}<br>"
                f"<b>Status:</b> {status_text}<br>"
                f"<b>Your Answer:</b> {result['user_answer']}<br>"
                f"<b>Correct Answer:</b> {result['correct_answer']}<br>"
                f"<b>Explanation:</b> {result['explanation']}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        option_index = 0
        for option in result["options"]:
            option_index += 1
            option_label = f"{option_index}. {option}"
            if option == result["correct_answer"]:
                st.markdown(f":green[{option_label}]")
            elif option == result["user_answer"] and not is_correct:
                st.markdown(f":red[{option_label}]")
            else:
                st.write(option_label)

        st.markdown("---")


if __name__ == "__main__":
    run_streamlit_app()