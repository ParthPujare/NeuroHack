@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies (this may take a while)...
python -m pip install -r requirements.txt
python -m pip install requests tqdm

echo Downloading Llama 3.2 Model (approx 3GB)...
python download_model.py

echo Starting NeuroHack Backend...
start "NeuroHack Backend" uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

echo Starting NeuroHack Frontend...
start "NeuroHack Frontend" streamlit run frontend/app.py

echo NeuroHack started! Check the new windows.
pause
