# Multi-Agent System with Dynamic Decision Making

This project is a **full-stack web application** that implements a **multi-agent AI system** as a solution for the AIML Assessment Round at Solar Industries India Limited. The system intelligently analyzes a user's query and dynamically routes it to the most appropriate specialized agent:

- **PDF RAG Agent** for document analysis  
- **Web Search Agent** for current events  
- **ArXiv Agent** for scientific research  

**Live Demo:** https://multiagentsystem-jpfb.onrender.com

---

## Architecture & Approach

The application is built with a **modular, full-stack architecture** designed for scalability and clear separation of concerns.

### Frontend
- Clean, responsive UI built with **HTML, CSS, and vanilla JavaScript**.  
- Allows users to upload PDF documents and submit queries to the backend.

### Backend (Flask)
- Robust **Flask server** serving the frontend and hosting all AI logic.  
- Exposes three main API endpoints:
  - `/uploadPdf`
  - `/ask`
  - `/logs`

### Controller Agent (The "Brain")
The core of the system. It receives all queries and uses a **hybrid routing strategy**:

- **Rule-Based Routing:**  
  For high-certainty queries (e.g., containing "arxiv" or "summarize this document"), fast, predefined rules select an agent immediately.

- **LLM-Based Routing:**  
  For ambiguous queries, a high-speed **LLM (gemma2-9b-it via Groq API)** makes an intelligent decision using context (like whether a PDF has been uploaded).

### Specialized Agents

- **PDF RAG Agent:**  
  Extracts text from uploaded PDFs, chunks it, and embeds it into a **FAISS vector store**. Retrieves relevant context for document-specific questions.

- **Web Search Agent:**  
  Uses **SerpAPI** to get real-time Google search results for general knowledge or current events.

- **ArXiv Agent:**  
  Connects directly to the **ArXiv API** to find and summarize scientific research papers.

### Answer Synthesis & Logging
- Controller Agent sends the retrieved context and original query to **Groq LLM** to generate a coherent answer.  
- All steps are logged for **full transparency**.

---

## Core Technologies Used

- **Backend:** Flask  
- **Frontend:** HTML, CSS, JavaScript  
- **LLM API:** Groq (gemma2-9b-it model)  
- **RAG & Embeddings:** LangChain, FAISS, all-MiniLM-L6-v2  
- **Web Search:** SerpAPI  
- **Deployment:** Gunicorn, Render  

---

 Setup and Local Execution

1. Clone the Repository
```bash
git clone https://github.com/your-username/MultiAgentSystem.git
cd MultiAgentSystem
```


### Create and activate a virtual environment:
Windows
```bash
python -m venv venv
venv\Scripts\activate
```


macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API Keys

Create a .env file inside the backend folder and add your keys:

GROQ_API_KEY="your_api_key_from_groq"
SERPAPI_KEY="your_api_key_from_serpapi"

3. Run the Application

With the virtual environment active:
```bash
flask run
```

The application will be accessible at http://127.0.0.1:5000

How to Use
1. Upload a PDF (Optional)

Click "Choose File", select a PDF, and click "Upload". The system will process it and create a vector store in memory for this session.

2. Ask a Question

PDF-specific queries: "Summarize this document" or "What methodology is used?"

Research papers: "Find a research paper on AI"

General knowledge: "What is the latest news on climate change?"

3. View Results

The application displays the generated answer, the agent used, and the controller's rationale.

4. Check Logs

Click the "Load Logs" button to see a raw trace of the controller's activity for your session.
