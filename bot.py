import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask
import threading

# ---- Keep Alive Webserver (optional für Railway, aber unschädlich) ----
app = Flask('')

@app.route('/')
def home():
    return "Bot läuft!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

# ---- Bot Setup ----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Channel IDs ----
LOG_AUDIO = 1353012344179134474
LOG_MSG = 1352670497535426671
LOG_MEMBER = 1409630469192155197
LOG_OTHER = 1353159802913554473

# ---------- Hilfsfunktion: Moderator aus Audit-Log ermitteln ----------
async def find_voice_flag_moderator(guild: discord.Guild, member: discord.Member, flag_name: str, new_value: bool):
    """
    Sucht im Audit-Log nach dem passenden member_update-Eintrag, bei dem
    das Flag (mute/deaf) für genau dieses Mitglied auf new_value geändert wurde.
    """
    try:
        # Mehrere Einträge prüfen, da kurz vorher auch andere Änderungen passiert sein können
        async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_update):
            # Prüfe, dass der Eintrag dieses Mitglied betrifft
            if not hasattr(entry, "target") or getattr(entry.target, "id", None) != member.id:
                continue

            # In discord.py 2.x haben wir ein Diff-Objekt mit before/after-Attributen
            before_val = getattr(entry.changes.before, flag_name, None)
            after_val = getattr(entry.changes.after, flag_name, None)

            # Wir suchen genau den Eintrag, in dem dieses Flag geändert wurde
            if after_val is None:
                continue
            if before_val == after_val:
                continue
            if after_val == new_value:
                return entry.user
    except discord.Forbidden:
        # Keine Audit-Log Rechte (sollte mit Admin nicht passieren)
        return None
    except Exception:
        return None
    return None

# ---- Events ----
@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")

# --- Member Join / Leave ---
@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="👋 Mitglied beigetreten", color=discord.Color.green())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account erstellt am", value=member.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        # Hinweis: „war schon mal da“ lässt sich zuverlässig nur mit eigener DB loggen.
        # Optionaler Platzhalter:
        embed.add_field(name="Status", value="Neues Mitglied oder Wiedereintritt (ohne DB-Prüfung)", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    channel = bot.get_channel(LOG_MEMBER)
    if channel:
        embed = discord.Embed(title="👋 Mitglied hat den Server verlassen", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        await channel.send(embed=embed)

# --- Voice Log inkl. Server-Mute/Deafen ---
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    channel = bot.get_channel(LOG_AUDIO)
    if not channel:
        return

    # --- Join / Leave / Move ---
    if before.channel != after.channel:
        if after.channel is not None and before.channel is None:
            embed = discord.Embed(
                title="🔊 Voice-Join",
                description=f"{member.mention} ist {after.channel.mention} beigetreten",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
        elif after.channel is None and before.channel is not None:
            embed = discord.Embed(
                title="🔇 Voice-Leave",
                description=f"{member.mention} hat {before.channel.mention} verlassen",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
        elif before.channel is not None and after.channel is not None:
            embed = discord.Embed(
                title="🔁 Voice-Move",
                description=f"{member.mention} wurde von {before.channel.mention} nach {after.channel.mention} verschoben",
                color=discord.Color.blurple()
            )
            await channel.send(embed=embed)

    # --- Serverweite Mute/Unmute (NICHT self_mute) ---
    if before.mute != after.mute:
        # Kleinen Moment warten, damit der Audit-Log-Eintrag sicher vorhanden ist
        await asyncio.sleep(0.6)
        moderator = await find_voice_flag_moderator(member.guild, member, "mute", after.mute)
        mod_mention = moderator.mention if isinstance(moderator, discord.User) or isinstance(moderator, discord.Member) else "Unbekannt"

        if after.mute:
            embed = discord.Embed(
                title="🔇 Server-Mute",
                description=f"{mod_mention} hat {member.mention} serverweit stummgeschaltet",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="🔊 Server-Unmute",
                description=f"{mod_mention} hat {member.mention} serverweit entstummt",
                color=discord.Color.green()
            )
        # Zusatzinfos
        if after.channel:
            embed.add_field(name="Kanal", value=after.channel.mention, inline=True)
        await channel.send(embed=embed)

    # --- Serverweite Deaf/Undeaf (NICHT self_deaf) ---
    if before.deaf != after.deaf:
        await asyncio.sleep(0.6)
        moderator = await find_voice_flag_moderator(member.guild, member, "deaf", after.deaf)
        mod_mention = moderator.mention if isinstance(moderator, (discord.User, discord.Member)) else "Unbekannt"

        if after.deaf:
            embed = discord.Embed(
                title="🔇 Server-Deafen",
                description=f"{mod_mention} hat {member.mention} serverweit taubgeschaltet",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🔊 Server-Undeafen",
                description=f"{mod_mention} hat {member.mention} wieder hörbar gemacht",
                color=discord.Color.green()
            )
        if after.channel:
            embed.add_field(name="Kanal", value=after.channel.mention, inline=True)
        await channel.send(embed=embed)

# --- Nachrichten Logs ---
@bot.event
async def on_message_delete(message: discord.Message):
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
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot:
        return
    if before.content == after.content:
        return
    channel = bot.get_channel(LOG_MSG)
    if channel:
        embed = discord.Embed(title="✏️ Nachricht bearbeitet", color=discord.Color.orange())
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Vorher", value=before.content or "*leer*", inline=False)
        embed.add_field(name="Nachher", value=after.content or "*leer*", inline=False)
        await channel.send(embed=embed)

# --- Server-Änderungen (Beispiele) ---
@bot.event
async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
    channel = bot.get_channel(LOG_OTHER)
    if channel:
        embed = discord.Embed(title="⚙️ Kanal geändert", color=discord.Color.blurple())
        embed.add_field(name="Vorher", value=before.name, inline=True)
        embed.add_field(name="Nachher", value=after.name, inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_guild_role_update(before: discord.Role, after: discord.Role):
    channel = bot.get_channel(LOG_OTHER)
    if channel:
        embed = discord.Embed(title="🎭 Rolle geändert", color=discord.Color.blurple())
        embed.add_field(name="Vorher", value=before.name, inline=True)
        embed.add_field(name="Nachher", value=after.name, inline=True)
        await channel.send(embed=embed)

# ---- Start Bot ----
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
