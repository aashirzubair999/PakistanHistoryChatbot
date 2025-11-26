import os
import asyncio
from dotenv import load_dotenv
from typing import List, Dict
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# -------------------------
# Load Vector Databases
# -------------------------
def load_vectordbs(base_dir="vectorstores") -> Dict[str, Chroma]:
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


# -------------------------
# Query a Single Store
# -------------------------
async def query_single_store_async(store_name: str, vectordb, user_query: str, k=3) -> List[Document]:
    """Query a single vector store asynchronously and attach store_name metadata."""
    if vectordb is None:
        return []

    # Run similarity search in a background thread
    docs = await asyncio.to_thread(vectordb.similarity_search, user_query, k=k)

    # Attach store_name to each doc for tracking
    for doc in docs:
        doc.metadata["store_name"] = store_name

    return docs


# -------------------------
# Query All Vector Stores
# -------------------------
async def query_all_top3(user_query: str, vectordbs: Dict) -> Dict:
    """
    Query all vector stores in parallel, get ALL docs, return top 3 most relevant overall.
    Tracks which document the answer comes from.
    """
    print("Querying all vector stores...")
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # Create all async tasks at once for all stores
    tasks = [
        query_single_store_async(store_name, vectordbs[store_name], user_query, k=100)
        for store_name in vectordbs.keys()
    ]

    # Run all tasks simultaneously
    results = await asyncio.gather(*tasks)

    # Combine ALL docs from all stores
    all_docs = [doc for docs in results for doc in docs]

    if not all_docs:
        return {
            "answer": None,
            "sources": [],
            "from": [],
            "found": False,
            "docs_count": 0
        }

    # Sort by similarity score descending
    all_docs.sort(key=lambda d: getattr(d, "score", 0), reverse=True)

    # Take ONLY top 3 most relevant overall
    top_3_docs = all_docs[:3]

    # Extract metadata BEFORE generating answer
    sources = list({doc.metadata.get("source_file") for doc in top_3_docs if doc.metadata.get("source_file")})
    stores_used = list({doc.metadata.get("store_name") for doc in top_3_docs})

    # Create prompt with explicit FOUND/NOT_FOUND format
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You must answer STRICTLY using ONLY the provided documents.\n\n"
         "If the answer EXISTS in the documents, respond EXACTLY like this:\n"
         "FOUND: <your answer here>\n\n"
         "If the answer is NOT in the documents, respond EXACTLY like this:\n"
         "Information not found in documents.\n\n"
         "Documents:\n{context}"),
        ("human", "{question}")
    ])
    chain = create_stuff_documents_chain(llm, prompt)

    # Generate answer from top 3 docs
    output = await asyncio.to_thread(chain.invoke, {"context": top_3_docs, "question": user_query})
    output = output.strip()

    # Check if answer was found
    found = output.startswith("FOUND:")
    
    if found:
        answer = output.replace("FOUND:", "").strip()
    else:
        answer = None

    return {
        "answer": answer,
        "sources": sources,
        "from": stores_used,
        "found": found,  # NEW: Boolean flag
        "docs_count": len(top_3_docs)
    }