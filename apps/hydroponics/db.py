# このファイルの役割：
#   水耕栽培のSQLite（data/hydroponics.db）への接続・テーブル作成・保存をまとめます。
#   collect.py のほか、今後作る check_stale.py・summary.py・seed_dummy.py も、DBはここの関数で開きます。
#   テーブルの形は仕様書の第7章です。

import sqlite3

from apps.hydroponics import config

# テーブルを作るSQL（仕様書の第7章のまま）。IF NOT EXISTS なので、何度実行しても今あるデータは消えない
SCHEMA = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    metric      TEXT NOT NULL,
    label       TEXT NOT NULL,
    value       REAL NOT NULL,
    unit        TEXT NOT NULL,
    measured_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_metric_time
    ON sensor_readings (metric, measured_at);

CREATE TABLE IF NOT EXISTS notifications (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    kind    TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_at TEXT NOT NULL
);
"""


def connect():
    """DBにつなぎ、テーブルがなければ作ってから接続を返す。使い終わったら呼び出した側で閉じる。"""
    path = config.BASE_DIR / config.HYDRO_DB_PATH
    # SQLiteはファイルは作るが、入れ物のフォルダ（data/）までは作らないので、先に作っておく
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def save_readings(conn, values, measured_at):
    """read() が返した形の値のリストに計測時刻を付けて、sensor_readings に保存する。"""
    rows = [
        (value["metric"], value["label"], value["value"], value["unit"], measured_at)
        for value in values
    ]
    # with conn: の中で保存すると、成功したら確定し、途中で失敗したらこの呼び出しの分を1件も残さずに取り消す
    with conn:
        conn.executemany(
            "INSERT INTO sensor_readings (metric, label, value, unit, measured_at)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
