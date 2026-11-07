def read():
    """BME280センサーから気温と湿度を取得し、決められたフォーマットのリストで返します。
    
    読めなかった場合は例外を発生させます。
    """
    # 規約に基づき、センサー用ライブラリの import は read() 内で行います[cite: 2]。
    import smbus2
    import bme280

    # I2C バス番号と BME280 の I2C アドレス（標準は 0x76 または 0x77）
    port = 1
    address = 0x76
    bus = smbus2.SMBus(port)

    try:
        # キャリブレーションデータを読み込み、センサーから値を測定
        calibration_params = bme280.load_calibration_params(bus, address)
        data = bme280.sample(bus, address, calibration_params)

        temp = data.temperature
        humidity = data.humidity

        # 仕様通りのフォーマットで返します[cite: 2]
        return [
            {
                "metric": "air_temp",
                "label": "気温",
                "value": temp,
                "unit": "°C",
            },
            {
                "metric": "humidity",
                "label": "湿度",
                "value": humidity,
                "unit": "%",
            },
        ]
    except Exception as e:
        # 読めなかった場合は 0 や直前の値で埋めず、例外を投げます[cite: 2]。
        raise RuntimeError(f"BME280からの読み取りに失敗しました: {e}") from e
    finally:
        # バスを安全に閉じる
        bus.close()