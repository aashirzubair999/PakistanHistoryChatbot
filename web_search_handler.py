import re
from langchain_openai import ChatOpenAI
from utils.prompt import SYSTEM_PROMPT

def query_web(user_query: str):
    print("Helloooooooooooooooo1")
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        model_kwargs={"tools": [{"type": "web_search_preview"}]}
    )

    prompt = f"""
    {SYSTEM_PROMPT}
    The user asked: "{user_query}".
    Search for real-time news related to Pakistan only not any other country.
    Summarize the results clearly.
    Important: Include the source links as well.
    """

    answer_obj = llm.invoke(prompt)
    
    # Join all text blocks
    answer_text = "".join(block["text"] for block in answer_obj.content if block.get("type") == "text")
    print("Answer:", answer_text)
    
    # Extract all URLs from Markdown-style links [text](url)
    urls = re.findall(r'\((https?://[^\s)]+)\)', answer_text)

    return {
        "answer": answer_text,
        "source": urls if urls else ["Web / Search"]
    }
