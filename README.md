# SIMP — Server Incentive & Metrics Platform

A Discord bot that turns server activity into a lightweight social economy: points, rent, leaderboards, and cycles built on top of raw activity logs (messages, mentions, voice time).

## How it works

SIMP observes everything that happens on the server and stores it in a local SQLite database. On a recurring **cycle**, the bot:

- Analyzes the accumulated logs and assigns points/values to players
- Deducts a "rent" amount from each player
- Publishes leaderboards and stats to the server
- Updates server-wide stats (rent collected, messages sent, call hours, total points, etc.)
- Starts the next cycle

Planned on top of this foundation:

- **Groups** — players can join groups that affect leaderboards and compete against each other
- **Events** — players can organize and participate in events for points and reputation
- **Game integrations** — Minecraft, VRChat, etc., tracked in-game for bonus points
- **Rich content bonuses** — posts with images, audio, video, or substantial text earn bonus points for artistic/educational value
- **Achievements** — per-player unlockable achievements
- **Cycle titles** — stat-based awards each cycle (e.g. "tagarela" for most messages, "exposed" for longest text, "dormiu?" for most time in call)

## Status

Early stage. Currently implemented: activity logging only (messages, mentions, voice sessions) and user syncing. The economy layer (points, rent, cycles, groups, achievements, events) is not built yet — logging is being finished first, as the foundation everything else depends on.

## Architecture

```
main.py          entrypoint — loop setup, schema init, graceful shutdown
bot.py           discord.Bot instance, event handlers (on_message, on_voice_state_update, etc.)
db.py            Database — connection + generic access to named SQL queries
models.py        active-record style models (User, Message, Mention, VoiceSession)
queries.py       loader/runner for named .sql queries (a small in-house aiosql alternative)
config.py        .env loader (DISCORD_TOKEN, GUILD_ID)
debug_cog.py      ephemeral slash commands for inspecting stored data during development
sql/
  schema.sql      table definitions
  queries/
    users.sql     named queries for the users table
    log.sql       named queries for message/mention/voice logs
```

### Design notes

- **Single dependency**: pycord only. No ORM, no aiosql — `queries.py` parses `-- name: query_name(params)suffix` comments out of `.sql` files and exposes them as callables, with `^`/`!`/`$`/none suffixes meaning "fetch one" / "execute" / "insert, return id" / "fetch all".
- **Models are active record**: e.g. `User.upsert(db, id=..., nickname=...)` returns a `User`, and instance methods like `user.add_balance(db, delta)` write to the db and update the in-memory object in the same call, so it never goes stale after a write.
- **Voice sessions** are tracked both in memory (`_open_voice_sessions`, for the running process) and in `log_voice` (nullable `left_at`/`duration` for open sessions). On startup, the bot reconciles the two: sessions still open in Discord are resumed, orphaned ones from a crash are closed out with an approximated end time.

## Setup

1. Create a `.env` file (not committed):
   ```
   DISCORD_TOKEN=your_bot_token
   GUILD_ID=your_guild_id
   ```
2. Install pycord:
   ```
   pip install py-cord
   ```
3. Run:
   ```
   python main.py
   ```

The database (`simp.db`) and its schema are created automatically on first run.

## Debug commands

While in development, `debug_cog.py` registers a set of ephemeral (private) slash commands scoped to `GUILD_ID` for inspecting stored data directly in Discord: `/stats`, `/messages`, `/channels`, `/voice`, `/top`. These are meant to be removed once the platform has real user-facing commands.
