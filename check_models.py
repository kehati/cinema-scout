import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Verify the key is loaded
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Available text/chat models for your API Key:")
print("-" * 40)

# Fetch the live list of models from Google
try:
    for model in genai.list_models():
        # We only care about models that can generate text/chat for LangChain
        if "generateContent" in model.supported_generation_methods:
            print(model.name)
except Exception as e:
    print(f"API Connection Error: {e}")