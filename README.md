# MCQ Quiz Application with Result Evaluation

A complete MCQ quiz generation and evaluation system built with FastAPI (backend) and Streamlit (frontend). Generate quiz questions from PDF documents and get instant evaluation with detailed explanations.

## Features

✨ **Core Features:**
- 📄 PDF upload and text extraction
- 🤖 AI-powered MCQ generation using Groq LLM (Llama 3.2)
- 📋 Clean, user-friendly quiz interface
- 📊 Instant result evaluation with visual feedback
- 💡 Detailed explanations for each answer
- 🎨 Color-coded results (green for correct, red for wrong)
- 💾 Session state management to prevent data loss

🔧 **Technical Highlights:**
- Modular, production-ready code architecture
- Clean separation of concerns (API, evaluation, UI)
- Comprehensive error handling
- CORS enabled for local development
- Proper type hints and documentation

## Project Structure

```
Mcq_Rag_chatbot/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── requirements.txt         # Backend dependencies
│   ├── services/
│   │   ├── mcq_service.py     # MCQ generation logic
│   │   └── pdf_reader.py      # PDF text extraction
│   └── utils/
│       └── prompt_template.py  # Utility functions
│
├── frontend/
│   ├── app.py                  # Main Streamlit application
│   ├── api_client.py           # Backend API communication
│   ├── evaluator.py            # Answer evaluation logic
│   ├── ui_components.py        # Reusable UI components
│   ├── requirements.txt         # Frontend dependencies
│   └── .env.example            # Environment configuration template
│
└── README.md                    # This file
```

## Setup Instructions

### 1. Clone Repository and Install Dependencies

```bash
# If not already cloned
git clone <repository-url>
cd Mcq_Rag_chatbot
```

### 2. Backend Setup

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Create .env file with your Groq API key
echo GROQ_API_KEY=your_groq_api_key_here > .env
```

**Get your Groq API key:**
- Visit https://console.groq.com
- Sign up/Log in
- Generate an API key
- Add it to `.env` file in the backend directory

### 3. Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install frontend dependencies (use same virtual environment)
pip install -r requirements.txt

# Create .env file (optional - default backend URL is localhost:8000)
copy .env.example .env
# Edit .env if your backend is running on a different address
```

### 4. Run the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

This will automatically open your browser to: `http://localhost:8501`

## Usage Guide

### Basic Workflow

1. **Upload PDF**
   - Click on the file uploader in the left sidebar
   - Select a PDF document

2. **Configure Quiz**
   - Choose a topic from the dropdown (Data Structures, Algorithms, etc.)
   - Set the number of questions (2-20) using the slider

3. **Generate MCQs**
   - Click the "Generate MCQs" button
   - Wait for the AI to generate questions (usually 10-30 seconds)

4. **Take Quiz**
   - Read each question carefully
   - Select your answer from the radio buttons
   - Move to the next question

5. **Submit & Review**
   - Click "Submit Quiz" to submit your answers
   - See your overall score and statistics
   - Review each question with detailed explanations
   - Click "Retake Quiz" to try again or upload a new PDF

## API Endpoints

### Generate MCQs
**POST** `/generate-mcqs/`

**Request:**
- `file` (FormData): PDF file
- `topic` (string): Quiz topic
- `num_questions` (integer): Number of questions

**Response:**
```json
{
  "success": true,
  "questions": [
    {
      "id": 1,
      "question": "What is the time complexity of binary search?",
      "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
      "correct_answer": "O(log n)",
      "explanation": "Binary search divides the sorted array into halves in each step, resulting in logarithmic time complexity."
    }
  ],
  "error": null
}
```

## Code Examples

### Evaluating Answers (evaluator.py)

```python
from evaluator import evaluate_answers, calculate_statistics

# Evaluate user answers
results = evaluate_answers(questions, user_answers)

# Calculate statistics
stats = calculate_statistics(results)
print(f"Score: {stats['score']}")
print(f"Percentage: {stats['percentage']}%")
```

### Making API Calls (api_client.py)

