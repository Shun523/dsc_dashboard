# このファイルの役割：ラズパイ用のセンサーの read() が約束の形で値を返すことを、PCで確認します。
#   実物のセンサーとライブラリの代わりに、同じ名前の偽物を差し込んで動かします。
#   配線や実際の値の正しさは、ラズパイでの動作確認（sensors/README.md）で確かめます。

import importlib
import runpy
import sys
import time
import types

import pytest

# sensors/README.md の表と同じ組み合わせ
EXPECTED = {
    "bh1750": {"light": ("照度", "lx")},
    "bme280": {"air_temp": ("気温", "℃"), "humidity": ("湿度", "%")},
    "water_level": {"water_level": ("水位", "cm")},
}


def fake_module(monkeypatch, name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def install_bh1750(monkeypatch, broken):
    class SMBus:
        def __init__(self, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read_i2c_block_data(self, address, command, length):
            if broken:
                raise OSError("I2Cの応答がない")
            return [0x01, 0x90]

    fake_module(monkeypatch, "smbus2", SMBus=SMBus)
    return None


def install_bme280(monkeypatch, broken):
    class SMBus:
        def __init__(self, port):
            pass

        def close(self):
            pass

    def sample(bus, address, params):
        if broken:
            raise OSError("I2Cの応答がない")
        return types.SimpleNamespace(temperature=21.5, humidity=48.2)

    fake_module(monkeypatch, "smbus2", SMBus=SMBus)
    fake_module(monkeypatch, "bme280", load_calibration_params=lambda bus, address: None, sample=sample)
    return None


def install_water_level(monkeypatch, broken):
    # 電源のオン・オフと、どの入力（A0〜A3）を読んだかを記録する
    record = {"power": [], "pins": []}

    class AnalogIn:
        def __init__(self, ads, pin):
            record["pins"].append(pin)

        @property
        def voltage(self):
            if broken:
                raise OSError("I2Cの応答がない")
            return 2.0

    gpio = fake_module(
        monkeypatch, "RPi.GPIO", BCM="BCM", OUT="OUT", HIGH=1, LOW=0,
        setmode=lambda mode: None, setup=lambda pin, mode: None,
        output=lambda pin, value: record["power"].append(value), cleanup=lambda pin=None: None,
    )
    fake_module(monkeypatch, "RPi", GPIO=gpio)
    fake_module(monkeypatch, "board", SCL="SCL", SDA="SDA")
    fake_module(monkeypatch, "busio", I2C=lambda scl, sda: object())
    ads1115 = fake_module(monkeypatch, "adafruit_ads1x15.ads1115", ADS1115=lambda i2c: object(), P0="A0", P1="A1")
    fake_module(monkeypatch, "adafruit_ads1x15", ads1115=ads1115)
    fake_module(monkeypatch, "adafruit_ads1x15.analog_in", AnalogIn=AnalogIn)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    return record


INSTALLERS = {"bh1750": install_bh1750, "bme280": install_bme280, "water_level": install_water_level}


def sensor_module(name):
    return importlib.import_module(f"apps.hydroponics.sensors.{name}")


@pytest.mark.parametrize("name", EXPECTED)
def test_read_returns_the_promised_format(monkeypatch, name):
    INSTALLERS[name](monkeypatch, broken=False)
    values = sensor_module(name).read()
    assert {value["metric"]: (value["label"], value["unit"]) for value in values} == EXPECTED[name]
    for value in values:
        assert set(value) == {"metric", "label", "value", "unit"}
        assert isinstance(value["value"], (int, float))


@pytest.mark.parametrize("name", EXPECTED)
def test_read_raises_when_the_sensor_cannot_be_read(monkeypatch, name):
    # 0 や前回の値で埋めず、例外で collect.py に失敗を知らせる
    INSTALLERS[name](monkeypatch, broken=True)
    with pytest.raises(Exception):
        sensor_module(name).read()


@pytest.mark.parametrize("name", EXPECTED)
def test_check_command_prints_the_values(monkeypatch, capsys, name):
    # ラズパイでの動作確認 `python -m apps.hydroponics.sensors.<名前>` で結果が表示されること
    INSTALLERS[name](monkeypatch, broken=False)
    monkeypatch.delitem(sys.modules, f"apps.hydroponics.sensors.{name}", raising=False)
    runpy.run_module(f"apps.hydroponics.sensors.{name}", run_name="__main__")
    output = capsys.readouterr().out
    for metric in EXPECTED[name]:
        assert metric in output


@pytest.mark.parametrize("broken", [False, True])
def test_water_level_reads_a1_and_always_turns_the_power_off(monkeypatch, broken):
    # A0 はEC用なので水位は A1。電極の腐食を防ぐため、失敗しても電源は必ず切る
    record = install_water_level(monkeypatch, broken)
    try:
        sensor_module("water_level").read()
    except Exception:
        assert broken
    assert record["pins"] == ["A1"]
    assert record["power"][0] == 1
    assert record["power"][-1] == 0
