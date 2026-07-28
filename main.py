import os
import json
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "vouch_data.json"

# CHANGE THIS: Paste your personal, unique Discord User ID number between the quotes
# (Right-click your name in Discord -> Copy User ID)
OWNER_ID = "YOUR_PERSONAL_DISCORD_USER_ID_HERE"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    # Print out all server IDs the bot is currently hiding in
    print("Connected Servers:")
    for guild in bot.guilds:
        print(f"• Name: {guild.name} | ID: {guild.id}")
    try:
        await bot.tree.sync()
        print("Synced commands successfully!")
    except Exception as e:
        print(f"Sync error: {e}")

# --- SECRET KICK COMMAND ---
@bot.tree.command(name="leave_server", description="Force the bot to leave an unauthorized server")
@app_commands.describe(server_id="The ID number of the server you want the bot to leave")
async def leave_server(interaction: discord.Interaction, server_id: str):
    # Only allow YOU to execute this escape command
    if str(interaction.user.id) != OWNER_ID:
        await interaction.response.send_message("❌ Error: You are not authorized to control this bot's network settings.", ephemeral=True)
        return

    try:
        guild_target = bot.get_guild(int(server_id))
        if guild_target is None:
            await interaction.response.send_message("🔍 Could not locate a server matching that ID.", ephemeral=True)
            return

        server_name = guild_target.name
        await guild_target.leave() # The bot drops out of the server instantly
        await interaction.response.send_message(f"✅ Success! Booted bot out of server: **{server_name}**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to drop server: {e}", ephemeral=True)

# --- VOUCH COMMANDS REMAINING BELOW ---
def save_vouch(target_id: str, voucher_mention: str, rating_stars: str, comment: str):
    star_count = len(rating_stars)
    db = load_data()
    if target_id not in db:
        db[target_id] = {"total_vouches": 0, "star_sum": 0, "history": []}
    db[target_id]["total_vouches"] += 1
    db[target_id]["star_sum"] += star_count
    db[target_id]["history"].append({"by": voucher_mention, "stars": rating_stars, "comment": comment})
    save_data(db)

@bot.tree.command(name="vouch", description="Vouch for a user with a star rating and comment")
async def vouch(interaction: discord.Interaction, user: discord.User, rating: str, comment: str = None):
    if user.id == interaction.user.id:
        await interaction.response.send_message("You cannot vouch for yourself!", ephemeral=True)
        return
    comment_text = comment if comment else "No comment provided."
    save_vouch(str(user.id), interaction.user.mention, rating, comment_text)
    embed = discord.Embed(title="✨ New Vouch Received! ✨", color=discord.Color.green())
    embed.add_field(name="User Vouched", value=user.mention, inline=True)
    embed.add_field(name="Rating", value=rating, inline=False)
    embed.add_field(name="Comment", value=comment_text, inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(os.environ.get("DISCORD_TOKEN"))
