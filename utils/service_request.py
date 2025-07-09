import requests
import base64
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()
BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")
API_GET_URL = "https://app.bluefolder.com/api/2.0/serviceRequests/get.aspx"

def get_auth_headers():
    token = f"{BLUEFOLDER_API_TOKEN}:x"
    encoded_token = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {encoded_token}",
        "Content-Type": "text/xml"
    }

def get_service_request_details(service_request_id: str):
    headers = get_auth_headers()
    xml_body = f"""
    <request>
        <serviceRequestId>{service_request_id}</serviceRequestId>
         <groupItemsByType></groupItemsByType>
    </request>
    """.strip()

    response = requests.post(API_GET_URL, data=xml_body, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.content)

        def xml_to_dict(element):
            return {
                child.tag: xml_to_dict(child) if list(child) else child.text
                for child in element
            }

        return xml_to_dict(root)
    else:
        print(f"[ERROR] Failed to fetch service request. Status: {response.status_code} Response: {response.text}")
        return None

# Example usage:
# if __name__ == "__main__":
#     service_request_id = "56201"  # Replace with actual serviceRequestId
#     details = get_service_request_details(service_request_id)

#     if details:
#         print("Service Request Details:")
#         print(details)
#     else:
#         print("No service request info found.")
