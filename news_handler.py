import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from utils.prompt import TRUSTED_SOURCES

llm = ChatOpenAI()

def is_news_queury(user_query: str) -> bool:
    prompt = f"""
    Detect if the following query is asking about **latest, breaking, or current events** such as:
    - news happening now, live updates, breaking news, trending events
    - press releases or official announcements made recently
    - ongoing developments or reports from media outlets that are current

    Do NOT classify general informational, historical, or educational questions as current news.  
    Examples of NOT current news queries:
    - “What is the Kashmir issue?”  
    - “Tell me history of Pakistan Army”  
    - “How does intelligence work in general?”  
    - “Why do countries go to war?”  

    Respond with **YES** only if the query is about **news or events that are happening currently or very recently**.  
    Otherwise respond with **NO**.

    Query: "{user_query}"
"""


    
    response = llm.invoke(prompt)
    if isinstance(response, AIMessage):
        text = response.content
    else:
        text = str(response)
    
    return text.strip().upper() == "YES"




def query_news(user_query: str, message: list = None):
    """
    Use the full messages list built in application.py.
    message: list of dicts, e.g., [{"role": "system", "content": ...}, ...]
    """
    print("Searching from the news handler...")
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        model_kwargs={"tools": [{"type": "web_search_preview"}]}
    )

    # Convert the messages list into a single prompt
    full_context = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in (message or [])])

    prompt = f"""
    The user asked: "{user_query}".
    Based on the conversation so far, summarize real-time news related to Pakistan.
    If the user asks for news about any other country, respond with:
    "I only provide information about Pakistan history."
    Include source links only from trusted sources: {', '.join(TRUSTED_SOURCES)}.
    Summarize clearly.
    Important: Result should be short and concise. It should be brief and to the point not too long. Should end in 3 to 4 lines.
    Conversation context:
    {full_context}
    """

    answer = llm.invoke(prompt)

    # Extract text
    answer_text = "".join(
        block["text"] for block in answer.content if block.get("type") == "text"
    ) if hasattr(answer, "content") else str(answer)

    # Extract URLs
    urls = re.findall(r'\((https?://[^\s)]+)\)', answer_text)

    return {
        "answer": answer_text,
        "source": urls if urls else ["Web / News"],
        "type": "News"
    }
