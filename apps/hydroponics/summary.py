# このファイルの役割：
#   専用画面とダッシュボードの両方へ返す要約データを作ります。
#   今後、収集・保存処理を実装したら、ここからSQLiteの最新値と判定結果を読みます。
#   センサー未接続の段階では、正常値やダミー値を作らず「未計測」を返します。

from . import config


def current_stage():
    """今の生育段階。HYDRO_STAGE が知らない値なら label を None にして、パネルで設定の誤りを知らせる。"""
    return {"id": config.HYDRO_STAGE, "label": config.HYDRO_STAGE_LABELS.get(config.HYDRO_STAGE)}


def get_summary():
    """水耕栽培仕様書の要約形式で、現在の未計測状態を返す。"""
    return {
        "measured_at": None,
        "stale": True,
        "overall": "system",
        "actions": [],
        "items": [],
        "stage": current_stage(),
    }
