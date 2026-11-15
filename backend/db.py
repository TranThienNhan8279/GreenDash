"""Truy cập SQL Server bằng pyodbc. MỌI truy vấn dùng tham số (?), không ghép chuỗi."""
import os
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()


def _conn_str() -> str:
    cs = os.environ.get("GREENDASH_DB")
    if not cs:
        raise RuntimeError("Thiếu biến môi trường GREENDASH_DB (xem .env.example)")
    return cs


@contextmanager
def connect(autocommit: bool = False):
    import pyodbc            # import muộn để test hàm lõi không cần cài ODBC
    cn = pyodbc.connect(_conn_str(), autocommit=autocommit)
    try:
        yield cn
    finally:
        cn.close()


def query(sql: str, params: tuple = ()) -> list:
    with connect() as cn:
        cur = cn.cursor()
        cur.execute(sql, params)
        if cur.description is None:
            return []
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def execute(sql: str, params: tuple = ()) -> int:
    """Chạy một lệnh ghi, commit, trả số dòng bị ảnh hưởng."""
    with connect() as cn:
        cur = cn.cursor()
        cur.execute(sql, params)
        n = cur.rowcount
        cn.commit()
        return n


def call_proc(sql: str, params: tuple = ()) -> list:
    """Gọi thủ tục (thủ tục tự quản lý transaction nên dùng autocommit)."""
    with connect(autocommit=True) as cn:
        cur = cn.cursor()
        cur.execute(sql, params)
        if cur.description is None:
            return []
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
