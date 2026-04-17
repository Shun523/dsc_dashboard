# 引き継ぎメモ

## プロジェクト概要

岡山大学DS部の部内DX推進として、複数の単体アプリを作り最終的に総合ダッシュボードに統合する計画。

## 全体構成

- **単体アプリ群**（新入生がバイブコーディングで担当）
  - スケジュールアプリ（既存: https://github.com/Shun523/dsc_schedule）
  - 天気アプリ（未作成）
  - 電車アプリ（未作成）
  - ニュースアプリ（未作成）
  - 部室人数検知アプリ（他部員が作成済み、リポジトリ未確認）
- **総合ダッシュボード**（このリポジトリ）
  - 全アプリのウィジェットを統合して表示
  - iPad・サイネージでの表示を想定

## 技術スタック（全アプリ統一）

- Next.js 15 + TypeScript
- Tailwind CSS
- Supabase（スケジュールアプリのみ）

## 今やること

`/tmp/dsc_dashboard/README.md` に設計図（mermaid）を書いた。この内容を `README.md` に反映してpushする。

以下の内容をREADME.mdに書いてください：

```markdown
# DSC Dashboard

岡山大学DS部 総合ダッシュボードプロジェクト

## 全体構成

\`\`\`mermaid
graph TD
  subgraph apps[単体アプリ群]
    schedule[スケジュールアプリ]
    weather[天気アプリ]
    transit[電車アプリ]
    news[ニュースアプリ]
    occupancy[部室人数検知アプリ]
  end

  subgraph external[外部サービス]
    supabase[(Supabase)]
    slack[Slack]
    weather_api[Open-Meteo API]
    transit_api[電車API]
    news_api[ニュースAPI]
  end

  dashboard[総合ダッシュボード]
  display[iPad / サイネージ]

  schedule <--> supabase
  schedule --> slack
  weather --> weather_api
  transit --> transit_api
  news --> news_api

  schedule --> dashboard
  weather --> dashboard
  transit --> dashboard
  news --> dashboard
  occupancy --> dashboard

  dashboard --> display
\`\`\`

## アプリ一覧

| アプリ | 概要 | リポジトリ |
|---|---|---|
| スケジュールアプリ | MTG日程調整・部室利用状況 | [dsc_schedule](https://github.com/Shun523/dsc_schedule) |
| 天気アプリ | 岡山の天気表示 | - |
| 電車アプリ | 電車時刻・遅延情報 | - |
| ニュースアプリ | ニュースフィード | - |
| 部室人数検知アプリ | 部室の現在の人数 | - |
| 総合ダッシュボード | 全アプリの統合表示 | このリポジトリ |

## 技術スタック

- **フロントエンド**: Next.js 15 + TypeScript
- **スタイリング**: Tailwind CSS
- **バックエンド**: Supabase
- **表示デバイス**: iPad / サイネージ
```

## 次のステップ

1. README.mdにmermaid設計図を反映してpush
2. 新入生向けテンプレートリポジトリの作成
3. 各単体アプリのspec.md（GEMINI.md）を作成
4. 天気アプリから実装開始
