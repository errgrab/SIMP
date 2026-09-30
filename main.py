import logging
import signal

from bot import bot, db, close_all_voice_sessions
from config import DISCORD_TOKEN


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s): %(message)s"
)

log = logging.getLogger("main")


if __name__ == "__main__":
    db.init_schema()
    bot.run(DISCORD_TOKEN)
    close_all_voice_sessions()
