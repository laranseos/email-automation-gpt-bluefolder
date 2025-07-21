# confirmation_reply_handler.py

import os
import json
from services.bluefolder_api import update_status, add_comment
from services.openai_client import chat_completion
from utils.email_utils import send_reply

DATA_PATH = "appointment_confirmation/data_tracking/sent_confirmations.json"

def was_confirmation_sent(thread_id):
    if not os.path.exists(DATA_PATH):
        return False
    with open(DATA_PATH, "r") as f:
        return thread_id in json.load(f)

def classify_reply(body):
    prompt = f"""
A customer replied to a service schedule confirmation. Classify the tone of this response into one of:

- "confirmed" (they clearly agree to the schedule)
- "query" (they ask questions or need more info)
- "reschedule" (they want to change the time)
- "other" (none of the above)

Reply only with one of the four labels.
Customer message:
{body}
"""
    res = chat_completion(prompt)
    return res.lower().strip()

def generate_followup(classification):
    subjects = {
        "confirmed": "Visit Confirmed - Thank You",
        "query": "Follow-up on Your Question",
        "reschedule": "Reschedule Request Received",
        "other": "Thanks for Your Reply"
    }
    bodies = {
        "confirmed": "Thanks for confirming your appointment. We'll see you then!",
        "query": "Thanks for your message. We'll get back to you shortly with answers to your questions.",
        "reschedule": "Thanks for your request. We'll review and follow up with new availability.",
        "other": "Thanks for your reply. We’ve noted your response and will follow up if needed."
    }
    return {"subject": subjects[classification], "body": bodies[classification]}

def handle_confirmation_reply(email_data, service_request_id):
    body = email_data["body"]
    thread_id = email_data.get("thread_id")
    sender_email = email_data["sender_email"]

    if not was_confirmation_sent(thread_id):
        return False

    classification = classify_reply(body)

    status_map = {
        "confirmed": "SCHEDULED",
        "query": "CONFIRMATION PENDING",
        "reschedule": "RESCHEDULE REQUESTED"
    }
    comment_map = {
        "confirmed": "Customer confirmed scheduled visit.",
        "query": "Customer has a question about scheduled visit.",
        "reschedule": "Customer requested rescheduling.",
        "other": "Received a reply regarding the scheduled visit."
    }

    # Update BlueFolder
    new_status = status_map.get(classification)
    if new_status:
        update_status(service_request_id, new_status)
    add_comment(service_request_id, comment_map[classification])

    # Send auto-reply
    followup = generate_followup(classification)
    send_reply(
        to_email=sender_email,
        subject=followup["subject"],
        body=followup["body"],
        thread_id=thread_id
    )
    return True
