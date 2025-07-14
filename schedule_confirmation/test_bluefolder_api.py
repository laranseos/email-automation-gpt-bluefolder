from bluefolder_api import fetch_all_assignments, diff_assignments
import time

def test_fetch_and_diff():
    print("\n=== Test: Fetch all assignments ===")
    new_assignments = fetch_all_assignments(days_ahead=30)  # fetch next 30 days

    if not new_assignments:
        print("❌ Failed to fetch assignments or no data returned.")
        return

    print(f"✅ Fetched {len(new_assignments)} assignments.")

    print("\n=== Test: Compare assignments (diff) ===")
    diff_result = diff_assignments(new_assignments)
    print(f"New assignments: {len(diff_result['new'])}")
    print(f"Updated assignments: {len(diff_result['updated'])}")

    # Optionally, print a sample from new and updated
    if diff_result['new']:
        print("\nSample new assignment:")
        print(diff_result['new'][0])

    if diff_result['updated']:
        print("\nSample updated assignment:")
        print(diff_result['updated'][0])

if __name__ == "__main__":
    test_fetch_and_diff()
