# このファイルの役割：
#   DS18B20（防水型）で液温（タンクの培養液の温度）を測ります（1-Wire、GPIO4）。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：ルートで `python -m apps.hydroponics.sensors.water_temp` を実行すると結果が表示されます。
#   PCでの確認：`python -m pytest apps/hydroponics/tests/test_water_temp.py` で、偽のセンサーの値を読めるか確かめられます。
#   ライブラリは使わず、ラズパイの OS が用意するファイルを読むだけです（requirements-pi.txt への追加は不要）。

import time
from pathlib import Path

# DS18B20 の値が出てくるフォルダ。ラズパイで 1-Wire を有効にすると、
# つないだセンサーごとに 28- で始まる名前のフォルダがここにできる。
# テストではこの場所を偽のフォルダに差し替えるので、read() の中ではこの名前を使って探す。
W1_DEVICES = Path("/sys/bus/w1/devices")

# 1行目が YES にならなかったときに、読み直す回数と間隔（秒）。
# 1回の読み取りは約0.75秒かかるので、3回読み直しても10秒以内に終わる
RETRIES = 3
RETRY_WAIT_SECONDS = 0.5

# 電源を入れた直後などに DS18B20 が返す初期値（85℃）。本当の温度ではないので使わない
POWER_ON_VALUE = 85000


def find_sensor_file():
    """28- で始まるフォルダの中の w1_slave ファイルを返す。見つからなければ例外を投げる。"""
    folders = sorted(W1_DEVICES.glob("28-*"))
    if not folders:
        raise RuntimeError(
            f"DS18B20 が見つかりません（{W1_DEVICES} に 28- で始まるフォルダがない）。"
            "配線と、raspi-config で 1-Wire を有効にしたかを確認してください"
        )
    if len(folders) > 1:
        # 2つ以上あると、どれがタンクの液温か分からないので読まない
        names = ", ".join(folder.name for folder in folders)
        raise RuntimeError(f"DS18B20 が2つ以上つながっています（{names}）。1つにしてください")
    return folders[0] / "w1_slave"


def parse(text):
    """w1_slave の中身から温度（℃）を取り出す。値が壊れていたら例外を投げる。"""
    lines = text.strip().splitlines()
    if len(lines) < 2:
        raise RuntimeError(f"DS18B20 の読み取り結果の形がおかしいです：{text!r}")
    # 1行目の最後の YES は「通信のチェック（CRC）が合った」という意味
    if not lines[0].strip().endswith("YES"):
        raise RuntimeError(f"DS18B20 の読み取りに失敗しました（CRC が合わない）：{lines[0]!r}")
    if "t=" not in lines[1]:
        raise RuntimeError(f"DS18B20 の読み取り結果に温度がありません：{lines[1]!r}")
    raw = int(lines[1].split("t=")[1])
    if raw == POWER_ON_VALUE:
        raise RuntimeError("DS18B20 が初期値（85℃）を返しました。電源や配線を確認してください")
    return raw / 1000


def read():
    """液温を測って、値のリストを返す。読み取りに失敗したら例外を投げる。"""
    sensor_file = find_sensor_file()

    # 配線が長いと、たまに CRC が合わないことがあるので、数回まで読み直す
    for attempt in range(RETRIES):
        try:
            temp = parse(sensor_file.read_text())
            break
        except RuntimeError:
            if attempt == RETRIES - 1:
                raise  # 最後まで読めなければ、そのまま失敗にする
            time.sleep(RETRY_WAIT_SECONDS)

    return [
        {"metric": "water_temp", "label": "液温", "value": temp, "unit": "℃"},
    ]


if __name__ == "__main__":
    print(read())
