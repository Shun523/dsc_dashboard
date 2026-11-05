# このファイルの役割：
#   ラズパイやセンサーがないPCで、本物の代わりにそれらしい値を返す偽のセンサーです。
#   本物のセンサーと同じ形の read() を持つので、collect.py からは区別せずに呼べます。
#   動作確認：ルートで `python -m apps.hydroponics.sensors.dummy` を実行すると結果が表示されます。

import random
from datetime import datetime

from apps.hydroponics import config

# 危険な値を返す確率（判定と通知を試すため。仕様書のH-3）
DANGER_RATE = 0.05

# 仮の満水位（cm）。キットを実測して config.py の HYDRO_FULL_LEVEL_CM が決まったら、そちらを使う
DUMMY_FULL_LEVEL_CM = 12.0


def read():
    """全項目のそれらしい値を返す。HYDRO_DUMMY_SKIP_METRICS に書いた項目は返さない。"""
    values = [
        # ふだんの範囲は仕様書の第6章の目安。危険な値は第8章の warn の範囲の外
        make_value("water_temp", "液温", "℃", normal=(15, 24), danger=(8.0, 29.5)),
        make_value("air_temp", "気温", "℃", normal=(15, 28)),
        make_value("humidity", "湿度", "%", normal=(40, 70)),
        make_light(),
        make_water_level(),
        make_value("ec", "EC", "mS/cm", normal=(1.1, 2.1), danger=(0.8, 2.8)),
    ]
    skip = config.HYDRO_DUMMY_SKIP_METRICS
    return [value for value in values if value["metric"] not in skip]


def make_value(metric, label, unit, normal, danger=None):
    """ふだんは normal の範囲の値を返し、ときどき danger の値（低い方か高い方）を返す。"""
    if danger is not None and random.random() < DANGER_RATE:
        value = random.choice(danger)
    else:
        value = random.uniform(*normal)
    return {"metric": metric, "label": label, "value": round(value, 2), "unit": unit}


def make_light():
    """昼（6時〜18時）は 0〜20000 lx、夜は 0 lx を返す。"""
    hour = datetime.now().hour
    lux = random.uniform(0, 20000) if 6 <= hour < 18 else 0.0
    return {"metric": "light", "label": "照度", "value": round(lux, 1), "unit": "lx"}


def make_water_level():
    """ふだんは満水位の 60〜100%、ときどき 40%（危険）の水位を cm で返す。"""
    full = config.HYDRO_FULL_LEVEL_CM or DUMMY_FULL_LEVEL_CM
    ratio = 0.4 if random.random() < DANGER_RATE else random.uniform(0.6, 1.0)
    return {"metric": "water_level", "label": "水位", "value": round(full * ratio, 1), "unit": "cm"}


if __name__ == "__main__":
    print(read())
