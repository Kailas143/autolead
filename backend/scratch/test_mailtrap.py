import requests
import os
from dotenv import load_dotenv

# Load env from backend directory
load_dotenv(".env")

def test_mailtrap_connection():
    token = os.getenv("MAILTRAP_API_TOKEN")
    from_email = os.getenv("EMAIL_FROM", "hello@aurvyz.com")
    from_name = os.getenv("EMAIL_FROM_NAME", "Aurvyz")
    
    # We'll try to send a test to yourself first
    to_email = from_email 
    
    print(f"Testing Mailtrap connection with token: {token[:4]}...{token[-4:]}")
    
    if not token:
        print("Error: MAILTRAP_API_TOKEN not found in .env")
        return

    url = "https://send.api.mailtrap.io/api/send"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": {"email": from_email, "name": from_name},
        "to": [{"email": to_email}],
        "subject": "Mailtrap SMTP Test",
        "html": "<h1>Success!</h1><p>Mailtrap API is working correctly with Aurvyz.</p>",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 202]:
            print("✅ SUCCESS: Mailtrap API is working correctly!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ FAILURE: {response.status_code}")
            print(f"Response: {response.text}")
            if "domain" in response.text.lower():
                print("\nNote: You likely need to verify 'aurvyz.com' in the Mailtrap Sending Domains dashboard.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_mailtrap_connection()
