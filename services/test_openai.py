
from dotenv import load_dotenv

# Load .env manually (in case the test is run directly)

load_dotenv()

# Import the client from your OpenAI wrapper
from openai_client import client

def test_openai_basic():
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0,
            max_tokens=10
        )
        print("✅ OpenAI Response:", response.choices[0].message.content.strip())
    except Exception as e:
        print("❌ Error communicating with OpenAI:", e)

if __name__ == "__main__":
    test_openai_basic()