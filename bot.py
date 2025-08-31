import discord
from discord.ext import commands
from flask import Flask
import threading
import os

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
        # Prüfen ob der User schonmal da war (via joined_at + created_at Vergleich)
        is_new = (member.joined_at == member.created_at)
        embed = discord.Embed(title="👋 Mitglied beigetreten", color=discord.Color.green())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)
        embed.add_field(name="Server beigetreten", value=member.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(name="Rollen", value=", ".join(roles) if roles else "Keine", inline=False)
        if is_new:
            embed.set_footer(text="📌 Neues Mitglied auf Discord & Server")
        else:
            embed.set_footer(text="📌 Mitglied war schonmal auf Discord, aber neu auf diesem Server")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="👋 Mitglied hat den Server verlassen", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(name="Rollen beim Verlassen", value=", ".join(roles) if roles else "Keine", inline=False)
        await channel.send(embed=embed)

# --- Voice Log ---
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_AUDIO)
    if not channel:
        return

    if before.channel != after.channel:
        if after.channel is not None:
            embed = discord.Embed(title="🔊 Voice-Join", description=f"{member} ist {after.channel} beigetreten", color=discord.Color.green())
            await channel.send(embed=embed)
        elif before.channel is not None:
            embed = discord.Embed(title="🔇 Voice-Leave", description=f"{member} hat {before.channel} verlassen", color=discord.Color.red())
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
bot.run(os.getenv("DISCORD_TOKEN"))

