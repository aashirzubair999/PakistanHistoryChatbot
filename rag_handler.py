import os
from dotenv import load_dotenv
from typing import List
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# -------------------------------------------------------------
# Load vector stores
# -------------------------------------------------------------
def load_vectordbs(base_dir="vectorstores"):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    def load_db(name):
        path = os.path.join(base_dir, f"{name}_vector_db")
        if os.path.exists(path):
            print(f"✓ Loaded {name} DB")
            return Chroma(persist_directory=path, embedding_function=embeddings)
        else:
            print(f"✗ Not found: {path}")
            return None

    return {
        "txt": load_db("txt"),
        "docx": load_db("docx"),
        "pdf": load_db("pdf"),
    }


# -------------------------------------------------------------
# QUERY SINGLE VECTORSTORE
# -------------------------------------------------------------
def query_single_store(vectordb, user_query, llm, k=3):
    if vectordb is None:
        return None, None  # skip

    docs = vectordb.similarity_search(user_query, k=k)
    if not docs:
        return None, None

    # Prompt forces LLM to declare FOUND or NOT_FOUND
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You must answer STRICTLY using the provided documents.\n"
         "If answer is in documents, reply exactly:\n"
         "FOUND: <answer>\n\n"
         "If NOT found, reply exactly:\n"
         "NOT_FOUND\n\n"
         "Documents:\n{context}"
         ),
        ("human", "{question}")
    ])

    chain = create_stuff_documents_chain(llm, prompt)

    result = chain.invoke({
        "context": docs,
        "question": user_query
    })

    output = result.strip()

    if output.startswith("FOUND:"):
        answer = output.replace("FOUND:", "").strip()

        # Extract unique source names
        seen = set()
        sources = []

        for d in docs:
            src = d.metadata.get("source") or d.metadata.get("file") or "Unknown"
            if src not in seen:
                seen.add(src)
                sources.append(src)

        return answer, sources

    return None, None  # means NOT_FOUND


# -------------------------------------------------------------
# MASTER QUERY: TXT → DOCX → PDF
# -------------------------------------------------------------
def query_rag(user_query, vectordbs):
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    search_order = ["txt", "docx", "pdf"]

    for store_name in search_order:
        vectordb = vectordbs.get(store_name)

        print(f"Searching in: {store_name}")

        answer, sources = query_single_store(vectordb, user_query, llm)

        if answer:  # FOUND
            return {
                "answer": answer,
                "sources": sources,
                "from": store_name
            }

    # No answers anywhere
    return {
    "answer": None,
    "sources": [],
    "from": None
}

