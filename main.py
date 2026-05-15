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
    GROQ_API_KEY = "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"  # ← Cambia si es necesario

client = Groq(api_key=GROQ_API_KEY)

# ==================== PROMPT MEJORADO ====================
SYSTEM_PROMPT = """Eres un abogado peruano experto en derecho del consumidor y laboral, especializado en estudiantes universitarios.

Analiza contratos según el Código de Protección al Consumidor (art. 50), Código Civil y normativa SUNAFIL.

Clasifica cada cláusula:
- 🔴 ABUSIVA: Viola la ley. No estás obligado a aceptarla.
- 🟡 RIESGOSA: Te pone en desventaja. Negóciala.
- 🟢 NORMAL: Cláusula estándar.

**REGLA OBLIGATORIA**: Responde SIEMPRE con un JSON válido y completo. Nunca omitas campos.

{
  "tipo_contrato": "Arrendamiento / Prácticas Preprofesionales / Servicios Educativos / General",
  "nivel_riesgo_global": "ALTO / MEDIO / BAJO",
  "recomendacion_general": "Escribe aquí una recomendación clara y corta (obligatorio)",
  "clausulas_riesgosas": [
    {
      "clausula_original": "texto de la cláusula",
      "nivel": "ABUSIVA / RIESGOSA / NORMAL",
      "categoria": "Económico / Legal / Renovación / etc",
      "explicacion_simple": "explicación breve y clara",
      "base_legal": "Explicación de la norma",
      "accion_recomendada": "qué debe hacer el estudiante"
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

# ==================== SERVIR FRONTEND ====================
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def home():
    return {"mensaje": "Letra Chica API - En línea con Groq"}
