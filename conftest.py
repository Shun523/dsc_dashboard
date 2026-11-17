# このファイルの役割：全部のテストに共通の準備です（pytest が自動で読みます）。
#   水耕栽培のDBを、テストごとの一時フォルダに置きます。
#   開発用のDB（apps/hydroponics/data/hydroponics.db）を、テストが読んだり書いたりしないようにするためです。

import pytest

from apps.hydroponics import config as hydro_config


@pytest.fixture(autouse=True)
def isolated_hydro_db(monkeypatch, tmp_path):
    monkeypatch.setattr(hydro_config, "HYDRO_DB_PATH", tmp_path / "hydroponics.db")
