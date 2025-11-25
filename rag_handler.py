import os
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# -------------------------------------------------------------
# Load vector stores (SAFE VERSION)
# -------------------------------------------------------------
def load_vectordbs(base_dir="vectorstores") -> Dict[str, Any]:
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f" Failed to load embeddings: {e}")
        return {"txt": None, "docx": None, "pdf": None}

    def load_db(name):
        try:
            path = os.path.join(base_dir, f"{name}_vector_db")
            if os.path.exists(path):
                print(f"✓ Loaded {name} DB")
                return Chroma(persist_directory=path, embedding_function=embeddings)
            else:
                print(f"Not found: {path}")
                return None
        except Exception as e:
            print(f"Error loading {name} DB: {e}")
            return None

    return {
        "txt": load_db("txt"),
        "docx": load_db("docx"),
        "pdf": load_db("pdf"),
    }


# -------------------------------------------------------------
# QUERY SINGLE VECTORSTORE (SAFE VERSION)
# -------------------------------------------------------------
def query_single_store(vectordb, user_query: str, llm, k=3):
    if vectordb is None:
        return None, None  # store missing → skip

    try:
        docs = vectordb.similarity_search(user_query, k=k)
    except Exception as e:
        print(f" similarity_search failed: {e}")
        return None, None

    if not docs:
        return None, None  # no matching docs

    # LLM prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You must answer STRICTLY using the provided documents.\n"
         "If answer is in documents, reply exactly:\n"
         "FOUND: <answer>\n\n"
         "If NOT found, reply exactly:\n"
         "NOT_FOUND\n\n"
         "Documents:\n{context}"),
        ("human", "{question}")
    ])

    try:
        chain = create_stuff_documents_chain(llm, prompt)
        result = chain.invoke({"context": docs, "question": user_query})
    except Exception as e:
        print(f"LLM chain error: {e}")
        return None, None

    if not result:
        return None, None

    output = str(result).strip()

    if output.startswith("FOUND:"):
        answer = output.replace("FOUND:", "").strip()

        # extract unique sources safely
        sources = []
        seen = set()

        for d in docs:
            try:
                src = d.metadata.get("source") or d.metadata.get("file") or "Unknown"
            except Exception:
                src = "Unknown"

            if src not in seen:
                seen.add(src)
                sources.append(src)

        return answer, sources

    return None, None


# -------------------------------------------------------------
# MASTER QUERY: TXT → DOCX → PDF (SAFE VERSION)
# -------------------------------------------------------------
def query_rag(user_query: str, vectordbs: dict):
    try:
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    except Exception as e:
        print(f" Failed to initialize LLM: {e}")
        return {
            "answer": None,
            "sources": [],
            "from": None,
            "error": "LLM initialization failed"
        }

    search_order = ["txt", "docx", "pdf"]

    for store_name in search_order:
        try:
            print(f"Searching in: {store_name}")
            vectordb = vectordbs.get(store_name)
            answer, sources = query_single_store(vectordb, user_query, llm)
        except Exception as e:
            print(f" Error in store '{store_name}': {e}")
            continue

        if answer:  # FOUND
            return {
                "answer": answer,
                "sources": sources,
                "from": store_name
            }

    # No results anywhere
    return {
        "answer": None,
        "sources": [],
        "from": None
    }
