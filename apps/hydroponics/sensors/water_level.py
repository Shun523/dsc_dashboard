# hydroponics/sensors/water_level.py

def read():
    import time
    import RPi.GPIO as GPIO
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    POWER_PIN = 17  # センサー電源制御用のGPIOピン番号

    # GPIOの初期設定
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(POWER_PIN, GPIO.OUT)

    try:
        # 電極腐食防止のため、測定時のみGPIO17から給電する[cite: 2]
        GPIO.output(POWER_PIN, GPIO.HIGH)
        time.sleep(0.1)  # 通電安定待ち

        # ADS1115（I2C ADC）の初期化と電圧読み取り
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        chan = AnalogIn(ads, ADS.P0)  # A0チャンネルに接続されていると仮定

        voltage = chan.voltage

        # TODO: 実測値から作成した換算表・計算式を適用して電圧（V）から水位（cm）に変換[cite: 1, 2]
        # (例: 1V = 2.5cm と仮定)
        water_level_cm = voltage * 2.5

    except Exception as e:
        # センサーの読み取り失敗時は、0や前の値で埋めずに例外を投げる仕様[cite: 2]
        raise RuntimeError(f"水位センサーの読み取りに失敗しました: {e}") from e

    finally:
        # 正常終了・エラー終了問わず、必ず電源を切ってGPIOを解放する[cite: 2]
        GPIO.output(POWER_PIN, GPIO.LOW)
        GPIO.cleanup(POWER_PIN)

    # 規定されたフォーマットで結果を返却[cite: 2]
    return [
        {
            "metric": "water_level",
            "label": "水位",
            "value": water_level_cm,
            "unit": "cm",
        }
    ]