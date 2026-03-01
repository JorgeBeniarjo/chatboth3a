import asyncio
import sys
import os
sys.path.insert(0, ".")

from services.sheets_loader import load_csv_data, get_knowledge_base
from services.chat_service import generate_chat_response
from models.chat_models import ChatRequest, Message

async def test():
    await load_csv_data()
    kb = get_knowledge_base()
    print(f"KB cargado: {len(kb)} chars")
    resp = await generate_chat_response(
        ChatRequest(messages=[Message(role="user", content="Hola, a que hora es el desayuno?")])
    )
    print("RESPUESTA:", resp)

asyncio.run(test())
