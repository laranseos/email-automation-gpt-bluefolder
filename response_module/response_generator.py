import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from utils.vector_search import search_vector_store
from utils.service_request import get_service_request_details

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
                    "Repairs": """
                                Upbeat vibe
                                Simple language
                                Common fitness issues that can be averted with proper maintenance
                                Home Owner Association Boards & Management
                                How we can augment property staff to off load
                                Email format
                                Overcome objections
                                What vendor setup does the property require
                                Ask if there is any current issues with the fitness equipment causing frustration
                                Ask what keys/fobs or entry requirements are to make a visit more streamlined
                                Who would be the contacts that confirm scheduled visits, approve any repairs and pay invoices
                                What preventive maintenance cycle is the client budgetted for
                                Discuss how older machines have a lifespan and how that impacts support
                                Best regards,
                                Ron McDonnell
                                Pronto Gym Services, Inc.
                                Choose@prontogymservices.com
                                888-733-8510; ext. 2
                            """,
    "Schedule Confirmations": """
                                Upbeat confirmations
                                Add "Fitness Equipment" with the subject line
                                Give 3 hour window 3 hour window starting 1/2 hour before the beginning of the scheduled timeslot
                                Ask if there is any unreported issues with the fitness equipment to address
                                Ask what keys/fobs or entry requirements are to make the visit more streamlined
                                Ask if there have been any contact changes
                                Email format
                                Reformat the email without any hyperlinks—just plain text.
                                Only list ASSIGNED TO technician
                                identify explain any out of stock
                                Identify and communicate outstanding invoice for this client and what needs to happen
                                Best regards,
                                Gerume Bekele
                                Pronto Gym Services, Inc.
                                Schedule@prontogymservices.com
                                888-733-8510; ext. 1
                            """,
    "Preventive Maintenance": """
                                Upbeat vibe
                                Simple language
                                Common fitness issues that can be averted with proper maintenance
                                How we can augment property staff to off load
                                Email format
                                Overcome objections
                                What vendor setup does the property require
                                Ask if there is any current issues with the fitness equipment causing frustration
                                Ask what keys/fobs or entry requirements are to make a visit more streamlined
                                Who would be the contacts that confirm scheduled visits, approve any repairs and pay invoices
                                What preventive maintenance cycle is the client budgeted for
                                Discuss how older machines have a lifespan and how that impacts support
                                Best regards,
                                Ron McDonnell
                                Pronto Gym Services, Inc.
                                Choose@prontogymservices.com
                                888-733-8510; ext. 2
                                """,
    "Repair Complete": """
                        Upbeat success,  Email Format, Technician assigned: ,  PO, Equipment worked on what was tested Resolved and tested
                        """,
    "End of Life - Decommissioning": """
                                Email format
                                Simple language
                                End of Life means manufacturer no longer supports/has replacement parts, Aftermarket replacement parts are limited to not available.
                                Nautilus Strength & Green series Went out of business
                                All product that is designated end of life and has current safety issues determined by a technician should be decommissioned and removed from the facility.
                                Using equipment list indicate all machines age status
                                Continued use creates a safety hazard for users and significant liability exposure for ownership
                                BH Fitness No Longer has Support In the US
                                When possible highlight the age of each machine
                                the email no hyperlinks, just plain text
                                Subject line to include client location name
                                use upbeat language while discussing how much value these capital units held to this point
                                Offer help to obtain replacement equipment
                                Ron McDonnell
                                Pronto Gym Services
                                (888) 733-8510
                                choose@prontogymservices.com        
                            """,
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
        service_request_id = top_match.get("id")

        if service_request_id:
            service_request = get_service_request_details(service_request_id)
            print("[INFO] Full Service Request Data:")
            print(service_request)
        else:
            service_request = None
    else:
        service_request = None

    print("\n[DEBUG] Loading Chroma DB and running similarity search...")

    relevant_docs = search_vector_store(body, num_results=3, similarity_threshold=0.7)
    context_text = "\n".join([doc.page_content for doc in relevant_docs])

    print("\n[DEBUG] Preparing prompt for GPT-4...")
    prompt_template = PromptTemplate(
        input_variables=["sender_name", "sender_email", "subject", "email", "context", "instructions", "service_request"],
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

service request service info related to Customer:
{service_request}
You have access to the full `service_request` dictionary.
It includes:
- Customer contact info (`customerContactName`, `customerContactEmail`, `customerContactPhone`)
- Facility/location info (`customerLocationName`, `customerLocationStreetAddress`, `customerLocationCity`, `customerLocationState`)
- Request type, description, and status (`description`, `detailedDescription`, `status`, `type`)
- Timestamps (`dateTimeCreated`, `statusLastUpdated`, `timeOpen`)
- Optional fields like PO number, billing address, and internal notes
Use this data to write a clear, contextual response related to repairs, PM, scheduling, or status.

Reply instructions:
{instructions}

Guidelines:
- Use simple, professional, and friendly language.
- Always start with: "Hi [First Name],"
- Focus only on the core message—no filler, no small talk.
- No hyperlinks—use plain text only.
- Maintain brand tone: clear, helpful, confident.
- Use line breaks for readability.
- Use service request info to reply
Sign off with as usual if not mentioned on instructions :
Ron McDonnell  
Pronto Gym Services  
📞 (888) 733-8510  
✉️ choose@prontogymservices.com

Reply:
"""
    )

    print("[INFO] Invoking GPT-4 chain...")
    chain = (
        RunnablePassthrough.assign(
            context=RunnableLambda(lambda x: context_text),
            instructions=RunnableLambda(lambda x: prompt_instructions),
            service_request=RunnableLambda(lambda x: service_request)
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
