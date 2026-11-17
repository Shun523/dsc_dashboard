# このファイルの役割：水温（DS18B20）の read() を、実物がないPCで確かめます。
#   ラズパイが作るフォルダとファイル（/sys/bus/w1/devices/28-…/w1_slave）を一時フォルダに偽物として作り、
#   read() がそこから正しく液温を読めるかを見ます。
#   read() がまだひな形のまま（NotImplementedError）のあいだは、テストを飛ばします（skipped と表示）。

import pytest

from apps.hydroponics.sensors import water_temp

GOOD = "72 01 4b 46 7f ff 0e 10 57 : crc=57 YES\n72 01 4b 46 7f ff 0e 10 57 t=23125\n"
BAD_CRC = "72 01 4b 46 7f ff 0e 10 57 : crc=00 NO\n72 01 4b 46 7f ff 0e 10 57 t=23125\n"


@pytest.fixture
def devices(tmp_path, monkeypatch):
    # センサーのフォルダの場所を、テスト用の一時フォルダに差し替える
    monkeypatch.setattr(water_temp, "W1_DEVICES", tmp_path)
    # 読み直しの待ち時間をなくして、テストを速くする
    monkeypatch.setattr(water_temp, "RETRY_WAIT_SECONDS", 0)
    return tmp_path


def put_sensor(devices, text, name="28-0123456789ab"):
    folder = devices / name
    folder.mkdir()
    (folder / "w1_slave").write_text(text)


def read_or_skip():
    try:
        return water_temp.read()
    except NotImplementedError:
        pytest.skip("water_temp.read() がまだ書かれていません")


def expect_error():
    with pytest.raises(Exception) as error:
        water_temp.read()
    if error.type is NotImplementedError:
        pytest.skip("water_temp.read() がまだ書かれていません")


def test_reads_the_temperature_in_the_promised_format(devices):
    put_sensor(devices, GOOD)
    assert read_or_skip() == [{"metric": "water_temp", "label": "液温", "value": 23.125, "unit": "℃"}]


def test_raises_when_no_sensor_is_connected(devices):
    # 28- で始まるフォルダがない＝配線が外れているか、1-Wire が無効
    expect_error()


def test_raises_when_the_reading_is_broken(devices):
    # 1行目の最後が YES でないときは、値が壊れているので使わない
    put_sensor(devices, BAD_CRC)
    expect_error()


def test_raises_on_the_power_on_value(devices):
    # 85℃（t=85000）は電源を入れた直後の初期値で、本当の温度ではない
    put_sensor(devices, GOOD.replace("t=23125", "t=85000"))
    expect_error()


def test_reads_negative_temperatures(devices):
    put_sensor(devices, GOOD.replace("t=23125", "t=-1250"))
    assert read_or_skip()[0]["value"] == -1.25


def test_retries_when_the_first_reading_is_broken(devices, monkeypatch):
    # 1回目は CRC が合わず、2回目で読めた場合は、2回目の値を返す
    put_sensor(devices, GOOD)
    texts = iter([BAD_CRC, GOOD])
    monkeypatch.setattr(water_temp.Path, "read_text", lambda self, *a, **k: next(texts))
    assert read_or_skip()[0]["value"] == 23.125


def test_raises_when_two_sensors_are_connected(devices):
    # どちらがタンクの液温か分からないので読まない
    put_sensor(devices, GOOD)
    put_sensor(devices, GOOD, name="28-ba9876543210")
    expect_error()
