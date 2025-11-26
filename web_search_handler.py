import re
from langchain_openai import ChatOpenAI
from utils.prompt import SYSTEM_PROMPT


def query_web(user_query: str):
    try:
        print("Hello from query_web")

        # --------------------------
        # LLM Initialization
        # --------------------------
        try:
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0,
                model_kwargs={"tools": [{"type": "web_search_preview"}]}
            )
        except Exception as e:
            print(f"LLM initialization failed: {e}")
            return {
                "answer": "Failed to initialize model.",
                "source": [],
                "type": "Web Search Error"
            }

        # --------------------------
        # Build prompt safely
        # --------------------------
        try:
            prompt = f"""
            {SYSTEM_PROMPT}
            The user asked: "{user_query}".
            Search for real-time news related to Pakistan only.
            The answer should be short and concise.
            and the source link should be separated in brackets and must be mentioned all at the end .
            Summarize the results clearly.
            """
        except Exception as e:
            print(f"Failed to build prompt: {e}")
            return {
                "answer": "Could not prepare search prompt.",
                "source": [],
                "type": "Web Search Error"
            }

        # --------------------------
        # Call the LLM
        # --------------------------
        try:
            answer_obj = llm.invoke(prompt)
        except Exception as e:
            print(f"Web search failed: {e}")
            return {
                "answer": "Web search failed. Try again later.",
                "source": [],
                "type": "Web Search Error"
            }

        # --------------------------
        # Parse response content safely
        # --------------------------
        try:
            # Protect against missing or unexpected structure
            if not hasattr(answer_obj, "content") or not isinstance(answer_obj.content, list):
                print("⚠ Unexpected LLM response format.")
                return {
                    "answer": "No valid search results returned.",
                    "source": [],
                    "type": "Web Search"
                }

            answer_text = ""
            for block in answer_obj.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    answer_text += block.get("text", "")

            answer_text = answer_text.strip()

            if answer_text == "":
                print("Empty response from model.")
                answer_text = "No relevant information found."
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            answer_text = "Could not parse search results."

        print("Answer:", answer_text)

        # --------------------------
        # Extract URLs safely
        # --------------------------
        try:
            urls = re.findall(r'\((https?://[^\s)]+)\)', answer_text)
        except Exception as e:
            print(f"URL extraction failed: {e}")
            urls = []

        return {
            "answer": answer_text,
            "source": urls if urls else ["Web / Search"],
            "type": "Web Search"
        }

    except Exception as e:
        # Final fallback (never let the backend crash)
        print(f"Unexpected error in query_web(): {e}")
        return {
            "answer": "An unexpected error occurred during web search.",
            "source": [],
            "type": "Web Search Error"
        }
