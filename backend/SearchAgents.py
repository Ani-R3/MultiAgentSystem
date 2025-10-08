import os
import logging
import requests
from time import sleep
from urllib.parse import urlencode

logger = logging.getLogger("SearchAgents")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - Search - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)

class WebSearchAgent:
    def __init__(self):
        self.api_key = os.environ.get("SERPAPI_KEY")  # optional
        self.fallback = True

    def Search(self, query, num_results=3):
        logger.info(f"WebSearchAgent searching for: {query}")
        # Try SerpAPI if key exists
        serp_key = self.api_key
        if serp_key:
            try:
                params = {
                    "q": query,
                    "engine": "google",
                    "api_key": serp_key,
                    "num": num_results
                }
                resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    # Extract rich information from organic results
                    for r in data.get("organic_results", [])[:num_results]:
                        title = r.get("title", "No Title")
                        snippet = r.get("snippet", "No snippet available.")
                        link = r.get("link", "#")
                        source_domain = r.get("displayed_link", "Unknown Source")
                        results.append(f"Title: {title}\nSource: {source_domain}\nLink: {link}\nSnippet: {snippet}")
                    
                    if results: # Return formatted results if found
                        logger.info(f"SerpAPI returned {len(results)} results.")
                        return "\n\n".join(results)
                    else: # Explicitly return empty string if no organic results
                        logger.warning("SerpAPI found no organic results.")
                        return ""
            except Exception as e:
                logger.error(f"SerpAPI error: {e}", exc_info=True)
                # Fallback to DuckDuckGo if SerpAPI fails

        # Fallback to DuckDuckGo Instant Answer API (lightweight)
        try:
            logger.info("Using DuckDuckGo (fallback) for web search")
            resp = requests.get("https://api.duckduckgo.com", params={"q": query, "format": "json", "no_redirect": 1}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText")
                related_topics = []
                if abstract:
                    related_topics.append(f"Summary: {abstract}")
                
                # Also get first few related topics if available
                for topic in data.get("RelatedTopics", [])[:num_results]:
                    text = topic.get("Text")
                    if text:
                        related_topics.append(f"Related: {text}")
                
                if related_topics:
                    logger.info(f"DuckDuckGo returned {len(related_topics)} results.")
                    return "\n\n".join(related_topics)
            logger.warning("DuckDuckGo fallback returned no results.")
            return "" # Explicitly return empty string
        except Exception as e:
            logger.error(f"Web search fallback failed: {e}", exc_info=True)
            return "Error performing web search."

class ArxivSearchAgent:
    def __init__(self):
        self.base = "http://export.arxiv.org/api/query"

    def Search(self, query, max_results=3):
        logger.info(f"ArXiv searching for: {query}")
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results
        }
        try:
            resp = requests.get(self.base, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"ArXiv API returned status {resp.status_code}")
                return "Error connecting to ArXiv API."
            
            text = resp.text
            entries = []
            parts = text.split("<entry>")
            for part in parts[1:]:
                try:
                    title = part.split("<title>")[1].split("</title>")[0].strip().replace('\n', ' ')
                    summary = part.split("<summary>")[1].split("</summary>")[0].strip().replace('\n', ' ')
                    entries.append(f"Title: {title}\nSummary: {summary}")
                except IndexError:
                    continue # Skip entry if it's malformed
                if len(entries) >= max_results:
                    break
            
            if not entries:
                return "No papers found on ArXiv for this query."
            return "\n\n".join(entries)
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}", exc_info=True)
            return "Error performing ArXiv search."

