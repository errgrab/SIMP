import unittest

from db import Database


class DatabaseTest(unittest.TestCase):
    def test_core_economy_workflow(self) -> None:
        with Database() as db:
            db.insert("guilds", {"id": 1, "name": "Hotel", "cycle_length": 604800})
            group_id = db.insert("groups", {"guild_id": 1, "name": "Torre A"})
            db.insert(
                "users",
                {
                    "id": 10,
                    "guild_id": 1,
                    "group_id": group_id,
                    "nickname": "Ana",
                    "balance": 100,
                },
            )
            cycle_id = db.insert(
                "cycles", {"guild_id": 1, "started_at": 1, "status": "open"}
            )

            user = db.get("users", id=10, guild_id=1)
            self.assertEqual(dict(user), {
                "id": 10,
                "guild_id": 1,
                "group_id": group_id,
                "nickname": "Ana",
                "balance": 100,
                "reputation": 0,
                "status": "active",
            })
            self.assertEqual(db.get("cycles", id=cycle_id)["status"], "open")

    def test_filters_handle_null_and_require_safe_mutations(self) -> None:
        with Database() as db:
            db.insert("guilds", {"id": 1, "name": "Hotel", "cycle_length": 10})
            db.insert("users", {"id": 10, "guild_id": 1})
            self.assertEqual(len(db.select("users", filters={"group_id": None})), 1)
            with self.assertRaises(ValueError):
                db.update("users", {"nickname": "unsafe"})
            with self.assertRaises(ValueError):
                db.delete("users")


if __name__ == "__main__":
    unittest.main()
