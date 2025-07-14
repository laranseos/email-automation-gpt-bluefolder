import os
from bluefolder_api import (
    get_all_service_requests,
    match_service_requests,
    display_matches,
    fetch_all_assignments
)

from dotenv import load_dotenv

# env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
# load_dotenv(dotenv_path=env_path)

# Load API key
load_dotenv()
BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")

# Sample parsed info to match (simulate output from GPT parsing)
sample_parsed_info = {
    "full_name": "colby morgan",
    "email": "colby@gmail.com",
}

def test_bluefolder_lookup():
    print("🔍 Fetching all open service requests...")
    xml_data = get_all_service_requests(BLUEFOLDER_API_TOKEN)
    print(f"✅ Fetched XML data (length: {len(xml_data)} characters)")

    print("📌 Running match against sample customer info...")
    matches = match_service_requests(
        xml_data,
        full_name=sample_parsed_info["full_name"],
        email=sample_parsed_info["email"],
    )

    if not matches:
        print("❌ No matches found.")
    else:
        print("✅ Matches found:")
        display_matches(matches)

if __name__ == "__main__":
    fetch_all_assignments()
