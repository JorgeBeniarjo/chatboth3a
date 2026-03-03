import asyncio
import sys
sys.path.insert(0, ".")

from services.kb_loader import load_kb_from_github, get_knowledge_base
from services.chat_service import generate_chat_response
from models.chat_models import ChatRequest, Message

async def test():
    print("=== TEST 1: Cargar KB desde GitHub ===")
    success = await load_kb_from_github()
    print(f"Carga exitosa: {success}")
    kb = get_knowledge_base()
    print(f"Tamaño KB: {len(kb)} chars")
    print(f"Primeros 300 chars:\n{kb[:300]}\n")

    print("=== TEST 2: Pregunta sobre horario de relax ===")
    resp = await generate_chat_response(
        ChatRequest(messages=[Message(role="user", content="A qué hora abre el centro de relax?")])
    )
    print(f"Respuesta: {resp}\n")

    print("=== TEST 3: Comando /reload ===")
    resp2 = await generate_chat_response(
        ChatRequest(messages=[Message(role="user", content="/reload hotelanclas2025")])
    )
    print(f"Respuesta reload: {resp2}")

asyncio.run(test())
