from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db import Database

@dataclass(slots=True)
class User:
    id: int
    nickname: str | None
    balance: int
    reputation: int
    status: str

    @classmethod
    def _from_row(cls, row: tuple) -> "User":
        return cls(id=row[0], nickname=row[1], balance=row[2], reputation=row[3], status=row[4])

    @classmethod
    def get(cls, db: "Database", id: int) -> "User | None":
        row = db.get_user(id=id)
        return cls._from_row(row) if row else None

    @classmethod
    def upsert(cls, db: "Database", id: int, nickname: str | None) -> None:
        db.upsert_user(id=id, nickname=nickname)

    @classmethod
    def top_by_balance(cls, db: "Database", limit: int = 10) -> list["User"]:
        rows = db.top_balance(limit=limit)
        return [cls._from_row(r) for r in rows]

    @classmethod
    def top_by_reputation(cls, db: "Database", limit: int = 10) -> list["User"]:
        rows = db.top_reputation(limit=limit)
        return [cls._from_row(r) for r in rows]

    def set_nickname(self, db: "Database", nickname: str | None) -> None:
        db.update_nickname(id=self.id, nickname=nickname)
        self.nickname = nickname

    def set_balance(self, db: "Database", balance: int) -> None:
        db.set_balance(id=self.id, balance=balance)
        self.balance = balance

    def set_reputation(self, db: "Database", reputation: int) -> None:
        db.set_reputation(id=self.id, reputation=reputation)
        self.reputation = reputation

    def add_balance(self, db: "Database", delta: int) -> None:
        db.add_balance(id=self.id, delta=delta)
        self.balance += delta

    def add_reputation(self, db: "Database", delta: int) -> None:
        db.add_reputation(id=self.id, delta=delta)
        self.reputation += delta

    def set_status(self, db: "Database", status: str) -> None:
        db.set_status(id=self.id, status=status)
        self.status = status


@dataclass(slots=True)
class WordStats:
    total_chars: int
    total_words: int
    total_repeated: int

@dataclass(slots=True)
class ChannelActivity:
    channel_id: int
    messages: int

class Message:
    @staticmethod
    def log(db: "Database", user_id: int, channel_id: int, message_id: int,
            chars: int, words: int, repeated_words: int) -> None:
        db.log_message(user_id=user_id, channel_id=channel_id,
                       message_id=message_id, chars=chars, words=words,
                       repeated_words=repeated_words)
    @staticmethod
    def count_since(db: "Database", user_id: int, since: int) -> int:
        return db.message_count_since(user_id=user_id, since=since)[0]

    @staticmethod
    def word_stats(db: "Database", user_id: int) -> WordStats:
        row = db.word_stats_for_user(user_id=user_id)
        return WordStats(row[0] or 0, row[1] or 0, row[2] or 0)

    @staticmethod
    def activity_by_channel(db: "Database", user_id: int) -> list[ChannelActivity]:
        return [ChannelActivity(*r) for r in db.activity_by_channel(user_id=user_id)]


@dataclass(slots=True)
class MentionCount:
    target_id: int
    times: int

class Mention:
    @staticmethod
    def log(db: "Database", user_id: int, channel_id: int,
            message_id: int, target_id: int) -> None:
        db.log_mention(
            user_id=user_id, channel_id=channel_id,
            message_id=message_id, target_id=target_id,
        )

    @staticmethod
    def most_mentioned_by(db: "Database", user_id: int) -> MentionCount | None:
        row = db.most_mentioned_by(user_id=user_id)
        return MentionCount(*row) if row else None

    @staticmethod
    def received_count(db: "Database", user_id: int) -> int:
        return db.mentions_received(user_id=user_id)[0]


@dataclass(slots=True)
class VoiceSession:
    id: int
    user_id: int
    channel_id: int
    joined_at: int
    left_at: int | None = None
    duration: int | None = None

    @classmethod
    def _from_row(cls, row: tuple) -> "VoiceSession":
        return cls(id=row[0], user_id=row[1], channel_id=row[2], joined_at=row[3], left_at=row[4], duration=row[5])

    @classmethod
    def _from_open_row(cls, row: tuple) -> "VoiceSession":
        return cls(id=row[0], user_id=row[1], channel_id=row[2], joined_at=row[3])

    @classmethod
    def open_sessions(cls, db: "Database") -> list["VoiceSession"]:
        rows = db.open_voice_sessions()
        return [cls._from_open_row(r) for r in rows]

    @classmethod
    def start(cls, db: "Database", user_id: int, channel_id: int, joined_at: int) -> "VoiceSession":
        row_id = db.start_voice_session(user_id=user_id, channel_id=channel_id, joined_at=joined_at)
        return cls(id=row_id, user_id=user_id, channel_id=channel_id, joined_at=joined_at)

    def end(self, db: "Database", left_at: int) -> None:
        db.end_voice_session(id=self.id, left_at=left_at)
        self.left_at = left_at
        self.duration = left_at - self.joined_at

    def total_time(db: "Database", user_id: int) -> int:
        return db.total_voice_time(user_id=user_id)[0]

