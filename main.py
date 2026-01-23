import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from proxy_manager import get_webshare_proxy_sync
import asyncio
from agent_logic import AgentLogic
from discord import app_commands
import datetime
import io
import zipfile


# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MAI')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PROXY_URL = get_webshare_proxy_sync()
bot = commands.Bot(command_prefix='!mai_', intents=intents, proxy=PROXY_URL)
agent = AgentLogic()

# --- KOYEB/RENDER HEALTH CHECK FIX ---
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MAI is alive!")

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Start web server in background
threading.Thread(target=run_server, daemon=True).start()
# -------------------------------------

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('MAI is ready to serve.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if bot is mentioned
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            logger.info(f"MAI mentioned by {message.author} in {message.channel}")

            # --- ADMIN COMMAND: !export ---
            if "!export" in message.content:
                if message.author.name != "technologiescv":
                    await message.reply("⛔ No tienes permisos para usar este comando.")
                    return

                # Parse days (e.g., "@MAI !export days:30" or just default 7)
                days = 7
                try:
                    import re
                    match = re.search(r'days:(\d+)', message.content)
                    if match:
                        days = int(match.group(1))
                except:
                    pass

                status_msg = await message.reply(f"⏳ **Exportando logs de los últimos {days} días...**\nEsto puede tardar un poco. Te lo enviaré por MD al terminar.")
                
                try:
                    # Run export logic
                    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
                    zip_buffer = io.BytesIO()
                    start_time = datetime.datetime.now()
                    channels_processed = 0
                    total_messages = 0

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for channel in message.guild.text_channels:
                            if not channel.permissions_for(message.guild.me).read_messages: continue
                            if not channel.permissions_for(message.guild.me).read_message_history: continue

                            channels_processed += 1
                            messages_data = []
                            try:
                                async for msg in channel.history(after=cutoff_date, limit=None, oldest_first=True):
                                    timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                                    content = f"[{timestamp}] {msg.author.name}: {msg.content}"
                                    if msg.attachments:
                                        att_urls = [a.url for a in msg.attachments]
                                        content += f" [ATTACHMENTS: {', '.join(att_urls)}]"
                                    messages_data.append(content)
                                    total_messages += 1

                                if messages_data:
                                    zip_file.writestr(f"{channel.name}.txt", "\n".join(messages_data))
                            except Exception as e:
                                zip_file.writestr(f"ERRORS/{channel.name}_error.txt", str(e))

                    zip_buffer.seek(0)
                    time_taken = (datetime.datetime.now() - start_time).total_seconds()

                    if total_messages == 0:
                        await message.author.send(f"⚠️ No se encontraron mensajes en los últimos {days} días.")
                        await status_msg.edit(content=f"⚠️ Proceso terminado. No había mensajes (mira tus MDs).")
                    else:
                        filename = f"chat_logs_{message.guild.name}_{datetime.datetime.now().strftime('%Y%m%d')}.zip"
                        file_obj = discord.File(zip_buffer, filename=filename)
                        
                        await message.author.send(
                            content=f"✅ **Exportación completada**\nPeriodo: {days} días\nMensajes: {total_messages}\nCanales: {channels_processed}",
                            file=file_obj
                        )
                        await status_msg.edit(content=f"✅ **Exportación enviada a tus Mensajes Directos.**")
                
                except Exception as e:
                    logger.error(f"Export failed: {e}")
                    await message.reply(f"❌ Error: {e}")
                
                return # Stop processing regular agent logic
            # ------------------------------

            # Fetch recent history for context (Last 5 messages)
            recent_history = [msg async for msg in message.channel.history(limit=5)]
            recent_history.reverse() # Oldest first
            
            # Remove the current message from history to avoid duplication
            recent_history = [m for m in recent_history if m.id != message.id]
            
            # Add timestamps to chat context
            chat_context = "\n".join([f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.author.name}: {m.content}" for m in recent_history])
            
            is_ticket_context = 'ticket' in message.channel.name.lower()

            # Current channel info
            current_channel_name = message.channel.name

            # Search Functionality
            async def search_memory(query, target_channel="ALL"):
                """Search chat history, optionally targeting a specific channel."""
                results = []
                logger.info(f"Searching for '{query}' in {target_channel}...")
                
                # Check if searching current channel - if so, include recent history we already have
                is_current_channel = target_channel.lower() == current_channel_name.lower()
                
                if is_current_channel and (query == "*" or not query.strip()):
                    # For current channel with wildcard, use the history we already fetched
                    logger.info(f"Using existing context for current channel '{current_channel_name}'")
                    if chat_context:
                        return f"[Historial reciente del canal actual #{current_channel_name}]\n{chat_context}"
                    else:
                        return f"AVISO: El canal #{current_channel_name} es el canal actual donde estamos hablando. El historial reciente está vacío o solo contiene tu mensaje."
                
                accessible_channels = [c for c in message.guild.text_channels 
                                     if c.permissions_for(message.guild.me).read_messages 
                                     and c.permissions_for(message.author).read_messages]
                
                # Match target channel if specified
                search_scope = []
                if target_channel != "ALL":
                    found = next((c for c in accessible_channels if c.name.lower() == target_channel.lower()), None)
                    if found:
                        search_scope = [found]
                    else:
                        logger.warning(f"Target channel {target_channel} not found, falling back to ALL.")
                        search_scope = accessible_channels
                else:
                    search_scope = accessible_channels
                
                # Execution
                total_limit = 25
                per_channel_limit = 50 if len(search_scope) == 1 else 10
                
                for channel in search_scope:
                    if len(results) >= total_limit: break
                    
                    try:
                        async for msg in channel.history(limit=per_channel_limit):
                            # Wildcard search or keyword match
                            if query == "*" or (query.lower() in msg.content.lower()):
                                if not msg.author.bot:
                                    timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M')
                                    results.append(f"[{timestamp}] [{msg.channel.name}] {msg.author.name}: {msg.content}")
                            
                            if len(results) >= total_limit: break
                    except Exception as e:
                        logger.warning(f"Error searching {channel.name}: {e}")
                
                if not results:
                    return f"AVISO DEL SISTEMA: No se encontraron mensajes para '{query}' en {target_channel}. NO INVENTES mensajes ni usuarios."
                return "\n".join(results[:total_limit])

            # Prepare channel list for agent context (Based on USER permissions)
            # Send format: "channel_name (<#channel_id>)" so LLM knows how to link
            channel_names = [f"{c.name} (<#{c.id}>)" for c in message.guild.text_channels 
                           if c.permissions_for(message.guild.me).read_messages 
                           and c.permissions_for(message.author).read_messages]
            
            # Prepare Server Stats
            server_stats = {
                "Server Name": message.guild.name,
                "Member Count": message.guild.member_count,
                "Text Channels": len(message.guild.text_channels),
                "Voice Channels": len(message.guild.voice_channels),
                "Server Owner": message.guild.owner.name if message.guild.owner else "Unknown"
            }

            # Status message holder
            status_msg = None
            
            # Callback functions for agent to show status and react
            async def show_status(status_text):
                """Show what MAI is doing."""
                nonlocal status_msg
                try:
                    if status_msg:
                        await status_msg.edit(content=status_text)
                    else:
                        status_msg = await message.channel.send(status_text)
                except Exception as e:
                    logger.warning(f"Could not show status: {e}")
            
            async def add_reaction(emoji):
                """Add a reaction to the user's message."""
                try:
                    await message.add_reaction(emoji)
                except Exception as e:
                    logger.warning(f"Could not add reaction: {e}")

            # Generate Response
            response = await agent.process_query(
                query=message.content.replace(f'<@{bot.user.id}>', '').strip(),
                user_name=message.author.name,
                available_channels=channel_names,
                server_stats=server_stats,
                is_ticket=is_ticket_context,
                chat_history=chat_context,
                search_tool=search_memory,
                current_channel=current_channel_name,
                status_callback=show_status,
                reaction_callback=add_reaction
            )
            
            # Clean up status message if exists
            if status_msg:
                try:
                    await status_msg.delete()
                except:
                    pass
            
            # Check if agent wants to add a reaction (format: REACT: 🔥 at end of message)
            if "REACT:" in response:
                try:
                    parts = response.rsplit("REACT:", 1)
                    response = parts[0].strip()
                    emoji = parts[1].strip().split()[0]  # Get first emoji
                    await add_reaction(emoji)
                except:
                    pass
            
            # Add AI disclaimer footer
            disclaimer = "\n\n-# *Respuesta generada por IA. Puede contener errores.*"
            
            # SAFETY FILTER: Force correct domain
            response = response.replace("meulify.com", "meulify.top")
            
            await message.reply(response + disclaimer)

    # Allow processing of commands if any
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def index_channel(ctx, channel_id: int):
    """Admin command to learn from a channel."""
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("Channel not found.")
        return
    
    await ctx.send(f"Starting indexing of {channel.name}... this might take a while.")
    
    messages = []
    async for msg in channel.history(limit=500): # Limit to recent 500 messages to avoid overload for now
        if not msg.author.bot and len(msg.content) > 10:
            messages.append(f"User: {msg.content}")
            
    if messages:
        agent.learn_from_text(messages, source=f"channel_{channel.name}")
        await ctx.send(f"Successfully indexed {len(messages)} messages from {channel.name}.")
    else:
        await ctx.send("No valid messages found to index.")

async def start_bot():
    if not TOKEN:
        logger.error("DISCORD_TOKEN not found!")
        return

    # Iniciar bot (el proxy ya está configurado en el constructor)
    logger.info(f"Starting bot (Proxy: {'Enabled' if PROXY_URL else 'Disabled'})...")
    await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
