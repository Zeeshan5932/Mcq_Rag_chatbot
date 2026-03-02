from langchain_groq import ChatGroq
from config import GROQ_API_KEY

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama3-70b-8192"
)

def generate_mcqs(text, topic, num_questions):
    prompt = f"""
    From the following text generate {num_questions} MCQs.
    Topic focus: {topic}

    Format output in JSON like:
    [
      {{
        "question": "",
        "options": ["A", "B", "C", "D"],
        "answer": "correct option"
      }}
    ]

    Text:
    {text[:5000]}
    """

    response = llm.invoke(prompt)
    return response.content