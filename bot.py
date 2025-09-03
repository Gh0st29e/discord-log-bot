import discord
from discord.ext import commands
from flask import Flask
import threading
import os

# ---- Keep Alive Webserver für Replit/Railway ----
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

# ---- Events ----
@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")

# --- Member Join / Leave ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="👋 Mitglied beigetreten", color=discord.Color.green())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account erstellt am", value=member.created_at.strftime("%d.%m.%Y %H:%M"), inline=False)

        # Prüfen, ob das Mitglied schon einmal auf dem Server war
        if member.joined_at and member.created_at:
            embed.set_footer(text="Neues Mitglied" if len(member.guild.members) == 1 else "Wiedereintritt möglich")

        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="👋 Mitglied hat den Server verlassen", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        await channel.send(embed=embed)

# --- Voice Log inkl. Server-Mute/Deafen ---
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_AUDIO)
    if not channel:
        return

    # --- Join / Leave Log ---
    if before.channel != after.channel:
        if after.channel is not None:
            embed = discord.Embed(
                title="🔊 Voice-Join",
                description=f"{member.mention} ist {after.channel.mention} beigetreten",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
        elif before.channel is not None:
            embed = discord.Embed(
                title="🔇 Voice-Leave",
                description=f"{member.mention} hat {before.channel.mention} verlassen",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

    # --- Serverweite Mute/Unmute ---
    if before.mute != after.mute:
        audit = await member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update).flatten()
        moderator = audit[0].user if audit else "Unbekannt"
        if after.mute:
            embed = discord.Embed(
                title="🔇 Server-Mute",
                description=f"{moderator.mention} hat {member.mention} serverweit stummgeschaltet",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="🔊 Server-Unmute",
                description=f"{moderator.mention} hat {member.mention} serverweit entstummt",
                color=discord.Color.green()
            )
        await channel.send(embed=embed)

    # --- Serverweite Deaf/Undeaf ---
    if before.deaf != after.deaf:
        audit = await member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update).flatten()
        moderator = audit[0].user if audit else "Unbekannt"
        if after.deaf:
            embed = discord.Embed(
                title="🔇 Server-Deafen",
                description=f"{moderator.mention} hat {member.mention} serverweit taubgeschaltet",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🔊 Server-Undeafen",
                description=f"{moderator.mention} hat {member.mention} wieder hörbar gemacht",
                color=discord.Color.green()
            )
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

# --- Server Änderungen Logs (Rollen / Kanäle etc.) ---
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
