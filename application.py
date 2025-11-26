import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from pathlib import Path


from utils.prompt import SYSTEM_PROMPT
from rag_handler import query_all_top3, load_vectordbs
from web_search_handler import query_web
from news_handler import query_news, is_news_queury
from sensitive_handler import is_sensitive, send_admin_email
import os

application = FastAPI()
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuery(BaseModel):
    query: str
    chat_history: list = []
    user_name: str = None
    user_email: str = None


# Serve the HTML frontend at root path
@application.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = Path("templates/index.html")
    if html_path.exists():
        return html_path.read_text()
    else:
        return "<h1>Error: templates/index.html not found</h1>"


llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)  # or your preferred LLM

def extract_name_email_llm(text: str):
    """
    Ask LLM to extract name and email from user text.
    Returns (name, email) or (None, None)
    """
    prompt = f"""
    You are an assistant that extracts a person's name and email from text.
    
    Rules:
    1. If the text contains an email-like string, that is the email.
    2. If the text contains one or more words before the email, take the first word as the name.
    3. Respond ONLY in JSON format like:
    {{
        "name": "User's name",
        "email": "User's email"
    }}
    

    Important Examples:
    - Input: "Salar salarkhan@gmail.com"
      Output: {{"name": "Salar", "email": "salarkhan@gmail.com"}}
    - Input: "My name is Aashir and my email is aashir@example.com"
      Output: {{"name": "Aashir", "email": "aashir@example.com"}}

    4. If you cannot find name or email, use null.
    Text: "{text}"
    """
    response = llm.invoke(prompt)
    # LLM might return string or AIMessage
    if isinstance(response, AIMessage):
        content = response.content
    else:
        content = str(response)
    # Try to parse JSON safely
    import json
    try:
        data = json.loads(content)
        name = data.get("name")
        email = data.get("email")
        return name, email
    except Exception as e:
        print(f"Failed to parse LLM JSON: {e}, content: {content}")
        return None, None



@application.post("/chat")
async def chat_endpoint(data: UserQuery):
    user_query = data.query
    chat_history = data.chat_history or []

    previous_ai_message = chat_history[-1].get("AI") if chat_history else None
    previous_was_sensitive = (
        previous_ai_message == "Sensitive query detected. Please provide your name and email."
    )

    # CASE 1: User replied after a sensitive warning
    if previous_was_sensitive:
        # Try extracting name/email using LLM
        name, email = extract_name_email_llm(user_query)

        # Check if extraction looks valid
        if name and email:
            # Send admin email about original sensitive query
            original_sensitive_query = chat_history[-1]["user"]
            result = send_admin_email(name, email, original_sensitive_query)
            # Ensure proper response format
            if "response" not in result:
                return {"response": {"AI": result.get("message", "Email sent successfully.")}}
            return result
        else:
            # Extraction failed, treat as normal query
            print("LLM could not confidently extract name/email. Processing as normal query.")
            previous_was_sensitive = False  # continue to normal processing

    # CASE 2: First-time sensitive query detection
    if is_sensitive(user_query):
        return {"response": {"AI": "Sensitive query detected. Please provide your name and email."}}

    # Build normal LLM messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["AI"]})
    messages.append({"role": "user", "content": user_query})

    print("user_query:", user_query)

    # News check
    if is_news_queury(user_query):
        news_result = query_news(user_query, messages)
        # Ensure proper response format
        if "response" not in news_result:
            return {"response": {"AI": news_result.get("message", news_result.get("answer", "No news found."))}}
        return news_result

    # RAG async query
    vectordbs = load_vectordbs(base_dir="vectorstores")
    rag_response = await query_all_top3(user_query, vectordbs)

    print("RAG sourse:", rag_response.get("sources"))  # Debug print
    print("RAG from:", rag_response.get("from"))  # Debug print
    

    if rag_response and rag_response.get("answer"):
        # Ensure proper response format
        return {"response": {"AI": rag_response["answer"]}}
    else:
        print("RAG did not find anything. Falling back to web search...")
        web_result = query_web(user_query)
        # Ensure proper response format
        if "response" not in web_result:
            return {"response": {"AI": web_result.get("message", web_result.get("answer", "No information found."))}}
        return web_result