# このファイルの役割：collect.py が全センサーの値を読んで、DBに保存することを確認します（仕様書の第6・7章）。
#   collect.py を書くときの約束（このテストが前提にしていること）：
#   - テストからは collect.main(["--sensor", "bh1750"]) のように、コマンドの引数をリストで渡して呼ぶ（引数なしは []）
#   - config.HYDRO_USE_DUMMY・config.HYDRO_DB_PATH・sensors.DUMMY_SENSORS・sensors.PI_SENSORS は、
#     実行のたびに `config.〜`・`sensors.〜` の形で読む（テストが差し替えるため。`from 〜 import` で名前だけを取り込まない）
#   - HYDRO_DB_PATH に絶対パスが入っていても、そのまま使える（`config.BASE_DIR / config.HYDRO_DB_PATH` ならそうなる）
#   - 判定と通知（judge.py・notify.py）はまだ呼ばない

import logging
import sqlite3
import types
from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

from apps.hydroponics import collect, config, sensors

AIR_TEMP = {"metric": "air_temp", "label": "気温", "value": 21.3, "unit": "℃"}
HUMIDITY = {"metric": "humidity", "label": "湿度", "value": 55.0, "unit": "%"}
LIGHT = {"metric": "light", "label": "照度", "value": 1200.0, "unit": "lx"}

# 偽のセンサーの read() が呼ばれた順番（センサーのファイル名が入る）
READ_LOG = []


@pytest.fixture(autouse=True)
def db_path(monkeypatch, tmp_path):
    """DBをテスト用の一時フォルダに置き、ダミーセンサーを使う設定にする。"""
    path = tmp_path / "data" / "hydroponics.db"  # data フォルダはまだない
    monkeypatch.setattr(config, "HYDRO_DB_PATH", path)
    monkeypatch.setattr(config, "HYDRO_USE_DUMMY", True)
    monkeypatch.setattr(config, "HYDRO_DUMMY_SKIP_METRICS", [])
    READ_LOG.clear()
    return path


def make_sensor(name, values=(), error=None):
    """本物と同じく apps.hydroponics.sensors.<name> という名前を持つ、偽のセンサーを作る。"""
    sensor = types.ModuleType(f"apps.hydroponics.sensors.{name}")

    def read():
        READ_LOG.append(name)
        if error is not None:
            raise error
        return [dict(value) for value in values]

    sensor.read = read
    return sensor


def saved_rows(db_path):
    """sensor_readings に保存された値を、保存した順に辞書のリストで返す。"""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT metric, label, value, unit, measured_at FROM sensor_readings ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def table_columns(db_path, table):
    with closing(sqlite3.connect(db_path)) as conn:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def test_dummy_run_creates_the_db_and_saves_every_metric(db_path):
    collect.main([])
    assert {row["metric"] for row in saved_rows(db_path)} == {
        "water_temp", "air_temp", "humidity", "light", "water_level", "ec",
    }


def test_creates_both_tables_from_the_spec(db_path):
    collect.main([])
    assert table_columns(db_path, "sensor_readings") == [
        "id", "metric", "label", "value", "unit", "measured_at",
    ]
    assert table_columns(db_path, "notifications") == ["id", "kind", "message", "sent_at"]


def test_saves_what_read_returns(monkeypatch, db_path):
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [make_sensor("bme280", [AIR_TEMP, HUMIDITY])])
    collect.main([])
    rows = saved_rows(db_path)
    assert [{key: row[key] for key in ("metric", "label", "value", "unit")} for row in rows] == [
        AIR_TEMP, HUMIDITY,
    ]


def test_all_values_share_one_jst_time_on_the_minute(monkeypatch, db_path):
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [
        make_sensor("bme280", [AIR_TEMP, HUMIDITY]),
        make_sensor("bh1750", [LIGHT]),
    ])
    collect.main([])
    times = {row["measured_at"] for row in saved_rows(db_path)}
    assert len(times) == 1  # 1回の実行で保存する値は、すべて同じ計測時刻
    text = times.pop()
    measured_at = datetime.fromisoformat(text)
    assert measured_at.isoformat() == text  # 2026-11-02T09:00:00+09:00 の形
    assert measured_at.utcoffset() == timedelta(hours=9)
    assert (measured_at.second, measured_at.microsecond) == (0, 0)
    assert abs(datetime.now(timezone.utc) - measured_at) < timedelta(minutes=2)


def test_failing_sensor_is_logged_and_the_others_are_saved(monkeypatch, db_path, caplog):
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [
        make_sensor("bme280", [AIR_TEMP]),
        make_sensor("broken", error=OSError("I2Cの応答がない")),
        make_sensor("bh1750", [LIGHT]),
    ])
    collect.main([])  # 例外で止まらない
    assert [row["metric"] for row in saved_rows(db_path)] == ["air_temp", "light"]
    errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
    assert any("broken" in message for message in errors)  # どのセンサーが失敗したか分かる


def test_broken_value_from_one_sensor_does_not_stop_the_others(monkeypatch, db_path):
    # read() が約束と違う値（value が None）を返しても、そのセンサーだけの失敗として扱う
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [
        make_sensor("bh1750", [dict(LIGHT, value=None)]),
        make_sensor("bme280", [AIR_TEMP]),
    ])
    collect.main([])
    assert [row["metric"] for row in saved_rows(db_path)] == ["air_temp"]


def test_reads_each_sensor_once_in_registration_order(monkeypatch):
    # 水位とECが同時に通電しないよう、登録した順に1つずつ読む（仕様書の第5章）
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [
        make_sensor("water_level"), make_sensor("ec"), make_sensor("bh1750"),
    ])
    collect.main([])
    assert READ_LOG == ["water_level", "ec", "bh1750"]


def test_uses_pi_sensors_when_dummy_is_off(monkeypatch, db_path):
    monkeypatch.setattr(config, "HYDRO_USE_DUMMY", False)
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [make_sensor("dummy", [HUMIDITY])])
    monkeypatch.setattr(sensors, "PI_SENSORS", [make_sensor("bh1750", [LIGHT])])
    collect.main([])
    assert READ_LOG == ["bh1750"]
    assert [row["metric"] for row in saved_rows(db_path)] == ["light"]


def test_sensor_option_reads_only_that_sensor(monkeypatch, db_path):
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [
        make_sensor("bme280", [AIR_TEMP]),
        make_sensor("bh1750", [LIGHT]),
    ])
    collect.main(["--sensor", "bh1750"])
    assert READ_LOG == ["bh1750"]
    assert [row["metric"] for row in saved_rows(db_path)] == ["light"]


def test_unknown_sensor_name_stops_with_an_error(monkeypatch):
    # 打ち間違えに気づけるよう、何も測らずにエラーで終える（argparse の choices や parser.error を使うと SystemExit になる）
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [make_sensor("bme280", [AIR_TEMP])])
    with pytest.raises(SystemExit) as error:
        collect.main(["--sensor", "bme208"])
    assert error.value.code != 0
    assert READ_LOG == []


def test_each_run_adds_rows_without_deleting_old_ones(monkeypatch, db_path):
    monkeypatch.setattr(sensors, "DUMMY_SENSORS", [make_sensor("bh1750", [LIGHT])])
    collect.main([])
    collect.main([])
    assert len(saved_rows(db_path)) == 2
