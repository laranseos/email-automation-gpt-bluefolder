import os
import time
import base64
import re
from typing import List, Dict, Optional
from email.utils import parseaddr
from email.mime.text import MIMEText


# === Fetch Unread Emails (Simple, Stateless) ===
def fetch_unread_emails(service, max_results: int = 5) -> List[Dict[str, str]]:
    """Fetch a limited number of unread emails from the inbox."""
    res = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q='is:unread',
        maxResults=max_results
    ).execute()
    return res.get('messages', [])


# === Fetch New Emails Since Timestamp (Stateful, Safer) ===
def fetch_new_emails(service, last_processed_time: Optional[float] = None) -> List[Dict[str, str]]:
    """
    Fetch unread emails received after the given timestamp.
    This helps avoid reprocessing old unread emails.
    """
    if last_processed_time is None:
        last_processed_time = time.time()
        print(f"⚠️ First run – processing emails after: {time.ctime(last_processed_time)}")

    results = service.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        q=f'is:unread after:{int(last_processed_time)}'
    ).execute()

    messages = results.get('messages', [])
    new_emails = []

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        timestamp = float(msg.get('internalDate', 0)) / 1000.0

        if timestamp <= last_processed_time:
            continue

        # Extract parts
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        sender_name, sender_email = parseaddr(sender)
        body = extract_body(payload)

        # Skip internal (same-domain) emails
        user_email = service.users().getProfile(userId='me').execute().get('emailAddress', '')
        if get_domain(sender_email) == get_domain(user_email):
            continue

        new_emails.append({
            'id': message['id'],
            'thread_id': msg.get('threadId'),
            'body': body,
            'subject': subject,
            'sender': sender_name,
            'sender_email': sender_email,
            'timestamp': timestamp
        })

    return new_emails


# === Extract Full Email Metadata (for single email) ===
def extract_email_info(service, msg_id: str) -> Dict[str, str]:
    """Extract sender, subject, body, thread from a specific email."""
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg.get('payload', {})
    headers = payload.get('headers', [])

    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
    sender_name, sender_email = parseaddr(sender)
    body = extract_body(payload)

    return {
        'msg_id': msg_id,
        'thread_id': msg.get('threadId'),
        'sender_email': sender_email,
        'sender_name': sender_name,
        'subject': subject,
        'body': body
    }


# === Extract Text Body from MIME Payload ===
def extract_body(payload) -> str:
    """Extract plain-text body from Gmail message payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        data = payload.get('body', {}).get('data', '')
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ''


# === Mark Email as Read ===
def mark_as_read(service, msg_id: str):
    """Mark the specified message as read (remove UNREAD label)."""
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


# === Send Reply to Email Thread ===
def send_reply(service, to_email: str, thread_id: str, body: str, subject: str):
    """Send a plain-text email reply in the same thread."""
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId='me',
        body={'raw': raw, 'threadId': thread_id}
    ).execute()


# === Helper: Extract domain from email ===
def get_domain(email: str) -> str:
    """Extract domain portion of email."""
    return email.split('@')[-1].lower() if '@' in email else email
