from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Document loaders from LangChain
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Vector DB and embeddings
from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings

# Load environment variables (like OPENAI_API_KEY)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
embeddings = FastAPI()

# Enable CORS for all origins (allow cross-origin requests)
embeddings.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional input model for the embedding route (folder_path defaults to 'documents')
class EmbeddingInput(BaseModel):
    folder_path: str = "documents"  # default folder

# --- Helper Functions ---

def get_all_document_paths(folder="documents"):
    """
    Return all PDF, TXT, and DOCX files in the specified folder.
    """
    supported_exts = (".pdf", ".txt", ".docx")
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(supported_exts)]

def load_documents_by_type(paths: list[str], file_type: str):
    """
    Load documents of a specific type from a list of file paths.
    Supported types: pdf, txt, docx
    Returns a list of loaded documents.
    """
    docs = []
    for path in paths:
        ext = path.split(".")[-1].lower()
        if ext != file_type:
            continue
        if ext == "pdf":
            loader = PyPDFLoader(path)
        elif ext == "txt":
            loader = TextLoader(path, encoding="utf-8")
        elif ext == "docx":
            loader = Docx2txtLoader(path)
        docs.extend(loader.load())
    return docs

def create_embeddings_by_type(paths: list[str]):
    """
    Create embeddings for documents grouped by type (pdf, txt, docx).
    Saves each type's vector database under 'vectorstores/{type}_vector_db'.
    Returns a dictionary with information about processed documents.
    """
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    types = ["pdf", "txt", "docx"]
    results = {}

    for t in types:
        # Load documents of this type
        docs = load_documents_by_type(paths, t)
        if not docs:
            results[t] = "No documents of this type"
            continue

        # Split large documents into chunks for embeddings
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(docs)

        # Create vector store for the chunks
        vectordb = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=f"vectorstores/{t}_vector_db"
        )

        # Save info about created chunks and vector DB path
        results[t] = {"chunks": len(split_docs), "path": f"vectorstores/{t}_vector_db"}

    return results

# --- FastAPI Route ---

@embeddings.post("/create_embedding")
async def create_embedding_endpoint(body: EmbeddingInput = None):
    """
    Endpoint to create embeddings for all documents in the specified folder.
    If no folder is provided, defaults to 'documents'.
    Returns info about processed document chunks and vector DB paths.
    """
    folder = body.folder_path if body else "documents"
    file_paths = get_all_document_paths(folder)
    
    if not file_paths:
        return {"error": f"No documents found in folder: {folder}"}
    
    try:
        result = create_embeddings_by_type(file_paths)
        return result
    except Exception as e:
        return {"error": str(e)}
