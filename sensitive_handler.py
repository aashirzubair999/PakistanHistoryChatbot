from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
from utils.prompt import SENSITIVE_KEYWORDS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email credentials stored in environment variables
sender_email = os.getenv("BOT_EMAIL")                 # Bot email address (Gmail)
recipient_email = os.getenv("ADMIN_EMAIL")            # Admin email address (receiver)
bot_password = os.getenv("BOT_EMAIL_APP_PASSWORD")    # Gmail App Password (not normal password)


def is_sensitive(query: str):
    """
    Checks if the incoming query contains sensitive keywords.
    Returns True if any keyword from SENSITIVE_KEYWORDS 
    exists inside the user query.
    """
    return any(word.lower() in query.lower() for word in SENSITIVE_KEYWORDS)


def send_admin_email(user_name, user_email, query):
    """
    Sends an email to the admin when a sensitive query is detected.

    Steps:
    1. Prepare the email message (user details + query + timestamp)
    2. Connect to Gmail SMTP server and send email (if credentials exist)
    3. If email cannot be sent, print a log message instead
    """
    
    # Current time for logging/notification
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Email content body
    body = f"""
    Sensitive Query Detected:
    User Name: {user_name}
    User Email: {user_email}
    Query: {query}
    Timestamp: {timestamp}
    """
    
    # Create the email object
    msg = MIMEText(body)
    msg['Subject'] = "Sensitive Query Notification"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Only attempt sending if all email credentials are available
    if sender_email and recipient_email and bot_password:
        try:
            # Connect to Gmail SMTP server
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # Enable TLS security

            # Login using bot email + app password
            server.login(sender_email, bot_password)

            # Send the email
            server.send_message(msg)
            server.quit()

            print("Email sent successfully")
        
        except Exception as e:
            # If email fails, log the error and return appropriate message
            print("Failed to send email:", e)
            return {
                "message": "Failed to send email, logged instead",
                "timestamp": timestamp
            }

    else:
        # Fallback when credentials are missing (development mode)
        print("Sensitive query detected (logged instead of sending email):")
        print(body)

    # Final success response returned to the client
    return {
        "message": "Admin notified (or logged)",
        "timestamp": timestamp
    }
