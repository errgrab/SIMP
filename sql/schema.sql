PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS users (
	id				INTEGER PRIMARY KEY, -- discord user_id

	nickname		TEXT,

	lvl				INTEGER NOT NULL DEFAULT 0,
	balance			INTEGER NOT NULL DEFAULT 0,
	reputation		INTEGER NOT NULL DEFAULT 0,

	status			TEXT NOT NULL
					DEFAULT 'active'
					CHECK (status IN ('active', 'debt', 'inactive', 'frozen'))
);

CREATE TABLE IF NOT EXISTS log_message (
	id				INTEGER PRIMARY KEY,
	user_id			INTEGER NOT NULL REFERENCES users(id),
	channel_id		INTEGER NOT NULL, -- discord channel_id
	message_id		INTEGER NOT NULL UNIQUE, -- discord message_id

	chars			INTEGER NOT NULL CHECK (chars >= 0),
	words			INTEGER NOT NULL CHECK (words >= 0),
	repeated_words	INTEGER NOT NULL DEFAULT 0 CHECK (repeated_words >= 0),
	image			BOOLEAN NOT NULL DEFAULT 0,

	created_at		INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS log_mention (
	id				INTEGER PRIMARY KEY,
	user_id			INTEGER NOT NULL REFERENCES users(id),
	channel_id		INTEGER NOT NULL, -- discord channel_id
	message_id		INTEGER NOT NULL, -- discord message_id

	target_id		INTEGER NOT NULL REFERENCES users(id),

	created_at		INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),

	UNIQUE (message_id, target_id)
);

CREATE TABLE IF NOT EXISTS log_voice (
	id				INTEGER PRIMARY KEY,
	user_id			INTEGER NOT NULL REFERENCES users(id),
	channel_id		INTEGER NOT NULL, -- discord channel_id

	joined_at		INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
	left_at 		INTEGER,
	duration		INTEGER CHECK (duration IS NULL OR duration >= 0)
);
