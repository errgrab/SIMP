-- name: log_message(user_id, channel_id, message_id, chars, words, repeated_words)!
INSERT INTO log_message (user_id, channel_id, message_id, chars, words, repeated_words)
VALUES (:user_id, :channel_id, :message_id, :chars, :words, :repeated_words);

-- name: message_count_since(user_id, since)^
SELECT COUNT(*) AS count
FROM log_message
WHERE user_id = :user_id AND created_at >= :since;

-- name: word_stats_for_user(user_id)^
SELECT
	SUM(words) AS total_words,
	SUM(chars) AS total_chars,
	SUM(repeated_words) AS total_repeated
FROM log_message
WHERE user_id = :user_id;

-- name: activity_by_channel(user_id)
SELECT channel_id, COUNT(*) AS messages
FROM log_message
WHERE user_id = :user_id
GROUP BY channel_id
ORDER BY messages DESC;

-- name: log_mention(user_id, channel_id, message_id, target_id)!
INSERT INTO log_mention (user_id, channel_id, message_id, target_id)
VALUES (:user_id, :channel_id, :message_id, :target_id)
ON CONFLICT (message_id, target_id) DO NOTHING;

-- name: most_mentioned_by(user_id)^
SELECT target_id, COUNT(*) AS times
FROM log_mention
WHERE user_id = :user_id
GROUP BY target_id
ORDER BY times DESC
LIMIT 1;

-- name: mentions_received(user_id)^
SELECT COUNT(*) AS count
FROM log_mention
WHERE target_id = :user_id;

-- name: start_voice_session(user_id, channel_id, joined_at)$
-- Returns new row id to close out later
INSERT INTO log_voice (user_id, channel_id, joined_at, left_at, duration)
VALUES (:user_id, :channel_id, :joined_at, NULL, NULL);

-- name: end_voice_session(id, left_at)!
UPDATE log_voice
SET left_at = :left_at, duration = :left_at - joined_at
WHERE id = :id;

-- name: open_voice_sessions()
SELECT id, user_id, channel_id, joined_at
FROM log_voice
WHERE left_at IS NULL;

-- name: total_voice_time(user_id)^
SELECT COALESCE(SUM(duration), 0) AS total_seconds
FROM log_voice
WHERE user_id = :user_id;
