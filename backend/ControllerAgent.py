# backend/ControllerAgent.py

import os
import logging
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

class ControllerAgent:
    def __init__(self, ragAgent, webSearchAgent, arxivSearchAgent):
        load_dotenv()
        self.ragAgent = ragAgent
        self.webSearchAgent = webSearchAgent
        self.arxivSearchAgent = arxivSearchAgent
        self.groqClient = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.lastPdfUploadTime = None
        self.pdfUploadTimeout = timedelta(minutes=30)
        
        self.logger = logging.getLogger("ControllerAgentLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            os.makedirs('logs', exist_ok=True)
            logHandler = logging.FileHandler('logs/controller_trace.log')
            logHandler.setFormatter(logging.Formatter('%(asctime)s - Controller - %(levelname)s - %(message)s'))
            self.logger.addHandler(logHandler)

    def SetPdfUploadTime(self):
        self.lastPdfUploadTime = datetime.now()
        self.logger.info(f"PDF context timer started at {self.lastPdfUploadTime}")

    def _IsPdfContextActive(self):
        if not self.lastPdfUploadTime: return False
        is_active = (datetime.now() - self.lastPdfUploadTime) < self.pdfUploadTimeout
        if not is_active: self.lastPdfUploadTime = None
        return is_active

    def _ChooseAgentLLM(self, userQuery):
        self.logger.info("Using LLM for intelligent routing...")
        try:
            pdf_status = "A PDF document is available for questions." if self._IsPdfContextActive() else "No PDF document has been uploaded."
            system_prompt = f"""You are an expert query routing agent. Your single task is to select the best tool for the user's query.
System Status: {pdf_status}
Available Tools:
- 'PDF_RAG': Use for questions directly about the content of the uploaded PDF document (e.g., 'what is GRAM?', 'what is the methodology?').
- 'ARXIV_SEARCH': Use for queries about scientific papers, research, or anything mentioning ArXiv.
- 'WEB_SEARCH': Use for all other general knowledge questions (e.g., 'who is Narendra Modi?'), current events, or if no other tool is appropriate.

Respond with ONLY the name of the tool, and nothing else. Your entire response must be a single word: PDF_RAG, ARXIV_SEARCH, or WEB_SEARCH."""
            
            chatCompletion = self.groqClient.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": userQuery}
                ],
                model="gemma2-9b-it",
                temperature=0.0
            )
            choice = chatCompletion.choices[0].message.content.strip().upper()
            self.logger.info(f"LLM router chose: {choice}")
            if "PDF" in choice: return "PDF_RAG"
            if "ARXIV" in choice: return "ARXIV_SEARCH"
            return "WEB_SEARCH"
        except Exception as e:
            self.logger.error(f"Error in LLM routing: {e}", exc_info=True)
            return "WEB_SEARCH"

    
    def _SynthesizeAnswerLLM(self, userQuery, context):
        self.logger.info("Synthesizing final answer with LLM...")
        system_prompt = """You are an expert Q&A and summarization assistant. Your task is to answer the user's query based *only* on the provided context.

Instructions:
- If the user asks for "latest news", "recent developments", or a general summary, synthesize a concise and coherent summary from ALL relevant context snippets provided.
- If the user asks a specific question, provide a clear and direct answer using information from the context.
- Prioritize factual information, sources, and links if they are provided in the context.
- If the context is irrelevant, empty, or does not contain a clear answer, you MUST respond with: 'I could not find a relevant answer in the provided information.'
- Do not make up information or use prior knowledge not present in the context."""
        try:
            chatCompletion = self.groqClient.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nUser Query: {userQuery}"}
                ],
                model="gemma2-9b-it",
                temperature=0.3 # Slightly increased for better summarization
            )
            return chatCompletion.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error during LLM synthesis: {e}", exc_info=True)
            return "An error occurred while generating the final response."
    
    
    def RouteQuery(self, userQuery):
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"New query received: '{userQuery}'")
        
        lowerQuery = userQuery.lower()
        chosenAgent = None
        rationale = ""
        
        # --- Priority 1: Simple Conversational Keywords ---
        conversational_keywords = ['hello', 'hi', 'hii', 'hey', 'who are you', 'what are you', 'hii buddy', 'hello buddy', 'what you can do']
        if lowerQuery in conversational_keywords:
            self.logger.info("Handling as a direct conversational query.")
            return {
                "answer": "I am a multi-agent AI assistant. I can search the web, find research papers on ArXiv, and answer questions about PDF documents you upload.",
                "agentUsed": "CONVERSATIONAL",
                "rationale": "Query was a direct conversational greeting."
            }

        # --- Priority 2: High-Certainty Rule-Based Routing ---
        if any(kw in lowerQuery for kw in ['arxiv', 'research paper', 'scientific paper']):
            chosenAgent = "ARXIV_SEARCH"
            rationale = "Query contained high-certainty keywords for ArXiv."
        elif self._IsPdfContextActive() and any(kw in lowerQuery for kw in ['this document', 'the pdf', 'in this file', 'summarize this', 'what is this pdf about', 'acknowledgement']):
            chosenAgent = "PDF_RAG"
            rationale = "PDF context is active and query used high-certainty keywords for the document."
        
        # --- Priority 3: LLM-Based Routing for Ambiguous Cases ---
        if not chosenAgent:
            chosenAgent = self._ChooseAgentLLM(userQuery)
            rationale = "Query was ambiguous, used LLM for intelligent routing."
        
        self.logger.info(f"Routing Decision: {chosenAgent} | Rationale: {rationale}")
        
        # --- Context Retrieval & Final Answer ---
        context = ""
        if chosenAgent == "PDF_RAG": context = self.ragAgent.QueryRAG(userQuery)
        elif chosenAgent == "ARXIV_SEARCH": context = self.arxivSearchAgent.Search(userQuery)
        else: context = self.webSearchAgent.Search(userQuery)

        if not context or not context.strip() or "error performing" in context.lower():
            self.logger.warning("Context was empty or indicated an error. Bypassing LLM synthesis.")
            finalAnswer = "I'm sorry, I was unable to retrieve the necessary information to answer your question."
        else:
            finalAnswer = self._SynthesizeAnswerLLM(userQuery, context)
        
        self.logger.info(f"Final Answer: {finalAnswer[:150]}...")
        return {"answer": finalAnswer, "agentUsed": chosenAgent, "rationale": rationale}

