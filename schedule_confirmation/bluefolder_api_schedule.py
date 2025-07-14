import base64
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()

BLUEFOLDER_API_TOKEN = os.getenv("BLUEFOLDER_API_TOKEN")
BLUEFOLDER_API_URL = "https://app.bluefolder.com/api/2.0/serviceRequests/getAssignmentList.aspx"

def save_json(file_path: str, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def fetch_all_assignments(days_ahead: int = 30) -> List[Dict]:
    """
    Fetch all assignments from BlueFolder for the next `days_ahead` days.
    Returns list of assignments as dictionaries and saves snapshot to disk.
    """
    print("\n🔄 [INFO] Fetching assignments from BlueFolder...")

    start = datetime.now().strftime("%Y-%m-%dT00:00:00")
    end = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%dT23:59:59")

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
        ### For first db setup
        ### save_json("db/assignments_current.json", assignments)
        ### print("💾 [SAVED] Assignments snapshot saved to db/assignments_current.json")
        return assignments

    except Exception as e:
        print(f"❌ [ERROR] Failed to parse XML: {e}")
        return []

def diff_assignments(new_assignments: List[Dict], old_assignments_path: str = "db/assignments_current.json") -> Dict[str, List[Dict]]:
    """
    Compare new assignments with the saved snapshot.
    Returns dict with 'new' and 'updated' lists.
    Logs details on which assignments are new or updated, and what changed.
    """
    print("\n🔍 [INFO] Comparing assignments with snapshot...")

    old_assignments = load_json(old_assignments_path)

    if not old_assignments:
        print("⚠️ [WARN] No existing snapshot found, treating all as new.")
        for a in new_assignments:
            print(f"🆕 New assignment: ID={a.get('assignmentId')}")
        return {"new": new_assignments, "updated": []}

    old_map = {a["assignmentId"]: a for a in old_assignments}
    new_map = {a["assignmentId"]: a for a in new_assignments}

    new_items = []
    updated_items = []

    for aid, new_a in new_map.items():
        old_a = old_map.get(aid)
        if not old_a:
            print(f"🆕 New assignment found: ID={aid}")
            new_items.append(new_a)
        else:
            if new_a != old_a:
                print(f"♻️ Updated assignment found: ID={aid}")
                # Check which fields changed
                changed_fields = []
                for key in new_a.keys():
                    old_val = old_a.get(key)
                    new_val = new_a.get(key)
                    if old_val != new_val:
                        changed_fields.append((key, old_val, new_val))
                if changed_fields:
                    print(f"   Changed fields:")
                    for field, old_v, new_v in changed_fields:
                        print(f"     - {field}: '{old_v}' => '{new_v}'")
                else:
                    print("   (Update detected but no field difference found — possible data type or ordering change.)")
                updated_items.append(new_a)

    print(f"🆕 Total new assignments found: {len(new_items)}")
    print(f"♻️ Total updated assignments found: {len(updated_items)}")

    return {"new": new_items, "updated": updated_items}