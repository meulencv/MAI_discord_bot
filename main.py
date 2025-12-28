import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from agent_logic import AgentLogic
import logging

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

bot = commands.Bot(command_prefix='!mai_', intents=intents)
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

    # PRIVACY PROTECTION: Ignore Ticket Channels
    if "ticket" in message.channel.name.lower():
        return

    # Check if bot is mentioned
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            logger.info(f"MAI mentioned by {message.author} in {message.channel}")
            
            # Context Analysis
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
                
                accessible_channels = [c for c in message.guild.text_channels if c.permissions_for(message.guild.me).read_messages]
                
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

            # Prepare channel list for agent context
            channel_names = [c.name for c in message.guild.text_channels 
                           if c.permissions_for(message.guild.me).read_messages]
            
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

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
