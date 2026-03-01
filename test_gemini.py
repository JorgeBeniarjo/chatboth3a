import asyncio
from models.chat_models import ChatRequest, Message
from services.sheets_loader import load_csv_data
from services.chat_service import generate_chat_response

async def main():
    print("Cargando csv data...")
    await load_csv_data()
    print("Enviando mensaje...")
    request = ChatRequest(messages=[Message(role="user", content="Hola asistente")])
    try:
        response = generate_chat_response(request)
        print("Respuesta:", response)
    except Exception as e:
        import traceback
        with open("error_detalles.txt", "w", encoding="utf-8") as f:
            f.write(str(type(e)) + "\n")
            f.write(str(e) + "\n")
            f.write(traceback.format_exc())

asyncio.run(main())
