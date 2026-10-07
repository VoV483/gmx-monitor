import sqlite3
from datetime import datetime, timezone


DB_FILE = "gmx_monitor.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Создаёт все таблицы, если их ещё нет.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS glv_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                glv_address TEXT NOT NULL,
                glv_name TEXT,
                total_assets_usd REAL NOT NULL,
                market_count INTEGER NOT NULL,
                active_market_count INTEGER NOT NULL,
                disabled_market_count INTEGER NOT NULL,
                top5_share REAL NOT NULL,
                top10_share REAL NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS glv_market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                market_address TEXT NOT NULL,
                balance_usd REAL NOT NULL,
                share_pct REAL NOT NULL,
                is_disabled INTEGER NOT NULL,
                FOREIGN KEY(snapshot_id)
                    REFERENCES glv_snapshots(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                snapshot_id INTEGER NOT NULL,

                market_address TEXT NOT NULL,
                market_name TEXT,

                glv_balance_usd REAL,
                glv_share_pct REAL,

                apy REAL,
                base_apy REAL,
                bonus_apr REAL,

                open_interest_long_usd REAL,
                open_interest_short_usd REAL,
                oi_long_share_pct REAL,
                oi_short_share_pct REAL,

                liquidity_long_usd REAL,
                liquidity_short_usd REAL,

                funding_long_raw TEXT,
                funding_short_raw TEXT,

                borrowing_long_raw TEXT,
                borrowing_short_raw TEXT,

                FOREIGN KEY(snapshot_id)
                    REFERENCES glv_snapshots(id)
            )
            """
        )

        conn.commit()


def save_glv_snapshot(glv):
    """
    Сохраняет общий snapshot GLV
    и состав рынков GLV.
    """

    markets = glv.get("markets", [])

    total_assets = sum(
        int(m.get("balanceUsd", 0))
        for m in markets
    ) / 1e30

    active_markets = [
        m
        for m in markets
        if not m.get("isDisabled", False)
    ]

    disabled_markets = [
        m
        for m in markets
        if m.get("isDisabled", False)
    ]

    sorted_markets = sorted(
        markets,
        key=lambda x: int(
            x.get("balanceUsd", 0)
        ),
        reverse=True,
    )

    top5_share = sum(
        int(m.get("share", 0))
        for m in sorted_markets[:5]
    ) / 1e30 * 100

    top10_share = sum(
        int(m.get("share", 0))
        for m in sorted_markets[:10]
    ) / 1e30 * 100

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO glv_snapshots (
                created_at,
                glv_address,
                glv_name,
                total_assets_usd,
                market_count,
                active_market_count,
                disabled_market_count,
                top5_share,
                top10_share
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                glv.get("glvToken"),
                glv.get("name"),
                total_assets,
                len(markets),
                len(active_markets),
                len(disabled_markets),
                top5_share,
                top10_share,
            ),
        )

        snapshot_id = cursor.lastrowid

        for market in markets:
            balance_usd = (
                int(market.get("balanceUsd", 0))
                / 1e30
            )

            share_pct = (
                int(market.get("share", 0))
                / 1e30
                * 100
            )

            cursor.execute(
                """
                INSERT INTO glv_market_snapshots (
                    snapshot_id,
                    market_address,
                    balance_usd,
                    share_pct,
                    is_disabled
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    market.get("address"),
                    balance_usd,
                    share_pct,
                    1
                    if market.get(
                        "isDisabled",
                        False,
                    )
                    else 0,
                ),
            )

        conn.commit()

    return snapshot_id


def save_market_metrics(
    snapshot_id,
    metrics,
):
    """
    Сохраняет market-level метрики
    для всех рынков GLV.
    """

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        for item in metrics:
            cursor.execute(
                """
                INSERT INTO market_metrics (
                    created_at,
                    snapshot_id,
                    market_address,
                    market_name,
                    glv_balance_usd,
                    glv_share_pct,
                    apy,
                    base_apy,
                    bonus_apr,
                    open_interest_long_usd,
                    open_interest_short_usd,
                    oi_long_share_pct,
                    oi_short_share_pct,
                    liquidity_long_usd,
                    liquidity_short_usd,
                    funding_long_raw,
                    funding_short_raw,
                    borrowing_long_raw,
                    borrowing_short_raw
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    created_at,
                    snapshot_id,
                    item.get("market_address"),
                    item.get("market_name"),
                    item.get("glv_balance_usd"),
                    item.get("glv_share_pct"),
                    item.get("apy"),
                    item.get("base_apy"),
                    item.get("bonus_apr"),
                    item.get(
                        "open_interest_long_usd"
                    ),
                    item.get(
                        "open_interest_short_usd"
                    ),
                    item.get(
                        "oi_long_share_pct"
                    ),
                    item.get(
                        "oi_short_share_pct"
                    ),
                    item.get(
                        "liquidity_long_usd"
                    ),
                    item.get(
                        "liquidity_short_usd"
                    ),
                    item.get(
                        "funding_long_raw"
                    ),
                    item.get(
                        "funding_short_raw"
                    ),
                    item.get(
                        "borrowing_long_raw"
                    ),
                    item.get(
                        "borrowing_short_raw"
                    ),
                ),
            )

        conn.commit()


def get_last_two_snapshots(
    glv_address,
):
    """
    Возвращает два последних snapshot GLV.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM glv_snapshots
            WHERE lower(glv_address) = lower(?)
            ORDER BY id DESC
            LIMIT 2
            """,
            (glv_address,),
        )

        return cursor.fetchall()


def get_market_snapshots(
    snapshot_id,
):
    """
    Возвращает состав рынков
    конкретного snapshot.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM glv_market_snapshots
            WHERE snapshot_id = ?
            """,
            (snapshot_id,),
        )

        return cursor.fetchall()


def get_market_metrics_count():
    """
    Сколько всего market-level записей
    накоплено в SQLite.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM market_metrics
            """
        )

        return cursor.fetchone()[0]

def get_latest_glv_snapshot(
    glv_address,
):
    """
    Последний snapshot GLV.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM glv_snapshots
            WHERE lower(glv_address) = lower(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (glv_address,),
        )

        return cursor.fetchone()


def get_glv_snapshot_before(
    glv_address,
    before_time,
):
    """
    Последний snapshot,
    сделанный до указанного времени.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM glv_snapshots
            WHERE lower(glv_address) = lower(?)
              AND created_at <= ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                glv_address,
                before_time,
            ),
        )

        return cursor.fetchone()


def get_market_metrics_for_snapshot(
    snapshot_id,
):
    """
    Все market metrics
    конкретного snapshot.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM market_metrics
            WHERE snapshot_id = ?
            ORDER BY glv_balance_usd DESC
            """,
            (snapshot_id,),
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]