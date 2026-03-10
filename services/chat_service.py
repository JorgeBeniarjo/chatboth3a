import os
import logging
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from models.chat_models import ChatRequest
from services.kb_loader import get_knowledge_base, load_kb_from_github

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3

async def generate_chat_response(request: ChatRequest) -> str:
    """
    Calls the Gemini API using the in-memory knowledge base (loaded from GitHub .md).
    Includes multilingual support, sentiment detection, feedback loop, and retry logic.
    Also handles the secret /reload command to refresh knowledge base on demand.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_api_key_aqui":
        logger.error("GEMINI_API_KEY no configurada correctamente.")
        return "Lo siento, el servicio no está configurado correctamente (API Key faltante). Por favor, avisa a recepción."

    # Detección del comando secreto de recarga
    last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
    reload_secret = os.getenv("RELOAD_KEY", "")
    if reload_secret and last_user_msg.strip() == f"/reload {reload_secret}":
        success = await load_kb_from_github()
        if success:
            return "♻️ ¡Base de conocimiento recargada correctamente desde GitHub! Ya tengo la información actualizada."
        else:
            return "❌ Error al recargar la base de conocimiento. Revisa los logs del servidor."

    try:
        client = genai.Client(api_key=api_key)

        # Inyección de contexto RAG desde GitHub
        kb_text = get_knowledge_base()
        system_instruction = (
            "Eres el asistente virtual oficial del Hotel Tres Anclas en Gandía. "
            "Tu objetivo es ser servicial, profesional y ayudar a convertir consultas en reservas.\n\n"
            "INFORMACIÓN BASE INAMOVIBLE (Prioridad Máxima):\n"
            "- Nombre: Hotel Tres Anclas\n"
            "- Dirección: Carrer de la Valldigna, 11, 46730 Platja de Gandia, Valencia, España.\n"
            "- Teléfono de Recepción: +34 962 84 82 40\n"
            "- Web Oficial: https://www.hoteltresanclas.com\n\n"
            "INFORMACIÓN OPERATIVA ACTUALIZADA (RAG desde GitHub):\n"
            "--- INICIO ---\n"
            f"{kb_text}\n"
            "--- FIN ---\n\n"
            "REGLAS CRÍTICAS DE COMPORTAMIENTO:\n"
            "1. LENGUAJE: Responde SIEMPRE en el mismo idioma en el que te hable el usuario "
            "(español, inglés, francés, alemán, etc.), pero usa siempre los datos exactos.\n"
            "2. DESCONOCIMIENTO: Si la respuesta NO está ni en la información base ni en la operativa, responde EXACTAMENTE: "
            "'[CODE_UNANSWERED] Lo siento, no dispongo de esa información específica en este momento. "
            "Por favor, contacta con Recepción (Tel: +34 962 84 82 40) para ayudarte mejor.'\n"
            "3. RESERVAS: Si el usuario muestra interés en reservar, precios o disponibilidad, consulta la "
            "información operativa para obtener el enlace de reservas o la web oficial y facilítalo.\n"
            "4. TONO Y FORMATO: Sé amable y usa emojis de forma sutil (✨, 🏨). "
            "Usa negritas para datos importantes como horarios o teléfonos.\n"

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
                break
            except ClientError as e:
                if e.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = 2 ** (attempt + 1)
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
                    raise

        # Feedback Loop: registrar estadísticas de uso
        is_unanswered = "[CODE_UNANSWERED]" in reply_text
        if is_unanswered:
            reply_text = reply_text.replace("[CODE_UNANSWERED]", "").strip()
            # Seguimos registrando en Fallos como antes
            asyncio.create_task(log_unanswered_question_to_sheets(last_user_msg))
        
        # Registramos SIEMPRE en Estadísticas
        asyncio.create_task(log_interaction_to_sheets(
            session_id=request.session_id,
            question=last_user_msg,
            answer=reply_text,
            is_unanswered=is_unanswered
        ))

        return reply_text

    except Exception as e:
        logger.exception("Error calling Gemini API:")
        return "Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo más tarde."


async def log_interaction_to_sheets(session_id: str, question: str, answer: str, is_unanswered: bool):
    """Envía todas las interacciones a la pestaña de Estadísticas."""
    import httpx
    webhook_url = os.getenv("FEEDBACK_WEBHOOK_URL")

    if not webhook_url:
        return

    try:
        data = {
            "type": "stat",
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "status": "fail" if is_unanswered else "ok"
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            await client.post(webhook_url, json=data)
    except Exception as e:
        logger.error(f"Error enviando estadística: {e}")


async def log_unanswered_question_to_sheets(question: str):
    """Envía la pregunta sin respuesta a Google Sheets (Hoja Fallos)."""
    import httpx
    webhook_url = os.getenv("FEEDBACK_WEBHOOK_URL")

    if not webhook_url:
        return

    try:
        # Mantenemos el formato exacto que ya le funciona al usuario
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            await client.post(webhook_url, json={"question": question})
    except Exception as e:
        logger.error(f"Error enviando fallo: {e}")
