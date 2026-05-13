
import google.generativeai as genai
import os
from app.core.config import settings

api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
genai.configure(api_key=api_key)

print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
