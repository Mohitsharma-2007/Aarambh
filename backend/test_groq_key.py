import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    r = httpx.post(url, headers=headers, json=data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    test_groq()
