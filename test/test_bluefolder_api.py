import requests
import base64
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import re
# ======= CONFIG =======
API_TOKEN = "351d49b7-3556-490f-bcf0-eafb266699aa"  # Insert directly
BASE_URL = "https://app.bluefolder.com/api/2.0/serviceRequests/"
DEFAULT_HEADERS = {
    "Authorization": "Basic " + base64.b64encode(f"{API_TOKEN}:x".encode()).decode(),
    "Content-Type": "text/xml"
}

# ======= HELPERS =======

def send_bluefolder_request(endpoint: str, xml_body: str) -> str:
    """
    Sends a POST request to a BlueFolder API endpoint.
    """
    url = BASE_URL + endpoint
    print(f"[INFO] Sending request to: {endpoint}")
    
    response = requests.post(endpoint, data=xml_body.strip(), headers=DEFAULT_HEADERS)

    if response.status_code != 200:
        print(f"[ERROR] Request failed: {response.status_code}")
        print("response.text")
        raise Exception("BlueFolder API Error")

    return response.text


def parse_xml_response(xml_str: str) -> Dict:
    """
    Converts BlueFolder XML response into a nested Python dictionary.
    """
    def etree_to_dict(elem):
        children = list(elem)
        if not children:
            return elem.text.strip() if elem.text else ""
        result = {}
        for child in children:
            tag = child.tag
            value = etree_to_dict(child)
            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(value)
                else:
                    result[tag] = [result[tag], value]
            else:
                result[tag] = value
        return result

    root = ET.fromstring(xml_str)
    return etree_to_dict(root)


def pretty_print(data: Dict, indent: int = 0):
    """
    Recursively pretty prints the dictionary response.
    For simple tag-value pairs, it prints in one line.
    """
    prefix = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                pretty_print(value, indent + 1)
            else:
                print(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            pretty_print(item, indent)
    else:
        print(f"{prefix}{data}")

def count_list_items(data: Dict) -> int:
    """
    Recursively count total items in all lists within the parsed XML dictionary.
    """
    count = 0
    if isinstance(data, dict):
        for value in data.values():
            sub_count = count_list_items(value)
            if sub_count is not None:
                count += sub_count
    elif isinstance(data, list):
        count += len(data)
        for item in data:
            sub_count = count_list_items(item)
            if sub_count is not None:
                count += sub_count
    return count  # ✅ Always return an integer

# ======= TEST CASES =======

def test_get_single_requests(service_request_id: str):
    xml_body = f"""
    <request>
        <serviceRequestId>{service_request_id}</serviceRequestId>
    </request>
    """
    xml_response = send_bluefolder_request("https://app.bluefolder.com/api/2.0/serviceRequests/get.aspx", xml_body)
    parsed = parse_xml_response(xml_response)
    print("\n=== Single Service Requests ===")
    #pretty_print(parsed)
    print(parse_service_request(xml_response))


def test_get_assignments(service_request_id: str):
    xml_body = f"""
    <request>
        <serviceRequestAssignmentList>
            <serviceRequestId>{service_request_id}</serviceRequestId>
        </serviceRequestAssignmentList>
    </request>
    """
    xml_response = send_bluefolder_request("getAssignmentList.aspx", xml_body)
    parsed = parse_xml_response(xml_response)
    print(f"\n=== Assignments for Request ID {service_request_id} ===")
    pretty_print(parsed)

def test_get_appointment_list(start_date="", end_date=""):
    """
    Calls the appointment list endpoint with optional filters.
    """
    xml_body = f"""
    <request>
      <appointmentList>
        <dateRangeStart>{start_date}</dateRangeStart>
        <dateRangeEnd>{end_date}</dateRangeEnd>
      </appointmentList>
    </request>
    """

    print("\n[INFO] Fetching appointments from BlueFolder...")
    xml_response = send_bluefolder_request("https://app.bluefolder.com/api/2.0/appointments/list.aspx", xml_body)
    # parsed = parse_xml_response(xml_response)
    print("\n=== Appointments ===")
    # count_list_items(parsed)
    pretty_print(xml_response)

def get_assignment_list(
    service_request_id: Optional[str] = "",
    customer_id: Optional[str] = "",
    date_range_start: Optional[str] = "",
    date_range_end: Optional[str] = "",
    user_ids: Optional[list] = None,
    date_range_type: Optional[str] = ""
):
    """
    Retrieves a list of assignments with optional filters.
    """
    user_id_xml = ""
    if user_ids:
        for uid in user_ids:
            user_id_xml += f"<userId>{uid}</userId>\n"

    xml_body = f"""
    <request>
        <serviceRequestAssignmentList>
            <serviceRequestId>{service_request_id}</serviceRequestId>
            <customerId>{customer_id}</customerId>
            <dateRangeStart>{date_range_start}</dateRangeStart>
            <dateRangeEnd>{date_range_end}</dateRangeEnd>
            <dateRangeType>{date_range_type}</dateRangeType>
            <assignedTo>
                {user_id_xml}
            </assignedTo>
        </serviceRequestAssignmentList>
    </request>
    """

    print("\n[INFO] Fetching assignments from BlueFolder...")
    xml_response = send_bluefolder_request("https://app.bluefolder.com/api/2.0/serviceRequests/getAssignmentList.aspx", xml_body)
    parsed = parse_xml_response(xml_response)

    print("\n=== Assignment List ===")
    pretty_print(parsed)
    count_list_items(parsed)
    return parsed

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
            "detailed_description": detailed_description,
        }
    }
# ======= MAIN =======
if __name__ == "__main__":
    # Run any tests here
   test_get_single_requests(56105)