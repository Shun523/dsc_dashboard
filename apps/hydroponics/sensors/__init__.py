# このファイルの役割：
#   使うセンサーの一覧です。センサーを足すときは、ここに import と1行を足します。
#   collect.py は、この一覧にあるセンサーの read() だけを順番に呼びます（フォルダの中を自動では探しません）。
#   どちらの一覧を使うかは .env の HYDRO_USE_DUMMY で切り替えます。

from apps.hydroponics.sensors import bh1750, bme280, dummy

# 開発用（ラズパイのないPC）。それらしい値を返すダミーセンサー
DUMMY_SENSORS = [dummy]

# ラズパイ用。read() ができて、ラズパイで動作確認できたものから足す
#   水位（water_level）：換算表ができるまで足さない（今は電圧×2.5 の仮の式で、cmではないため）
#   水温（water_temp）：read() ができて、センサーをつないで確かめてから足す
#   どれか1つが読めなくても、collect.py はほかのセンサーの保存を続ける
PI_SENSORS = [bme280, bh1750]
