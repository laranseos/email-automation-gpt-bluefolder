# test_categorizer.py
from categorizer import categorize_email

def test_categorize_email():
    test_cases = [
        {
            "subject": "Treadmill is broken and needs repair ASAP",
            "body": "Hi, the treadmill on the second floor stopped working completely. Please send a technician.",
            "expected_category": 1
        },
        {
            "subject": "Request for quote on new equipment",
            "body": "Could you please provide an estimate for replacing the gym flooring?",
            "expected_category": 2
        },
        {
            "subject": "Confirming appointment for July 15th",
            "body": "Just wanted to confirm the scheduled repair appointment for July 15th at 10 AM.",
            "expected_category": 3
        },
        {
            "subject": "General question about repair process",
            "body": "Can you explain how your service warranty works?",
            "expected_category": 12
        },
        {
            "subject": "Spam message here",
            "body": "You won a prize! Click here now!",
            "expected_category": 13
        }
    ]

    for i, case in enumerate(test_cases, start=1):
        print(f"\nTest case #{i}:")
        category = categorize_email(case['subject'], case['body'])
        print(f"Subject: {case['subject']}")
        print(f"Expected Category: {case['expected_category']}, Predicted: {category}")
        assert category == case['expected_category'], f"Failed test case #{i}"

if __name__ == "__main__":
    test_categorize_email()
    print("\nAll test cases passed!")
