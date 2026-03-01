import os
import logging
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from models.chat_models import ChatRequest
from services.sheets_loader import get_knowledge_base

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3

async def generate_chat_response(request: ChatRequest) -> str:
    """
    Calls the Gemini API using the loaded in-memory knowledge base as System Instructions.
    Includes multilingual support, sentiment detection, feedback loop, and retry logic.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_api_key_aqui":
        logger.error("GEMINI_API_KEY no configurada correctamente.")
        return "Lo siento, el servicio no está configurado correctamente (API Key faltante). Por favor, avisa a recepción."

    try:
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
            "1. LENGUAJE: Responde SIEMPRE en el mismo idioma en el que te hable el usuario "
            "(español, inglés, francés, alemán, etc.), pero usa siempre los datos exactos.\n"
            "2. DESCONOCIMIENTO: Si la respuesta NO está ni en la información base ni en la operativa, responde EXACTAMENTE: "
            "'[CODE_UNANSWERED] Lo siento, no dispongo de esa información específica en este momento. "
            "Por favor, contacta con Recepción (Tel: +34 962 84 82 40) para ayudarte mejor.'\n"
            "3. RESERVAS: Si el usuario muestra interés en reservar, precios o disponibilidad, invítale a usar "
            "nuestro motor de reservas oficial: https://www.hoteltresanclas.com/es/reservas/\n"
            "4. TONO Y FORMATO: Sé amable y usa emojis de forma sutil (✨, 🏨). "
            "Usa negritas para datos importantes como horarios o teléfonos.\n"
            "5. SENTIMIENTO: Si detectas que el usuario está muy enfadado o expresa una queja grave, "
            "añade al final: 'Aviso: He pasado nota de tu malestar al departamento correspondiente.'\n"
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

        # Llamada asíncrona a Gemini con reintentos para errores 429
        reply_text = ""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=config
                )
                reply_text = response.text
                break  # Éxito, salimos del bucle de reintentos
            except ClientError as e:
                if e.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = 2 ** (attempt + 1)  # 2s, 4s
                        logger.warning(f"Cuota excedida (429). Reintento en {wait_time}s... (intento {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error("Cuota de la API agotada tras todos los reintentos.")
                        return (
                            "Lo sentimos, nuestro asistente virtual está muy ocupado en este momento. "
                            "Para consultas urgentes, contáctanos directamente: "
                            "**Tel: +34 962 84 82 40**. ¡Intentamos mejorar el servicio! ✨"
                        )
                else:
                    raise  # Otro tipo de error, lo propagamos al except exterior

        # Lógica de Feedback Loop (registro de preguntas sin respuesta en Google Sheets)
        if "[CODE_UNANSWERED]" in reply_text:
            last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "Desconocida")
            asyncio.create_task(log_unanswered_question_to_sheets(last_user_msg))
            reply_text = reply_text.replace("[CODE_UNANSWERED]", "").strip()

        return reply_text

    except Exception as e:
        logger.exception("Error calling Gemini API:")
        return "Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo más tarde."


async def log_unanswered_question_to_sheets(question: str):
    """Envía la pregunta sin respuesta a Google Sheets vía Webhook."""
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
