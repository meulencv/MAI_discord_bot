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
            
            # Context Analysis (Ticket vs General)
            # Simple heuristic: If channel name contains 'ticket' or is in a specific category (user can configure)
            is_ticket_context = 'ticket' in message.channel.name.lower()
            
            # If it's a ticket, we pass the current chat history as immediate context
            ticket_context = ""
            if is_ticket_context:
                # Fetch recent history for context
                history = [msg async for msg in message.channel.history(limit=10)]
                history.reverse() # Oldest first
                ticket_context = "\n".join([f"{m.author.name}: {m.content}" for m in history])

            # Generate Response
            response = agent.process_query(
                query=message.content.replace(f'<@{bot.user.id}>', '').strip(),
                user_name=message.author.name,
                is_ticket=is_ticket_context,
                ticket_history=ticket_context
            )
            
            await message.reply(response)

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
