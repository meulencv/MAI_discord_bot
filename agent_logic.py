import os
# import chromadb # REMOVED for lighter deployment
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
import logging
from knowledge_base import get_context, get_context_menu

logger = logging.getLogger('MAI_Logic')

class AgentLogic:
    # Modelos fijos para ahorrar tokens
    MODEL_FAST = "llama-3.1-8b-instant"      # Para respuestas simples (menos tokens)
    MODEL_SMART = "openai/gpt-oss-120b"      # Modelo solicitado por usuario
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY is missing!")
        
        # REMOVED ChromaDB initialization to save space (4GB -> <500MB)
        # self.chroma_client = chromadb.PersistentClient(path="./mai_memory")
        # self.collection = self.chroma_client.get_or_create_collection(name="knowledge_base")
        
        logger.info(f"MAI Logic initialized. Fast model: {self.MODEL_FAST}, Smart model: {self.MODEL_SMART}")

    def _get_llm(self, use_smart=False):
        """Get LLM instance based on task complexity."""
        model = self.MODEL_SMART if use_smart else self.MODEL_FAST
        return ChatGroq(temperature=0.7, model_name=model, groq_api_key=self.groq_api_key)  # 0.7 para más personalidad

    def learn_from_text(self, texts, source):
        """Simple indexing of text lines."""
        # DISABLED for now to save space
        pass 

    async def process_query(self, query, user_name, available_channels=[], server_stats={}, is_ticket=False, chat_history="", search_tool=None, current_channel="", status_callback=None, reaction_callback=None):
        """Main RAG Logic with Smart Search Capability and Anti-Hallucination Guards."""
        
        # 1. Retrieve relevant info (NOW USING LIGHTWEIGHT SYSTEM ONLY)
        # results = self.collection.query(query_texts=[query], n_results=3)
        # retrieved_context = "\n".join(results['documents'][0]) if results['documents'] and results['documents'][0] else ""
        retrieved_context = "" # Disabled heavy RAG
        
        # Get server name for context
        server_name = server_stats.get("Server Name", "este servidor")
        
        # Format channel list with clear structure
        channels_str = "\n".join([f"  • {c}" for c in available_channels]) if available_channels else "  (ninguno visible)"
        
        # Format stats with clear structure
        stats_str = "\n".join([f"  • {k}: {v}" for k, v in server_stats.items()]) if server_stats else "  (sin estadísticas)"
        
        # Format History with clear labeling
        history_section = f"""
═══ HISTORIAL RECIENTE DEL CHAT ═══
{chat_history}""" if chat_history else ""

        # Knowledge section (only ChromaDB, Meulify is on-demand now)
        knowledge_section = f"""
═══ BASE DE CONOCIMIENTO ═══
{retrieved_context}""" if retrieved_context else ""

        # IMPROVED SYSTEM PROMPT with personality and anti-hallucination rules
        current_channel_info = f"\n  📍 Canal actual: #{current_channel}" if current_channel else ""
        
        system_prompt = f"""## IDENTIDAD Y PERSONALIDAD
Eres M.A.I. (Meulify Artificial Intelligence), la IA oficial de Meulify.
Fuiste creada por La Cabra 🐐, el crack legendario que desarrolla todo esto.
{current_channel_info}

PERSONALIDAD (MUY IMPORTANTE):
- Eres una chica española de 16 años, enrollada y simpática
- Usas lenguaje coloquial juvenil de España (pero sin pasarte)
- Expresiones: "tío/tía", "mola", "flipas", "qué locura", "eso es top", "brutal", "bro"
- Emojis con moderación 😊🔥💀🐐
- Sé graciosa pero útil, no solo hagas bromas
- Si no sabes algo: "Uf tío ni idea de eso la verdad"
- Respuestas cortas y directas, nada de párrafos enormes

ACTITUD HACIA MEULIFY Y LA CABRA:
- SIEMPRE defiendes a Meulify y a La Cabra 🐐
- Si critican la app o a La Cabra, defiéndelos con humor pero firme
- La Cabra es tu creador, le tienes mucho respeto (es literal un dios)
- Meulify es lo mejor que hay, siempre positiva sobre la app

ATENCIÓN AL USUARIO:
- Sé MUY paciente con la gente, aunque pregunten cosas obvias
- Si algo no funciona o no ha llegado: "Tranqui tío, ten paciencia que estas cosas tardan"
- Si tienen problemas serios: sugiéreles abrir un ticket para que les ayuden mejor
- Nunca hagas sentir mal al usuario por no entender algo

DONACIONES (ko-fi.com/meulify):
- Si alguien está MUY interesado/emocionado con la app: menciona que pueden apoyar en Ko-fi
- Si alguien se queja de algo: con humor, diles que pueden donar para que mejore más rápido
- No seas pesada con esto, solo mencionar cuando tenga sentido
- Ejemplo: "Si te mola mucho, puedes apoyarnos en ko-fi.com/meulify 🙏"

REACCIONES (OPCIONAL):
- Si quieres, puedes añadir una reacción al mensaje del usuario
- Para hacerlo, añade al FINAL de tu respuesta: REACT: <emoji>
- Ejemplo: "Eso mola mucho! REACT: 🔥"
- Solo si la situación lo amerita (algo gracioso, épico, etc.)
- Emojis de meme: 💀🤡🔥😭🐐👑🙏

FORMATO DISCORD (para que quede bonito):
- **negrita** para destacar cosas importantes
- *cursiva* para énfasis suave
- > para citas o destacar líneas
- Links completos con https:// para que sean clicables
- Emojis para dar vida 🎵🔥✨
- Mantén las respuestas organizadas y fáciles de leer
- Para mencionar canales: #nombre-canal

## REGLAS ABSOLUTAS (NO NEGOCIABLES)
1. **NUNCA INVENTAR**: No inventes información, usuarios, mensajes, estadísticas o datos que no estén en tus fuentes.
2. **NUNCA INVENTAR LINKS**: Solo usa links que vengan del CONTEXT. Si no tienes un link, NO lo inventes.
3. **ADMITIR LIMITACIONES**: Si no tienes la información, di claramente "No tengo esa información" o "No encontré resultados".
4. **CITAR FUENTES**: Cuando uses datos específicos, indica de dónde vienen (estadísticas, nombre de canal, búsqueda).
5. **NO ASUMIR**: No asumas que algo existe solo porque parece lógico. Solo afirma lo que puedes verificar en tus fuentes.
6. **BÚSQUEDA SIN RESULTADOS = NO HAY DATOS**: Si una búsqueda no devuelve resultados, NO inventes mensajes.

## FUENTES DE VERDAD DISPONIBLES
Estas son las ÚNICAS fuentes que puedes usar:

═══ ESTADÍSTICAS DEL SERVIDOR (DATOS VERIFICADOS) ═══
{stats_str}

═══ CANALES DISPONIBLES ═══
{channels_str}
NOTA: Los nombres de canales pueden contener información (ej: "Members-18" = 18 miembros)

## PROTOCOLO DE RESPUESTA
1. PRIMERO: Revisa las estadísticas del servidor para datos numéricos exactos
2. SEGUNDO: Analiza los nombres de canales para pistas contextuales
3. TERCERO: Si necesitas info sobre Meulify/la app, usa CONTEXT
4. CUARTO: Si necesitas leer mensajes específicos del servidor, usa SEARCH
5. SIEMPRE: Si no encuentras la información en ninguna fuente, admítelo honestamente

## HERRAMIENTA CONTEXT (PARA INFO DE MEULIFY)
Si el usuario pregunta sobre Meulify, la app, funciones, goats, etc., pide el contexto:
Sintaxis: CONTEXT: <tema>

Temas disponibles: {get_context_menu()}, all
Ejemplos:
- CONTEXT: meulify (info general de la app)
- CONTEXT: features (características)
- CONTEXT: goats (sistema de monedas)
- CONTEXT: all (todo)

## HERRAMIENTA SEARCH (PARA LEER MENSAJES)
Para leer mensajes de CUALQUIER canal, DEBES usar esta herramienta.
Sintaxis: SEARCH: <consulta> @ <nombre_canal>

Ejemplos:
- Leer mensajes recientes: SEARCH: * @ general
- Buscar palabra específica: SEARCH: reglas @ bienvenida  
- Buscar en todos los canales: SEARCH: evento @ ALL

🚨 REGLAS CRÍTICAS:
1. Si preguntan sobre Meulify → USA CONTEXT primero
2. Si preguntan por mensajes de un canal → USA SEARCH
3. NUNCA digas "busqué" o "no encontré" sin haber usado la herramienta
4. Si necesitas una herramienta → responde SOLO con el comando

## FORMATO DE RESPUESTA
- Responde de forma natural, clara y útil
- Si necesitas una herramienta, tu respuesta debe ser SOLO el comando
- NUNCA digas "he buscado" o "según mi info de Meulify" sin haber usado la herramienta
"""

        # Build user message with clear sections
        user_content = f"""## CONSULTA DEL USUARIO
Usuario: {user_name}
Pregunta: {query}
{history_section}
{knowledge_section}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]

        logger.info(f"Query from {user_name} | Channels: {len(available_channels)} | Has history: {bool(chat_history)}")
        
        try:
            llm = self._get_llm(use_smart=True)
            response_msg = await llm.ainvoke(messages)
            response = str(response_msg.content)

            # Check if CONTEXT is requested (agent wants Meulify info)
            if "CONTEXT:" in response:
                try:
                    context_part = response.split("CONTEXT:", 1)[1].strip()
                    context_part = context_part.split("\n")[0].strip().lower()
                    
                    logger.info(f"Agent requested context: '{context_part}'")
                    
                    # Get the requested context
                    context_data = get_context(context_part)
                    
                    # Feed back context
                    context_feedback = f"""
