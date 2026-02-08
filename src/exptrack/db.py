from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Iterable


@dataclass
class Run:
    id: int
    name: str
    created_at: str
    tags: str
    notes: str
    config_json: str


@dataclass
class MetricPoint:
    id: int
    run_id: int
    name: str
    step: int
    value: float
    created_at: str


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    tags        TEXT NOT NULL DEFAULT '',
    notes       TEXT NOT NULL DEFAULT '',
    config_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    name        TEXT NOT NULL,
    step        INTEGER NOT NULL,
    value       REAL NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_run_name_step
ON metrics(run_id, name, step);
"""


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class ExperimentDB:
    def __init__(self, path: str):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)

    # ----------------
    # Runs
    # ----------------
    def create_run(
        self,
        name: str,
        tags: str = "",
        notes: str = "",
        config: Optional[dict[str, Any]] = None,
    ) -> int:
        config = config or {}
        config_json = json.dumps(config, ensure_ascii=False)
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs(name, created_at, tags, notes, config_json) VALUES (?, ?, ?, ?, ?)",
                (name, now_iso(), tags, notes, config_json),
            )
            return int(cur.lastrowid)

    def list_runs(self, limit: int = 50) -> list[Run]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at, tags, notes, config_json FROM runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Run(**dict(r)) for r in rows]

    def get_run(self, run_id: int) -> Optional[Run]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, name, created_at, tags, notes, config_json FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return Run(**dict(row)) if row else None

    def delete_run(self, run_id: int) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            return cur.rowcount > 0

    # ----------------
    # Metrics
    # ----------------
    def log_metric(self, run_id: int, name: str, step: int, value: float) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO metrics(run_id, name, step, value, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, name, int(step), float(value), now_iso()),
            )
            return int(cur.lastrowid)

    def list_metric_names(self, run_id: int) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT name FROM metrics WHERE run_id = ? ORDER BY name ASC",
                (run_id,),
            ).fetchall()
        return [r["name"] for r in rows]

    def get_metric_series(self, run_id: int, name: str) -> list[tuple[int, float]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT step, value FROM metrics WHERE run_id = ? AND name = ? ORDER BY step ASC",
                (run_id, name),
            ).fetchall()
        return [(int(r["step"]), float(r["value"])) for r in rows]

    def iter_metrics(self, run_id: int) -> Iterable[MetricPoint]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, run_id, name, step, value, created_at FROM metrics WHERE run_id = ? ORDER BY name, step",
                (run_id,),
            ).fetchall()
        for r in rows:
            yield MetricPoint(**dict(r))
