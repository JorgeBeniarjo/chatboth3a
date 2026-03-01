import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from models.chat_models import ChatRequest
from services.sheets_loader import load_csv_data
from services.chat_service import generate_chat_response

# Aseguramos que el directorio estático exista
os.makedirs("static", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cargar los datos del CSV a RAM al iniciar el servidor
    await load_csv_data()
    yield

app = FastAPI(title="Hotel Tres Anclas - API Asistente IA", lifespan=lifespan)

# Configuración CORS: 
# Restringido para producción al dominio oficial del hotel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.hoteltresanclas.com",
        "https://hoteltresanclas.com",
        "http://localhost:8000",   # Para pruebas locales
        "http://127.0.0.1:8000"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta estática para servir widget.js y widget.css
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Backend Asistente IA operativa."}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para recibir mensajes del widget y devolver la respuesta de Gemini.
    """
    response_text = await generate_chat_response(request)
    return {"reply": response_text}
