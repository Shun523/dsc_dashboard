# このファイルの役割：
#   登録されたセンサーを順に読み、同じ計測時刻を付けてDBに保存します（仕様書の第6章）。cronで5分ごとに実行します。
#   実行：ルートで `python -m apps.hydroponics.collect`。1つだけ測るときは `--sensor bh1750` のように付ける。
#   判定（judge.py）と通知（notify.py）は、それぞれができてから collect() の最後に足します。
#   確認：`pytest apps/hydroponics/tests/test_collect.py`

import argparse
import logging
from contextlib import closing
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler

from apps.hydroponics import config, db, sensors

logger = logging.getLogger(__name__)

# 日本時間。夏時間がないので +9時間で固定する（ZoneInfo は Windows だと tzdata を別に入れる必要があるため）
JST = timezone(timedelta(hours=9))


def active_sensors():
    """HYDRO_USE_DUMMY に合わせて、ダミーか実センサーの一覧を返す。"""
    # テストが差し替えるので、ファイルの先頭で取り込まずに、ここで毎回 config.〜・sensors.〜 の形で読む
    if config.HYDRO_USE_DUMMY:
        return sensors.DUMMY_SENSORS
    return sensors.PI_SENSORS


def sensor_name(sensor):
    """センサーのファイル名を返す（例：apps.hydroponics.sensors.bh1750 なら "bh1750"）。"""
    # "." で区切ったうちの、最後の部分
    return sensor.__name__.split(".")[-1]


def now_minute():
    """今の日本時間を、秒を0にそろえた文字列で返す（例："2026-11-02T09:00:00+09:00"）。"""
    return datetime.now(JST).replace(second=0, microsecond=0).isoformat()


def collect(sensor_list):
    """sensor_list のセンサーを登録順に1つずつ読み、同じ計測時刻で保存する。"""
    # 1回の実行で保存する値は、すべて同じ計測時刻にする
    measured_at = now_minute()
    # closing を使うと、途中で何が起きても最後に必ず接続を閉じる
    with closing(db.connect()) as conn:
        for sensor in sensor_list:
            try:
                db.save_readings(conn, sensor.read(), measured_at)
            except Exception:
                # 失敗したセンサーの値は保存しない（0や前回の値で埋めない）。ログに残して次のセンサーへ進む
                logger.exception("センサー %s の読み取りか保存に失敗しました", sensor_name(sensor))


def setup_logging():
    """ログを logs/hydroponics.log に書く設定をする。"""
    log_dir = config.BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    # ファイルが1MBを超えたら hydroponics.log.1 などに名前を変えて、新しいファイルに書き始める（3世代まで残す）
    handler = RotatingFileHandler(
        log_dir / "hydroponics.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def main(argv=None):
    """コマンドの引数を読み、全センサー（--sensor を付けたらそのセンサーだけ）を測る。"""
    sensor_list = active_sensors()
    parser = argparse.ArgumentParser(description="センサーを読んで、DBに保存します。")
    # choices に一覧を渡すと、知らない名前を指定したときにエラーで止まる
    parser.add_argument(
        "--sensor",
        choices=[sensor_name(sensor) for sensor in sensor_list],
        help="このセンサーだけを1回測る（ファイル名で指定。例：bh1750）",
    )
    # argv はテストが渡す引数のリスト。None のときは、コマンドに付けた引数を使う
    args = parser.parse_args(argv)
    if args.sensor:
        sensor_list = [sensor for sensor in sensor_list if sensor_name(sensor) == args.sensor]
    # HYDRO_MANUAL_METRICS（ECを当番が手で測る場合）の扱いは、ECセンサーが決まってから足す
    collect(sensor_list)


if __name__ == "__main__":
    setup_logging()
    main()
