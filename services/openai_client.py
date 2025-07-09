import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env variables (only if not already loaded)
load_dotenv()

# Initialize OpenAI client with API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("Missing OPENAI_API_KEY in .env file.")

client = OpenAI(api_key=api_key)