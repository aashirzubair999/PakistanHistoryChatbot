from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
from dotenv import load_dotenv

# Document loaders from LangChain
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Vector DB and embeddings
from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings_app = FastAPI()

embeddings_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmbeddingInput(BaseModel):
    folder_path: str = "documents"

def get_all_document_paths(folder="documents"):
    """Return all PDF, TXT, and DOCX files in the specified folder."""
    supported_exts = (".pdf", ".txt", ".docx")
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(supported_exts)]

def load_documents_by_type(paths: list[str], file_type: str):
    """
    Load documents of a specific type and attach metadata (filename, type, timestamp).
    """
    docs = []
    for path in paths:
        ext = path.split(".")[-1].lower()
        if ext != file_type:
            continue
        
        try:
            if ext == "pdf":
                loader = PyPDFLoader(path)
            elif ext == "txt":
                loader = TextLoader(path, encoding="utf-8")
            elif ext == "docx":
                loader = Docx2txtLoader(path)
            
            loaded_docs = loader.load()
            
            # Attach metadata to each document
            for doc in loaded_docs:
                if doc.metadata is None:
                    doc.metadata = {}
                
                # Add custom metadata fields
                doc.metadata["source_file"] = os.path.basename(path)  # filename
                doc.metadata["file_type"] = ext                       # extension
                doc.metadata["full_path"] = os.path.abspath(path)    # full path
                doc.metadata["loaded_at"] = datetime.now().isoformat()  # timestamp
                
            docs.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue
    
    return docs

def create_embeddings_by_type(paths: list[str]):
    """
    Create embeddings for documents grouped by type, preserving all metadata.
    """
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    types = ["pdf", "txt", "docx"]
    results = {}

    for t in types:
        # Load documents with metadata
        docs = load_documents_by_type(paths, t)
        if not docs:
            results[t] = "No documents of this type"
            continue

        # Split documents - metadata is automatically copied to chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(docs)

        # Verify metadata is on chunks (debugging)
        for chunk in split_docs[:1]:  # Check first chunk
            print(f"[{t}] Chunk metadata: {chunk.metadata}")

        # Create vector store with metadata
        vectordb = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=f"vectorstores/{t}_vector_db"
        )

        results[t] = {
            "chunks": len(split_docs),
            "path": f"vectorstores/{t}_vector_db",
            "metadata_stored": True
        }

    return results

@embeddings_app.post("/create_embedding")
async def create_embedding_endpoint(body: EmbeddingInput = None):
    """Create embeddings for all documents with metadata preserved."""
    folder = body.folder_path if body else "documents"
    file_paths = get_all_document_paths(folder)
    
    if not file_paths:
        return {"error": f"No documents found in folder: {folder}"}
    
    try:
        result = create_embeddings_by_type(file_paths)
        return result
    except Exception as e:
        return {"error": str(e)}

