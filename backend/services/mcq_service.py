from langchain_groq import ChatGroq
from config import GROQ_API_KEY
import json
import re

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama3-70b-8192"
)

def generate_mcqs(text, topic, num_questions):
    """
    Generate MCQs with explanations from the given text.
    Returns a list of questions with proper structure.
    """
    prompt = f"""
    From the following text, generate exactly {num_questions} multiple choice questions.
    Topic focus: {topic}

    For each question, provide:
    1. A clear question text
    2. Exactly 4 options (A, B, C, D)
    3. The correct answer (one of the options)
    4. A brief explanation of why the answer is correct

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
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Try to extract JSON from the response
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            mcqs = json.loads(json_str)
        else:
            mcqs = json.loads(content)
        
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