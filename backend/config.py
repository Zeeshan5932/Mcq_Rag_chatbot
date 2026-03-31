import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

GROQ_API_KEY = (os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'"))