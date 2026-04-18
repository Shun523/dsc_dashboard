# 岡山大学DS部 総合ダッシュボード プロジェクト要件定義・アーキテクチャ設計書

あなたは本プロジェクトのシニアエンジニアとして、以下の設計に基づき、具体的な実装ステップの構築、コンポーネント設計、および新入生向けテンプレートの作成をサポートしてください。

## 1. プロジェクトの目的と背景
* **目的**: 部室のiPad（サイネージ）に常時表示する総合ダッシュボードの開発。
* **教育的背景**: 新入生数チームがそれぞれ単体アプリ（天気、電車、ニュース等）を「バイブコーディング（AIを活用した直感的開発）」で作成し、それを統合して成功体験を積ませる。
* **技術課題の解決**: 新入生のGitコンフリクトや環境差異を防ぐため、モノレポは採用せず**「各アプリは独立リポジトリ」**とする。

## 2. 全体アーキテクチャ（統合方式）
ダッシュボードと各アプリは **iframeを用いた「メイン＆サイドバーレイアウト」** で統合する。JSONによるAPI連携は行わない。

> **方針の根拠**: JSON API方式も検討したが、新入生がバイブコーディングで作ったUIの成果をそのまま活かすため、iframe方式を意図的に採用する（教育的達成感を優先）。

* **画面レイアウト（7:3分割）**:
  * 左側70%: スケジュールアプリを大きくiframe表示（スクロール禁止）。
  * 右側30%: 天気、電車などの他アプリの「ミニウィジェット」を縦に並べてiframe表示。
* **透過オーバーレイリンク（Transparent Overlay Link）による遷移**:
  * 右側のミニウィジェットは、カード全体を Next.js の `<Link href="{各アプリのURL}">` で囲む。
  * 内部の `<iframe>` には `pointer-events: none` を当て、直接の操作を禁止する。
  * タップするとブラウザの標準的な画面遷移で、そのアプリの全画面ページ（`/`）へジャンプする。
  * `postMessage` 等の複雑な親子通信は使用しない。
* **各アプリからの戻り導線**:
  * 各アプリの全画面ページ（`/`）右下に配置する「ダッシュボードへ戻る」ボタンは、環境変数 `NEXT_PUBLIC_DASHBOARD_URL` を参照して通常の `<a>` / `<Link>` で遷移する。

## 3. 各アプリチームの要件（テンプレートリポジトリの仕様）
各チームは **Next.js (App Router) + Tailwind CSS** を使用する。Supabaseの利用は状態管理が必要なアプリ（スケジュールなど）のみ任意とし、必須ではない（天気アプリのように外部APIを叩くだけのものは不要）。以下の2画面を必ず実装する。

1. `/widget` (ダッシュボード埋め込み用):
   * 縦横比固定（例: 高さ200px）のウィジェットUI。
   * スクロール禁止（`overflow: hidden`）。
   * `next.config.ts` の `Content-Security-Policy` (frame-ancestors) でダッシュボードからのiframe埋め込みを許可すること。許可ドメインは環境変数 `process.env.NEXT_PUBLIC_DASHBOARD_URL` から動的に生成し、ハードコードしない（ローカル開発と本番でURLが異なるため）。
2. `/` (全画面メインアプリ):
   * 遷移後に表示されるリッチなメイン画面。新入生がAIを使って自由に機能開発（バイブコーディング）を行う。
   * 画面右下に必ず「ダッシュボードへ戻る」共通ボタン（テンプレートに同梱）を配置すること。遷移先は `NEXT_PUBLIC_DASHBOARD_URL`。

## 4. AI駆動開発の暴走防止ルール（GEMINI.md / .cursorrules）
新入生がAI（Gemini等）を用いて開発する際、デザインの統一感を破壊させないため、テンプレートリポジトリのルートに以下のルールを明記したファイルを配置する。AIエディタはこのルールを絶対厳守すること。

