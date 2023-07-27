import discord
import os
import requests
import json
import random
from keep_alive import keep_alive
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# TARGET_CHANNEL_ID = 1131754439410208808
ROLE_NAME = "NO LIFE"

# Set it true while giving a role 
giving_role = False

# Emoji to react
EMOJI = "🔔"

# Message
MSG = "BING BONG"

# Set Time for the special role  (mins)
SPAN = 60

# Target channel name
CHANNEL_NAME = "test_channel"

# ServerName
GUILD_NAME = "たぬめんぽんぽこりーん"

TARGET_GUILD_ID = None
TARGET_CHANNEL = None

@client.event
async def on_ready():
    global TARGET_GUILD_ID, TARGET_CHANNEL_ID # Set them as global
    for guild in client.guilds:
        if guild.name == GUILD_NAME:
            TARGET_GUILD_ID = guild.id
            break
    
    for channel in client.get_guild(TARGET_GUILD_ID).channels:
        if channel.name == CHANNEL_NAME:
            TARGET_CHANNEL_ID = channel.id
            break
    print(f'We have logged in as -- {client.user}')
    # start the loop of the function
    client.loop.create_task(send_message_randome_with_reaction())


@client.event
async def on_reaction_add(reaction, user):
    global giving_role
    if not user.bot:  # ignore bot
        if reaction.message.author == client.user and reaction.emoji == EMOJI:
            if giving_role:
                return

            giving_role = True
            try:
                # add the role to the user clicked reaction
                guild = reaction.message.guild
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                await user.add_roles(role)

                # delete the message after giving the role
                await reaction.message.delete()
              
                # after 1 hour, remove role
                await asyncio.sleep(60*SPAN)
                await user.remove_roles(role)
          
            finally:
                giving_role = False


async def send_message_randome_with_reaction():
    channel = client.get_channel(TARGET_CHANNEL_ID)
    
    if channel is None:
        print(f"Error: Target channel '{CHANNEL_NAME}' not found in the guild.")
        return

    while True:
        sent_message = await channel.send(MSG)
        await sent_message.add_reaction(EMOJI)

        # Set random interval between 1 hour to 2 hours
        interval_min = 60 * 60
        interval_max = 60 * 120 
        random_interval = random.randint(interval_min, interval_max)
        
        # Sleep random interval
        await asyncio.sleep(random_interval)


keep_alive()
client.run(os.environ['TOKEN'])
