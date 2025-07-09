import os
import sys

# Add project root to path to allow relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from response_module.response_generator import generate_email_reply  # replace with your actual module name

def test_generate_email_reply():
    # Example email data
    email_data = {
        "sender_name": "Jane Doe",
        "sender_email": "jane.doe@example.com",
        "subject": "Request for Repair Quote",
        "body": (
            "Hello,\n"
            "I'd like to get a quote for repairing our gym treadmill. "
            "Can someone provide details?\nThanks!"
        )
    }

    # Example category (2 = Request for Quote or Estimate received)
    category = 2

    # Dummy Bluefolder matches, format: list of (score, dict) tuples
    matches = [
        (0.85, {
            "id": "SR12345",
            "customerName": "Jane Doe",
            "status": "Open"
        })
    ]

    reply = generate_email_reply(email_data, category, matches)
    print("Subject:", reply["subject"])
    print("Body:\n", reply["body"])


if __name__ == "__main__":
    test_generate_email_reply()
