# このファイルの役割：
#   水耕栽培アプリ専用の設定を置きます。ダッシュボードの設定は読みません。

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 単体起動時に「ダッシュボードに戻る」リンクを出したい場合のURL。
# 共通の入口（ルートの app.py）で動かす場合は空のままでよいです。
DASHBOARD_URL = os.getenv("HYDRO_DASHBOARD_URL", "")
PORT = int(os.getenv("HYDRO_PORT", "8001"))
SUMMARY_REFRESH_SECONDS = 60
FETCH_TIMEOUT_SECONDS = 10
IDLE_RETURN_SECONDS = 180

# true ならダミーセンサー、false なら実センサーの一覧を使う（ラズパイでは false にする）
HYDRO_USE_DUMMY = os.getenv("HYDRO_USE_DUMMY", "true").lower() == "true"
# ダミーセンサーが返さない項目。欠測の表示を確かめるときに ["ec"] のように書く
HYDRO_DUMMY_SKIP_METRICS = []
# 満水位（タンクの底からの高さ、cm）。キットを実測するまでは None
HYDRO_FULL_LEVEL_CM = None

# 生育段階。栽培リーダーが生育を見て .env の HYDRO_STAGE を書き換える（仕様書の第8・14章）
HYDRO_STAGE = os.getenv("HYDRO_STAGE", "germination").strip().lower()
# 生育段階ごとの、画面に出す名前
HYDRO_STAGE_LABELS = {"germination": "発芽まで", "seedling": "発芽〜本葉", "growing": "本葉〜収穫"}

# SQLiteファイルの場所。BASE_DIR（apps/hydroponics）からの相対パスで、cronとWebで同じファイルを使う
HYDRO_DB_PATH = "data/hydroponics.db"

# ---- 判定とパネル（仕様書の第8・9章）----

# 項目ごとの表示名と単位。まだ一度も値が届いていない項目をパネルに出すときに使う
HYDRO_METRICS = {
    "water_temp": {"label": "液温", "unit": "℃"},
    "air_temp": {"label": "気温", "unit": "℃"},
    "humidity": {"label": "湿度", "unit": "%"},
    "light": {"label": "照度", "unit": "lx"},
    "water_level": {"label": "水位", "unit": "cm"},
    "ec": {"label": "EC", "unit": "mS/cm"},
}
# 5分ごとに届くはずの項目。値が届かなければ「欠測」にする。センサーを PI_SENSORS に登録したら足す
HYDRO_EXPECTED_METRICS = list(HYDRO_METRICS) if HYDRO_USE_DUMMY else ["air_temp", "humidity", "light"]
# 手で間欠測定する項目（ECの電極を入れっぱなしにできない場合など）。欠測の判定を時間単位にする
HYDRO_MANUAL_METRICS = []
HYDRO_STALE_MINUTES = 15
HYDRO_MANUAL_STALE_HOURS = 36
# パネルと専用画面に出す項目と順番（ダッシュボードのパネルは先頭の4つまで）
HYDRO_PANEL_METRICS = ["water_temp", "ec", "water_level", "air_temp", "humidity", "light"]

# 項目ごとの基準値。ok の範囲内なら正常、ok の外でも warn の範囲内なら注意、warn の外なら危険（両端を含む）
# 担当者が自分の項目の基準値を決めたら、ここに1行足す。書いていない項目は判定しない（色も今やることも出さない）
# 水位とECは生育段階で変わるので、下の HYDRO_WATER_LEVEL_BY_STAGE・HYDRO_EC_BY_STAGE に書く
HYDRO_THRESHOLDS = {
    "water_temp": {"ok": (15, 25), "warn": (10, 28)},  # ℃。仮の値（水温の担当が確定する）
}
# 範囲を外れたときに「今やること」に出す対処の文。high は高すぎるとき、low は低すぎるとき
# パネルには「液温が高い（27.1℃）。」のあとに、この文が続く。書いていなければ「様子を確認してください」
HYDRO_ADVICE = {
    "water_temp": {"high": "遮光するか、窓から離してください", "low": "タンクを保温するか、窓から離してください"},
    "water_level": {"low": "量を計算できないため、目で確認して水を足してください"},
    "ec": {"high": "量を計算できないため、目で確認して水を足してください",
           "low": "量を計算できないため、目で確認して液肥を足してください"},
}
# 生育段階ごとのECの範囲（mS/cm）。None の段階は判定しない
HYDRO_EC_BY_STAGE = {
    "germination": None,
    "seedling": {"ok": (0.8, 1.2), "warn": (0.5, 1.5), "target": 1.0},
    "growing": {"ok": (1.2, 2.0), "warn": (1.0, 2.5), "target": 1.6},
}
# 生育段階ごとの水位。満水位（HYDRO_FULL_LEVEL_CM）に対する%で、下がりすぎだけを判定する（数字は仮）
HYDRO_WATER_LEVEL_BY_STAGE = {
    "germination": {"target": 100, "ok_min": 90, "warn_min": 80},
    "seedling": {"target": 100, "ok_min": 90, "warn_min": 80},
    "growing": {"target": 50, "ok_min": 40, "warn_min": 30},
}
# この範囲の外は、物理的にありえない値としてセンサー異常にする
HYDRO_SANITY = {
    "water_temp": (-10, 50),
    "air_temp": (-10, 50),
    "ec": (0.05, 10),
}
