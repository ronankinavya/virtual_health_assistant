from dotenv import load_dotenv
import os, google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("🔍 GEMINI_API_KEY =", api_key)

genai.configure(api_key=api_key)

model = genai.GenerativeModel("models/gemini-flash-latest")
response = model.generate_content("Hello Gemini! Just testing.")
print("✅ Gemini response:", response.text)
