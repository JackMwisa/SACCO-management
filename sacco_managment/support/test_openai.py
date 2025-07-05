# test_gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def test_gemini():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        # Configure API
        genai.configure(api_key=api_key)

        # ✅ Use a valid model name from your list
        model = genai.GenerativeModel("models/gemini-1.5-pro")

        # Test prompt
        response = model.generate_content("Hello, write a short test message")

        # Output response
        print("✅ Success! Response:")
        print(response.text)

    except Exception as e:
        print("❌ Gemini API error:", str(e))

if __name__ == "__main__":
    test_gemini()
