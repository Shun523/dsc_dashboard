# このファイルの役割：judge.py が、項目ごとの最新の値から状態と「今やること」を決めることを確認します（仕様書の第8章）。
#   judge.judge(latest, now) に、DBから読んだ形の最新の値（項目名 → 行）と今の時刻を渡して確かめます。
#   設定（config）はテストの中で差し替え、ラズパイやDBがなくても動くようにしています。

from datetime import datetime, timedelta, timezone

import pytest

from apps.hydroponics import config, judge

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 11, 17, 14, 30, tzinfo=JST)


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    """判定に使う設定を、このテスト用の値に固定する。"""
    monkeypatch.setattr(config, "HYDRO_STAGE", "growing")
    monkeypatch.setattr(config, "HYDRO_PANEL_METRICS",
                        ["water_temp", "ec", "water_level", "air_temp", "humidity", "light"])
    monkeypatch.setattr(config, "HYDRO_EXPECTED_METRICS", [])
    monkeypatch.setattr(config, "HYDRO_MANUAL_METRICS", [])
    monkeypatch.setattr(config, "HYDRO_STALE_MINUTES", 15)
    monkeypatch.setattr(config, "HYDRO_MANUAL_STALE_HOURS", 36)
    monkeypatch.setattr(config, "HYDRO_FULL_LEVEL_CM", 20.0)
    monkeypatch.setattr(config, "HYDRO_THRESHOLDS", {"water_temp": {"ok": (15, 25), "warn": (10, 28)}})
    monkeypatch.setattr(config, "HYDRO_ADVICE", {
        "water_temp": {"high": "遮光するか、窓から離してください", "low": "タンクを保温するか、窓から離してください"},
        "water_level": {"low": "量を計算できないため、目で確認して水を足してください"},
        "ec": {"high": "量を計算できないため、目で確認して水を足してください",
               "low": "量を計算できないため、目で確認して液肥を足してください"},
    })


def row(metric, value, minutes_ago=0):
    """DBの最新の行と同じ形を作る。minutes_ago 分前に測ったことにする。"""
    info = {
        "water_temp": ("液温", "℃"), "air_temp": ("気温", "℃"), "humidity": ("湿度", "%"),
        "light": ("照度", "lx"), "water_level": ("水位", "cm"), "ec": ("EC", "mS/cm"),
    }[metric]
    measured_at = (NOW - timedelta(minutes=minutes_ago)).isoformat()
    return {"metric": metric, "label": info[0], "value": value, "unit": info[1], "measured_at": measured_at}


def latest_of(*rows):
    return {r["metric"]: r for r in rows}


def item(result, metric):
    return next(i for i in result["items"] if i["metric"] == metric)


def texts(result):
    return [action["text"] for action in result["actions"]]


@pytest.mark.parametrize("value, status", [
    (15, "ok"), (25, "ok"), (14.9, "warn"), (25.1, "warn"),
    (10, "warn"), (28, "warn"), (9.9, "danger"), (28.1, "danger"),
])
def test_thresholds_include_both_ends(value, status):
    result = judge.judge(latest_of(row("water_temp", value), row("air_temp", 20.0)), NOW)
    assert item(result, "water_temp")["status"] == status


def test_out_of_range_value_shows_the_value_and_the_advice():
    result = judge.judge(latest_of(row("water_temp", 27.1)), NOW)
    assert texts(result) == ["液温が高い（27.1℃）。遮光するか、窓から離してください"]
    assert result["actions"][0]["level"] == "warn"
    assert result["overall"] == "warn"

    result = judge.judge(latest_of(row("water_temp", 8.0)), NOW)
    assert texts(result) == ["液温が低い（8.0℃）。タンクを保温するか、窓から離してください"]
    assert result["actions"][0]["level"] == "danger"


