import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_auth import get_gmail_service
from utils.email_utils import fetch_unread_emails
from handlers.email_handler import handle_email

def test_handle_unread_emails():
    service = get_gmail_service()
    unread_messages = fetch_unread_emails(service)

    if not unread_messages:
        print("📭 No unread emails found.")
        return

    print(f"📨 Found {len(unread_messages)} unread email(s). Processing...")

    for msg in unread_messages:
        msg_id = msg["id"]
        print(f"\n🔧 Handling unread message ID: {msg_id}")
        try:
            handle_email(service, msg_id)
        except Exception as e:
            print(f"❌ Error handling message {msg_id}: {e}")

if __name__ == "__main__":
    test_handle_unread_emails()
