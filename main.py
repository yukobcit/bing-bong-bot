import discord
import os
import random
import asyncio
import pymongo
import datetime
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

mongo_uri = os.environ.get("MONGO_URI")
mongo_collection_name = os.environ.get("MONGO_COLLECTION")

try:
    mongo_client = pymongo.MongoClient(mongo_uri)
    # Code for successful connection
    print("Connected to MongoDB!")
except pymongo.errors.ConnectionFailure as e:
    # Error handling for connection failure
    print(f"Failed to connect to MongoDB: {e}")

db = mongo_client[os.environ.get("MONGO_DB")]
mongo_collection = db[mongo_collection_name]

# TARGET_CHANNEL_ID = 1131754439410208808
ROLE_NAME = "NO LIFE"

# Set it true while giving a role
giving_role = False

# Emoji to react
EMOJI = "🔔"

# Message
MSG = "BING BONG"

# Set Time for the special role (mins)
SPAN = 60

# Target channel name
CHANNEL_NAME = "test_channel"

# ServerName
GUILD_NAME = "たぬめんぽんぽこりーん"

TARGET_GUILD_ID = None
TARGET_CHANNEL = None


@bot.event
async def on_ready():
    global TARGET_GUILD_ID, TARGET_CHANNEL_ID  # Set them as global
    for guild in bot.guilds:
        if guild.name == GUILD_NAME:
            TARGET_GUILD_ID = guild.id
            break

    for channel in bot.get_guild(TARGET_GUILD_ID).channels:
        if channel.name == CHANNEL_NAME:
            TARGET_CHANNEL_ID = channel.id
            break
    print(f'We have logged in as -- {bot.user}')
    # start the loop of the function
    bot.loop.create_task(send_message_random_with_reaction())


@bot.event
async def on_reaction_add(reaction, user):
    global giving_role
    if not user.bot:  # ignore bot
        if reaction.message.author == bot.user and reaction.emoji == EMOJI:
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

                # Add or update data in db
                current_time = datetime.datetime.now()
                data = {
                    "message_id": reaction.message.id,
                    "server_id": reaction.message.guild.id,
                    "user_id": user.id,
                    "reaction_time": current_time,
                    "reacted": True
                }
                query = {"message_id": reaction.message.id}
                mongo_collection.update_one(query, {"$set": data}, upsert=True)

                # after 1 hour, remove role
                await asyncio.sleep(60 * 1)
                await user.remove_roles(role)

            finally:
                giving_role = False


async def send_message_random_with_reaction():
    channel = bot.get_channel(TARGET_CHANNEL_ID)

    if channel is None:
        print(
            f"Error: Target channel '{CHANNEL_NAME}' not found in the guild.")
        return

    while True:

        # Check and delete unreacted messages from the previous cycle
        unreacted_messages = mongo_collection.find({"reacted": False})
        for unreacted_message in unreacted_messages:
            message_id = unreacted_message["message_id"]
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                pass  # Message is already deleted or not accessible

        sent_message = await channel.send(MSG)
        await sent_message.add_reaction(EMOJI)

        # Set random interval between 1 hour to 2 hours
        interval_min = 60 * 2
        interval_max = 60 * 3
        random_interval = random.randint(interval_min, interval_max)

        # Save the message ID and current time to the database
        data = {
            "message_id": sent_message.id,
            "timestamp": datetime.datetime.now(),
            "reacted": False
        }
        mongo_collection.insert_one(data)

        # Sleep random interval
        await asyncio.sleep(random_interval)


@bot.command(name="bb-leader")
async def leaderboard(ctx):
    print("leaderboard")
    # Get the start and end timestamps for the current month
    now = datetime.datetime.now()
    start_of_month = now.replace(day=1,
                                 hour=0,
                                 minute=0,
                                 second=0,
                                 microsecond=0)
    end_of_month = now.replace(day=1,
                               month=now.month + 1,
                               hour=0,
                               minute=0,
                               second=0,
                               microsecond=0)

    # Query the MongoDB for data within the current month
    query = {"reaction_time": {"$gte": start_of_month, "$lt": end_of_month}}
    cursor = mongo_collection.find(query)

    # Aggregate points for each user
    user_points = {}
    for document in cursor:
        user_id = int(document["user_id"])  # Convert user ID to an integer
        user_points[user_id] = user_points.get(user_id, 0) + 1

    # Sort points in descending order
    sorted_users = sorted(user_points.items(),
                          key=lambda x: x[1],
                          reverse=True)

    # Create and send the leaderboard
    leaderboard = "Leader Board:\n"
    for rank, (user_id, points) in enumerate(sorted_users, start=1):
        # Get user name (fetch the user object from the user ID)
        user = await bot.fetch_user(user_id)
        user_name = user.name if user else "Unknown User"
        leaderboard += f"{rank}. {user_name}: {points} points\n"

    await ctx.send(leaderboard)


bot.run(os.environ['TOKEN'])
