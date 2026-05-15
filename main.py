from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import fitz
import os
import json
import re
from groq import Groq
from typing import Optional

app = FastAPI(title="Letra Chica")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== GROQ ====================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    GROQ_API_KEY = "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"  # Temporal

client = Groq(api_key=GROQ_API_KEY)

# ==================== PROMPT ====================
SYSTEM_PROMPT = """Eres un abogado peruano experto..."""  # (mantén tu prompt actual)

def extraer_texto_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ""
    for page in doc:
        texto += page.get_text("text")
    return re.sub(r'\s+', ' ', texto).strip()

@app.post("/analizar")
async def analizar_contrato(file: Optional[UploadFile] = File(None), texto_directo: Optional[str] = Form(None)):
    # (mantén esta función igual como la tienes)
    ...

# ==================== SERVIR FRONTEND ====================
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def home():
    return {"mensaje": "Letra Chica API - En línea"}
