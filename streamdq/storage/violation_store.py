"""
Violation storage — SQLite (demo) and PostgreSQL (prod).
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from typing import Optional

from streamdq.rules.base import Violation


class ViolationStore:
    """
    Persist violations to SQLite (demo) or PostgreSQL (prod).

    Supports:
    - Batch inserts (efficient)
    - Buffered writes (F5-a: accumulates inserts, flushes every N records or N seconds)
    - Query by rule_id, entity_id, severity, time range
    - JSON serialization of details/expected/snapshot

    Usage:
        store = ViolationStore("sqlite")
        store.store_batch([violation1, violation2])
        results = store.query("SELECT * FROM violations WHERE rule_id = ?", ("SYN001",))
    """

    # F5-a: Buffer flush parameters
    _BUFFER_SIZE = 500   # Flush after this many accumulated violations
    _FLUSH_INTERVAL_SEC = 5.0  # Flush after this many seconds (timer-based)

    def __init__(self, backend: str = "sqlite", connection_str: str = None):
        self.backend = backend
        self._buffer: list = []   # F5-a: Accumulated rows pending flush
        self._last_flush_time = __import__("time").time()
        self._write_lock = __import__("threading").Lock()

        if backend == "sqlite":
            db_path = connection_str or "/tmp/streamdq_violations.db"
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_db()
        elif backend == "postgres":
            try:
                import psycopg2
            except ImportError:
                raise ImportError(
                    "psycopg2 required for PostgreSQL backend. "
                    "Install with: pip install psycopg2-binary"
                )
            self.conn = psycopg2.connect(connection_str or "")
            self._init_db_postgres()
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _init_db(self):
        """Initialize SQLite schema with optimized settings for write throughput."""
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=10000")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                rule_name TEXT,
                entity_id TEXT,
                entity_type TEXT,
                severity TEXT,
                violation_type TEXT,
                details TEXT,
                expected TEXT,
                record_snapshot TEXT,
                detected_at TEXT,
                processing_latency_ms REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                -- NG-eval-01: entity_index for ground-truth matching
                -- Injected anomalies carry entity_index; violations are matched to ground truth
                -- by joining violations.entity_index = ground_truth.entity_index
                entity_index TEXT
            )
        """)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rule_id ON violations(rule_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_id ON violations(entity_id)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_index ON violations(entity_index)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_detected_at ON violations(detected_at)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_severity ON violations(severity)"
        )
        self.conn.commit()

    def _init_db_postgres(self):
        """Initialize PostgreSQL schema."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id SERIAL PRIMARY KEY,
                rule_id TEXT NOT NULL,
                rule_name TEXT,
                entity_id TEXT,
                entity_type TEXT,
                severity TEXT,
                violation_type TEXT,
                details JSONB,
                expected JSONB,
                record_snapshot JSONB,
                detected_at TIMESTAMP,
                processing_latency_ms REAL,
                created_at TIMESTAMP DEFAULT NOW(),
                -- NG-eval-01: entity_index for ground-truth matching
                entity_index TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rule_id ON violations(rule_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_id ON violations(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_index ON violations(entity_index)")
        self.conn.commit()
        cursor.close()

    REQUIRED_VIOLATION_FIELDS = ("rule_id", "entity_id", "entity_type", "severity", "violation_type")

    def store(self, violation: Violation):
        """Store a single violation."""
        self.store_batch([violation])

    def store_batch(self, violations: list[Violation]):
        """Store a batch of violations with buffered writes (F5-a).

        NG-22: Validates required fields before buffering. Violations missing
        required fields (rule_id, entity_id, entity_type, severity, violation_type)
        are logged and skipped — prevents NOT NULL constraint failures in SQLite/PostgreSQL.

        Accumulates rows in memory and flushes to disk when:
        - Buffer reaches _BUFFER_SIZE (500 records), OR
        - Time since last flush exceeds _FLUSH_INTERVAL_SEC (5 seconds)
        """
        if not violations:
            return

        for v in violations:
            # NG-22: Validate required fields before buffering
            for field in self.REQUIRED_VIOLATION_FIELDS:
                if getattr(v, field, None) is None:
                    import logging
                    logging.warning(
                        f"[ViolationStore] Skipping violation with missing required field "
                        f"{field}: rule={getattr(v, 'rule_id', None)}, "
                        f"entity={getattr(v, 'entity_id', None)}"
                    )
                    break
            else:
                self._buffer.append((
                    v.rule_id,
                    v.rule_name,
                    v.entity_id,
                    v.entity_type,
                    v.severity,
                    v.violation_type,
                    json.dumps(v.details),
                    json.dumps(v.expected),
                    json.dumps(v.record_snapshot),
                    v.detected_at.isoformat() if v.detected_at else None,
                    v.processing_latency_ms,
                    getattr(v, "entity_index", None),  # NG-eval-01: ground-truth index
                ))

        self._maybe_flush()

    def _maybe_flush(self):
        """Flush buffer if size threshold or time threshold reached."""
        import time
        now = time.time()
        should_flush = (
            len(self._buffer) >= self._BUFFER_SIZE
            or (self._buffer and (now - self._last_flush_time) >= self._FLUSH_INTERVAL_SEC)
        )
        if should_flush:
            self._flush()

    def _flush(self):
        """Write buffered rows to database."""
        if not self._buffer:
            return
        import time
        rows = self._buffer
        self._buffer = []
        self._last_flush_time = time.time()
        with self._write_lock:
            if self.backend == "sqlite":
                self.conn.executemany("""
                    INSERT INTO violations
                        (rule_id, rule_name, entity_id, entity_type, severity,
                         violation_type, details, expected, record_snapshot,
                         detected_at, processing_latency_ms, entity_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)
                self.conn.commit()
            else:
                # NG-eval-01: PostgreSQL uses JSONB for details/expected/snapshot
                # entity_index is a plain TEXT column
                self.conn.executemany("""
                    INSERT INTO violations
                        (rule_id, rule_name, entity_id, entity_type, severity,
                         violation_type, details, expected, record_snapshot,
                         detected_at, processing_latency_ms, entity_index)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                """, rows)
                self.conn.commit()

    def query(
        self,
        sql: str,
        params: tuple = (),
        limit: int = 1000,
    ) -> list[dict]:
        """
        Execute a SQL query and return results as list of dicts.
        Flushes pending writes first to ensure consistent reads.
        """
        self._flush()
        cursor = self.conn.execute(sql, params)
        rows = cursor.fetchmany(limit)
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(cols, row)) for row in rows]

    def count(self, where: str = "", params: tuple = ()) -> int:
        """Count violations matching optional WHERE clause. Flushes pending writes first."""
        self._flush()
        sql = f"SELECT COUNT(*) FROM violations {where}".strip()
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else 0

    def get_summary(self) -> dict:
        """Get a summary of all violations. Flushes pending writes first."""
        self._flush()  # Ensure buffered writes are persisted before reading
        total = self.count()
        by_rule = self.query("""
            SELECT rule_id, COUNT(*) as count
            FROM violations
            GROUP BY rule_id
            ORDER BY count DESC
        """)
        by_severity = self.query("""
            SELECT severity, COUNT(*) as count
            FROM violations
            GROUP BY severity
        """)
        by_type = self.query("""
            SELECT violation_type, COUNT(*) as count
            FROM violations
            GROUP BY violation_type
        """)
        return {
            "total": total,
            "by_rule": {r["rule_id"]: r["count"] for r in by_rule},
            "by_severity": {r["severity"]: r["count"] for r in by_severity},
            "by_type": {r["violation_type"]: r["count"] for r in by_type},
        }

    def close(self):
        """Flush remaining buffer and close the database connection."""
        self._flush()
        self.conn.close()
