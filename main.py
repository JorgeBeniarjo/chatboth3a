import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from models.chat_models import ChatRequest
from services.kb_loader import load_kb_from_github
from services.chat_service import generate_chat_response

# Aseguramos que el directorio estático exista
os.makedirs("static", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cargar la base de conocimiento desde GitHub al arrancar el servidor
    await load_kb_from_github()
    yield

app = FastAPI(title="Hotel Tres Anclas - API Asistente IA", lifespan=lifespan)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.hoteltresanclas.com",
        "https://hoteltresanclas.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (widget.js, widget.css)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Backend Asistente IA operativa."}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint principal para recibir mensajes del widget."""
    response_text = await generate_chat_response(request)
    return {"reply": response_text}

@app.post("/reload")
async def reload_kb(secret: str = ""):
    """
    Recarga la base de conocimiento desde GitHub sin reiniciar el servidor.
    Requiere la clave secreta definida en la variable RELOAD_SECRET.
    """
    expected_secret = os.getenv("RELOAD_SECRET", "")
    if not expected_secret or secret != expected_secret:
        raise HTTPException(status_code=403, detail="Clave incorrecta o no configurada.")

    success = await load_kb_from_github()
    if success:
        return {"status": "ok", "message": "✅ Base de conocimiento recargada correctamente desde GitHub."}
    else:
        raise HTTPException(status_code=500, detail="Error al recargar la base de conocimiento. Revisa los logs.")
