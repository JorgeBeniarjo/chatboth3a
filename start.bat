@echo off
echo =======================================================
echo Iniciando Backend Asistente IA - Hotel Tres Anclas
echo =======================================================

cd %~dp0

if not exist venv (
    echo Creando entorno virtual local de Python...
    python -m venv venv
)

echo Activando entorno e instalando requerimientos...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo =======================================================
echo Servidor iniciado. No cierres esta ventana.
echo Si ya has puesto la GEMINI_API_KEY en el .env,
echo abre el archivo ../index.html en tu navegador.
echo =======================================================
uvicorn main:app --reload
