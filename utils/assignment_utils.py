import json
from utils.json_parser import load_json
from typing import List, Dict

def diff_assignments(new_assignments: List[Dict], old_assignments_path: str = "data/assignments_current.json") -> Dict[str, List[Dict]]:
    """
    Compare new assignments with the saved snapshot.
    Returns dict with 'new' and 'updated' assignment lists.
    """
    print("\n🔍 [INFO] Comparing assignments with snapshot...")

    try:
        old_assignments = load_json(old_assignments_path)
    except Exception:
        print("⚠️ [WARN] No existing snapshot. Assuming all are new.")
        return {"new": new_assignments, "updated": []}

    # Index old by assignmentId
    old_map = {a["assignmentId"]: a for a in old_assignments}
    new_map = {a["assignmentId"]: a for a in new_assignments}

    new_items = []
    updated_items = []

    for assignment_id, new_a in new_map.items():
        old_a = old_map.get(assignment_id)

        if not old_a:
            new_items.append(new_a)
        elif new_a != old_a:
            updated_items.append(new_a)

    print(f"🆕 New assignments: {len(new_items)}")
    print(f"♻️ Updated assignments: {len(updated_items)}")

    return {"new": new_items, "updated": updated_items}
