import discord

from config import GUILD_ID
from models import User, Message, Mention, VoiceSession
from db import Database


def fmt_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


class DebugCog(discord.Cog):
    def __init__(self, bot: discord.Bot, db: "Database"):
        self.bot = bot
        self.db = db

    @discord.slash_command(guild_ids=[GUILD_ID], description="[debug] Stats gerais de um usuário")
    async def stats(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        user = user or ctx.author
        u = User.get(self.db, user.id)
        if not u:
            return await ctx.respond("Usuário não está no db.", ephemeral=True)

        ws = Message.word_stats(self.db, user.id)
        voice = VoiceSession.total_time(self.db, user.id)
        received = Mention.received_count(self.db, user.id)
        top = Mention.most_mentioned_by(self.db, user.id)

        lines = [
            f"**{u.nickname}** (`{u.id}`)",
            f"balance: {u.balance} | reputation: {u.reputation} | status: {u.status}",
            f"palavras: {ws.total_words} | chars: {ws.total_chars} | repetidas: {ws.total_repeated}",
            f"call: {fmt_duration(voice)}",
            f"menções recebidas: {received}",
            f"mais mencionado por ele: " + (f"<@{top.target_id}> ({top.times}x)" if top else "ninguém"),
        ]
        await ctx.respond("\n".join(lines), ephemeral=True)

    @discord.slash_command(guild_ids=[GUILD_ID], description="[debug] Mensagens nas últimas N horas")
    async def messages(self, ctx: discord.ApplicationContext, hours: int = 24, user: discord.Member = None):
        user = user or ctx.author
        since = int(discord.utils.utcnow().timestamp()) - hours * 3600
        count = Message.count_since(self.db, user.id, since)
        await ctx.respond(f"{user.display_name}: **{count}** mensagens nas últimas {hours}h", ephemeral=True)

    @discord.slash_command(guild_ids=[GUILD_ID], description="[debug] Mensagens por canal")
    async def channels(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        user = user or ctx.author
        rows = Message.activity_by_channel(self.db, user.id)
        if not rows:
            return await ctx.respond("Sem mensagens.", ephemeral=True)
        text = "\n".join(f"<#{r.channel_id}>: {r.messages}" for r in rows[:15])
        await ctx.respond(text, ephemeral=True)

    @discord.slash_command(guild_ids=[GUILD_ID], description="[debug] Tempo em call")
    async def voice(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        user = user or ctx.author
        total = VoiceSession.total_time(self.db, user.id)
        await ctx.respond(f"{user.display_name}: **{fmt_duration(total)}** em call", ephemeral=True)

    @discord.slash_command(guild_ids=[GUILD_ID], description="[debug] Top usuários")
    @discord.option("by", choices=["balance", "reputation"], default="balance")
    async def top(self, ctx: discord.ApplicationContext, by: str, limit: int = 10):
        fn = User.top_by_balance if by == "balance" else User.top_by_reputation
        users = fn(self.db, limit)
        text = "\n".join(
            f"{i}. {u.nickname or u.id}: {getattr(u, by)}" for i, u in enumerate(users, 1)
        )
        await ctx.respond(text or "vazio", ephemeral=True)
