import requests
import json
import sys

def simulate_reply(email, message):
    url = "http://localhost:8000/api/v1/webhooks/reply"
    payload = {
        "from": email,
        "body": message
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    email = "kailasvs94@gmail.com"
    message = "Yes, I would be interested in learning more about your AI systems."
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        message = sys.argv[2]
        
    print(f"Simulating reply from {email}...")
    simulate_reply(email, message)
