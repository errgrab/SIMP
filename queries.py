import re
import sqlite3
from pathlib import Path

# Matches: -- name: query_name
#          -- name: query_name(a, b, c)
#          -- name: query_name(a, b, c)^ / ! / $
_NAME_RE = re.compile(
    r"^--\s*name:\s*(\w+)\s*(?:\(([^)]*)\))?\s*([\^!$])?\s*$",
    re.MULTILINE,
)

_VALID_SUFFIXES = {"^", "!", "$", None}


def load_queries(sql_dir: str) -> dict[str, tuple[str, frozenset[str], str | None]]:
    """Parse all .sql files into {name: (sql_text, param_names, suffix)}."""
    queries = {}
    for path in Path(sql_dir).glob("*.sql"):
        text = path.read_text()
        matches = list(_NAME_RE.finditer(text))
        for i, m in enumerate(matches):
            name = m.group(1)
            raw_params = m.group(2)
            suffix = m.group(3)  # '^', '!', '$', or None

            params = (
                frozenset(p.strip() for p in raw_params.split(","))
                if raw_params
                else frozenset()
            )

            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()

            if name in queries:
                raise ValueError(f"Duplicate query name '{name}' in {path}")
            queries[name] = (body, params, suffix)
    return queries


class Queries:
    def __init__(self, sql_dir: str):
        self._queries = load_queries(sql_dir)

    def __getattr__(self, name: str):
        if name not in self._queries:
            raise AttributeError(f"No query named '{name}'")
        sql, expected_params, suffix = self._queries[name]

        def run(conn: sqlite3.Connection, **params):
            if set(params) != expected_params:
                missing = expected_params - set(params)
                extra = set(params) - expected_params
                parts = []
                if missing:
                    parts.append(f"missing: {sorted(missing)}")
                if extra:
                    parts.append(f"unexpected: {sorted(extra)}")
                raise TypeError(f"'{name}' param mismatch — {', '.join(parts)}")

            cur = conn.execute(sql, params)

            if suffix == "^":  # fetch one row or None
                row = cur.fetchone()
                conn.commit()
                return row
            elif suffix == "!":  # execute only, no return
                conn.commit()
                return None
            elif suffix == "$":  # insert, return new id
                conn.commit()
                return cur.lastrowid
            else:  # no suffix: fetch all rows
                rows = cur.fetchall()
                conn.commit()
                return rows

        return run
