import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_auth import get_gmail_service
from services.openai_client import client
from utils.json_parser import safe_parse_gpt_json
from dotenv import load_dotenv
import requests
import base64

import xml.etree.ElementTree as ET
import re

load_dotenv()

BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")
DEFAULT_HEADERS = {
    "Authorization": "Basic " + base64.b64encode(f"{BLUEFOLDER_API_TOKEN}:x".encode()).decode(),
    "Content-Type": "text/xml"
}

def send_bluefolder_request(request_url: str, xml_body: str) -> str:
    """
    Sends a POST request to a BlueFolder API request_url.
    """
    print(f"[INFO] Sending request to: {request_url}")
    
    response = requests.post(request_url, data=xml_body.strip(), headers=DEFAULT_HEADERS)

    if response.status_code != 200:
        print(f"[ERROR] Request failed: {response.status_code}")
        print("response.text")
        raise Exception("BlueFolder API Error")

    return response.text

def parse_service_request(xml_str):
    root = ET.fromstring(xml_str)
    # Extract customer name
    customer_name = root.findtext('.//customerContactName', default='').strip()

    # Extract customer emails (split on ; or , if present)
    raw_emails = root.findtext('.//customerContactEmail', default='')
    customer_emails = [email.strip().lower() for email in re.split(r'[;,]', raw_emails) if email.strip()]

    # Extract status
    status = root.findtext('.//status', default='').strip()

    # Extract service type and description
    service_type = root.findtext('.//type', default='').strip()
    description = root.findtext('.//description', default='').strip()
    detailed_description = root.findtext('.//detailedDescription', default='').strip()
    return {
        "customer_name": customer_name,
        "customer_emails": customer_emails,
        "status": status,
        "email_details": {
            "type": service_type,
            "description": description,
        },
        "detailed_description": detailed_description,
    }
    
def get_service_request(service_request_id: str):
    xml_body = f"""
    <request>
        <serviceRequestId>{service_request_id}</serviceRequestId>
    </request>
    """
    xml_response = send_bluefolder_request("https://app.bluefolder.com/api/2.0/serviceRequests/get.aspx", xml_body)
    print("\n=== Single Service Requests ===")

    return xml_response

def get_user_name_by_id(user_id: str) -> str:
    xml_body = f"""
    <request>
        <userId>{user_id}</userId>
    </request>
    """
    xml_response = send_bluefolder_request("https://app.bluefolder.com/api/2.0/users/get.aspx", xml_body)
    root = ET.fromstring(xml_response)
    full_name = root.findtext(".//fullName")
    return full_name or "Unknown"

def get_assignment_info(assignment: dict) -> dict:
    """
    From assignment dict, return a dict with assignee name, startDate, and endDate.
    """
    assigned_user_id = assignment.get("assignedUserId")
    start_date = assignment.get("startDate")
    end_date = assignment.get("endDate")

    assignee_name = get_user_name_by_id(assigned_user_id)

    return {
        "assigneeName": assignee_name,
        "startDate": start_date,
        "endDate": end_date
    }

def create_message(to_email: str, subject: str, body_text: str) -> dict:
    message = MIMEMultipart("alternative")
    message["To"] = to_email
    message["Subject"] = subject

    part1 = MIMEText(body_text, "plain")
    message.attach(part1)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def generate_and_send_confirmation_email(assignment: dict) -> bool:
    """
    Generate a confirmation email using GPT and send it.
    The recipient email is read from the parsed service request info.
    """

    service_request_id = assignment.get("serviceRequestId")
    if not service_request_id:
        print("❌ [ERROR] No serviceRequestId in assignment.")
        return False

    # Step 1: Get Service Request XML
    raw_request_data = get_service_request(service_request_id)
    if not raw_request_data:
        print("❌ [ERROR] No service request data found.")
        return False

    # Step 2: Parse Service Request Info
    service_request_info = parse_service_request(raw_request_data)
    if not service_request_info:
        print("❌ [ERROR] Failed to parse service request data.")
        return False
    print(f"ℹ️ [INFO] Service request info: {service_request_info}")

    # Step 3: Get Assignment Info (technician, times)
    assignment_info = get_assignment_info(assignment)
    if not assignment_info:
        print("❌ [ERROR] Failed to get assignment info.")
        return False
    print(f"ℹ️ [INFO] Assignment info: {assignment_info}")

    # Step 4: Target recipient
    to_email = service_request_info.get("customer_emails", [])[0] if service_request_info.get("customer_emails") else None
    if not to_email:
        print("❌ [ERROR] No customer email found.")
        return False
    print(f"📧 [INFO] Sending confirmation to: {to_email}")
    
    prompt = f"""

    You are an assistant for Pronto Gym Services, a company that maintains and repairs fitness equipment for residential and commercial clients.

Your job is to generate a professional, and friendly appointment confirmation email using the provided structured data and full service request XML.

Assignment Info:
{assignment_info}

Service Request Info:
{service_request_info}

Original Assignment Raw Data:
{assignment}

Instructions :

Upbeat confirmations
Add "Fitness Equipment" with the subject line 
Give 3 hour window 3 hour window starting 1/2 hour before the beginning of the scheduled timeslot
Ask if there is any unreported issues with the fitness equipment to address
Ask what keys/fobs or entry requirements are to make the visit more streamlined
Ask if there have been any contact changes
Email format
Reformat the email without any hyperlinks—just plain text.

Only list ASSIGNED TO technician 
 
identify explain any out of stock
Identify and communicate outstanding invoice for this client and what needs to happen

Best regards,
Gerume Bekele
Pronto Gym Services, Inc.
📧 Schedule@prontogymservices.com
📞 (888-733-8510; ext. 1


Raw Service Request XML:
```xml
{raw_request_data}

Example format:
```json
{{
  "subject": "Fitness Equipment – Service Confirmation at [Location Name]",
  "body_text": "Hi [Customer Name],\\n\\nWe’re confirming your fitness equipment appointment at [Location]...\\n\\n[rest of text, formatted as readable plain text]\\n\\nBest regards,\\nGerume Bekele\\nPronto Gym Services, Inc.\\nSchedule@prontogymservices.com\\n(888) 733-8510; ext. 1",
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

        else:
            print("⚠️ [WARN] GPT parsing failed. Using default content.")
            subject = "Your Appointment is Confirmed"
            body_text = "This confirms your scheduled service. We appreciate your business!"

    except Exception as e:
        print(f"❌ [ERROR] GPT request failed: {e}")
        subject = "Your Appointment is Confirmed"
        body_text = "This confirms your scheduled service. We appreciate your business!"

    # Send the email
    service = get_gmail_service()
    to_email = "larans7277@gmail.com"  # For testing, replace with actual email
    message = create_message(to_email, subject, body_text)
    try:
        result = service.users().messages().send(userId="me", body=message).execute()
        print(f"✅ Email sent to {to_email}. Message ID: {result['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == "__main__":
    # Run any tests here
    
    test_assignment = {
        "assignmentId": "58969069",
        "assignmentToken": "4ED741F7-A463-484E-8A97-8E478DFA2B96",
        "serviceRequestId": "56019",
        "assignedUserId": "46525",
        "assignmentComment": "",
        "startDate": "2025-07-17T14:30:00",
        "endDate": "2025-07-17T15:30:00",
        "allDayEvent": "0",
        "dateTimeCreated": "2025-07-03T17:26:17.717",
        "createdByUserId": "0",
        "isComplete": "0",
        "completedByUserId": "0",
        "completionComment": ""
    }

    generate_and_send_confirmation_email(test_assignment)
