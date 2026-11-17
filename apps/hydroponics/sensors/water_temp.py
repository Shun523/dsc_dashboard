# このファイルの役割：
#   DS18B20（防水型）で液温（タンクの培養液の温度）を測ります（1-Wire、GPIO4）。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：ルートで `python -m apps.hydroponics.sensors.water_temp` を実行すると結果が表示されます。
#   PCでの確認：`python -m pytest apps/hydroponics/tests/test_water_temp.py` で、偽のセンサーの値を読めるか確かめられます。

from pathlib import Path

# DS18B20 の値が出てくるフォルダ。ラズパイで 1-Wire を有効にすると、
# つないだセンサーごとに 28- で始まる名前のフォルダがここにできる。
# テストではこの場所を偽のフォルダに差し替えるので、read() の中ではこの名前を使って探す。
W1_DEVICES = Path("/sys/bus/w1/devices")


def read():
    """液温を測って、値のリストを返す。読み取りに失敗したら例外を投げる。"""
    # TODO：ここに次の処理を書き、下の raise の行を消す。
    #   1. W1_DEVICES の中から、名前が 28- で始まるフォルダを探す。見つからなければ例外を投げる。
    #   2. そのフォルダの中の w1_slave というファイルを読む。中身は次のような2行。
    #        72 01 4b 46 7f ff 0e 10 57 : crc=57 YES
    #        72 01 4b 46 7f ff 0e 10 57 t=23125
    #   3. 1行目の最後が YES でなければ、読み取り失敗として例外を投げる。
    #   4. 2行目の t= の後ろの数字を 1000 で割ると℃になる（t=23125 なら 23.125℃）。
    #   ライブラリは使わず、Python の標準の機能（Path の glob や read_text）だけで書ける。
    raise NotImplementedError("water_temp.read() はまだ書かれていません")
    # 読めたら、次の形で返す：
    # return [
    #     {"metric": "water_temp", "label": "液温", "value": temp, "unit": "℃"},
    # ]


if __name__ == "__main__":
    print(read())
