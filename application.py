# application.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.prompt import SYSTEM_PROMPT, NEWS_KEYWORDS

from rag_handler import query_rag, load_vectordbs
from web_search_handler import query_web
from news_handler import query_news
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
    user_name: str = None
    user_email: str = None


# Load all vector stores (docx, txt, pdf)
vectordbs = load_vectordbs(base_dir="vectorstores")
print(f"Loaded vector databases: {list(vectordbs.keys())}")


@application.post("/chat")
async def chat_endpoint(data: UserQuery):
    user_query = data.query
    print("user_query:", user_query)

    # 1. Check for sensitive content
    if is_sensitive(user_query):
        if not data.user_name or not data.user_email:
            return {"message": "Sensitive query detected. Please provide your name and email."}
        return send_admin_email(data.user_name, data.user_email, user_query)

    # 2. Check for news-related queries
    if any(word.lower() in user_query.lower() for word in NEWS_KEYWORDS):
        return query_news(user_query)

    # 3. RAG document query (searches all vector stores)
    rag_response = query_rag(user_query, vectordbs)

    if rag_response and rag_response.get("answer"):
        return rag_response
    else:
        print("RAG did not find anything. Falling back to web search...")
        return query_web(user_query)   # send original user query, not RAG result!

