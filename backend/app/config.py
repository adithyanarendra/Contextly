import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_docs")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))
