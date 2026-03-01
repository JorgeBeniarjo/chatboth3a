import os
import logging
from google import genai
from google.genai import types
from models.chat_models import ChatRequest
from services.sheets_loader import get_knowledge_base

logger = logging.getLogger(__name__)

def generate_chat_response(request: ChatRequest) -> str:
    """
    Calls the Gemini 1.5 Flash API using the loaded in-memory knowledge base
    as System Instructions.
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
            "Eres el asistente virtual oficial del Hotel Tres Anclas. "
            "Responde de manera amable, profesional y concisa a las preguntas de los usuarios "
            "utilizando EXCLUSIVAMENTE la siguiente información operativa en tiempo real:\n\n"
            "--- INICIO INFORMACIÓN OPERATIVA ---\n"
            f"{kb_text}\n"
            "--- FIN INFORMACIÓN OPERATIVA ---\n\n"
            "REGLAS:\n"
            "1. Si el usuario pregunta algo que no está en la información operativa proporcionada, indícale "
            "amablemente que no dispones de esa información y sugiérele contactar con Recepción.\n"
            "2. Usa formato claro e invierte tiempo en redactar párrafos legibles (puedes usar listas cortas si ayuda).\n"
            "3. Tu tono es servicial y directo.\n"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3, # Baja temperatura para que sea fáctico
        )
        
        # Preparación del historial de mensajes
        contents = []
        for msg in request.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg.content)])
            )
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        logger.exception(f"Error calling Gemini API:")
        return "Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo más tarde."
