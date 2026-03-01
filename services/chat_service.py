import os
import logging
from google import genai
from google.genai import types
from models.chat_models import ChatRequest
from services.sheets_loader import get_knowledge_base

logger = logging.getLogger(__name__)

async def generate_chat_response(request: ChatRequest) -> str:
    """
    Calls the Gemini 1.5 Flash API using the loaded in-memory knowledge base
    as System Instructions. Includes multilingual support, sentiment detection logic,
    and a feedback loop for unanswered questions. (Async version)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_api_key_aqui":
        logger.error("GEMINI_API_KEY no configurada correctamente.")
        return "Lo siento, el servicio no está configurado correctamente (API Key faltante). Por favor, avisa a recepción."
        
    try:
        # Usamos el cliente asíncrono
        client = genai.Client(api_key=api_key)
        
        # Inyección de contexto RAG
        kb_text = get_knowledge_base()
        system_instruction = (
            "Eres el asistente virtual oficial del Hotel Tres Anclas en Gandía. "
            "Tu objetivo es ser servicial, profesional y ayudar a convertir consultas en reservas.\n\n"
            "INFORMACIÓN BASE INAMOVIBLE (Prioridad Máxima):\n"
            "- Nombre: Hotel Tres Anclas\n"
            "- Dirección: Carrer de la Valldigna, 11, 46730 Platja de Gandia, Valencia, España.\n"
            "- Teléfono de Recepción: +34 962 84 82 40\n"
            "- Web Oficial: https://www.hoteltresanclas.com\n\n"
            "INFORMACIÓN OPERATIVA EN TIEMPO REAL (RAG):\n"
            "--- INICIO ---\n"
            f"{kb_text}\n"
            "--- FIN ---\n\n"
            "REGLAS CRÍTICAS DE COMPORTAMIENTO:\n"
            "1. LENGUAJE: Responde SIEMPRE en el mismo idioma en el que te hable el usuario...\n"
            "2. DESCONOCIMIENTO: Si la respuesta NO está ni en la información base ni en la operativa, responde EXACTAMENTE: "
            "'[CODE_UNANSWERED] Lo siento, no dispongo de esa información específica en este momento. Por favor, contacta con Recepción (Tel: +34 962 84 82 40) para ayudarte mejor.'\n"
            "3. RESERVAS: Si el usuario muestra interés en reservar, precios o disponibilidad, invítale a usar nuestro motor de reservas oficial: "
            "https://www.hoteltresanclas.com/es/reservas/\n"
            "4. TONO Y FORMATO: Sé amable y usa emojis de forma sutil (✨, 🏨). Usa negritas para datos importantes como horarios o teléfonos.\n"
            "5. SENTIMIENTO: Si detectas que el usuario está muy enfadado o expresa una queja grave, añade al final de tu respuesta: "
            "'Aviso: He pasado nota de tu malestar al departamento correspondiente para que lo revisen cuanto antes.'\n"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3, 
        )
        
        # Preparación del historial de mensajes
        contents = []
        for msg in request.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg.content)])
            )
            
        # Llamada asíncrona a Gemini
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        
        reply_text = response.text

        # Lógica de Feedback Loop (Enviamos a Sheets sin esperar respuesta)
        if "[CODE_UNANSWERED]" in reply_text:
            last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "Desconocida")
            # En un entorno async, esto ahora funcionará correctamente
            import asyncio
            asyncio.create_task(log_unanswered_question_to_sheets(last_user_msg))
            reply_text = reply_text.replace("[CODE_UNANSWERED]", "").strip()

        return reply_text
        
    except Exception as e:
        logger.exception(f"Error calling Gemini API:")
        return "Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo más tarde."

async def log_unanswered_question_to_sheets(question: str):
    """Envía la pregunta que la IA no supo responder a Google Sheets vía Webhook."""
    import httpx
    webhook_url = os.getenv("FEEDBACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("FEEDBACK_WEBHOOK_URL no configurada. No se pudo registrar la pregunta.")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            await client.post(webhook_url, json={"question": question})
            logger.info(f"Pregunta sin respuesta registrada en Google Sheets: {question}")
    except Exception as e:
        logger.error(f"Error enviando feedback a Google Sheets: {e}")
