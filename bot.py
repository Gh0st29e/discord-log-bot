import discord
from discord.ext import commands
from flask import Flask
import threading
import os
import json

# ---- Keep Alive Webserver für Railway / Replit ----
app = Flask('')

@app.route('/')
def home():
    return "Bot läuft!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# ---- Bot Setup ----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Channel IDs ----
LOG_AUDIO = 1353012344179134474
LOG_MSG = 1352670497535426671
LOG_MEMBER = 1409630469192155197
LOG_OTHER = 1353159802913554473

# ---- Member Datenbank ----
MEMBER_DB = "members.json"

def load_members():
    if not os.path.exists(MEMBER_DB):
        return {}
    with open(MEMBER_DB, "r") as f:
        return json.load(f)

def save_members(data):
    with open(MEMBER_DB, "w") as f:
        json.dump(data, f, indent=4)

# ---- Events ----
@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")

# --- Member Join / Leave ---
@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        members = load_members()
        user_id = str(member.id)

        if user_id in members:
            status_text = "🔄 Wiederkehrendes Mitglied (war schon einmal auf dem Server)"
        else:
            status_text = "🆕 Neues Server-Mitglied"
            members[user_id] = {"name": str(member), "first_join": str(member.joined_at)}
            save_members(members)

        embed = discord.Embed(title="👋 Mitglied beigetreten", color=discord.Color.green())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account erstellt am", value=member.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="Status", value=status_text, inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="🚪 Mitglied hat den Server verlassen", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        await channel.send(embed=embed)

# --- Voice Log ---
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_AUDIO)
    if not channel:
        return

    if before.channel != after.channel:
        if after.channel is not None:
            embed = discord.Embed(
                title="🔊 Voice-Join",
                description=f"{member} ist {after.channel} beigetreten",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
        elif before.channel is not None:
            embed = discord.Embed(
                title="🔇 Voice-Leave",
                description=f"{member} hat {before.channel} verlassen",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

    # Serverweit stumm/taub prüfen
    if before.mute != after.mute:
        if after.mute:
            action = "wurde serverweit stummgeschaltet"
        else:
            action = "wurde serverweit entstummt"
        embed = discord.Embed(title="🎙️ Voice-Aktion", description=f"{member} {action}", color=discord.Color.orange())
        await channel.send(embed=embed)

    if before.deaf != after.deaf:
        if after.deaf:
            action = "wurde serverweit taubgeschaltet"
        else:
            action = "wurde serverweit enttaubt"
        embed = discord.Embed(title="🎧 Voice-Aktion", description=f"{member} {action}", color=discord.Color.orange())
        await channel.send(embed=embed)

# --- Nachrichten Logs ---
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    channel = bot.get_channel(LOG_MSG)
    if channel:
        embed = discord.Embed(title="🗑️ Nachricht gelöscht", color=discord.Color.red())
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        embed.add_field(name="Inhalt", value=message.content or "*leer*", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    channel = bot.get_channel(LOG_MSG)
    if channel:
        embed = discord.Embed(title="✏️ Nachricht bearbeitet", color=discord.Color.orange())
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Vorher", value=before.content or "*leer*", inline=False)
        embed.add_field(name="Nachher", value=after.content or "*leer*", inline=False)
        await channel.send(embed=embed)

# --- Server Änderungen Logs ---
@bot.event
async def on_guild_channel_update(before, after):
    channel = bot.get_channel(LOG_OTHER)
    if channel:
        embed = discord.Embed(title="⚙️ Kanal geändert", color=discord.Color.blurple())
        embed.add_field(name="Vorher", value=before.name, inline=True)
        embed.add_field(name="Nachher", value=after.name, inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_guild_role_update(before, after):
    channel = bot.get_channel(LOG_OTHER)
    if channel:
        embed = discord.Embed(title="🎭 Rolle geändert", color=discord.Color.blurple())
        embed.add_field(name="Vorher", value=before.name, inline=True)
        embed.add_field(name="Nachher", value=after.name, inline=True)
        await channel.send(embed=embed)

# ---- Start Bot ----
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
