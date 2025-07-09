import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.openai_client import client
from utils.json_parser import safe_parse_gpt_json

def parse_email_with_gpt(email_subject, email_body, sender_name, sender_email):
    prompt = f"""
Extract structured customer service info from this email.
service_request_id is just 5 digit number series, not include characters.

Sender Name: {sender_name}
Sender Email: {sender_email}
Email Subject: {email_subject}  
Email Content:
\"\"\"
{email_body}
\"\"\"

Return JSON with:
- full_name
- email
- company
- phone_number
- location
- contact_person
- service_request_id
- issue_description
- preferred_date
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    content = response.choices[0].message.content

    return safe_parse_gpt_json(content)
