from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# ==================== CONFIGURACIÓN GROQ ====================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Si no tienes variable de entorno, pon tu clave aquí (temporalmente)
if not GROQ_API_KEY:
    GROQ_API_KEY = "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"   # ← Tu clave real

client = Groq(api_key=GROQ_API_KEY)

# ==================== PROMPT PROFESIONAL ====================
SYSTEM_PROMPT = """Eres un abogado peruano experto en derecho del consumidor y laboral, especializado en estudiantes universitarios.

Analiza contratos según:
- Código de Protección y Defensa del Consumidor (art. 50°)
- Código Civil peruano
- Normativa SUNAFIL para prácticas preprofesionales

Clasifica cada cláusula:
- 🔴 ABUSIVA: Viola la ley. No estás obligado a aceptarla.
- 🟡 RIESGOSA: Te pone en desventaja. Negóciala.
- 🟢 NORMAL: Cláusula estándar.

Responde **solo** en este JSON:
{
  "tipo_contrato": "...",
  "nivel_riesgo_global": "ALTO / MEDIO / BAJO",
  "recomendacion_general": "...",
  "clausulas_riesgosas": [
    {
      "clausula_original": "...",
      "nivel": "ABUSIVA / RIESGOSA / NORMAL",
      "categoria": "...",
      "explicacion_simple": "...",
      "base_legal": "...",
      "accion_recomendada": "..."
    }
  ]
}
Sé claro, protector y conciso.
"""

def extraer_texto_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ""
    for page in doc:
        texto += page.get_text("text")
    return re.sub(r'\s+', ' ', texto).strip()

@app.post("/analizar")
async def analizar_contrato(file: Optional[UploadFile] = File(None), texto_directo: Optional[str] = Form(None)):
    if file:
        contenido = await file.read()
        texto = extraer_texto_pdf(contenido)
    elif texto_directo:
        texto = texto_directo.strip()
    else:
        raise HTTPException(400, detail="Debes subir un PDF o pegar texto")

    if len(texto) < 50:
        raise HTTPException(400, detail="El texto es muy corto")

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analiza este contrato según las leyes peruanas:\n\n{texto[:13000]}"}
            ],
            temperature=0.3,
            max_tokens=3500,
            response_format={"type": "json_object"}
        )

        resultado = json.loads(completion.choices[0].message.content)
        return resultado

    except Exception as e:
        raise HTTPException(500, detail=f"Error al analizar: {str(e)}")

@app.get("/")
def home():
    return {"mensaje": "Letra Chica API - En línea con Groq"}