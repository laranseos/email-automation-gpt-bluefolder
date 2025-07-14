import json
import re

def safe_parse_gpt_json(content: str) -> dict:
    """
    Safely parse GPT output into JSON, handling markdown-wrapped blocks and formatting issues.
    Returns a dictionary or a fallback error dict on failure.
    """
    try:

        # Extract JSON from markdown-style block
        match = re.search(r"```(?:json)?\s*({.*?})\s*```", content, re.DOTALL)
        json_str = match.group(1) if match else content.strip()

        # Clean up common JSON issues
        json_str = json_str.replace("“", '"').replace("”", '"')  # smart quotes
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)       # trailing commas

        # Parse JSON
        parsed = json.loads(json_str)
        print("✅ Parsed JSON successfully")
        return parsed

    except json.JSONDecodeError as e:
        print(f"⚠️ JSONDecodeError: {e}")
        return {
            "error": "Could not parse JSON",
            "raw_output": content,
            "exception": str(e)
        }
def save_json(file_path: str, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)