def test_metric_without_thresholds_is_shown_but_not_judged():
    # 担当者が基準値を決めるまでは none。色を変えず、今やることも出さない
    result = judge.judge(latest_of(row("air_temp", 35.0), row("light", 0.0)), NOW)
    assert item(result, "air_temp")["status"] == "none"
    assert item(result, "air_temp")["value"] == 35.0
    assert result["actions"] == []
    assert result["overall"] == "ok"


def test_advice_can_be_missing_and_a_general_text_is_used(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_THRESHOLDS", {"air_temp": {"ok": (10, 30), "warn": (5, 35)}})
    monkeypatch.setattr(config, "HYDRO_ADVICE", {})
    result = judge.judge(latest_of(row("air_temp", 31.0)), NOW)
    assert texts(result) == ["気温が高い（31.0℃）。様子を確認してください"]


def test_old_value_is_stale_and_not_returned():
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=16), row("air_temp", 20.0)), NOW)
    stale = item(result, "water_temp")
    assert stale["status"] == "stale"
    assert stale["value"] is None
    assert stale["measured_at"] == (NOW - timedelta(minutes=16)).isoformat()
    assert texts(result) == ["液温の値が届いていません（最後の計測 14:14）。センサーと配線を確認してください"]
    assert result["actions"][0]["level"] == "system"
    assert result["overall"] == "system"
    assert result["stale"] is False


def test_value_exactly_at_the_limit_is_not_stale_yet():
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=15)), NOW)
    assert item(result, "water_temp")["status"] == "ok"


def test_stale_from_another_day_shows_the_date():
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=24 * 60), row("air_temp", 20.0)), NOW)
    assert texts(result) == ["液温の値が届いていません（最後の計測 11/16 14:30）。センサーと配線を確認してください"]


def test_manual_metric_uses_hours(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_MANUAL_METRICS", ["water_temp"])
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=35 * 60)), NOW)
    assert item(result, "water_temp")["status"] == "ok"
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=37 * 60)), NOW)
    assert item(result, "water_temp")["status"] == "stale"


