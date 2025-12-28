import os
import chromadb
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
import logging

logger = logging.getLogger('MAI_Logic')

class AgentLogic:
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY is missing!")
            
        # Initialize Groq LLM (Mixtral is a good balance of speed/quality)
        self.llm = ChatGroq(temperature=0.3, model_name="mixtral-8x7b-32768", groq_api_key=self.groq_api_key)
        
        # Initialize ChromaDB (Persistent storage)
        self.chroma_client = chromadb.PersistentClient(path="./mai_memory")
        self.collection = self.chroma_client.get_or_create_collection(name="knowledge_base")

    def learn_from_text(self, texts, source):
        """Simple indexing of text lines."""
        ids = [f"{source}_{i}" for i in range(len(texts))]
        metadatas = [{"source": source} for _ in range(len(texts))]
        
        # Chroma Default Embedding is usually 'all-MiniLM-L6-v2' (lightweight)
        # We assume texts are strings.
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Learned {len(texts)} items from {source}")

    def process_query(self, query, user_name, is_ticket=False, ticket_history=""):
        """
        Main RAG Logic.
        1. Search global knowledge base (public channels).
        2. If ticket, analyze ticket context.
        3. Synthesize answer.
        """
        
        # 1. Retrieve relevant info from Public Memory
        results = self.collection.query(
            query_texts=[query],
            n_results=3
        )
        
        retrieved_context = "\n".join(results['documents'][0]) if results['documents'] else "No relevant past discussions found."
        
        # 2. Construct Prompt based on Permissions
        system_prompt = f"""You are MAI, a helpful AI assistant for a Discord server. 
You answer questions based on the retrieved server history and current context.
Be concise, friendly, and helpful.

RULES:
- If you don't know the answer, admit it.
- Do not make up facts.
- Use the provided CONTEXT to answer.
"""

        user_content = f"""
USER: {user_name}
QUERY: {query}

--- RETRIEVED KNOWLEDGE (Public) ---
{retrieved_context}
------------------------------------
"""

        if is_ticket:
            user_content += f"""
--- TICKET CONTEXT (Private/Sensitive) ---
This is a private ticket. You have access to the conversation above.
{ticket_history}
------------------------------------------
"""
        else:
            user_content += "\n(Note: This is a public channel. No private ticket data is accessible.)"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]

        logger.info(f"Sending query to Groq... (Ticket Mode: {is_ticket})")
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error calling Groq: {e}")
            return "Lo siento, tuve un error al procesar tu solicitud."
