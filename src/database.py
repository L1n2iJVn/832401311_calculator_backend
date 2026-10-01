"""计算历史的 SQLite 持久化层（数据层）。

只使用 Python 标准库自带的 :mod:`sqlite3`，因此本项目没有任何第三方
依赖。为了在 ``ThreadingHTTPServer`` 多线程环境下安全读写，所有数据库
操作都通过一把线程锁串行化。
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List


class Database:
    """对 calculation_history 表的一个轻量封装。"""

    def __init__(self, path: str) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calculation_history (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    result     TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def insert(self, expression: str, result: str) -> int:
        """插入一条历史记录并返回自增 id。"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            cursor = self._conn.execute(
                "INSERT INTO calculation_history (expression, result, created_at) "
                "VALUES (?, ?, ?)",
                (expression, result, created_at),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def list_all(self) -> List[Dict[str, Any]]:
        """返回全部历史记录（按 id 倒序，最新在前）。"""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT id, expression, result, created_at "
                "FROM calculation_history ORDER BY id DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete(self, record_id: int) -> int:
        """按 id 删除一条记录，返回受影响行数（0 表示不存在）。"""
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM calculation_history WHERE id = ?", (record_id,)
            )
            self._conn.commit()
            return cursor.rowcount

    def clear(self) -> int:
        """清空全部历史记录，返回删除的行数。"""
        with self._lock:
            cursor = self._conn.execute("DELETE FROM calculation_history")
            self._conn.commit()
            return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._conn.close()
