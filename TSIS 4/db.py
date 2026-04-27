"""
db.py
-----
PostgreSQL persistence layer using psycopg2.

If the database is unavailable (e.g. running locally without Postgres)
every public function degrades gracefully: saves are silently skipped and
reads return empty lists / None.  A single DB_AVAILABLE flag controls this.

Schema (auto-created on first connect):

    CREATE TABLE players (
        id       SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE game_sessions (
        id            SERIAL PRIMARY KEY,
        player_id     INTEGER REFERENCES players(id),
        score         INTEGER   NOT NULL,
        level_reached INTEGER   NOT NULL,
        played_at     TIMESTAMP DEFAULT NOW()
    );
"""

import datetime
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False

from config import DB_CONFIG

DB_AVAILABLE = False
_pool_conn = None   # single persistent connection (fine for a single-process game)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------
def connect():
    """Try to connect and create tables. Sets DB_AVAILABLE."""
    global DB_AVAILABLE, _pool_conn
    if not _PSYCOPG2_AVAILABLE:
        print("[db] psycopg2 not installed — running in offline mode")
        return False
    try:
        _pool_conn = psycopg2.connect(**DB_CONFIG)
        _pool_conn.autocommit = False
        _create_schema()
        DB_AVAILABLE = True
        print(f"[db] connected to {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
        return True
    except Exception as e:
        print(f"[db] connection failed ({e}) — running in offline mode")
        DB_AVAILABLE = False
        return False


@contextmanager
def _cursor():
    """Yield a cursor; commit on success, rollback on error."""
    if not DB_AVAILABLE or _pool_conn is None:
        raise RuntimeError("DB not available")
    cur = _pool_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
        _pool_conn.commit()
    except Exception:
        _pool_conn.rollback()
        raise
    finally:
        cur.close()


def close():
    global _pool_conn, DB_AVAILABLE
    if _pool_conn:
        try:
            _pool_conn.close()
        except Exception:
            pass
    _pool_conn = None
    DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------
def _create_schema():
    with _cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id       SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id            SERIAL PRIMARY KEY,
                player_id     INTEGER REFERENCES players(id),
                score         INTEGER   NOT NULL,
                level_reached INTEGER   NOT NULL,
                played_at     TIMESTAMP DEFAULT NOW()
            );
        """)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_or_create_player(username: str) -> int | None:
    """Return player id, creating the row if it doesn't exist yet."""
    if not DB_AVAILABLE:
        return None
    username = username.strip()[:50] or "Player"
    try:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) "
                "ON CONFLICT (username) DO NOTHING RETURNING id",
                (username,)
            )
            row = cur.fetchone()
            if row:
                return row["id"]
            # already existed — fetch it
            cur.execute("SELECT id FROM players WHERE username = %s", (username,))
            return cur.fetchone()["id"]
    except Exception as e:
        print(f"[db] get_or_create_player: {e}")
        return None


def save_session(player_id: int, score: int, level_reached: int) -> bool:
    """Insert a game_sessions row. Returns True on success."""
    if not DB_AVAILABLE or player_id is None:
        return False
    try:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) "
                "VALUES (%s, %s, %s)",
                (player_id, score, level_reached)
            )
        return True
    except Exception as e:
        print(f"[db] save_session: {e}")
        return False


def get_top10() -> list[dict]:
    """Return top 10 all-time scores as a list of dicts."""
    if not DB_AVAILABLE:
        return []
    try:
        with _cursor() as cur:
            cur.execute("""
                SELECT p.username,
                       gs.score,
                       gs.level_reached,
                       gs.played_at
                FROM   game_sessions gs
                JOIN   players p ON p.id = gs.player_id
                ORDER  BY gs.score DESC
                LIMIT  10
            """)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"[db] get_top10: {e}")
        return []


def get_personal_best(player_id: int) -> int:
    """Return the player's best score, or 0 if none."""
    if not DB_AVAILABLE or player_id is None:
        return 0
    try:
        with _cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) AS best "
                "FROM game_sessions WHERE player_id = %s",
                (player_id,)
            )
            return cur.fetchone()["best"]
    except Exception as e:
        print(f"[db] get_personal_best: {e}")
        return 0
