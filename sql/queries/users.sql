-- name: upsert_user(id, nickname)!
-- Create a user if they don't exist yet
INSERT INTO users (id, nickname)
	VALUES (:id, :nickname)
	ON CONFLICT (id) DO UPDATE SET nickname = excluded.nickname
	WHERE users.nickname IS NOT excluded.nickname;

-- name: sync_users(members)!
-- Bulk upsert: members is a JSON array of {"id": int, "nickname": str}
INSERT INTO users (id, nickname)
SELECT json_extract(value, '$.id'), json_extract(value, '$.nickname')
FROM json_each(:members)
WHERE true
ON CONFLICT (id) DO UPDATE SET nickname = excluded.nickname;

-- name: get_user(id)^
SELECT * FROM users WHERE id = :id;

-- name: update_nickname(id, nickname)!
UPDATE users SET nickname = :nickname WHERE id = :id;

-- name: set_balance(id, balance)!
UPDATE users SET balance = :balance WHERE id = :id;

-- name: set_reputation(id, reputation)!
UPDATE users SET reputation = :reputation WHERE id = :id;

-- name: add_balance(id, delta)!
UPDATE users SET balance = balance + :delta WHERE id = :id;

-- name: add_reputation(id, delta)!
UPDATE users SET reputation = reputation + :delta WHERE id = :id;

-- name: set_status(id, status)!
UPDATE users SET status = :status WHERE id = :id;

-- name: top_balance(limit)
SELECT * FROM users ORDER BY balance DESC LIMIT :limit;

-- name: top_reputation(limit)
SELECT * FROM users ORDER BY reputation DESC LIMIT :limit;
