import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.openai_client import client

def build_categorization_prompt(subject: str, body: str) -> str:
        return f"""
    You are a professional-grade email classification assistant for a commercial service company. Your task is to analyze incoming emails and assign the most appropriate category based on the sender's intent. These emails are typically related to service requests, scheduling, billing, follow-ups, or general communication.

    You must evaluate **both the subject and body** of the email to determine the correct category.

    ## Categories (Respond with the NUMBER only):
    1. New Service Request  
    2. Request for Quote / Estimate  
    3. Appointment / Confirmation  
    4. Insurance / Vendor Compliance  
    5. Availability Update  
    6. Follow-up on Ongoing Job  
    7. Feedback / Review on Completed Service  
    8. Invoice / Payment Questions  
    9. Complaint / Issue After Service  
    10. Warranty Claim  
    11. Cancellation Request  
    12. General Questions / Support  
    13. Others / Spam  

    ## Classification Guidelines:
    - **Always consider the full subject and body** together.
    - Identify the sender’s **main intent** — not just keywords.
    - Choose **1** if they are asking for a technician or help with a new issue.
    - Choose **2** if they are asking about pricing, quote, or estimate (explicit or implied).
    - Choose **3** if the sender confirms or proposes a specific time/date for a meeting or service.
    - Choose **4** if the email refers to vendor onboarding, COI, W9, or insurance.
    - Choose **5** for inquiries or updates about technician/staff availability.
    - Choose **6** if they refer to a job already started or ongoing and want an update or reschedule.
    - Choose **7** if they provide positive or negative feedback with no issue needing resolution.
    - Choose **8** if the sender is asking about an invoice, payment, billing discrepancy, etc.
    - Choose **9** if they are unhappy after service (e.g., "the issue is still not fixed", “problem returned”).
    - Choose **10** for warranty-related repairs, within a time-based or contract-based coverage.
    - Choose **11** if the email clearly requests to cancel a scheduled job, meeting, or dispatch.
    - Choose **12** if the email is a general question not fitting other categories (e.g., asking about equipment type, repair process, or a product).
    - Choose **13** if the email is vague, spam, off-topic, or clearly not actionable.
    ## Important Notes:
    - Always use both subject and body to determine the sender’s core intent.
    - **Choose 1 (New Service Request)** if the email is requesting repair, service, or technical support for a new issue — i.e., this is the first time the sender is asking for help with this specific problem. Examples:
        - “Treadmill is broken”, “Something is stuck”, “Can someone come out?”, “Need a technician”, “Equipment isn’t working.”
        - Even if they mention urgency or scheduling — if it’s about a **new issue**, not a follow-up, use 1.
        - Do **not** use 1 if they’re following up on a previous job, complaining about incomplete work, or asking about warranty.
    - Choose 2 if they are asking for pricing, a quote, or an estimate.
    - Choose 3 if they are proposing or confirming a specific date/time.
    - Choose 6–10 if the sender is referring to a previous or completed job.
    - Choose 13 if the email is unclear, irrelevant, or contains no real intent.
    - Always return only the category number.
## Output Rules:
- Respond with the category number **only**.
- **Do not** return any label, description, explanation, or markdown.
- Response must be a single digit (or 2 digits for 10–13), e.g., `4` or `12`.

## Email Subject:
{subject}

## Email Body:
\"\"\"
{body}
\"\"\"

Category Number:
""".strip()

def categorize_email(subject: str, body: str) -> int:
    prompt = build_categorization_prompt(subject, body)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )
        result = response.choices[0].message.content.strip()
        category = int(result)
        return category if 1 <= category <= 13 else 13
    except Exception as e:
        print(f"⚠️ Categorization error: {e}")
        return 13
