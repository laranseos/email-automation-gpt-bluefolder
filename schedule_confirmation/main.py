import time
from bluefolder_api_schedule import fetch_all_assignments, diff_assignments, save_json, load_json
from email_service import generate_and_send_confirmation_email
import os, json

ASSIGNMENTS_SNAPSHOT_PATH = "db/assignments_current.json"
SENT_LOG_PATH = "db/assignments_sent.json"
FETCH_DAYS_AHEAD = 30  # how far ahead to fetch assignments
SLEEP_INTERVAL = 30 * 60  # 30 minutes in seconds

def load_sent_log():
    """
    Loads the sent log JSON data from SENT_LOG_PATH.
    Returns an empty dict if file not found or on JSON decode error.
    """
    if not os.path.exists(SENT_LOG_PATH):
        return {}

    try:
        with open(SENT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Warning: Failed to load sent log ({e}), returning empty dict.")
        return {}
    
def save_sent_log(log):
    save_json(SENT_LOG_PATH, log)

def main_loop():
    print("🚀 Starting assignment confirmation service...")

    while True:
        print("\n🔄 Fetching assignments...")
        assignments = fetch_all_assignments(days_ahead=FETCH_DAYS_AHEAD)
        if not assignments:
            print("❌ No assignments fetched. Will retry after delay.")
            time.sleep(SLEEP_INTERVAL)
            continue

        print("🔍 Comparing assignments with previous snapshot...")
        diff = diff_assignments(assignments, old_assignments_path=ASSIGNMENTS_SNAPSHOT_PATH)

        sent_log = load_sent_log()

        # to_process = diff['new'] + diff['updated']
        to_process = diff['new']
        print(f"📨 Assignments to confirm: {len(to_process)}")

        for assignment in to_process:
            assignment_id = assignment.get("assignmentId")

            if assignment_id in sent_log:
                print(f"ℹ️ Confirmation already sent for assignment {assignment_id}, skipping.")
                continue

            print(f"✉️ Sending confirmation for assignment {assignment_id}...")
            try:
                # Assume generate_and_send_confirmation_email returns True/False
                success = generate_and_send_confirmation_email(assignment)
                if success:
                    sent_log[assignment_id] = True
                    save_sent_log(sent_log)
                    print(f"✅ Confirmation sent and logged for {assignment_id}")
                else:
                    print(f"❌ Failed to send confirmation for {assignment_id}")
            except Exception as e:
                print(f"❌ Error sending confirmation for {assignment_id}: {e}")

        # Update snapshot after processing
        save_json(ASSIGNMENTS_SNAPSHOT_PATH, assignments)
        print(f"💾 Updated assignments snapshot saved.")

        print(f"\n⏳ Sleeping for {SLEEP_INTERVAL//60} minutes...\n")
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main_loop()
