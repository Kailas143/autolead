import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load env from backend directory
load_dotenv(".env")

def test_zoho_connection():
    host = os.getenv("ZOHO_SMTP_HOST", "smtp.zoho.in")
    port = int(os.getenv("ZOHO_SMTP_PORT", 465))
    user = os.getenv("ZOHO_SMTP_USER")
    password = os.getenv("ZOHO_SMTP_PASSWORD")
    
    print(f"Testing connection to {host}:{port} as {user}...")
    
    if not user or not password:
        print("Error: ZOHO_SMTP_USER or ZOHO_SMTP_PASSWORD not found in .env")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = user
        msg["Subject"] = "Zoho SMTP Test"
        msg.attach(MIMEText("Connection successful!", "plain"))

        if port == 465:
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
        
        print("✅ SUCCESS: Zoho SMTP is working correctly!")
    except Exception as e:
        print(f"❌ FAILURE: {str(e)}")
        print("\nNote: Even without 2FA, Zoho may block 'Less Secure Apps'.")
        print("Consider enabling 2FA and using an App Password for better security and reliability.")

if __name__ == "__main__":
    test_zoho_connection()
