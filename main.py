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

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot global variable (will be initialized in a function)
bot = None
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

def setup_bot_events(bot_instance):
    @bot_instance.event
    async def on_ready():
        logger.info(f'Logged in as {bot_instance.user} (ID: {bot_instance.user.id})')
        logger.info('MAI is ready to serve.')

    @bot_instance.event
    async def on_message(message):
        if message.author == bot_instance.user:
            return

        # Check if bot is mentioned
        if bot_instance.user.mentioned_in(message) and not message.mention_everyone:
            async with message.channel.typing():
                logger.info(f"MAI mentioned by {message.author} in {message.channel}")

                # --- ADMIN COMMAND: !export ---
                if "!export" in message.content:
                    if message.author.name != "technologiescv":
                        await message.reply("⛔ No tienes permisos para usar este comando.")
                        return

                    # Parse days
                    days = 7
                    try:
                        import re
                        match = re.search(r'days:(\d+)', message.content)
                        if match:
                            days = int(match.group(1))
                    except:
                        pass

                    status_msg = await message.reply(f"⏳ **Exportando logs de los últimos {days} días...**")
                    
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
                                        messages_data.append(content)
                                        total_messages += 1

                                    if messages_data:
                                        zip_file.writestr(f"{channel.name}.txt", "\n".join(messages_data))
                                except Exception as e:
                                    zip_file.writestr(f"ERRORS/{channel.name}_error.txt", str(e))

                        zip_buffer.seek(0)
                        if total_messages == 0:
                            await message.author.send(f"⚠️ No se encontraron mensajes.")
                            await status_msg.edit(content=f"⚠️ Proceso terminado. No había mensajes.")
                        else:
                            filename = f"chat_logs_{message.guild.name}_{datetime.datetime.now().strftime('%Y%m%d')}.zip"
                            file_obj = discord.File(zip_buffer, filename=filename)
                            await message.author.send(content=f"✅ **Exportación completada**", file=file_obj)
                            await status_msg.edit(content=f"✅ **Exportación enviada a tus MD.**")
                    except Exception as e:
                        logger.error(f"Export failed: {e}")
                        await message.reply(f"❌ Error: {e}")
                    return

                # Fetch recent history
                recent_history = [msg async for msg in message.channel.history(limit=5)]
                recent_history.reverse()
                recent_history = [m for m in recent_history if m.id != message.id]
                chat_context = "\n".join([f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.author.name}: {m.content}" for m in recent_history])
                is_ticket_context = 'ticket' in message.channel.name.lower()
                current_channel_name = message.channel.name

                # Search Functionality
                async def search_memory(query, target_channel="ALL"):
                    results = []
                    is_current_channel = target_channel.lower() == current_channel_name.lower()
                    if is_current_channel and (query == "*" or not query.strip()):
                        if chat_context: return f"[Historial reciente #{current_channel_name}]\n{chat_context}"
                        else: return f"AVISO: #{current_channel_name} está vacío."
                    
                    search_scope = message.guild.text_channels if target_channel == "ALL" else [c for c in message.guild.text_channels if c.name.lower() == target_channel.lower()]
                    
                    for channel in search_scope:
                        if not channel.permissions_for(message.guild.me).read_messages: continue
                        try:
                            async for msg in channel.history(limit=50):
                                if query == "*" or (query.lower() in msg.content.lower()):
                                    if not msg.author.bot:
                                        results.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] [{msg.channel.name}] {msg.author.name}: {msg.content}")
                                if len(results) >= 25: break
                        except: pass
                    return "\n".join(results) if results else "No se encontraron mensajes."

                # Agent call
                # Prepare channel list and stats
                channel_names = [f"{c.name} (<#{c.id}>)" for c in message.guild.text_channels if c.permissions_for(message.guild.me).read_messages]
                
                status_m = None
                async def show_s(text):
                    nonlocal status_m
                    if status_m: await status_m.edit(content=text)
                    else: status_m = await message.channel.send(text)
                
                async def add_r(emoji): await message.add_reaction(emoji)

                response = await agent.process_query(
                    query=message.content.replace(f'<@{bot_instance.user.id}>', '').strip(),
                    user_name=message.author.name,
                    available_channels=channel_names,
                    server_stats={"Server": message.guild.name},
                    is_ticket=is_ticket_context,
                    chat_history=chat_context,
                    search_tool=search_memory,
                    current_channel=current_channel_name,
                    status_callback=show_s,
                    reaction_callback=add_r
                )
                
                if status_m: await status_m.delete()
                
                if "REACT:" in response:
                    try:
                        parts = response.rsplit("REACT:", 1)
                        response = parts[0].strip()
                        emoji = parts[1].strip().split()[0]
                        await add_r(emoji)
                    except: pass
                
                response = response.replace("meulify.com", "meulify.top")
                await message.reply(response + "\n\n-# *Respuesta generada por IA.*")

        await bot_instance.process_commands(message)

    @bot_instance.command()
    @commands.has_permissions(administrator=True)
    async def index_channel(ctx, channel_id: int):
        channel = bot_instance.get_channel(channel_id)
        if not channel:
            await ctx.send("Channel not found.")
            return
        await ctx.send(f"Indexing {channel.name}...")
        messages = []
        async for msg in channel.history(limit=500):
            if not msg.author.bot and len(msg.content) > 10:
                messages.append(f"User: {msg.content}")
        if messages:
            agent.learn_from_text(messages, source=f"channel_{channel.name}")
            await ctx.send(f"Indexed {len(messages)} messages.")
        else:
            await ctx.send("No valid messages found.")

async def start_bot():
    global bot
    if not TOKEN:
        logger.error("DISCORD_TOKEN not found!")
        return

    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            proxy_url = get_webshare_proxy_sync()
            logger.info(f"Starting bot (Attempt {attempt+1}/{max_retries}, Proxy: {'Enabled' if proxy_url else 'Disabled'})...")
            
            # Re-initialize bot with fresh proxy if it's the second attempt or more
            # (First attempt also initializes it)
            bot = commands.Bot(command_prefix='!mai_', intents=intents, proxy=proxy_url)
            
            # Setup events and commands for the new bot instance
            setup_bot_events(bot)
            
            await bot.start(TOKEN)
            break # Success!
        except (aiohttp.ClientError, discord.HTTPException, asyncio.TimeoutError) as e:
            logger.error(f"Connection error (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.critical("Max retries reached. Could not connect to Discord.")

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
