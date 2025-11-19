from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
from utils.prompt import SENSITIVE_KEYWORDS
from dotenv import load_dotenv

load_dotenv()


sender_email = os.getenv("BOT_EMAIL")  # set in your .env file
recipient_email = os.getenv("ADMIN_EMAIL")  # set in your .env file
bot_password = os.getenv("BOT_EMAIL_APP_PASSWORD")  # 16-char App Password


def is_sensitive(query: str):
    return any(word.lower() in query.lower() for word in SENSITIVE_KEYWORDS)


def send_admin_email(user_name, user_email, query):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Compose email body
    body = f"""
    Sensitive Query Detected:
    User Name: {user_name}
    User Email: {user_email}
    Query: {query}
    Timestamp: {timestamp}
    """
    
    msg = MIMEText(body)
    msg['Subject'] = "Sensitive Query Notification"
    
    # Sender and recipient
   
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # If email credentials are set, send email
    
    if sender_email and recipient_email and bot_password:
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, bot_password)
            server.send_message(msg)
            server.quit()
            print("Email sent successfully")
        except Exception as e:
            print("Failed to send email:", e)
            return {"message": "Failed to send email, logged instead", "timestamp": timestamp}
    else:
        # Development fallback: just log the sensitive query
        print("Sensitive query detected (logged instead of sending email):")
        print(body)
    
    return {"message": "Admin notified (or logged)", "timestamp": timestamp}