```text
# AIアシスタントへの絶対的な制約事項（Rule）

1. 【コンポーネントの保護】 `components/ui/` 配下のファイルは絶対に編集・削除しないこと。
2. 【UI実装のルール】 標準のHTMLタグ（<button>, <input> 等）に直接Tailwindクラスを当てて独自のUIを作ることを固く禁ずる。必ず `components/ui/` から提供されている既存のコンポーネントをインポートして使用すること。
3. 【新規コンポーネントの配置先】 アプリ独自の新しいコンポーネントを作成する場合は、必ず `components/features/` ディレクトリ内に作成すること。`components/ui/` には絶対に新規ファイルを追加しない。
4. 【カラーコードの禁止】 Tailwindのユーティリティクラスで色を直接ハードコードしないこと（例: `text-red-500` や `bg-[#ff0000]` は禁止）。必ず `text-primary`、`bg-secondary`、`text-muted` など、テーマ変数を使用すること。
5. 【パッケージ追加の許可】 新しいnpmパッケージをインストールする構成変更を提案する場合、実行前に必ずユーザーに許可を求めること。
6. 【ダッシュボード連携】 `/widget` 画面を作成する際は、親要素の高さと幅に100%追従し、スクロールバーを絶対に出さない実装にすること。
7. 【APIキーの保護】 外部APIのキーやシークレットを含む環境変数には、絶対に `NEXT_PUBLIC_` プレフィックスを付けないこと。付けるとクライアント側に露出し流出する。外部API呼び出しは Route Handler または Server Component でサーバー側から行うこと。
```

## 5. デプロイ環境とローカル開発

### 5-1. デプロイ先
全アプリ・ダッシュボードとも **Vercel** にデプロイする。GitHubリポジトリと連携し、`main` ブランチへのpushで自動デプロイされる。

### 5-2. URL命名規則
| アプリ | ローカル開発 | 本番URL |
|---|---|---|
| ダッシュボード | `http://localhost:3000` | `https://dsc-dashboard.vercel.app` |
| スケジュール | `http://localhost:3001` | `https://dsc-schedule.vercel.app` |
| 天気 | `http://localhost:3002` | `https://dsc-weather.vercel.app` |
| 電車 | `http://localhost:3003` | `https://dsc-transit.vercel.app` |
| ニュース | `http://localhost:3004` | `https://dsc-news.vercel.app` |
| 部室人数 | `http://localhost:3005` | `https://dsc-occupancy.vercel.app` |

各アプリの `package.json` で dev ポートを固定：
```json
"scripts": { "dev": "next dev -p 3002" }
```

### 5-3. 環境変数
各アプリの `.env.local` に以下を設定：
```
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
```
本番ではVercelのプロジェクト設定画面で `https://dsc-dashboard.vercel.app` を登録する。未設定時はビルドエラーにする（起動してから壊れるより早期に気づけるため）。

### 5-4. 実行環境
- **Node.js**: 20 LTS
- **TypeScript**: `strict: true` 必須
- `.nvmrc` に `20` を記載してテンプレートに同梱

## 6. セキュリティ要件

### 6-1. iframe sandbox属性
ダッシュボード側がウィジェットを埋め込む `<iframe>` には以下を必ず付ける：
```html
<iframe sandbox="allow-scripts" src="..." />
```
- `allow-same-origin` は付けない
- `allow-top-navigation` は付けない（親ページの遷移を奪われない）

### 6-2. ダッシュボード自身のクリックジャック対策
ダッシュボードの `next.config.ts` で以下のレスポンスヘッダを設定：
```
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'
```

### 6-3. APIキー管理
- 外部API呼び出しは Next.js **Route Handler または Server Component** で行う
- APIキーを格納する環境変数は `NEXT_PUBLIC_` を絶対に付けない（付けるとクライアントに露出する）
- GitHubに `.env.local` を誤コミットしないよう `.gitignore` にデフォルトで含める

### 6-4. HTTPS強制
全アプリHTTPS必須。Vercelが自動で付与する。

## 7. ウィジェット仕様

### 7-1. サイズ
- 幅: 親コンテナの100%（ダッシュボード側サイドバー幅 = 画面30%）
- 高さ: **180px固定**
- 個数: 最大4個（天気・電車・ニュース・部室人数）
- ウィジェット間の縦マージン: 12px

### 7-2. 自動更新
- **ウィジェット内部**: 60秒ごとにデータを再取得（Server Components の `revalidate: 60` または `setInterval`）
- **ダッシュボード全体**: 5分に1回 `window.location.reload()`（長時間表示のメモリリーク対策）

### 7-3. フォールバック
ダッシュボード側に `WidgetFrame` コンポーネントを用意し、各ウィジェットをこれで包む：
- 10秒以内に `onLoad` が発火しなければフォールバックUI表示
- `onerror` 発火時もフォールバックに切り替え

```tsx
<WidgetFrame src={weatherUrl} fallback="天気情報を取得できません" />
```

## 8. テンプレート・運用

### 8-1. テンプレートリポジトリのディレクトリ構造
```
dsc-template-app/
├── app/
│   ├── page.tsx                # / 全画面メイン
│   ├── widget/page.tsx         # /widget 埋め込み用
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                     # 触るな（shadcn/ui標準）
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── back-to-dashboard.tsx
│   └── features/               # 独自コンポーネントはここ
├── lib/
│   └── utils.ts
├── GEMINI.md
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── .env.example
├── .nvmrc
└── README.md
```

### 8-2. デザイントークン
shadcn/ui の標準トークンを採用。`app/globals.css` に以下を記載：
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83% 53%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16% 47%;
  --accent: 210 40% 96%;
  --destructive: 0 84% 60%;
  --border: 214.3 31.8% 91.4%;
}
```
Tailwindで `text-primary`、`bg-muted` のように参照する。

### 8-3. 戻るボタン仕様
- 配置: `position: fixed; bottom: 16px; right: 16px`
- 最小タップ領域: 48×48px（iOSガイドライン準拠）
- 文言: `← ダッシュボードへ戻る`
- 実装: shadcn/ui の `<Button variant="secondary">` を使用
- `components/ui/back-to-dashboard.tsx` としてテンプレートに同梱

### 8-4. iPad運用
- ブラウザ: Safari
- モード: **アクセスガイド**（設定 → アクセシビリティ）でフルスクリーン固定
- 向き: 横向き
- 自動スリープ: オフ（設定 → 画面表示と明るさ → 自動ロック → なし）
- ダッシュボードURLをホーム画面に追加し、アイコン起動することでアドレスバー非表示化

## 9. 参考ドキュメント
- [GUIDE.md](./GUIDE.md): 各決定の背景、使う技術の解説、初心者向け実装ガイド
- [HANDOFF.md](./HANDOFF.md): プロジェクト引き継ぎメモ