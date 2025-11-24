import re
from langchain_openai import ChatOpenAI
from utils.prompt import SYSTEM_PROMPT, TRUSTED_SOURCES




def query_news(user_query: str):
    print("Hello from query_news")
    llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    model_kwargs={"tools": [{"type": "web_search_preview"}]}
    )


    prompt = f"""
    {SYSTEM_PROMPT}
    The user asked: "{user_query}".
    Search for real-time news related to Pakistan only not any other country.
    If the news is asked for any other country, simply respond with "I only provide information about Pakistan history."
    Summarize the news articles you find.
    Summarize the results clearly.
    Include the source links, only from trusted sources: {', '.join(TRUSTED_SOURCES)}.
    """

    answer = llm.invoke(prompt)

    answer_text = "".join(block["text"] for block in answer.content if block.get("type") == "text")
    print("Answer:", answer_text)
    
    # Extract all URLs from Markdown-style links [text](url)
    urls = re.findall(r'\((https?://[^\s)]+)\)', answer_text)


    print("anser:",answer)
    return {
        "answer": "".join(block["text"] for block in answer.content if block.get("type") == "text"),
        "source": urls if urls else ["Web / News"],
        "type": "News"
    }
