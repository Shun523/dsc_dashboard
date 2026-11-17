# このファイルの役割：
#   項目ごとの最新の値から、状態（正常・注意・危険・欠測・センサー異常）と「今やること」を決めます（仕様書の第8章）。
#   基準値と対処の文は config.py の HYDRO_THRESHOLDS・HYDRO_ADVICE などに書きます。ここは数字を持ちません。
#   補給量の計算（水や液肥を何L・何mL足すか）はまだ作っていません。今は「目で確認して」の文を出します。

from datetime import datetime, timedelta, timezone

from apps.hydroponics import config

JST = timezone(timedelta(hours=9))

# 「今やること」を並べる順番。危険を先に出す
LEVEL_ORDER = {"danger": 0, "system": 1, "warn": 2}


def judge(latest, now):
    """
    latest：項目名 → DBの最新の行（metric・label・value・unit・measured_at）の辞書
    now：今の時刻（タイムゾーン付き）
    パネルの要約データのうち、measured_at・stale・overall・actions・items を返す。
    """
    stage_ok = config.HYDRO_STAGE in config.HYDRO_WATER_LEVEL_BY_STAGE
    items = [make_item(metric, latest.get(metric), now) for metric in shown_metrics(latest)]

    # 判定の順番：欠測（make_item で決めた）→ センサー異常 → 基準値
    # ECは液温で補正するので、液温の状態が決まってから最後に判定する
    by_metric = {item["metric"]: item for item in items}
    actions = []
    for item in sorted(items, key=lambda i: i["metric"] == "ec"):
        if item["status"] != "pending":
            continue
        row = latest[item["metric"]]
        if is_insane(item["metric"], row["value"]):
            item["status"] = "sensor_error"
            actions.append(action("system", f"{row['label']}センサーの値が異常です（{value_text(row)}）。配線を確認してください"))
        elif item["metric"] == "ec" and not readable(by_metric.get("water_temp")):
            item["status"] = "sensor_error"
            actions.append(action("system", "液温が読めないため、ECを判定できません。液温センサーを確認してください"))
        else:
            item["status"], direction = range_status(item["metric"], row["value"], stage_ok)
            if item["status"] in ("warn", "danger"):
                actions.append(action(item["status"], out_of_range_text(row, direction)))

    stale_items = [item for item in items if item["status"] == "stale"]
    all_stale = bool(items) and len(stale_items) == len(items)
    if all_stale:
        actions = [action("system", "データが届いていません。ラズパイと配線を確認してください")]
    else:
        actions += [action("system", stale_text(item, now)) for item in stale_items]
    if not stage_ok:
        actions.append(action("system", "生育段階の設定（HYDRO_STAGE）が正しくありません"))

    # 値を返すのは、欠測でない項目だけ（古い値を最新のように見せない）
    for item in items:
        if item["status"] == "stale":
            item["value"] = None

    times = [item["measured_at"] for item in items if item["measured_at"]]
    return {
        "measured_at": max(times, key=datetime.fromisoformat) if times else None,
        "stale": all_stale,
        "overall": overall(items, stage_ok),
        "actions": sorted(actions, key=lambda a: LEVEL_ORDER[a["level"]]),
        "items": items,
    }


def shown_metrics(latest):
    """パネルに出す項目。値があるか、届くはずの項目だけを HYDRO_PANEL_METRICS の順に並べる。"""
    return [
        metric for metric in config.HYDRO_PANEL_METRICS
        if metric in latest or metric in config.HYDRO_EXPECTED_METRICS
    ]


def make_item(metric, row, now):
    """1項目分の表示データを作る。欠測ならここで決め、それ以外は pending（あとで判定）にする。"""
    if row is None:
        info = config.HYDRO_METRICS.get(metric, {"label": metric, "unit": ""})
        return {"metric": metric, "label": info["label"], "value": None, "unit": info["unit"],
                "measured_at": None, "status": "stale"}
    limit = (timedelta(hours=config.HYDRO_MANUAL_STALE_HOURS) if metric in config.HYDRO_MANUAL_METRICS
             else timedelta(minutes=config.HYDRO_STALE_MINUTES))
    too_old = now - datetime.fromisoformat(row["measured_at"]) > limit
    return {"metric": metric, "label": row["label"], "value": row["value"], "unit": row["unit"],
            "measured_at": row["measured_at"], "status": "stale" if too_old else "pending"}