def test_expected_metric_that_never_arrived_is_stale(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_EXPECTED_METRICS", ["air_temp", "light"])
    result = judge.judge(latest_of(row("air_temp", 20.0)), NOW)
    light = item(result, "light")
    assert light == {"metric": "light", "label": "照度", "value": None, "unit": "lx",
                     "measured_at": None, "status": "stale"}
    assert texts(result) == ["照度の値が届いていません。センサーと配線を確認してください"]


def test_items_follow_the_panel_order_and_skip_unused_metrics(monkeypatch):
    # パネルに出す項目でも、値が一度もなく、届く予定もない項目（まだ付けていないEC）は出さない
    monkeypatch.setattr(config, "HYDRO_PANEL_METRICS", ["light", "ec", "air_temp"])
    result = judge.judge(latest_of(row("air_temp", 20.0), row("light", 300.0), row("humidity", 50.0)), NOW)
    assert [i["metric"] for i in result["items"]] == ["light", "air_temp"]


def test_measured_at_is_the_newest_time():
    result = judge.judge(latest_of(row("air_temp", 20.0, minutes_ago=5), row("light", 300.0, minutes_ago=0)), NOW)
    assert result["measured_at"] == NOW.isoformat()


def test_all_items_stale_means_data_stopped():
    result = judge.judge(latest_of(row("air_temp", 20.0, minutes_ago=60), row("light", 300.0, minutes_ago=60)), NOW)
    assert result["stale"] is True
    assert texts(result) == ["データが届いていません。ラズパイと配線を確認してください"]
    assert result["overall"] == "system"


def test_impossible_value_is_a_sensor_error(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_SANITY", {"water_temp": (-10, 50)})
    result = judge.judge(latest_of(row("water_temp", -127.0)), NOW)
    assert item(result, "water_temp")["status"] == "sensor_error"
    assert texts(result) == ["液温センサーの値が異常です（-127.0℃）。配線を確認してください"]
    assert result["overall"] == "system"


def test_ec_cannot_be_judged_without_water_temperature():
    # ECは液温で温度補償するので、液温が読めないときはECも異常として扱う
    result = judge.judge(latest_of(row("water_temp", 20.0, minutes_ago=30), row("ec", 1.6)), NOW)
    assert item(result, "ec")["status"] == "sensor_error"
    assert "液温が読めないため、ECを判定できません。液温センサーを確認してください" in texts(result)


@pytest.mark.parametrize("stage, value, status", [
    ("germination", 0.2, "none"),
    ("seedling", 0.8, "ok"), ("seedling", 1.3, "warn"), ("seedling", 1.6, "danger"),
    ("growing", 1.2, "ok"), ("growing", 1.1, "warn"), ("growing", 2.6, "danger"),
])
def test_ec_ranges_follow_the_growth_stage(monkeypatch, stage, value, status):
    monkeypatch.setattr(config, "HYDRO_STAGE", stage)
    result = judge.judge(latest_of(row("water_temp", 20.0), row("ec", value)), NOW)
    assert item(result, "ec")["status"] == status


def test_ec_text_uses_two_decimals():
    result = judge.judge(latest_of(row("water_temp", 20.0), row("ec", 1.05)), NOW)
    assert texts(result) == ["ECが低い（1.05 mS/cm）。量を計算できないため、目で確認して液肥を足してください"]


@pytest.mark.parametrize("stage, cm, status", [
    ("seedling", 18.0, "ok"), ("seedling", 17.9, "warn"), ("seedling", 16.0, "warn"), ("seedling", 15.9, "danger"),
    ("growing", 8.0, "ok"), ("growing", 7.9, "warn"), ("growing", 6.0, "warn"), ("growing", 5.9, "danger"),
    ("growing", 20.0, "ok"),  # 目標より高くても注意にしない（下がりすぎだけを見る）
])
def test_water_level_is_judged_by_the_stage_target(monkeypatch, stage, cm, status):
    monkeypatch.setattr(config, "HYDRO_STAGE", stage)
    result = judge.judge(latest_of(row("water_level", cm)), NOW)
    assert item(result, "water_level")["status"] == status


def test_water_level_text_shows_the_ratio_to_full():
    result = judge.judge(latest_of(row("water_level", 7.0)), NOW)
    assert texts(result) == ["水位が低い（7.0cm、満水の35%）。量を計算できないため、目で確認して水を足してください"]


def test_water_level_is_not_judged_until_the_full_level_is_measured(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_FULL_LEVEL_CM", None)
    result = judge.judge(latest_of(row("water_level", 1.0)), NOW)
    assert item(result, "water_level")["status"] == "none"


def test_unknown_stage_turns_off_stage_based_metrics(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_STAGE", "seeding")
    result = judge.judge(latest_of(row("water_temp", 20.0), row("ec", 5.0), row("water_level", 1.0)), NOW)
    assert item(result, "ec")["status"] == "none"
    assert item(result, "water_level")["status"] == "none"
    assert texts(result) == ["生育段階の設定（HYDRO_STAGE）が正しくありません"]
    assert result["overall"] == "system"


def test_overall_and_action_order_put_danger_first(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_THRESHOLDS", {
        "water_temp": {"ok": (15, 25), "warn": (10, 28)},
        "air_temp": {"ok": (10, 30), "warn": (5, 35)},
    })
    result = judge.judge(latest_of(
        row("air_temp", 31.0),                    # warn
        row("humidity", 50.0, minutes_ago=30),    # stale → system
        row("water_temp", 30.0),                  # danger
    ), NOW)
    assert [a["level"] for a in result["actions"]] == ["danger", "system", "warn"]
    assert result["overall"] == "danger"


def test_all_ok_has_no_actions():
    result = judge.judge(latest_of(row("water_temp", 20.0), row("air_temp", 20.0)), NOW)
    assert result["overall"] == "ok"
    assert result["actions"] == []
    assert result["stale"] is False
