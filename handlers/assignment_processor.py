import os
from datetime import datetime, timedelta

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.bluefolder_api import fetch_all_assignments, get_service_request_details
from utils.json_parser import load_json, save_json
from utils.assignment_utils import diff_assignments
from pathlib import Path

# Config
SNAPSHOT_PATH = "../data/assignments_current.json"
SENT_LOG_PATH = "../data/assignments_sent.json"


def process_assignments():
    """
    Full pipeline:
    - Fetch current assignments from BlueFolder
    - Compare with snapshot
    - Fetch extra service/customer info for new ones
    - Log assignments that need confirmation
    """

    print("\n📡 [STEP] Processing BlueFolder Assignments...")

    new_data = fetch_all_assignments()
    diff = diff_assignments(new_data, SNAPSHOT_PATH)

    new_assignments = diff["new"]
    updated_assignments = diff["updated"]

    if not new_assignments and not updated_assignments:
        print("✅ [INFO] No new or updated assignments. Skipping.")
        return

    # Load sent log
    if os.path.exists(SENT_LOG_PATH):
        sent_log = load_json(SENT_LOG_PATH)
        sent_ids = {item["assignmentId"] for item in sent_log}
    else:
        sent_log = []
        sent_ids = set()

    to_confirm = []

    for assignment in new_assignments:
        assignment_id = assignment.get("assignmentId")

        if assignment_id in sent_ids:
            print(f"⚠️ [SKIP] Assignment {assignment_id} already confirmed.")
            continue

        service_request_id = assignment.get("serviceRequestId")

        if not service_request_id:
            print(f"❌ [SKIP] Missing serviceRequestId for assignment {assignment_id}")
            continue

        print(f"📦 [FETCH] Details for SR #{service_request_id} (assignment {assignment_id})")
      #  extra_info = get_service_request_details(service_request_id)

        full_assignment = {
            **assignment,
        #    "serviceRequest": extra_info,
        }

        to_confirm.append(full_assignment)
        sent_log.append({"assignmentId": assignment_id, "timestamp": datetime.now().isoformat()})

    # Save sent log
    save_json(SENT_LOG_PATH, sent_log)

    # Save new snapshot (update state)
    save_json(SNAPSHOT_PATH, new_data)
    print(f"✅ [DONE] Snapshot updated & {len(to_confirm)} assignments ready for email confirmation.")

    return to_confirm
