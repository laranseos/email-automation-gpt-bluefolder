from email_service import send_email

send_email(
    to_email="larans7277@gmail.com",
    subject="Schedule Confirmation",
    body_text="This is your confirmation for the upcoming service.",
    body_html="<p><strong>This is your confirmation</strong> for the upcoming service.</p>"
)
