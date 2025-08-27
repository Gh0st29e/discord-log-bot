import discord
from discord.ext import commands
import os

# ---- IDs deiner Log-Kanäle ----
LOG_AUDIO_ID = 1353012344179134474
LOG_MESSAGES_ID = 1352670497535426671
LOG_MEMBER_ID = 1409630469192155197
LOG_OTHER_ID = 1353159802913554473

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Hilfsfunktion für Embeds ----
def make_embed(title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# ---- Wenn Bot startet ----
@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")

# ---- Audio-Logs ----
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_AUDIO_ID)

    if before.channel != after.channel:
        if after.channel:
            await channel.send(embed=make_embed(
                "Sprachkanal betreten",
                f"{member.mention} hat **{after.channel}** betreten."
            ))
        elif before.channel:
            await channel.send(embed=make_embed(
                "Sprachkanal verlassen",
                f"{member.mention} hat **{before.channel}** verlassen."
            ))

    if before.mute != after.mute:
        await channel.send(embed=make_embed(
            "Mute-Status geändert",
            f"{member.mention} wurde {'stummschalten' if after.mute else 'entstummt'}."
        ))

    if before.deaf != after.deaf:
        await channel.send(embed=make_embed(
            "Deaf-Status geändert",
            f"{member.mention} wurde {'taub gestellt' if after.deaf else 'hörbar gemacht'}."
        ))

# ---- Nachrichten-Logs ----
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    channel = bot.get_channel(LOG_MESSAGES_ID)
    await channel.send(embed=make_embed(
        "Nachricht gelöscht",
        f"Von: {message.author.mention}\n"
        f"In: {message.channel.mention}\n"
        f"Inhalt: {message.content}"
    ))

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    channel = bot.get_channel(LOG_MESSAGES_ID)
    await channel.send(embed=make_embed(
        "Nachricht bearbeitet",
        f"Von: {before.author.mention}\n"
        f"In: {before.channel.mention}\n"
        f"Vorher: {before.content}\n"
        f"Nachher: {after.content}"
    ))

# ---- Member-Logs ----
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_MEMBER_ID)
    if member.joined_at and member.created_at:
        if (member.joined_at - member.created_at).days < 1:
            info = "⚠️ Neuer Account (jünger als 1 Tag)"
        else:
            info = "Bestehender Account"
    else:
        info = "Unbekannt"
    await channel.send(embed=make_embed(
        "Mitglied beigetreten",
        f"{member.mention} ist dem Server beigetreten.\n{info}"
    ))

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_MEMBER_ID)
    await channel.send(embed=make_embed(
        "Mitglied hat den Server verlassen",
        f"{member} hat den Server verlassen."
    ))

# ---- Server-Änderungen (Rollen, Kanäle etc.) ----
@bot.event
async def on_guild_channel_update(before, after):
    channel = bot.get_channel(LOG_OTHER_ID)
    await channel.send(embed=make_embed(
        "Kanal geändert",
        f"Vorher: {before.name}\nNachher: {after.name}"
    ))

@bot.event
async def on_guild_role_update(before, after):
    channel = bot.get_channel(LOG_OTHER_ID)
    await channel.send(embed=make_embed(
        "Rolle geändert",
        f"Vorher: {before.name}\nNachher: {after.name}"
    ))

# ---- Start ----
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN is None:
        print("⚠️ Fehler: Bitte setze die Environment Variable DISCORD_TOKEN!")
    else:
        bot.run(TOKEN)
