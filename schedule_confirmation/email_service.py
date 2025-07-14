import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_auth import get_gmail_service
from services.openai_client import client
from utils.json_parser import safe_parse_gpt_json


def create_message(to_email: str, subject: str, body_text: str, body_html: str = "") -> dict:
    message = MIMEMultipart("alternative")
    message["To"] = to_email
    message["Subject"] = subject

    part1 = MIMEText(body_text, "plain")
    message.attach(part1)

    if body_html:
        part2 = MIMEText(body_html, "html")
        message.attach(part2)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def generate_and_send_confirmation_email(assignment: dict) -> bool:
    """
    Generate a confirmation email using GPT and send it.
    The recipient email is read from assignment['customerEmail'].
    """
    to_email = "larans7277@gmail.com"
    # to_email = assignment.get("customerEmail")
    # if not to_email:
    #     print("❌ [ERROR] No customerEmail found in assignment.")
    #     return False

    prompt = f"""
You are an assistant for a gym equipment repair company.

Generate a short, professional appointment confirmation email using this assignment data:

- Assignment ID: {assignment.get("assignmentId")}
- Service Request ID: {assignment.get("serviceRequestId")}
- Start Date: {assignment.get("startDate")}
- End Date: {assignment.get("endDate")}
- Assigned User ID: {assignment.get("assignedUserId")}

Respond ONLY in JSON with these keys:
- subject (string): subject line for the email
- body_text (string): plain text content 
- body_html (string): same content in HTML using <p> tags

Body_text is followng prompt based.
Upbeat confirmations
Add "Fitness Equipment" with the subject line
Give 3 hour window 3 hour window starting 1/2 hour before the beginning of the scheduled timeslot
Ask if there is any unreported issues with the fitness equipment to address
Ask what keys/fobs or entry requirements are to make the visit more streamlined
Ask if there have been any contact changes
Email format
Reformat the email without any hyperlinks—just plain text.
Only list ASSIGNED TO technician
Identify explain any out of stock
Identify and communicate outstanding invoice for this client and what needs to happen
Best regards,
Gerume Bekele
Pronto Gym Services, Inc.
Schedule@prontogymservices.com
888-733-8510; ext. 1

Example format:
```json
{{
  "subject": "Subject will be Service request ID",
  "body_text": "generated text",
  "body_html": "more styled html content"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512
        )

        content = response.choices[0].message.content
        print("🤖 [DEBUG] GPT raw response:\n", content)

        parsed = safe_parse_gpt_json(content)
        if parsed:
            print("✅ [INFO] Parsed GPT email successfully.")
            subject = parsed.get("subject", "Your Appointment is Confirmed")
            body_text = parsed.get("body_text", "This confirms your scheduled service. We appreciate your business!")
            body_html = parsed.get("body_html", f"<p>{body_text}</p>")
        else:
            print("⚠️ [WARN] GPT parsing failed. Using default content.")
            subject = "Your Appointment is Confirmed"
            body_text = "This confirms your scheduled service. We appreciate your business!"
            body_html = f"<p>{body_text}</p>"

    except Exception as e:
        print(f"❌ [ERROR] GPT request failed: {e}")
        subject = "Your Appointment is Confirmed"
        body_text = "This confirms your scheduled service. We appreciate your business!"
        body_html = f"<p>{body_text}</p>"

    # Send the email
    service = get_gmail_service()
    message = create_message(to_email, subject, body_text, body_html)
    try:
        result = service.users().messages().send(userId="me", body=message).execute()
        print(f"✅ Email sent to {to_email}. Message ID: {result['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


