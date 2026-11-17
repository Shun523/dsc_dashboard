# このファイルの役割：水耕栽培アプリ単体でも、画面とAPIのURLが正しく動くことを確認します。

import importlib
from contextlib import closing
from datetime import datetime, timedelta, timezone

from apps.hydroponics import config, db
from apps.hydroponics.app import app
from tests.html_helpers import Elements, hydro_js_config

JST = timezone(timedelta(hours=9))


def save(values, minutes_ago):
    """DB（テストごとの一時フォルダ。ルートの conftest.py）に、minutes_ago 分前の計測として保存する。"""
    measured_at = (datetime.now(JST).replace(second=0, microsecond=0) - timedelta(minutes=minutes_ago)).isoformat()
    with closing(db.connect()) as conn:
        db.save_readings(conn, values, measured_at)
    return measured_at


def air_temp(value):
    return {"metric": "air_temp", "label": "気温", "value": value, "unit": "℃"}


def light(value):
    return {"metric": "light", "label": "照度", "value": value, "unit": "lx"}


def test_summary_shows_the_latest_values_from_the_db(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_EXPECTED_METRICS", ["air_temp", "light"])
    monkeypatch.setattr(config, "HYDRO_STAGE", "germination")
    save([air_temp(18.0), light(100.0)], minutes_ago=10)
    newest = save([air_temp(21.5), light(850.0)], minutes_ago=5)
    data = app.test_client().get("/api/summary").get_json()
    assert data["measured_at"] == newest
    assert [(i["metric"], i["value"], i["status"]) for i in data["items"]] == [
        ("air_temp", 21.5, "none"), ("light", 850.0, "none"),
    ]
    assert data["overall"] == "ok"
    assert data["actions"] == []
    assert data["stage"] == {"id": "germination", "label": "発芽まで"}


def test_summary_reports_a_sensor_whose_values_do_not_arrive(monkeypatch):
    # ラズパイで BME280 だけ読めないとき：照度は出し、気温・湿度は欠測として知らせる
    monkeypatch.setattr(config, "HYDRO_EXPECTED_METRICS", ["air_temp", "humidity", "light"])
    save([light(850.0)], minutes_ago=0)
    data = app.test_client().get("/api/summary").get_json()
    statuses = {i["metric"]: i["status"] for i in data["items"]}
    assert statuses == {"air_temp": "stale", "humidity": "stale", "light": "none"}
    assert data["overall"] == "system"
    assert "湿度の値が届いていません。センサーと配線を確認してください" in [a["text"] for a in data["actions"]]


def test_unmeasured_api_does_not_invent_sensor_values():
    response = app.test_client().get("/api/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["measured_at"] is None
    assert data["stale"] is True
    assert data["overall"] == "system"
    assert data["items"] == []


def test_summary_shows_the_growth_stage_even_before_measuring(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_STAGE", "seedling")
    data = app.test_client().get("/api/summary").get_json()
    assert data["measured_at"] is None
    assert data["stage"] == {"id": "seedling", "label": "発芽〜本葉"}


def test_unknown_growth_stage_is_reported_instead_of_guessed(monkeypatch):
    # .env の書き間違いを、どれかの段階として扱わずにパネルで気づけるようにする
    monkeypatch.setattr(config, "HYDRO_STAGE", "seeding")
    data = app.test_client().get("/api/summary").get_json()
    assert data["stage"] == {"id": "seeding", "label": None}


def test_growth_stage_is_read_from_env(monkeypatch):
    # ラズパイでは .env の HYDRO_STAGE を書き換えて切り替える。大文字や空白が混じっても読めるようにする
    monkeypatch.setenv("HYDRO_STAGE", " Growing ")
    try:
        importlib.reload(config)
        assert config.HYDRO_STAGE == "growing"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_standalone_urls_and_optional_dashboard_link(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_URL", "")
    client = app.test_client()
    response = client.get("/?from=dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    js_config = hydro_js_config(html)
    assert js_config["summaryUrl"] == "/api/summary"
    assert js_config["idleReturnSeconds"] == 0
    assert "ダッシュボードに戻る" not in html
    for tag, attrs in Elements(html).elements:
        if tag == "script" and attrs.get("src"):
            assert client.get(attrs["src"]).status_code == 200

    monkeypatch.setattr(config, "DASHBOARD_URL", "https://dashboard.example.test/")
    html = client.get("/?from=dashboard").get_data(as_text=True)
    assert hydro_js_config(html)["dashboardUrl"] == "https://dashboard.example.test/"
    assert hydro_js_config(html)["idleReturnSeconds"] == 180
    assert hydro_js_config(client.get("/").get_data(as_text=True))["idleReturnSeconds"] == 0
