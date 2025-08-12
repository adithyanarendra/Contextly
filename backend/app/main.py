from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import upload, ask, export
from .database import engine
from . import models
import os
from .config import UPLOAD_DIR

app = FastAPI(title="Contextly Backend")  # or any project name you chose

origins = [
    "http://localhost:5173",  # Vite default dev server
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# create DB tables
models.Base.metadata.create_all(bind=engine)

# ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.include_router(upload.router)
app.include_router(ask.router)
app.include_router(export.router)


@app.get("/")
def root():
    return {"status": "ok"}
