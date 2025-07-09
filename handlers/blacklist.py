import re

BLACKLISTED_EMAILS = {
    "internal@prontogymservices.com",
    # add any exact full addresses here
}

BLACKLISTED_DOMAINS = {
    "prontogymservices.com",  # your company domain to exclude internal
    "spamdomain.com",
    "noreply.com",
}

def is_blacklisted(email: str) -> bool:
    email = email.strip().lower()
    
    # Check exact email blacklist
    if email in BLACKLISTED_EMAILS:
        return True

    # Extract domain
    match = re.search(r"@([\w.-]+)$", email)
    domain = match.group(1) if match else ""

    # Check domain blacklist
    if domain in BLACKLISTED_DOMAINS:
        return True

    # Check common system prefixes like no-reply, noreply, donotreply
    local_part = email.split("@")[0]
    if re.match(r"^(no-?reply|donot-?reply|noreply|bounce|mailer-daemon|postmaster)$", local_part):
        return True

    return False
