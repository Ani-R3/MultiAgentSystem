# backend/RAGAgent.py

import os
import logging
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Constants
PDF_UPLOADS_DIR = "uploads"
VECTOR_STORE_PATH = "vector_store"
os.makedirs(PDF_UPLOADS_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

logger = logging.getLogger("RAGAgentLogger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - RAG - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class RAGAgent:
    def __init__(self):
        logger.info("Initializing RAG Agent...")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            logger.info("✓ Embedding model loaded.")
        except Exception as e:
            logger.error(f"✗ Failed to load embedding model: {e}", exc_info=True)
            raise
        self.vectorStore = None
        self.LoadVectorStore()

    def ProcessPDF(self, pdfPath):
        try:
            logger.info(f"Processing PDF: {os.path.basename(pdfPath)}")
            doc = fitz.open(pdfPath)
            page_count = len(doc)
            
            all_texts, all_metadatas = [], []
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                if not page_text.strip(): continue
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_text(page_text)
                
                for i, chunk in enumerate(chunks):
                    all_texts.append(chunk)
                    all_metadatas.append({"source": os.path.basename(pdfPath), "page": page_num + 1})
            
            doc.close()
            logger.info(f"✓ Extracted {len(all_texts)} chunks from {page_count} pages.")

            if not all_texts:
                logger.error("✗ No text chunks extracted.")
                return False

            logger.info("Creating new vector store for the uploaded PDF...")
            self.vectorStore = FAISS.from_texts(texts=all_texts, embedding=self.embeddings, metadatas=all_metadatas)
            self.vectorStore.save_local(VECTOR_STORE_PATH)
            logger.info("✓ Vector store created and saved.")
            return True

        except Exception as e:
            logger.error(f"✗ Error processing PDF: {e}", exc_info=True)
            return False

    def LoadVectorStore(self):
        if os.path.exists(f"{VECTOR_STORE_PATH}/index.faiss"):
            try:
                self.vectorStore = FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"✓ Vector store loaded successfully with {self.vectorStore.index.ntotal} vectors.")
            except Exception as e:
                logger.error(f"✗ Error loading vector store: {e}", exc_info=True)
        else:
            logger.info("No existing vector store found.")

    def QueryRAG(self, userQuery):
        logger.info(f"RAG received query: '{userQuery}'")
        if not self.vectorStore:
            logger.warning("✗ No vector store loaded.")
            return "No documents have been uploaded."

        # SMART RETRIEVAL
        generic_summaries = ['summarize', 'summary', 'overview', 'abstract', 'what is this about', 'what is this document about', 'what is the pdf about']
        if any(kw in userQuery.lower() for kw in generic_summaries):
            logger.info("Generic summary requested. Fetching content from the first page.")
            try:
                # Get all chunks from the first page
                retrieved_docs = [self.vectorStore.docstore.get_document(doc_id) for doc_id, doc in self.vectorStore.index_to_docstore_id.items() if self.vectorStore.docstore.get_document(doc_id).metadata.get('page') == 1]
                if not retrieved_docs: # Fallback if first page has no content
                     retrieved_docs = self.vectorStore.similarity_search(userQuery, k=3)
            except Exception as e:
                logger.error(f"Could not get docs by page, falling back to similarity search. Error: {e}")
                retrieved_docs = self.vectorStore.similarity_search(userQuery, k=3)
        else:
            logger.info("Specific query received. Performing similarity search.")
            retrieved_docs = self.vectorStore.similarity_search(userQuery, k=5)
        
        if not retrieved_docs:
            logger.warning("✗ No relevant document chunks found.")
            return ""

        context_parts = [f"--- Context from {doc.metadata.get('source', 'N/A')} (Page {doc.metadata.get('page', 'N/A')}) ---\n{doc.page_content}" for doc in retrieved_docs]
        full_context = "\n\n".join(context_parts)
        logger.info(f"✓ Returning {len(full_context)} chars of context.")
        return full_context