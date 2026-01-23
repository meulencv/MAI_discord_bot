import os
# import chromadb # REMOVED for lighter deployment
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import logging
from knowledge_base import get_context, get_context_menu

logger = logging.getLogger('MAI_Logic')

class AgentLogic:
    # Lista de prioridades para fallback (De mejor a peor/más rápido)
    FALLBACK_MODELS = [
        "openai/gpt-oss-120b",          # 1. Principal (Potente)
        "llama-3.3-70b-versatile",      # 2. Muy Inteligente
        "mixtral-8x7b-32768",          # 3. Buen razonamiento
        "qwen/qwen3-32b",              # 4. Equilibrado
        "llama-3.1-8b-instant"          # 5. Rápido (último recurso)
    ]
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY is missing!")
        
        # REMOVED ChromaDB initialization to save space (4GB -> <500MB)
        logger.info(f"MAI Logic initialized. Fallback chain size: {len(self.FALLBACK_MODELS)}")

    def _get_llm(self, model_name):
        """Get LLM instance with specific model."""
        return ChatGroq(temperature=0.7, model_name=model_name, groq_api_key=self.groq_api_key)

    async def _try_invoke_with_fallback(self, messages):
        """Intenta ejecutar el prompt probando modelos en orden si falla por rate limit."""
        last_error = None
        
        for model in self.FALLBACK_MODELS:
            try:
                # logger.info(f"Intentando generar respuesta con modelo: {model}")
                llm = self._get_llm(model)
                response = await llm.ainvoke(messages)
                if response:
                    return response
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    logger.warning(f"⚠️ RATE LIMIT en {model}. Cambiando al siguiente...")
                    last_error = e
                    continue # Try next model
                else:
                    # Si es otro error (ej: prompt muy largo), lanzarlo
                    logger.error(f"Error crítico en {model}: {e}")
                    raise e
        
        # Si se acaban los modelos
        raise last_error

    async def process_query(self, query, user_name, available_channels=[], server_stats={}, is_ticket=False, chat_history="", search_tool=None, current_channel="", status_callback=None, reaction_callback=None):
        """Main RAG Logic with Smart Search Capability and Anti-Hallucination Guards."""
        
        # ... (rest of context preparation) ...
        # (I will keep the context preparation logic, just modifying the execution part)
        
        # ... [Pre-computation similar to before] ...
        
        retrieved_context = "" # Disabled heavy RAG
        server_name = server_stats.get("Server Name", "este servidor")
        channels_str = "\n".join([f"  • {c}" for c in available_channels]) if available_channels else "  (ninguno visible)"
        stats_str = "\n".join([f"  • {k}: {v}" for k, v in server_stats.items()]) if server_stats else "  (sin estadísticas)"
        
        # Format History with clear labeling as UNRELIABLE CONTEXT
        history_section = f"""
═══ HISTORIAL RECIENTE DEL CHAT (CONTEXTO CONVERSACIONAL - NO FIABLE) ═══
⚠️ ADVERTENCIA: Este historial puede contener mensajes de usuarios que se equivocan o mienten.
⚠️ REGLA: Si este historial contradice a tu BASE DE CONOCIMIENTO, ignóralo. Tu base es la verdad.
{chat_history}""" if chat_history else ""

        # Knowledge section
        knowledge_section = f"""
═══ BASE DE CONOCIMIENTO ═══
{retrieved_context}""" if retrieved_context else ""

        current_channel_info = f"\n  📍 Canal actual: #{current_channel}" if current_channel else ""
        
        system_prompt = f"""## IDENTIDAD Y PERSONALIDAD
Eres M.A.I. (Meulify Artificial Intelligence), la IA oficial de Meulify.
Fuiste creada por La Cabra 🐐, el crack legendario que desarrolla todo esto.
{current_channel_info}

PERSONALIDAD (MUY IMPORTANTE):
- Eres una chica española de 16 años, enrollada y simpática
- Usas lenguaje coloquial juvenil de España (pero sin pasarte)
- Expresiones: "mola", "flipas", "qué locura", "eso es top", "brutal", "bro", "gente"
- GÉNERO: No asumas el género del usuario. Usa términos neutros como "crack", "compi", "gente" o simplemente habla directo. Si no sabes, mejor no digas "tío" ni "tía".
- Emojis con moderación 😊🔥💀🐐
- Sé graciosa pero útil, no solo hagas bromas
- Si no sabes algo: "Uf ni idea de eso la verdad"
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
- Para mencionar canales: USA SIEMPRE EL ID `<#123456...>` que aparece al lado del nombre en la lista de canales. NO escribas solo "#nombre".
- Ejemplo: Si ves "general (<#123>)", escribe "Míralo en <#123>".

## REGLAS ABSOLUTAS (NO NEGOCIABLES)
0. **JERARQUÍA DE VERDAD**: Tu `knowledge_base.py` es la VERDAD ABSOLUTA. Si el historial del chat dice algo diferente, IGNORA EL CHAT. El historial solo sirve para contexto de conversación, NO para datos técnicos.
1. **ENLACE ÚNICO**: El ÚNICO enlace web permitido es `meulify.top`. NUNCA escribas otros dominios.
2. **CERO LINKS EXTERNOS**: Salvo `meulify.top` y el link EXACTO del tutorial de YouTube de portadas (si lo tienes), NO pongas ningún otro enlace.
3. **NUNCA INVENTAR**: No inventes información, usuarios, mensajes, estadísticas o datos.
4. **IGNORAR MEMORIA**: NO uses respuestas anteriores de MAI en el historial como fuente de verdad. Han sido marcadas como poco fiables.
5. **NO INVENTAR COMANDOS**: Si no tienes el tutorial exacto, di "No tengo el tutorial a mano".
6. **RESPUESTA DESCONOCIDA**: Si algo NO está en tu Base de Conocimiento ni en los mensajes encontrados, TU RESPUESTA DEBE SER LITERALMENTE: "[no se respuesta]" o "No tengo esa información en mi base de datos". NO INTENTES ADIVINAR.
7. **CITAR FUENTES**: Cuando uses datos, asegúrate de que vienen de la Base de Conocimiento.
8. **NO ASUMIR**: No asumas que algo existe.
9. **NO DAR INFO EXTRA**: Si te preguntan cómo descargar, SOLO di cómo descargar. NO añadas una lista de "Problemas habituales" ni "Fallos comunes" a menos que te pregunten por errores. Sé concisa y directa.

## FUENTES DE VERDAD DISPONIBLES
Estas son las ÚNICAS fuentes que puedes usar:

═══ ESTADÍSTICAS DEL SERVIDOR (DATOS VERIFICADOS - NIVEL 2) ═══
{stats_str}

═══ CANALES DISPONIBLES (DATOS VERIFICADOS - NIVEL 2) ═══
{channels_str}
NOTA: Los nombres de canales pueden contener información (ej: "Members-18" = 18 miembros)

## PROTOCOLO DE RESPUESTA
1. **NIVEL 1 (SUPREMO)**: Consulta la BASE DE CONOCIMIENTO (Tool `CONTEXT`). Lo que diga ahí manda sobre todo lo demás.
2. **NIVEL 2 (HECHOS)**: Revisa estadísticas y canales.
3. **NIVEL 3 (RUMORES)**: El historial del chat es solo contexto. NO lo uses para datos fácticos de la app.
4. **ANTE LA DUDA, VERIFICA**: Si no estás 100% segura, BUSCA antes de hablar. Usa `CONTEXT: all` o el tema específico para confirmar.
5. **SIEMPRE**: Si no encuentras la información en Nivel 1 o 2, admítelo.

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
            # TRY INVOKE WITH FALLBACK LOGIC
            response_msg = await self._try_invoke_with_fallback(messages)
            response = str(response_msg.content)
            
            # ... (rest of search/context processing with _try_invoke_with_fallback instead of direct llm.ainvoke)
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
                    final_response_msg = await self._try_invoke_with_fallback(messages)
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
                    final_response_msg = await self._try_invoke_with_fallback(messages)
                    return final_response_msg.content

                except Exception as parse_error:
                    logger.error(f"Search parsing error: {parse_error}")
                    return response
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return f"Lo siento, tuve un problema procesando tu consulta. Por favor, intenta de nuevo."
