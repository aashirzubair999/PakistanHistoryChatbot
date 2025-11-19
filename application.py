# application.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.prompt import SYSTEM_PROMPT, NEWS_KEYWORDS

# from rag_handler import query_rag, create_embeddings
# from web_search_handler import query_web
# from news_handler import query_news
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

# Load RAG vector DB at startup
# from rag_handler import get_all_document_paths
# doc_paths = get_all_document_paths("documents")
# vectordb = create_embeddings(doc_paths)

@application.post("/chat")
async def chat_endpoint(data: UserQuery):
    user_query = data.query
    print("user_query:",user_query)

    # 1. Check sensitive
    if is_sensitive(user_query):
        if not data.user_name or not data.user_email:
            return {"message": "Sensitive query detected. Please provide your name and email."}
        return send_admin_email(data.user_name, data.user_email, user_query)

    # 2. Check news
    # if any(word.lower() in user_query.lower() for word in NEWS_KEYWORDS):
    #     return query_news(user_query)

    # # 3. RAG document query
    # rag_response = query_rag(user_query, vectordb)
    # if rag_response and rag_response["answer"]:
    #     return rag_response

    # # 4. Fallback to web search
    # return query_web(user_query)
