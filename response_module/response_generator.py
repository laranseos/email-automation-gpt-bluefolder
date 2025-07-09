import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from utils.vector_search import search_vector_store

CHROMA_PATH = "../rag/chroma_db"

# Map email categories to service types
CATEGORY_TO_SERVICE_TYPE = {
    1: "Repairs",
    2: "Repairs",
    3: "Schedule Confirmations",
    4: "Preventive Maintenance",
    5: "Schedule Confirmations",
    6: "Repair Complete",
    7: "Feedback",
    8: "Invoice or Billing",
    9: "Repairs",
    10: "Repairs",
    11: "Cancellations",
    12: "General Support",
    13: "Spam"
}

# Descriptions for email categories (for prompt clarity)
CATEGORY_DESCRIPTIONS = {
    1: "New service request received",
    2: "Request for quote or estimate",
    3: "Appointment or confirmation",
    4: "Insurance or vendor compliance request",
    5: "Availability update",
    6: "Follow-up on ongoing job",
    7: "Feedback or review",
    8: "Invoice or payment question",
    9: "Complaint or issue after service",
    10: "Warranty claim",
    11: "Cancellation request",
    12: "General question or support request",
    13: "Other or spam message"
}

# Instructions per service type
SERVICE_PROMPTS = {
    "Repairs": "We received a repair-related request. Address it clearly. Confirm any possible action. Reference matched service request info if available.",
    "Schedule Confirmations": "This is a schedule confirmation or time proposal. Confirm time if reasonable and ask for entry access if needed.",
    "Preventive Maintenance": "This is a preventive maintenance inquiry. Confirm the visit, ask about equipment issues, entry access, and point of contact.",
    "Repair Complete": "Customer is likely following up after a repair. Reassure them the repair is complete or in progress. Provide reference if possible.",
    "End of Life - Decommissioning": "This involves machines beyond support. Politely explain decommissioning, safety concerns, and recommend replacement options.",
    "Cancellations": "Customer is cancelling a visit. Confirm the cancellation. Ask if they’d like to reschedule.",
    "General Support": "Customer has a general question. Respond briefly with support info or let them know you’re looking into it.",
    "Invoice or Billing": "Respond to invoice or billing issues. Reference invoice # or status if available.",
    "Feedback": "Acknowledge their feedback. Thank them and mention it will be shared with the team.",
    "Spam": "No reply needed."
}

def generate_email_reply(data: dict, category: int, matches: List) -> Dict[str, str]:
    """
    Generate a reply email using GPT-4 with contextual information.
    Debugging version with step-by-step logs.
    """

    print("[DEBUG] Extracting email fields...")
    subject = data.get("subject", "")
    body = data.get("body", "")
    sender_name = data.get("sender_name", "")
    sender_email = data.get("sender_email", "")

    service_type = CATEGORY_TO_SERVICE_TYPE.get(category, "General Support")
    category_desc = CATEGORY_DESCRIPTIONS.get(category, "General inquiry")
    service_instructions = SERVICE_PROMPTS.get(service_type, SERVICE_PROMPTS["General Support"])
    prompt_instructions = f"Email category: {category_desc}.\nService type: {service_type}.\nInstructions: {service_instructions}"
    print(f"[INFO] Category {category} → {service_type}")
    print(f"[INFO] Prompt instructions:\n{prompt_instructions}")

    if service_type == "Spam":
        print("[INFO] Message marked as spam. No reply needed.")
        return {"subject": "", "body": ""}

    if matches:
        top_match = matches[0][1]
        match_info = (
            f"Service Request ID: {top_match.get('id', 'N/A')}, "
            f"Customer: {top_match.get('customerName', 'N/A')}, "
            f"Status: {top_match.get('status', 'N/A')}"
        )
    else:
        match_info = "No matching service request found."
    print(f"[INFO] Matched service info: {match_info}")

    print("\n[DEBUG] Loading Chroma DB and running similarity search...")

    relevant_docs = search_vector_store(body, num_results=3, similarity_threshold=0.7)
    context_text = "\n".join([doc.page_content for doc in relevant_docs])

    print("\n[DEBUG] Preparing prompt for GPT-4...")
    prompt_template = PromptTemplate(
        input_variables=["sender_name", "sender_email", "subject", "email", "context", "instructions", "match_info"],
        template="""
You are an automated assistant for Pronto Gym Services.

Extract the sender's first name using any of this information:
- Sender Name: {sender_name}
- Sender Email: {sender_email}
- Email Subject: {subject}
- Email Content: {email}

If you cannot confidently find a first name, use 'there' as a fallback.

Then, using the extracted first name, generate a short, friendly, helpful email reply.

Relevant company documents:
{context}

Matched service info:
{match_info}

Reply instructions:
{instructions}

Guidelines:
- Use simple, friendly language.
- No hyperlinks, plain text only.
- Keep reply under 80 words.
- Sign as Ron McDonnell, Pronto Gym Services.

Start your reply with: "Hi [First Name],"

Reply:
"""
    )

    print("[INFO] Invoking GPT-4 chain...")
    chain = (
        RunnablePassthrough.assign(
            context=RunnableLambda(lambda x: context_text),
            instructions=RunnableLambda(lambda x: prompt_instructions),
            match_info=RunnableLambda(lambda x: match_info)
        )
        | prompt_template
        | ChatOpenAI(model="gpt-4", temperature=0.3)
        | StrOutputParser()
    )

    try:
        final_body = chain.invoke({
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "email": body
        })
        print("[SUCCESS] GPT-4 generated reply successfully.")
    except Exception as e:
        print(f"[ERROR] GPT-4 failed to generate response: {e}")
        final_body = "Hi there,\n\nWe received your message and will get back to you shortly.\n\n– Ron McDonnell"

    return {
        "subject": f"Re: {subject}",
        "body": final_body
    }