```python
from api_client import APIClient

api_client = APIClient(base_url="http://localhost:8000")
questions = api_client.generate_mcqs(pdf_file, "Python", 5)
```

### Rendering Results (ui_components.py)

```python
from ui_components import render_result_summary, render_question_review

# Render summary
render_result_summary(stats)

# Render each question review
for idx, result in enumerate(evaluation_results, 1):
    render_question_review(idx, result)
```

## Configuration

### Backend Environment Variables (.env)

```
GROQ_API_KEY=your_groq_api_key_here
```

### Frontend Environment Variables (.env)

```
BACKEND_URL=http://localhost:8000
```

## Error Handling

The application handles common errors gracefully:

- **Missing PDF**: Prompts user to upload a file
- **API Connection Error**: Shows error message if backend is not running
- **Empty MCQ Response**: Alerts user and suggests retrying
- **Invalid Backend Response**: Validates response structure and handles malformed data
- **PDF Processing Error**: Catches and reports PDF extraction issues

## Extending the Application

### Adding More Topics

Edit `app.py` in the Streamlit app:

```python
topic = st.selectbox(
    "📚 Select Topic",
    options=[
        "Data Structures",
        "Algorithms",
        "Your New Topic",  # Add here
        # ...
    ]
)
```

### Adding Quiz Timer

Extend `app.py`:

```python
import time
from datetime import timedelta

start_time = st.session_state.get("start_time", time.time())
elapsed = time.time() - start_time
remaining = max(0, 300 - elapsed)  # 5 minute limit

st.metric("Time Remaining", f"{int(remaining)}s")
```

### Adding Download Report

Implement in `ui_components.py`:

```python
def render_downloadable_report(stats, evaluation_results):
    import pandas as pd
    
    data = [{
        'Question': r['question'],
        'Your Answer': r['user_answer'],
        'Correct Answer': r['correct_answer'],
        'Status': 'Correct' if r['is_correct'] else 'Wrong'
    } for r in evaluation_results]
    
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    
    return csv
```

### Retry Wrong Questions

Add to `app.py`:

```python
if st.button("🔁 Retry Wrong Questions"):
    wrong_indices = [r['index'] for r in evaluation_results if not r['is_correct']]
    st.session_state.questions = [questions[i] for i in wrong_indices]
    reset_quiz()
    st.rerun()
```

## Performance Tips

1. **PDF Size**: Use PDFs under 20MB for faster processing
2. **Question Count**: Start with 5-10 questions for quick generation
3. **Backend Response**: First request to Groq API may be slow (requires download of model)
4. **Browser**: Use modern browsers (Chrome, Firefox, Edge) for best experience

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
uvicorn main:app --port 8001
```

### Streamlit won't connect to backend
```bash
# Ensure backend is running
# Check .env file for correct BACKEND_URL
# Try http://host.docker.internal:8000 if using Docker

# Check network
curl http://localhost:8000/docs
```

### API returns errors
- Check Groq API key is valid: https://console.groq.com
- Check PDF is readable and contains text
- Check model availability: https://console.groq.com/keys

### Session state issues
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/  # macOS/Linux
rmdir %USERPROFILE%\.streamlit\  # Windows
```

## Tech Stack

**Backend:**
- FastAPI 0.115.5
- Uvicorn 0.32.1
- LangChain 0.3.7
- Groq API (Llama 3.2 70B)
- PyPDF 5.1.0
- Python 3.10+

**Frontend:**
- Streamlit 1.35.0
- Requests 2.31.0
- Python 3.10+

**Optional Additions:**
- pandas (for reports)
- reportlab (for PDF generation)

## Future Enhancements

🚀 Planned Features:
- ✅ Quiz timer functionality
- ✅ Question retry mechanism
- ✅ Download result reports (PDF/CSV)
- ✅ Multiple quiz attempt tracking
- ✅ Difficulty-based question generation
- ✅ Category-wise performance analysis
- ✅ User authentication and progress tracking
- ✅ Mobile-responsive design improvements

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section
2. Review the code comments
3. Check the API response format
4. Verify environment configuration

---

**Last Updated:** March 2026
**Version:** 1.0.0
