# このファイルの役割：ダミーセンサーが、本物のセンサーと同じ形でそれらしい値を返すことを確認します。

import pytest

from apps.hydroponics import config, sensors
from apps.hydroponics.sensors import dummy

# センサーのREADMEの表と同じ組み合わせ（pHと、見送ったポンプの電流は返さない）
EXPECTED = {
    "water_temp": ("液温", "℃"),
    "air_temp": ("気温", "℃"),
    "humidity": ("湿度", "%"),
    "light": ("照度", "lx"),
    "water_level": ("水位", "cm"),
    "ec": ("EC", "mS/cm"),
}


@pytest.fixture(autouse=True)
def default_settings(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_DUMMY_SKIP_METRICS", [])
    monkeypatch.setattr(config, "HYDRO_FULL_LEVEL_CM", None)


def test_dummy_is_registered_for_development():
    assert dummy in sensors.DUMMY_SENSORS
    assert dummy not in sensors.PI_SENSORS


def test_dummy_returns_every_metric_in_the_sensor_format():
    values = dummy.read()
    assert {value["metric"]: (value["label"], value["unit"]) for value in values} == EXPECTED
    for value in values:
        assert set(value) == {"metric", "label", "value", "unit"}
        assert isinstance(value["value"], float)


def test_dummy_values_stay_in_the_normal_ranges_unless_dangerous(monkeypatch):
    monkeypatch.setattr(dummy.random, "random", lambda: 1.0)  # 危険な値を出さない
    for _ in range(200):
        values = {value["metric"]: value["value"] for value in dummy.read()}
        assert 15 <= values["water_temp"] <= 24
        assert 15 <= values["air_temp"] <= 28
        assert 40 <= values["humidity"] <= 70
        assert 0 <= values["light"] <= 20000
        assert 0.6 * dummy.DUMMY_FULL_LEVEL_CM <= values["water_level"] <= dummy.DUMMY_FULL_LEVEL_CM
        assert 1.1 <= values["ec"] <= 2.1


def test_dummy_sometimes_returns_dangerous_values(monkeypatch):
    monkeypatch.setattr(dummy.random, "random", lambda: 0.0)  # 必ず危険な値を出す
    values = {value["metric"]: value["value"] for value in dummy.read()}
    # 仕様書の第8章の warn の範囲（液温 10〜28℃、EC 1.0〜2.5、水位 満水位の50%以上）の外
    assert not 10 <= values["water_temp"] <= 28
    assert not 1.0 <= values["ec"] <= 2.5
    assert values["water_level"] < 0.5 * dummy.DUMMY_FULL_LEVEL_CM


def test_dummy_uses_the_measured_full_level_when_set(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_FULL_LEVEL_CM", 20.0)
    monkeypatch.setattr(dummy.random, "random", lambda: 1.0)
    level = next(value["value"] for value in dummy.read() if value["metric"] == "water_level")
    assert 12.0 <= level <= 20.0


def test_dummy_light_is_zero_at_night(monkeypatch):
    class Night:
        @staticmethod
        def now():
            return Night()

        hour = 22

    monkeypatch.setattr(dummy, "datetime", Night)
    light = next(value["value"] for value in dummy.read() if value["metric"] == "light")
    assert light == 0.0


def test_dummy_skips_metrics_listed_in_settings(monkeypatch):
    monkeypatch.setattr(config, "HYDRO_DUMMY_SKIP_METRICS", ["ec"])
    assert "ec" not in {value["metric"] for value in dummy.read()}
