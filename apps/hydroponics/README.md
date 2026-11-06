# 水耕栽培アプリ

小松菜の計測状況を表示する専用アプリです。
ダッシュボードには要約を表示し、パネルを押すとこのアプリを開きます。
仕様はルートの `水耕栽培センサー管理 技術仕様書.md` を参照してください。

## 起動と設定

ルートの [README](../../README.md) の手順で依存ライブラリを入れ、
リポジトリのルートで `python app.py` を実行すると、ダッシュボードと一緒に起動します。

単体で開発する場合は、ルートで次を実行します。

```bash
python -m apps.hydroponics.app
```

専用画面は `http://127.0.0.1:8001/`、要約APIは `/api/summary` です。
単体起動時にも「ダッシュボードに戻る」を表示したい場合は、
このフォルダの `.env.example` を `.env` にコピーし、`HYDRO_DASHBOARD_URL` を設定します。
秘密情報・環境ごとの設定はこのアプリの `.env` に、その他の設定は `config.py` に置きます。

## ダッシュボードとの接続

共通入口では、専用画面を `/apps/hydroponics/`、要約APIを
`/apps/hydroponics/api/summary` として公開します。
ダッシュボードはこのAPIと、公開した `static/summary.js`・`static/summary.css` だけを使います。
水耕栽培のPythonコードやDBへの直接の依存はありません。

要約形式は仕様書の第9章に従います。
`summary.py` の `get_summary()` が、専用画面とパネルの両方のデータを作ります。
APIが失敗したときはHTTP 503を返し、両画面は前回の表示を残します。

## センサー値の収集

`collect.py` が、登録されたセンサーを順に読んで `data/hydroponics.db` に保存します（仕様書の第6・7章）。
PCでは `.env` の `HYDRO_USE_DUMMY=true`（初期値）でダミーセンサーを、
ラズパイでは `false` にして実センサー（`sensors/__init__.py` の `PI_SENSORS`）を使います。

```bash
python -m apps.hydroponics.collect                  # 全センサーを1回測って保存する
python -m apps.hydroponics.collect --sensor bh1750  # 1つだけ測る
```

読み取りに失敗したセンサーは `logs/hydroponics.log` に記録され、ほかのセンサーの保存は続きます。

### ラズパイで5分ごとに動かす

`deploy/hydroponics_crontab.txt` を cron に登録します。
リポジトリが `/home/pi/dsc_dashboard` 以外にある場合は、先にファイルの中のパスを書き換えてください。

```bash
crontab apps/hydroponics/deploy/hydroponics_crontab.txt  # そのユーザーの cron の設定が、このファイルの中身で置き換わる
crontab -l                                               # 登録された中身を確認する
```

10分ほど待ってから、計測時刻ごとに値が増えているかを確認します（`sqlite3` は `sudo apt install sqlite3` で入れます）。
1時間後に12回分そろっていれば、センサーの「1時間連続で取れる」の目安を満たします。

```bash
sqlite3 apps/hydroponics/data/hydroponics.db \
  "SELECT measured_at, COUNT(*) FROM sensor_readings GROUP BY measured_at ORDER BY measured_at DESC LIMIT 12;"
```

値が増えないときは、`apps/hydroponics/logs/hydroponics.log` と、cron の実行記録（`journalctl -u cron --since "1 hour ago"`）を見てください。

## 生育段階の切り替え

ECと水位の目標は、生育段階（`.env` の `HYDRO_STAGE`）で切り替わります。
今の段階はパネルと専用画面に「生育段階：発芽まで」のように出ます。

| HYDRO_STAGE | 時期 | 切り替える目安 |
| --- | --- | --- |
| `germination` | 種まきから発芽まで（初期値） | ― |
| `seedling` | 発芽して本葉が出るまで | 双葉が開いた |
| `growing` | 本葉が出てから収穫まで | 本葉が出て、根がポッドの下まで十分に伸びた |

栽培リーダーが目で見て決め、ラズパイで次のように切り替えます。

```bash
cd ~/dsc_dashboard
nano apps/hydroponics/.env            # HYDRO_STAGE=seedling のように書き換えて保存する
sudo systemctl restart dashboard      # パネルの表示に反映する
```

5分ごとの収集は、次の実行から新しい値を使います。
書き間違えると、パネルに「生育段階：設定が正しくありません」と出ます。

## 現在の状態

専用画面・要約API・パネルの接続、生育段階の表示、センサー値の収集・保存（`collect.py`・`db.py`）は実装済みです。
要約APIはまだDBを読まず、未計測状態を返します。判定・通知・グラフ・作業記録は今後実装します。
センサーのひな形は `sensors/` にあり、書き方は [センサーのREADME](sensors/README.md) を見てください。
