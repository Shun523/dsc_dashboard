# このファイルの役割：
#   専用画面とダッシュボードの両方へ返す要約データを作ります（仕様書の第9章）。
#   DBから項目ごとの最新の値を読み、judge.py で状態と「今やること」を決めます。
#   DBにまだ値が1つもなければ、正常値やダミー値を作らず「未計測」を返します。

from contextlib import closing
from datetime import datetime

from . import config, db, judge


def current_stage():
    """今の生育段階。HYDRO_STAGE が知らない値なら label を None にして、パネルで設定の誤りを知らせる。"""
    return {"id": config.HYDRO_STAGE, "label": config.HYDRO_STAGE_LABELS.get(config.HYDRO_STAGE)}


def get_summary(now=None):
    """水耕栽培仕様書の要約形式で、今の状態を返す。"""
    now = now or datetime.now(judge.JST)
    with closing(db.connect()) as conn:
        latest = db.latest_readings(conn)
    if not latest:
        return {
            "measured_at": None,
            "stale": True,
            "overall": "system",
            "actions": [],
            "items": [],
            "stage": current_stage(),
        }
    return {**judge.judge(latest, now), "stage": current_stage()}
