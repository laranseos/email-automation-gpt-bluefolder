from parser import parse_email_with_gpt

def test_parse_email():
    subject = "Service request: treadmill repair needed"
    body = """
Hi,

My treadmill suddenly stopped working. It's making a strange noise and won't start.
Please help. contat here 58437394873

Thanks,
Colby Nales
Promto teams net
"""
    sender_name = "John Doe"
    sender_email = "johndoe@example.com"

    result = parse_email_with_gpt(subject, body, sender_name, sender_email)

    print("Parsed Output:")
    print(result)

if __name__ == "__main__":
    test_parse_email()
