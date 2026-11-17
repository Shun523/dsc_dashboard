# このファイルの役割：
#   BH1750 で照度（窓からの日射）を測ります（I2C、アドレスは 0x23）。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：ルートで `python -m apps.hydroponics.sensors.bh1750` を実行すると結果が表示されます。


def read():
    """照度センサーから明るさを読み取る"""
    #ライブラリ読み込み
    import smbus2

    # センサーの設定（アドレスと指示）
    address = 0x23
    command = 0x10

    try:
        # センサーと通信する
        with smbus2.SMBus(1) as bus:
            data = bus.read_i2c_block_data(address, command, 2)

        # 2つのデータを1つにまとめる
        high = data[0]
        low = data[1]
        raw_value = high * 256 + low

        # 照度に変換する
        light = round(raw_value / 1.2, 2)

    except Exception as e:
        raise RuntimeError(
            f"照度センサーの読み取りに失敗しました: {e}"
        )

    # 測定結果を返す
    return [
        {
            "metric": "light",
            "label": "照度",
            "value": light,
            "unit": "lx",
        }
    ]


if __name__ == "__main__":
    print(read())
