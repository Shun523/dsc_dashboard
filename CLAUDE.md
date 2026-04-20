# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## リポジトリの性質

本リポジトリは現時点では**仕様・計画ドキュメントのみ**。`package.json` やソースコードはまだ存在せず、ダッシュボード本体（Next.js 15 + TypeScript + Tailwind）の実装は未着手。

## ドキュメント構成と参照優先順位

- **`spec.md`** — 要件定義・アーキテクチャ設計の正本。統合方式・レイアウト・セキュリティ要件・ポート/URL 規約・デザイントークン・テンプレート構造・iPad 運用・AI 駆動開発ルールはすべてここ。**実装上の判断が必要なときは必ず `spec.md` を読む**
- **`GUIDE.md`** — `spec.md` の各決定の「なぜ」を新入生向けに解説。技術解説・背景・実装例はここ
- **`README.md`** — 対外的なプロジェクト概要

`spec.md` と `GUIDE.md` が矛盾した場合は **`spec.md` を優先**する。

## Claude として踏み外しやすい確定方針

以下は `spec.md` に明記されているが、AI が勝手に別案を提案しがちなポイント。意思確認なしに方針転換を提案しないこと：

- **マルチリポ + iframe 統合**（モノレポ化・JSON API 方式は教育的意図により明示的に却下）
- **`postMessage` 不採用**。親子間通信はブラウザ標準の URL 遷移のみ
- **`components/ui/` は編集も新規追加も禁止**。独自部品は `components/features/`
- **シークレットに `NEXT_PUBLIC_` を付けない**。外部 API 呼び出しは Route Handler / Server Component 経由のみ
- **CSP の許可オリジンはハードコード禁止**。`NEXT_PUBLIC_DASHBOARD_URL` から動的生成

詳細と根拠は `spec.md` §2・§4・§5-3・§6 を参照。

## コマンド

`package.json` 実装後は Next.js 標準コマンドが適用される（`next dev -p 3000` / `next build` / `next start` / `next lint`）。プロジェクト固有スクリプトを追加したら本ファイルも更新すること。

## 言語

ドキュメントおよびユーザー向け文言はすべて日本語。`spec.md`（硬め・簡潔）と `GUIDE.md`（解説調・初心者向け）のトーンを、編集対象ファイルに合わせて使い分けること。
