import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import base64
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import re
from utils.json_parser import save_json
from dotenv import load_dotenv

load_dotenv()

BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")
BLUEFOLDER_API_URL = "https://app.bluefolder.com/api/2.0/serviceRequests/getAssignmentList.aspx"

def get_all_service_requests(api_token):
    token = f"{api_token}:x"
    encoded_token = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_token}",
        "Content-Type": "text/xml"
    }

    xml_body = """
    <request>
        <serviceRequestList>
            <listType>basic</listType>
            <status>open</status>
        </serviceRequestList>
    </request>
    """.strip()

    response = requests.post(
        "https://app.bluefolder.com/api/2.0/serviceRequests/list.aspx",
        data=xml_body,
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(f"Failed to fetch service requests: {response.status_code} - {response.text}")

    return response.text

def match_score(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def parse_datetime(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        return datetime.min

def match_service_requests(
    xml_data,
    full_name,
    email,
    contact_person=None,
    company=None,
    phone_number=None,
    service_request_id=None,
    location=None
):
    root = ET.fromstring(xml_data)
    matches = []

    for sr in root.findall(".//serviceRequest"):
        sr_data = {
            "id": sr.findtext("serviceRequestId"),
            "externalId": sr.findtext("externalId", ""),
            "customerName": sr.findtext("customerName", ""),
            "contactName": sr.findtext("customerContactName", ""),
            "contactEmail": sr.findtext("customerContactEmail", ""),
            "contactPhone": sr.findtext("customerContactPhone", ""),
            "contactPhoneMobile": sr.findtext("customerContactPhoneMobile", ""),
            "description": sr.findtext("description", ""),
            "created": sr.findtext("dateTimeCreated", ""),
            "status": sr.findtext("status", ""),
            "locationStreet": sr.findtext("customerLocationStreetAddress", ""),
            "locationCity": sr.findtext("customerLocationCity", ""),
            "locationState": sr.findtext("customerLocationState", "")
        }

        if service_request_id and sr_data["id"] == str(service_request_id):
            matches.append((1.0, sr_data))
            continue

        score = 0
        total_weight = 0
        score_debug = {}

        name_inputs = [v for v in [full_name, contact_person, company] if v]
        target_names = [sr_data["customerName"], sr_data["contactName"]]

        name_score = 0
        for input_name in name_inputs:
            for target in target_names:
                name_score = max(name_score, match_score(input_name, target))

        score += name_score * 1.5
        total_weight += 1.5
        score_debug["name_score * 1.5"] = name_score * 1.5

        email_score = 0
        if email:
            input_email = email.strip().lower()
            raw_emails = sr_data.get("contactEmail", "")
            email_list = [e.strip().lower() for e in re.split(r"[;,]", raw_emails) if e.strip()]
            email_score = max((match_score(input_email, e) for e in email_list), default=0)

        score += email_score * 1.5
        total_weight += 1.5
        score_debug["email_score * 1.5"] = email_score * 1.5

        if phone_number:
            phone_score = max(
                match_score(sr_data["contactPhone"], phone_number),
                match_score(sr_data["contactPhoneMobile"], phone_number)
            )
            score += phone_score * 1.25
            total_weight += 1.25
            score_debug["phone_score * 1.25"] = phone_score * 1.25

        location_input = f"{sr_data['locationStreet']} {sr_data['locationCity']} {sr_data['locationState']}".strip()
        if location:
            location_score = match_score(location_input, location) 
            score += location_score * 0.75
            total_weight += 0.75
            score_debug["location_score * 0.75"] = location_score * 0.75

        normalized_score = score / total_weight if total_weight > 0 else 0
        sr_data["score_debug"] = score_debug

        if normalized_score >= 0.6:
            matches.append((normalized_score, sr_data))

    matches.sort(key=lambda x: (x[0], parse_datetime(x[1]["created"])), reverse=True)
    return matches

def display_matches(matches, limit=5):
    print(f"\n🔎 Top {min(limit, len(matches))} Matches:")
    for i, (score, sr) in enumerate(matches[:limit]):
        print(f"\n#{i + 1} - Match Score: {score:.2f} (normalized)")
        print(f"ServiceRequestID: {sr.get('id', '')}")
        print(f"Customer Name: {sr.get('customerName', '')}")
        print(f"Contact Name: {sr.get('contactName', '')}")
        print(f"Email: {sr.get('contactEmail', '')}")
        print(f"Phone: {sr.get('contactPhone', '') or sr.get('contactPhoneMobile', '')}")
        print(f"Location: {sr.get('locationStreet', '')}, {sr.get('locationCity', '')}, {sr.get('locationState', '')}")
        print(f"Created: {sr.get('created', '')} | Status: {sr.get('status', '')}")
        print(f"Description: {sr.get('description', '')}")

        if 'score_debug' in sr:
            print("🔍 Score Breakdown:")
            total = 0
            for k, v in sr['score_debug'].items():
                print(f"  {k}: {v:.2f}")
                total += v
            print(f"  ➤ Total Raw Score: {total:.2f}")

        print("-" * 120)

def fetch_all_assignments() -> list:
    """
    Fetches all assignments from BlueFolder for the next year.
    Returns a list of dicts and saves to local JSON.
    """
    print("\n🔄 [INFO] Fetching assignments from BlueFolder...")

    start = datetime.now().strftime("%Y-%m-%dT00:00:00")
    end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59")

    xml_body = f"""
    <request>
        <serviceRequestAssignmentList>
            <dateRangeStart>{start}</dateRangeStart>
            <dateRangeEnd>{end}</dateRangeEnd>
        </serviceRequestAssignmentList>
    </request>
    """

    token = f"{BLUEFOLDER_API_TOKEN}:x"
    encoded_token = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_token}",
        "Content-Type": "text/xml"
    }

    try:
        response = requests.post(BLUEFOLDER_API_URL, data=xml_body.strip(), headers=headers)
        response.raise_for_status()
        print("✅ [INFO] Response received from BlueFolder.")
    except Exception as e:
        print(f"❌ [ERROR] Failed to fetch assignments: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
        assignments = []

        for item in root.findall("serviceRequestAssignment"):
            assignment = {}

            for child in item:
                if child.tag == "assignedTo":
                    user_id = child.findtext("userId", default="")
                    assignment["assignedUserId"] = user_id
                else:
                    assignment[child.tag] = child.text or ""

            assignments.append(assignment)

        print(f"📦 [INFO] Parsed {len(assignments)} assignments.")
        save_json("../data/assignments_current.json", assignments)
        print("💾 [SAVED] Assignments snapshot saved to data/assignments_current.json")

        return assignments

    except Exception as e:
        print(f"❌ [ERROR] Failed to parse XML: {e}")
        return []