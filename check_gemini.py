import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

print(f"Package version: {genai.__version__}")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    print("Listing models...")
    for m in genai.list_models():
        print(f"Model name: {m.name}")
except Exception as e:
    print(f"Error: {e}")
