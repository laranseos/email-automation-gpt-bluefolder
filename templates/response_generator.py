def generate_email_reply(category: int, matches: list) -> str:
    # Basic category messages
    category_messages = {
        1: "New Service Request received.",
        2: "Request for Quote or Estimate received.",
        3: "Appointment or Confirmation received.",
        4: "Insurance or Vendor Compliance request received.",
        5: "Availability Update received.",
        6: "Follow-up on Ongoing Job received.",
        7: "Feedback or Review received.",
        8: "Invoice or Payment question received.",
        9: "Complaint or Issue after Service received.",
        10: "Warranty Claim received.",
        11: "Cancellation Request received.",
        12: "General Question or Support request received.",
        13: "Other or Spam message received."
    }

    message = category_messages.get(category, category_messages[13])

    # If there is at least one match, add some info
    if matches:
        top_match = matches[0][1]  # tuple (score, match_dict)
        match_info = (
            f"\n\nReference Details:\n"
            f"- Service Request ID: {top_match.get('id', 'N/A')}\n"
            f"- Customer Name: {top_match.get('customerName', 'N/A')}\n"
            f"- Status: {top_match.get('status', 'N/A')}"
        )
    else:
        match_info = ""

    reply = f"{message}{match_info}\n\n– Pronto Gym Services"
    return reply
