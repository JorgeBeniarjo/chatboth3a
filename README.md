# Asistente Virtual IA - Hotel Tres Anclas

Backend desarrollado en Python (FastAPI) y Frontend en Vanilla JS para proveer a la web del hotel de un asistente IA en tiempo real (Gemini 1.5 Flash).

## 🚀 Despliegue Local Rápidamente

1. Asegúrate de tener **Python 3.9+** instalado en tu PC.
2. Abre el archivo `.env` en esta carpeta e introduce tu clave real de Gemini (`GEMINI_API_KEY`).
3. Haz doble clic en el archivo `start.bat` (si estás en Windows). Esto instalará automáticamente las dependencias en un entorno virtual e iniciará el servidor backend.
4. Con el servidor corriendo, ve a la carpeta anterior y abre `index.html` en tu navegador para interactuar con el widget web de prueba.

## ⚙️ Despliegue Manual por Consola

1. Abre una terminal en esta carpeta (`backend`).
2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Mac/Linux:
   source venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicia el servidor:
   ```bash
   uvicorn main:app --reload
   ```

## ☁️ Despliegue en Producción (Render, Railway, Cloud Run)

Para desplegar este backend en un servicio Cloud Platform:

1. **Variables de Entorno**: Configura en la plataforma destino las variables `GEMINI_API_KEY` y `CSV_URLS`.
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000` (o `$PORT` dependiendo del PaaS).
4. **CORS (Seguridad)**: Edita `main.py` y cambia `allow_origins=["*"]` por los dominios exactos de tu web oficial (ej. `["https://hoteltresanclas.com"]`).
5. **Inyección en la Web Oficial**: Añade esta etiqueta antes del cierre de `</body>` en tu web de producción, cambiando la URL local por la de tu backend desplegado:
   `<script src="https://TU-GCP-RENDER-URL.com/static/widget.js" defer></script>`
