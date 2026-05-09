import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import re
import os

# Configuration
PREFIX = "+"
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Stockage des warns en mémoire
warns = {}
muted_users = {}
bot_start_time = datetime.utcnow()

# ==================== EVENTS ====================

@bot.event
async def on_ready():
    print(f"✅ Syndex Bot connecté en tant que {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{PREFIX}help | Syndex"
    ))

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="bienvenue")
    if channel:
        embed = discord.Embed(
            title=f"👋 Bienvenue sur {member.guild.name} !",
            description=f"Salut {member.mention}, bienvenue sur **Syndex** !\nOn est content de t'avoir parmi nous 🔥",
            color=0x00ffff
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Membre #{member.guild.member_count}")
        await channel.send(embed=embed)

# ==================== HELP ====================

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📋 Syndex Bot — Toutes les commandes",
        description="Préfixe : `+`",
        color=0x00ffff
    )

    embed.add_field(name="🛡️ __Modération__", value="""
`+ban @user raison` — Bannir un membre
`+unban @user` — Débannir un membre
`+tempban @user 24h raison` — Ban temporaire
`+kick @user raison` — Expulser un membre
`+mute @user raison` — Rendre muet
`+unmute @user` — Retirer le mute
`+tempmute @user 30m raison` — Mute temporaire
`+warn @user raison` — Avertir un membre
`+history @user` — Voir les warns
`+clearwarn @user` — Effacer les warns
`+clear 10` — Supprimer X messages
""", inline=False)

    embed.add_field(name="🔒 __Salons__", value="""
`+lock` — Verrouiller le salon
`+unlock` — Déverrouiller le salon
`+slowmode 10` — Slowmode en secondes (0 pour désactiver)
`+announce #salon message` — Envoyer une annonce
`+pin` — Épingler le dernier message
`+unpin` — Désépingler le dernier message
""", inline=False)

    embed.add_field(name="👤 __Membres & Rôles__", value="""
`+addrole @user NomDuRole` — Donner un rôle
`+removerole @user NomDuRole` — Retirer un rôle
`+role list` — Voir tous les rôles
`+nick @user nouveaunom` — Changer le pseudo d'un membre
`+setnick nouveaunom` — Changer son propre pseudo
`+dm @user message` — Envoyer un MP via le bot
""", inline=False)

    embed.add_field(name="ℹ️ __Informations__", value="""
`+userinfo @user` — Infos d'un membre
`+serverinfo` — Infos du serveur
`+avatar @user` — Photo de profil
`+membercount` — Nombre de membres
`+uptime` — Temps de fonctionnement du bot
""", inline=False)

    embed.add_field(name="🎮 __Fun__", value="""
`+8ball question` — Boule magique
`+dice` — Lancer un dé
`+coinflip` — Pile ou face
`+poll question` — Créer un sondage
""", inline=False)

    embed.set_footer(text="Syndex Bot | Toutes les commandes")
    await ctx.send(embed=embed)

