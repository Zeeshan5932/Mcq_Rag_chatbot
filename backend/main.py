from fastapi import FastAPI, UploadFile, File, Form
from services.pdf_reader import extract_text_from_pdf
from services.mcq_service import generate_mcqs
import json

app = FastAPI()

@app.post("/generate-mcqs/")
async def generate(
    file: UploadFile = File(...),
    topic: str = Form(...),
    num_questions: int = Form(...)
):
    text = extract_text_from_pdf(file.file)
    mcqs = generate_mcqs(text, topic, num_questions)

    return {"mcqs": mcqs}