def readable(item):
    """その項目の値が使えるか（あって、欠測でもセンサー異常でもない）。"""
    return item is not None and item["status"] not in ("stale", "sensor_error")


def is_insane(metric, value):
    low, high = config.HYDRO_SANITY.get(metric, (float("-inf"), float("inf")))
    return not low <= value <= high


def range_status(metric, value, stage_ok):
    """基準値と比べて (状態, 向き) を返す。向きは高すぎるなら "high"、低すぎるなら "low"。"""
    if metric == "water_level":
        return water_level_status(value, stage_ok)
    if metric == "ec":
        limits = config.HYDRO_EC_BY_STAGE.get(config.HYDRO_STAGE) if stage_ok else None
    else:
        limits = config.HYDRO_THRESHOLDS.get(metric)
    if not limits:
        return "none", None
    ok_low, ok_high = limits["ok"]
    warn_low, warn_high = limits["warn"]
    direction = "high" if value > ok_high else "low"
    if ok_low <= value <= ok_high:
        return "ok", None
    if warn_low <= value <= warn_high:
        return "warn", direction
    return "danger", direction


def water_level_status(cm, stage_ok):
    """水位は満水位に対する%で、今の段階の下限と比べる。目標より高くても注意にしない。"""
    if not stage_ok or not config.HYDRO_FULL_LEVEL_CM:
        return "none", None
    limits = config.HYDRO_WATER_LEVEL_BY_STAGE[config.HYDRO_STAGE]
    percent = full_percent(cm)
    if percent >= limits["ok_min"]:
        return "ok", None
    if percent >= limits["warn_min"]:
        return "warn", "low"
    return "danger", "low"


def full_percent(cm):
    return cm * 100 / config.HYDRO_FULL_LEVEL_CM


def value_text(row):
    """「27.1℃」「1.05 mS/cm」のように、値と単位を文にする（ECは小数点以下2桁）。"""
    number = f"{row['value']:.2f}" if row["metric"] == "ec" else f"{row['value']:.1f}"
    joined = row["unit"] in ("℃", "%", "cm")
    return f"{number}{row['unit']}" if joined else f"{number} {row['unit']}"


def out_of_range_text(row, direction):
    word = "高い" if direction == "high" else "低い"
    shown = value_text(row)
    if row["metric"] == "water_level":
        shown += f"、満水の{full_percent(row['value']):.0f}%"
    advice = config.HYDRO_ADVICE.get(row["metric"], {}).get(direction, "様子を確認してください")
    return f"{row['label']}が{word}（{shown}）。{advice}"


def stale_text(item, now):
    if item["measured_at"] is None:
        return f"{item['label']}の値が届いていません。センサーと配線を確認してください"
    return (f"{item['label']}の値が届いていません（最後の計測 {last_time(item['measured_at'], now)}）。"
            "センサーと配線を確認してください")


def last_time(measured_at, now):
    """最後の計測時刻を「14:14」、今日でなければ「11/16 14:30」の形にする。"""
    moment = datetime.fromisoformat(measured_at).astimezone(JST)
    same_day = moment.date() == now.astimezone(JST).date()
    return moment.strftime("%H:%M") if same_day else moment.strftime("%m/%d %H:%M")


def overall(items, stage_ok):
    """全体の状態：危険 → システム異常（欠測・センサー異常・段階の設定ミス）→ 注意 → 正常 の順に決める。"""
    statuses = {item["status"] for item in items}
    if "danger" in statuses:
        return "danger"
    if statuses & {"stale", "sensor_error"} or not stage_ok:
        return "system"
    if "warn" in statuses:
        return "warn"
    return "ok"


def action(level, text):
    return {"level": level, "text": text}
