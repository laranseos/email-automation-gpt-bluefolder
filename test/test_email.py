import os
import sys

# Add project root to path to allow relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_auth import get_gmail_service
from utils.email_utils import fetch_unread_emails, extract_email_info, mark_as_read

def test_fetch_and_print_unread():
    service = get_gmail_service()

    unread = fetch_unread_emails(service)
    if not unread:
        print("📭 No unread emails.")
        return

    print(f"📨 Found {len(unread)} unread email(s).")

    for i, msg in enumerate(unread, start=1):
        print(f"\n📩 Email #{i}")
        info = extract_email_info(service, msg['id'])
        print(f"From: {info['sender_name']} <{info['sender_email']}>")
        print(f"Subject: {info['subject']}")
        print(f"Body: {info['body'][:300]}...")  # Show first 300 chars

        # Optional: mark as read to avoid re-processing during testing
        mark_as_read(service, info['msg_id'])

if __name__ == "__main__":
    test_fetch_and_print_unread()
