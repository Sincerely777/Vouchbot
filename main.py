import os
import json
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# File where data will be stored safely on Railway
DATA_FILE = "vouch_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# --- STORAGE FUNCTIONS ---
def save_vouch(target_id: str, voucher_mention: str, rating_stars: str, comment: str):
    """Saves vouch data into a local tracking file."""
    star_count = len(rating_stars)
    db = load_data()
    
    if target_id not in db:
        db[target_id] = {
            "total_vouches": 0,
            "star_sum": 0,
            "history": []
        }
    
    db[target_id]["total_vouches"] += 1
    db[target_id]["star_sum"] += star_count
    db[target_id]["history"].append({
        "by": voucher_mention,
        "stars": rating_stars,
        "comment": comment
    })
    save_data(db)

# --- COMMAND 1: VOUCH ---
@bot.tree.command(name="vouch", description="Vouch for a user with a star rating and comment")
@app_commands.describe(
    user="The Discord user you want to vouch for",
    rating="Choose a rating from 1 to 5 stars",
    comment="Optional: Add details about your trade"
)
@app_commands.choices(rating=[
    app_commands.Choice(name="⭐ (1 Star)", value="⭐"),
    app_commands.Choice(name="⭐⭐ (2 Stars)", value="⭐⭐"),
    app_commands.Choice(name="⭐⭐⭐ (3 Stars)", value="⭐⭐⭐"),
    app_commands.Choice(name="⭐⭐⭐⭐ (4 Stars)", value="⭐⭐⭐⭐"),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ (5 Stars)", value="⭐⭐⭐⭐⭐"),
])
async def vouch(
    interaction: discord.Interaction, 
    user: discord.User, 
    rating: app_commands.Choice[str], 
    comment: str = None
):
    if user.id == interaction.user.id:
        await interaction.response.send_message("You cannot vouch for yourself!", ephemeral=True)
        return

    comment_text = comment if comment else "No comment provided."

    # Save to the local database file
    save_vouch(str(user.id), interaction.user.mention, rating.value, comment_text)

    embed = discord.Embed(title="✨ New Vouch Received! ✨", color=discord.Color.green())
    embed.add_field(name="User Vouched", value=user.mention, inline=True)
    embed.add_field(name="Vouched By", value=interaction.user.mention, inline=True)
    embed.add_field(name="Rating", value=rating.value, inline=False)
    embed.add_field(name="Comment", value=comment_text, inline=False)

    await interaction.response.send_message(embed=embed)

# --- COMMAND 2: RECORDS ---
@bot.tree.command(name="records", description="View the detailed vouch history of a user")
@app_commands.describe(user="The user whose profile you want to check")
async def records(interaction: discord.Interaction, user: discord.User):
    user_id = str(user.id)
    db = load_data()
    
    if user_id not in db or db[user_id]["total_vouches"] == 0:
        await interaction.response.send_message(f"🔍 {user.mention} doesn't have any vouches yet!", ephemeral=True)
        return
        
    data = db[user_id]
    avg_rating = round(data["star_sum"] / data["total_vouches"], 1)
    
    embed = discord.Embed(title=f"📊 Vouch Profile: {user.name}", color=discord.Color.blue())
    embed.add_field(name="Total Reviews", value=str(data["total_vouches"]), inline=True)
    embed.add_field(name="Average Score", value=f"⭐ {avg_rating} / 5.0", inline=True)
    
    recent_reviews = ""
    for v in data["history"][-5:]:
        recent_reviews += f"• **By:** {v['by']} | **Rating:** {v['stars']}\n ↳ *\"{v['comment']}\"*\n\n"
        
    embed.add_field(name="Recent Feedback", value=recent_reviews or "No written comments.", inline=False)
    await interaction.response.send_message(embed=embed)

# --- COMMAND 3: LEADERBOARD ---
@bot.tree.command(name="leaderboard", description="View the top-rated traders in the server")
async def leaderboard(interaction: discord.Interaction):
    db = load_data()
    if len(db.keys()) == 0:
        await interaction.response.send_message("The leaderboard is currently empty!", ephemeral=True)
        return

    leaderboard_list = []
    
    for key in db.keys():
        user_data = db[key]
        if user_data["total_vouches"] > 0:
            avg = user_data["star_sum"] / user_data["total_vouches"]
            leaderboard_list.append({
                "id": key,
                "total": user_data["total_vouches"],
                "score": avg
            })
            
    leaderboard_list.sort(key=lambda x: (x["score"], x["total"]), reverse=True)
    
    embed = discord.Embed(title="🏆 Elite Sprite Traders Leaderboard", color=discord.Color.gold())
    
    description_text = ""
    for index, entry in enumerate(leaderboard_list[:10], start=1):  # Top 10
        description_text += f"**#{index}** <@{entry['id']}> — **Score:** ⭐ {round(entry['score'], 1)} ({entry['total']} reviews)\n"
        
    embed.description = description_text
    await interaction.response.send_message(embed=embed)

bot.run(os.environ.get("DISCORD_TOKEN"))
