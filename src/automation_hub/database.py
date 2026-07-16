from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/automation_hub.db"))


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    finally:
        db.close()


def initialize() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('skill', 'mcp')),
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                endpoint TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                config_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                steps_json TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                output_json TEXT,
                error TEXT,
                FOREIGN KEY(workflow_id) REFERENCES workflows(id)
            );
            """
        )
        if db.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 0:
            db.executemany(
                """
                INSERT INTO resources(kind,name,description,endpoint,config_json)
                VALUES(?,?,?,?,?)
                """,
                [
                    ("skill", "Resumo executivo", "Converte conteúdo em decisões.", None,
                     json.dumps({"mode": "simulation"})),
                    ("mcp", "GitHub", "Acessa repositórios, issues e PRs.", "stdio://github",
                     json.dumps({"mode": "simulation"})),
                ],
            )


def rows(query: str, parameters: tuple = ()) -> list[dict]:
    with connection() as db:
        return [dict(row) for row in db.execute(query, parameters).fetchall()]
