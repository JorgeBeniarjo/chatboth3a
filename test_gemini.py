import asyncio
import os
from models.chat_models import ChatRequest, Message
from services.sheets_loader import load_csv_data
from services.chat_service import generate_chat_response

async def main():
    print("Cargando csv data...")
    await load_csv_data()
    print("Enviando mensaje...")
    request = ChatRequest(messages=[Message(role="user", content="Hola asistente")])
    try:
        # Ahora es asíncrono
        response = await generate_chat_response(request)
        print("Respuesta:", response)
    except Exception as e:
        import traceback
        error_msg = f"{type(e)}\n{e}\n{traceback.format_exc()}"
        print("Error detectado:")
        print(error_msg)
        with open("error_detalles.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)

if __name__ == "__main__":
    asyncio.run(main())
