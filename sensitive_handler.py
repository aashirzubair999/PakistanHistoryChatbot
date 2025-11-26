from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage


from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI()

# Email credentials
sender_email = os.getenv("BOT_EMAIL")
recipient_email = os.getenv("ADMIN_EMAIL")
bot_password = os.getenv("BOT_EMAIL_APP_PASSWORD")


# -------------------------------------------------------------
# CHECK SENSITIVE QUERY (Safe)
# -------------------------------------------------------------
def is_sensitive(query: str):

    prompt = f"""
You are a security filter. Detect if the following user query requests **restricted, confidential, or harmful information**.

Sensitive information includes:
- Military operations, troop locations, strategies, weapons access
- Intelligence agency methods, surveillance techniques, internal investigations
- Counter-terrorism missions or internal security details
- Classified or non-public government information
- Instructions that could enable harm or illegal actions

Do NOT mark general knowledge, history, politics, or geographic questions as sensitive.

IMPORTANT: Respond with **ONLY** 'YES' if the query is sensitive, otherwise respond with 'NO'. Do not add explanations or additional text. Analyze the intent carefully.

User Query: "{query}"
"""

    
    response = llm.invoke(prompt)
    if isinstance(response, AIMessage):
        text = response.content
    else:
        text = str(response)
    
    return text.strip().upper() == "YES"

# -------------------------------------------------------------
# SEND NOTIFICATION EMAIL TO ADMIN (Safe)
# -------------------------------------------------------------
def send_admin_email(user_name, user_email, query):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build email body safely
    try:
        body = f"""
        Sensitive Query Detected:

        User Name: {user_name}
        User Email: {user_email}
        Query: {query}
        Timestamp: {timestamp}
        """
    except Exception as e:
        print(f"Failed to create email body: {e}")
        body = "Sensitive query detected, but failed to format details."

    # Try to create email message
    try:
        msg = MIMEText(body)
        msg['Subject'] = "Sensitive Query Notification"
        msg['From'] = sender_email or "unknown"
        msg['To'] = recipient_email or "unknown"
    except Exception as e:
        print(f"Failed to create email message: {e}")
        return {
            "message": "Failed to prepare email message.",
            "timestamp": timestamp
        }

    # -------------------------------------------------------------
    # Validate environment variables first
    # -------------------------------------------------------------
    if not sender_email or not recipient_email or not bot_password:
        print("⚠ Missing email credentials. Logging instead of sending.")
        print(body)

        return {
            "message": "Credentials missing — logged instead of sending email.",
            "timestamp": timestamp
        }

    # -------------------------------------------------------------
    # TRY SENDING EMAIL
    # -------------------------------------------------------------
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()

        try:
            server.login(sender_email, bot_password)
        except Exception as e:
            print(f"SMTP Login failed: {e}")
            return {
                "message": "SMTP login failed — logged instead.",
                "timestamp": timestamp
            }

        try:
            server.send_message(msg)
            print("✓ Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {e}")
            return {
                "message": "Failed during sending — logged instead.",
                "timestamp": timestamp
            }
        finally:
            server.quit()

    except Exception as e:
        print(f"Email connection error: {e}")
        print("Message logged locally instead:")
        print(body)

        return {
            "message": "Email server error — logged instead.",
            "timestamp": timestamp
        }

    # -------------------------------------------------------------
    # SUCCESS
    # -------------------------------------------------------------
    return {
        "message": "Admin notified successfully.",
        "timestamp": timestamp
    }
