import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from handlers.blacklist import is_blacklisted
from handlers.categorizer import categorize_email
from handlers.parser import parse_email_with_gpt
from services.bluefolder_api import get_all_service_requests, match_service_requests
from utils.email_utils import extract_email_info, mark_as_read, send_reply
from templates.response_generator import generate_email_reply

import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")

def handle_email(service, msg_id: str):
    try:
        # Step 1: Extract email info
        data = extract_email_info(service, msg_id)
        sender_email = data["sender_email"]
        subject = data["subject"]
        body = data["body"]

        print(f"📨 Received email from {sender_email} | Subject: {subject}")

        # Step 2: Check blacklist
        if is_blacklisted(sender_email):
            print(f"🚫 Blacklisted sender: {sender_email}")
            mark_as_read(service, msg_id)
            return

        # Step 3: Categorize email
        category = categorize_email(subject, body)
        print(f"📌 Email categorized as #{category}")

        # Step 4: Parse structured info
        parsed = parse_email_with_gpt(subject, body, data["sender_name"], sender_email)
        print("🧾 Parsed Info:")
        print(json.dumps(parsed, indent=2))

        # Step 5: Fetch & match BlueFolder service request
        xml_data = get_all_service_requests(BLUEFOLDER_API_TOKEN)
        matches = match_service_requests(
            xml_data,
            full_name=parsed.get("full_name"),
            email=parsed.get("email"),
            contact_person=parsed.get("contact_person"),
            company=parsed.get("company"),
            phone_number=parsed.get("phone_number"),
            service_request_id=parsed.get("service_request_id"),
            location=parsed.get("location")
        )

        # Step 6: Generate reply
        reply_body = generate_email_reply(category, matches)
        send_reply(service, to_email=sender_email, thread_id=data["thread_id"], msg_text=reply_body)

        # Step 7: Mark email as read
        mark_as_read(service, msg_id)
        print("✅ Email processed and replied.")

    except Exception as e:
        print(f"❌ Error handling email: {e}")