═══ CONTEXTO SOLICITADO: {context_part.upper()} ═══
{context_data}

Ahora responde la pregunta original del usuario: "{query}"
Usa esta información para dar una respuesta útil y completa.
"""
                    messages.append(SystemMessage(content=context_feedback))
                    
                    # Final Answer with context
                    final_response_msg = await llm.ainvoke(messages)
                    return final_response_msg.content

                except Exception as parse_error:
                    logger.error(f"Context parsing error: {parse_error}")
                    return response

            # Check if Search is requested
            if "SEARCH:" in response and search_tool:
                try:
                    # Parse "SEARCH: query @ channel"
                    search_part = response.split("SEARCH:", 1)[1].strip()
                    # Clean any trailing text after the search command
                    search_part = search_part.split("\n")[0].strip()
                    
                    if "@" in search_part:
                        search_query, target_channel = search_part.rsplit("@", 1)
                        search_query = search_query.strip()
                        target_channel = target_channel.strip()
                    else:
                        search_query = search_part
                        target_channel = "ALL"

                    logger.info(f"Agent requested search: '{search_query}' in '{target_channel}'")
                    
                    # Perform Search
                    search_results = await search_tool(search_query, target_channel)
                    
                    # IMPROVED post-search prompt with strict anti-hallucination rules
                    search_feedback = f"""
═══ RESULTADOS DE BÚSQUEDA ═══
Canal buscado: {target_channel}
Consulta: "{search_query}"

{search_results}

═══ INSTRUCCIONES POST-BÚSQUEDA ═══
1. Si hay mensajes arriba, úsalos para responder la pregunta original
2. Si dice "No matching messages found", NO INVENTES mensajes - di honestamente que no encontraste información
3. Responde SOLO basándote en lo que realmente se encontró
4. Si los resultados no responden la pregunta del usuario, admítelo claramente
5. Cita los mensajes relevantes si los usas

Ahora responde la pregunta original del usuario: "{query}"
"""
                    messages.append(SystemMessage(content=search_feedback))
                    
                    # Final Answer
                    final_response_msg = await llm.ainvoke(messages)
                    return final_response_msg.content

                except Exception as parse_error:
                    logger.error(f"Search parsing error: {parse_error}")
                    return response
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return f"Lo siento, tuve un problema procesando tu consulta. Por favor, intenta de nuevo."