# ==================== MODÉRATION ====================

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Membre banni", color=0xff0000)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Raison", value=reason)
    embed.add_field(name="Modérateur", value=ctx.author.mention)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, username):
    banned = [entry async for entry in ctx.guild.bans()]
    for entry in banned:
        if entry.user.name == username:
            await ctx.guild.unban(entry.user)
            embed = discord.Embed(title="✅ Membre débanni", description=f"**{username}** a été débanni.", color=0x00ff00)
            await ctx.send(embed=embed)
            return
    await ctx.send("❌ Utilisateur introuvable dans les bans.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def tempban(ctx, member: discord.Member, duration: str, *, reason="Aucune raison"):
    # Parse duration (ex: 24h, 30m, 7d)
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1]
    amount = int(duration[:-1])
    seconds = amount * time_units.get(unit, 60)

    await member.ban(reason=reason)
    embed = discord.Embed(title="⏱️ Ban temporaire", color=0xff6600)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Durée", value=duration)
    embed.add_field(name="Raison", value=reason)
    await ctx.send(embed=embed)

    await asyncio.sleep(seconds)
    await ctx.guild.unban(member)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👟 Membre expulsé", color=0xff6600)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Raison", value=reason)
    embed.add_field(name="Modérateur", value=ctx.author.mention)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, *, reason="Aucune raison"):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)
    await member.add_roles(role)
    embed = discord.Embed(title="🔇 Membre mute", color=0xffff00)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Raison", value=reason)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        embed = discord.Embed(title="🔊 Membre unmute", description=f"{member.mention} peut de nouveau parler.", color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Ce membre n'est pas mute.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def tempmute(ctx, member: discord.Member, duration: str, *, reason="Aucune raison"):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1]
    amount = int(duration[:-1])
    seconds = amount * time_units.get(unit, 60)

    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)
    embed = discord.Embed(title="⏱️ Mute temporaire", color=0xffff00)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Durée", value=duration)
    embed.add_field(name="Raison", value=reason)
    await ctx.send(embed=embed)

    await asyncio.sleep(seconds)
    await member.remove_roles(role)
    await ctx.send(f"✅ {member.mention} a été unmute automatiquement.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):
    uid = str(member.id)
    if uid not in warns:
        warns[uid] = []
    warns[uid].append({"reason": reason, "by": str(ctx.author), "date": str(datetime.utcnow().strftime("%d/%m/%Y"))})
    embed = discord.Embed(title="⚠️ Avertissement", color=0xffaa00)
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Raison", value=reason)
    embed.add_field(name="Total warns", value=len(warns[uid]))
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def history(ctx, member: discord.Member):
    uid = str(member.id)
    user_warns = warns.get(uid, [])
    if not user_warns:
        await ctx.send(f"✅ {member.mention} n'a aucun avertissement.")
        return
    embed = discord.Embed(title=f"📋 Warns de {member.name}", color=0xffaa00)
    for i, w in enumerate(user_warns, 1):
        embed.add_field(name=f"Warn #{i} — {w['date']}", value=f"Raison : {w['reason']}\nPar : {w['by']}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def clearwarn(ctx, member: discord.Member):
    uid = str(member.id)
    warns[uid] = []
    embed = discord.Embed(title="✅ Warns effacés", description=f"Tous les warns de {member.mention} ont été supprimés.", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"✅ **{amount}** messages supprimés.")
    await asyncio.sleep(3)
    await msg.delete()

# ==================== SALONS ====================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Salon verrouillé", description=f"{ctx.channel.mention} est maintenant verrouillé.", color=0xff0000)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Salon déverrouillé", description=f"{ctx.channel.mention} est maintenant ouvert.", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        await ctx.send("✅ Slowmode désactivé.")
    else:
        await ctx.send(f"✅ Slowmode réglé à **{seconds}** secondes.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    embed = discord.Embed(title="📢 Annonce", description=message, color=0x00ffff)
    embed.set_footer(text=f"Annonce par {ctx.author.name}")
    await channel.send(embed=embed)
    await ctx.send(f"✅ Annonce envoyée dans {channel.mention}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def pin(ctx):
    messages = [m async for m in ctx.channel.history(limit=2)]
    if len(messages) >= 2:
        await messages[1].pin()
        await ctx.send("✅ Message épinglé.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unpin(ctx):
    pins = await ctx.channel.pins()
    if pins:
        await pins[0].unpin()
        await ctx.send("✅ Message désépinglé.")
    else:
        await ctx.send("❌ Aucun message épinglé.")

# ==================== RÔLES & MEMBRES ====================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle **{role_name}** introuvable.")
        return
    await member.add_roles(role)
    embed = discord.Embed(title="✅ Rôle ajouté", description=f"{role.mention} donné à {member.mention}", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle **{role_name}** introuvable.")
        return
    await member.remove_roles(role)
    embed = discord.Embed(title="✅ Rôle retiré", description=f"{role.mention} retiré de {member.mention}", color=0xff6600)
    await ctx.send(embed=embed)

@bot.command()
async def role(ctx, action: str = "list"):
    if action == "list":
        roles = [r.mention for r in ctx.guild.roles if r.name != "@everyone"]
        embed = discord.Embed(title=f"📋 Rôles de {ctx.guild.name}", description="\n".join(roles) or "Aucun rôle", color=0x00ffff)
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, new_nick):
    await member.edit(nick=new_nick)
    embed = discord.Embed(title="✅ Pseudo changé", description=f"Pseudo de {member.mention} changé en **{new_nick}**", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
async def setnick(ctx, *, new_nick):
    await ctx.author.edit(nick=new_nick)
    await ctx.send(f"✅ Ton pseudo a été changé en **{new_nick}**")

@bot.command()
@commands.has_permissions(kick_members=True)
async def dm(ctx, member: discord.Member, *, message):
    try:
        embed = discord.Embed(title=f"📩 Message de {ctx.guild.name}", description=message, color=0x00ffff)
        await member.send(embed=embed)
        await ctx.send(f"✅ MP envoyé à {member.mention}")
    except:
        await ctx.send("❌ Impossible d'envoyer un MP à cet utilisateur.")

# ==================== INFORMATIONS ====================

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    embed = discord.Embed(title=f"👤 Infos de {member.name}", color=0x00ffff)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Surnom", value=member.nick or "Aucun")
    embed.add_field(name="Compte créé", value=member.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="A rejoint le", value=member.joined_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Rôles", value=", ".join(roles) or "Aucun", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"🌐 Infos de {guild.name}", color=0x00ffff)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="ID", value=guild.id)
    embed.add_field(name="Propriétaire", value=guild.owner.mention)
    embed.add_field(name="Membres", value=guild.member_count)
    embed.add_field(name="Salons", value=len(guild.channels))
    embed.add_field(name="Rôles", value=len(guild.roles))
    embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"))
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Avatar de {member.name}", color=0x00ffff)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def membercount(ctx):
    embed = discord.Embed(title="👥 Membres", description=f"Le serveur compte **{ctx.guild.member_count}** membres.", color=0x00ffff)
    await ctx.send(embed=embed)

@bot.command()
async def uptime(ctx):
    delta = datetime.utcnow() - bot_start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    embed = discord.Embed(title="⏱️ Uptime", description=f"Le bot tourne depuis **{hours}h {minutes}m {seconds}s**", color=0x00ffff)
    await ctx.send(embed=embed)

# ==================== FUN ====================

@bot.command(name="8ball")
async def eight_ball(ctx, *, question):
    import random
    responses = [
        "Oui absolument 🔥", "C'est certain ✅", "Sans aucun doute 💯",
        "Très probable 👍", "Les signes disent oui ✨",
        "Je ne sais pas 🤷", "Difficile à dire 😐", "Peut-être 🤔",
        "Non ❌", "Certainement pas 🚫", "Mes sources disent non 👎", "Oublie ça 💀"
    ]
    embed = discord.Embed(title="🎱 Boule magique", color=0x00ffff)
    embed.add_field(name="Question", value=question)
    embed.add_field(name="Réponse", value=random.choice(responses))
    await ctx.send(embed=embed)

@bot.command()
async def dice(ctx):
    import random
    result = random.randint(1, 6)
    embed = discord.Embed(title="🎲 Lancer de dé", description=f"Tu as obtenu : **{result}**", color=0x00ffff)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    import random
    result = random.choice(["Pile 🪙", "Face 💫"])
    embed = discord.Embed(title="🪙 Pile ou Face", description=f"Résultat : **{result}**", color=0x00ffff)
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="📊 Sondage", description=question, color=0x00ffff)
    embed.set_footer(text=f"Sondage par {ctx.author.name}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

# ==================== GESTION ERREURS ====================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu n'as pas les permissions pour cette commande.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membre introuvable.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant. Utilise `+help` pour voir comment utiliser cette commande.")
    else:
        await ctx.send(f"❌ Erreur : {str(error)}")

# ==================== LANCEMENT ====================

bot.run(TOKEN)
