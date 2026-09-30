import logging
import discord
import json

from db import Database
from models import User, VoiceSession, Message, Mention
from config import GUILD_ID
from debug_cog import DebugCog


log = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = discord.Bot(intents=intents)
db = Database("simp.db")
bot.add_cog(DebugCog(bot, db))

_open_voice_sessions: dict[int, VoiceSession] = {}


def word_repeat_count(content: str) -> int:
    words = content.strip().lower().split()
    seen = set()
    repeated = 0
    for w in words:
        if w in seen:
            repeated += 1
        else:
            seen.add(w)
    return repeated


async def reconcile_voice_sessions():
    now = int(discord.utils.utcnow().timestamp())
    connected: dict[int, discord.VoiceChannel] = {}
    guild = bot.get_guild(GUILD_ID)

    for vc in guild.voice_channels:
        for member in vc.members:
            if not member.bot:
                connected[member.id] = vc

    for session in VoiceSession.open_sessions(db):
        still_here = connected.get(session.user_id)
        member = guild.get_member(session.user_id)
        username = member.display_name

        if still_here and still_here.id == session.channel_id:
            _open_voice_sessions[session.user_id] = session
            connected.pop(session.user_id, None)
            log.info(f"Voice resumed: [{session.id}] {username} on {still_here.name}")
        else:
            session.end(db, left_at=now)
            log.info(f"Voice closed: [{session.id}] {username} (left_at approximated)")

    for user_id, vc in connected.items():
        member = vc.guild.get_member(user_id)
        User.upsert(db, id=user_id, nickname=member.display_name)
        session = VoiceSession.start(db, user_id=user_id, channel_id=vc.id, joined_at=now)
        _open_voice_sessions[user_id] = session
        log.info(f"Voice session started on reconnect: {member.display_name} on {vc.name}")


def close_all_voice_sessions():
    now = int(discord.utils.utcnow().timestamp())

    for user_id, session in list(_open_voice_sessions.items()):
        session.end(db, left_at=now)
        log.info(f"Voice closed on shutdown: [{session.id}] user {user_id}")
    _open_voice_sessions.clear()

    # segurança: se por algum motivo houver linhas abertas que o dict
    # local não tem (ex: bug, race condition), fecha elas também
    for session in VoiceSession.open_sessions(db):
        session.end(db, left_at=now)
        log.info(f"Voice closed on shutdown (orphan): [{session.id}]")


async def sync_guild_members():
    guild = bot.get_guild(GUILD_ID)
    members = [
        {"id": m.id, "nickname": m.display_name}
        async for m in guild.fetch_members(limit=None)
        if not m.bot
    ]
    db.sync_users(members=json.dumps(members))
    log.info(f"Synced {len(members)} members in {guild.name}")


@bot.event
async def on_ready():
    log.info(f"Bot logged in as: {bot.user}")
    await sync_guild_members()
    await reconcile_voice_sessions()


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild: return

    User.upsert(db, id=message.author.id, nickname=message.author.display_name)
    content = message.content
    words = content.split()

    Message.log(
        db,
        user_id=message.author.id,
        channel_id=message.channel.id,
        message_id=message.id,
        chars=len(content),
        words=len(words),
        repeated_words=word_repeat_count(content),
    )

    log.info(f"Message logged: {message.author.display_name}: chars: {len(content)}, words: {len(words)}, repeated: {word_repeat_count(content)}")

    targets = {m.id: m for m in message.mentions if not m.bot}

    ref = message.reference
    if ref and isinstance(ref.resolved, discord.Message):
        author = ref.resolved.author
        if not author.bot and author.id != message.author.id:
            targets[author.id] = author

    for member in targets.values():
        User.upsert(db, id=member.id, nickname=member.display_name)
        Mention.log(
            db,
            user_id=message.author.id,
            channel_id=message.channel.id,
            message_id=message.id,
            target_id=member.id,
        )
        log.info(f"Mention logged: {message.author.display_name} -> {member.display_name}")


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
):
    if member.bot: return

    now = int(discord.utils.utcnow().timestamp())

    if before.channel is not None and before.channel != after.channel:
        session = _open_voice_sessions.pop(member.id, None)
        if session:
            session.end(db, left_at=now)
            log.info(f"Voice logged: ending {member.display_name} on {before.channel.name}")

    if after.channel is not None and before.channel != after.channel:
        User.upsert(db, id=member.id, nickname=member.display_name)
        session = VoiceSession.start(
            db, user_id=member.id, channel_id=after.channel.id, joined_at=now
        )
        _open_voice_sessions[member.id] = session
        log.info(f"Voice logged: starting {member.display_name} on {after.channel.name}")

