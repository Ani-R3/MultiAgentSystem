import os
import logging
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Constants
PDF_UPLOADS_DIR = "uploads"
os.makedirs(PDF_UPLOADS_DIR, exist_ok=True)

logger = logging.getLogger("RAGAgentLogger")
if not logger.handlers:
    logger.setLevel(logging.INFO)
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

    def ProcessPDF(self, pdfPath):
        try:
            logger.info(f"Processing PDF: {os.path.basename(pdfPath)}")
            doc = fitz.open(pdfPath)
            
            all_texts = []
            all_metadatas = []

            # Process page by page to be more memory efficient
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                if not page_text.strip():
                    continue
                
                # Use smaller chunks for memory efficiency
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
                chunks = text_splitter.split_text(page_text)
                
                for chunk in chunks:
                    all_texts.append(chunk)
                    all_metadatas.append({"source": os.path.basename(pdfPath), "page": page_num + 1})

            doc.close()
            logger.info(f"✓ Extracted {len(all_texts)} chunks.")

            if not all_texts:
                logger.error("✗ No text chunks extracted from PDF.")
                return False

            logger.info("Creating new vector store in memory from PDF chunks...")
            # This is the key fix: Create a new, temporary vector store in memory for each upload.
            # We do NOT save to disk, which prevents the memory crash on Render.
            self.vectorStore = FAISS.from_texts(texts=all_texts, embedding=self.embeddings, metadatas=all_metadatas)
            logger.info("✓ Vector store created successfully for this session.")
            return True

        except Exception as e:
            logger.error(f"✗ Error processing PDF: {e}", exc_info=True)
            # Re-raise the exception to be caught by the bulletproof handler in app.py
            raise

    def QueryRAG(self, userQuery):
        logger.info(f"RAG received query: '{userQuery}'")
        if not self.vectorStore:
            logger.warning("✗ Vector store is not available for this session.")
            return "No document has been processed in this session. Please upload a PDF first."

        logger.info("Performing similarity search...")
        retrieved_docs = self.vectorStore.similarity_search(userQuery, k=4)
        
        if not retrieved_docs:
            logger.warning("✗ No relevant document chunks found.")
            return ""

        context_parts = [f"--- Context from {doc.metadata.get('source', 'N/A')} (Page {doc.metadata.get('page', 'N/A')}) ---\n{doc.page_content}" for doc in retrieved_docs]
        full_context = "\n\n".join(context_parts)
        logger.info(f"✓ Returning {len(full_context)} chars of context.")
        return full_context