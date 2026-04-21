# 新入生向け開発ガイド

このドキュメントは「初めてWeb開発をやる新入生」に向けた解説です。spec.mdで決まった仕様の「なぜそうなっているのか」を順に説明します。AIに実装を任せていても、自分が何を作っているかが分かるよう、背景・用語・落とし穴を丁寧に書いています。

> **読み方**: 必要なときに目次から該当セクションを開いてください。全部を最初に読む必要はありません。

---

## 目次

1. [このプロジェクトで作るもの](#1-このプロジェクトで作るもの)
2. [バイブコーディングとの付き合い方](#2-バイブコーディングとの付き合い方)
3. [使う技術の紹介](#3-使う技術の紹介)
4. [設計の「なぜ」解説](#4-設計のなぜ解説)
5. [セキュリティ解説](#5-セキュリティ解説)
6. [実装ガイド](#6-実装ガイド)
7. [デプロイガイド（Vercel）](#7-デプロイガイドvercel)
8. [iPad運用ガイド](#8-ipad運用ガイド)
9. [よくあるハマりどころ](#9-よくあるハマりどころ)

---

## 1. このプロジェクトで作るもの

岡山大学DS部の部室にあるiPadで、**朝誰かが起動して夜スリープする形で常時表示する**ダッシュボード画面を作ります（完全 24h 稼働ではなくスリープ運用）。

画面の構成：
- **左70%**: スケジュールアプリ（MTG日程、部室利用状況）
- **右30%**: 小さなウィジェット4つ（天気・電車・ニュース・部室の人数）

ウィジェットをタップすると、そのアプリの全画面ページに飛びます。右下の「ダッシュボードへ戻る」ボタンで戻ります。

各アプリは**同じリポジトリの `apps/` 以下の別ディレクトリ・別チーム**が担当します。最後にダッシュボードが全アプリを統合します。
アプリ開発におけるルールはGEMINI.mdに記載します。


---

## 2. バイブコーディングとの付き合い方

バイブコーディングとは「AIに自然言語で指示して、感覚的にコードを書いてもらう」開発スタイルです。このプロジェクトでは新入生がこの手法で実装します。

### AIを使うときの心構え

- **AIが書いたコードの意味を理解しよう**: 動くからOKではなく、何をしているかを言語化できる状態を目指す
- **ルールファイル（GEMINI.md）を絶対に消さない**: AIの暴走を防ぐ安全装置です
- **エラーが出たら全文コピーしてAIに見せる**: 自己流に要約すると解決が遠のきます
- **新しいパッケージを入れる提案が出たら一度止める**: 本当に必要か、AIに理由を聞く

### AIがやりがちな問題と対策

| AIの挙動 | 対策 |
|---|---|
| デザインをバラバラにする | `components/ui/` を使わせるルールで防御 |
| APIキーを `NEXT_PUBLIC_` で公開する | GEMINI.md のルール7で禁止 |
| 勝手に大量パッケージを追加する | ルール5で事前確認を義務化 |
| `components/ui/` を勝手に書き換える | ルール1で保護 |

---

## 3. 使う技術の紹介

### 3-1. Next.js（ネクスト・ジェーエス）
ReactというUIライブラリを使いやすくまとめた **フレームワーク** です。Webアプリを作るときの「ルーティング（URLの管理）」「画像最適化」「サーバー処理」などを全部用意してくれます。

- 公式: https://nextjs.org/
- 本プロジェクトは **App Router** を使います（`app/` フォルダの中にページファイルを置く新しい方式）

### 3-2. React（リアクト）
Next.jsの中身。UIを「コンポーネント」という部品に分けて組み立てる仕組み。ボタン・カード・画面などを全部コンポーネントとして書きます。

### 3-3. TypeScript（タイプスクリプト）
JavaScriptに **型** を足したもの。変数や関数が「何の種類のデータを扱うか」を明示することで、バグを書いた瞬間にエディタが警告してくれます。

このプロジェクトは `strict: true` で厳しめに設定します。最初は型エラーに戸惑いますが、**型エラーはバグの予告**なので丁寧に直しましょう。

### 3-4. Tailwind CSS（テイルウィンド）
クラス名でスタイルを当てるCSSライブラリ。`<button className="bg-blue-500 px-4 py-2">` のように書きます。

本プロジェクトでは **色は `bg-primary` などのテーマ変数を使う**ルールです。`bg-blue-500` のような直接指定は禁止（色が統一されなくなるため）。

### 3-5. shadcn/ui（シャドシーエヌ・ユーアイ）
ボタン・カードなどの基本UIコンポーネント集。**npmパッケージではなくコードをそのままコピーしてプロジェクトに置く**のが特徴。

本プロジェクトのテンプレートには `components/ui/` にあらかじめ置かれています。**絶対に編集しない**でください（デザイン統一のため）。

### 3-6. Supabase（スーパベース）
データベース + 認証 + ストレージをまとめたバックエンドサービス。PostgreSQLがベース。

このプロジェクトでは **スケジュールアプリなど、データを保存する必要があるアプリだけ**使います。天気アプリのように外部APIを叩くだけのアプリには不要です。

### 3-7. Vercel（バーセル）
Next.jsを作った会社が提供するデプロイサービス。GitHubとつなぐだけで、push = 自動で本番公開。無料枠で十分です。

- 公式: https://vercel.com/
- HTTPS自動化、プレビューURL、環境変数管理などが全部付いてくる

### 3-8. Git / GitHub
コードのバージョン管理ツール（Git）とその共有サービス（GitHub）。チーム開発の土台です。

- 最低限知っておくコマンド: `git add`, `git commit`, `git push`, `git pull`, `git status`
- AIが自動でコミットしてくれる場合もあるが、**自分でも意味を理解する**

### 3-9. iframe（アイフレーム）
HTMLの仕組みで、あるWebページの中に別のWebページを埋め込めるもの。
```html
<iframe src="https://dsc-weather.vercel.app/widget" />
```
本プロジェクトの統合の核です。詳細は [§4-2](#4-2-なぜiframe統合なのか) で説明します。

---

## 4. 設計の「なぜ」解説

### 4-1. なぜモノレポにしたのか
全アプリを `apps/` 以下の同一リポジトリで管理する理由：

1. **共通コンポーネントを共有できる**: `packages/ui/` に shadcn/ui を置けば全アプリで使い回せる
2. **環境が統一される**: Node.js バージョン・tsconfig・Tailwind 設定を 1 箇所で管理
3. **開発が楽になる**: `pnpm dev` 一発で全アプリが起動する
4. **デプロイは独立している**: Vercel でアプリごとに別プロジェクトを作り、`apps/<name>` を Root Directory に指定すればアプリ単位でデプロイできる

**「コンフリクトが増えないか？」**: 各チームは `apps/自分のアプリ/` しか触らないため、実質コンフリクトは発生しません。`packages/ui/` 等の共通部分は上級生が管理します。

### 4-2. なぜiframe統合なのか
代替案としてJSON API方式（各アプリがJSONを返し、ダッシュボード側がUIを描く）も検討しましたが、現時点ではiframe方式を採用しています。

**iframeを選んだ理由：**
- **各チームの作業量が少ない**: UIだけ作ればよく、APIを別途実装する必要がない
- **既存アプリをそのまま活かせる**: スケジュール・部室人数アプリはすでに動いており、API化のための作り直しが不要
- **ダッシュボード側の実装コストが低い**: API受け取り＋UI再実装が不要

**iframeのデメリット（正直に）：**
- 各アプリが独立したブラウザコンテキストを持つため、メモリ使用量が多い
- §7-3 のソフトリロード・全体リロード戦略で対策しているが、完全な解決ではない

**フォールバック方針：** §8-6 の 24 時間放置テストでヒープ増加が合格基準（200MB）を超えた場合は、JSON API 方式への切り替えを検討します。

### 4-3. 透過オーバーレイリンク（Transparent Overlay Link）とは
右サイドバーのウィジェットは、ユーザーがiframe内のボタンを誤タップしないよう、iframeを「見せるだけ」にして、カード全体をリンク化します。

```tsx
<Link href="https://dsc-weather.vercel.app">
  <iframe
    src="https://dsc-weather.vercel.app/widget"
    sandbox="allow-scripts"
    style={{ pointerEvents: "none" }}
  />
</Link>
```

- `pointer-events: none` でiframe内のクリックを無効化
- 外側の `<Link>` が全体をクリッカブルにする
- タップ → 通常のURL遷移で全画面ページへ

### 4-4. なぜshadcn/uiなのか
- コードをコピーして使うので、気に入らない部分は自分で直せる
- 業界標準で情報が多い（困ったときググりやすい）
- TailwindベースなのでTailwindの知識がそのまま活きる

### 4-5. なぜVercelなのか
- Next.jsとの相性が最も良い（両者同じ会社）
- 無料枠で学生利用には十分
- GitHub連携でpushするだけで公開
- HTTPSが自動で付く（セキュリティ要件を自然に満たす）

---

## 5. セキュリティ解説

### 5-1. iframeのsandbox属性とは
iframeに埋め込んだ中身が、親ページに悪さをできないよう制限する仕組みです。

```html
<iframe sandbox="allow-scripts" />
```

`sandbox="allow-scripts"` の意味：
- JavaScriptは動かしてOK（これを外すとReactが動かない）
- それ以外の権限（フォーム送信、ポップアップ、親ページ遷移など）は全部禁止

**なぜ重要**: 新入生がAIで作ったコードに、`window.top.location = "悪いサイト"` みたいな危険コードが紛れ込んでも、sandboxが防いでくれます。

### 5-2. CSP (Content Security Policy) と frame-ancestors
「このページを誰がiframeで埋め込んでいいか」をサーバー側から指定するセキュリティヘッダです。

```
Content-Security-Policy: frame-ancestors https://dsc-dashboard.vercel.app
```

この設定を各アプリの `/widget` に付けることで、**ダッシュボード以外のサイトが勝手に埋め込むこと**を防ぎます。悪意ある人が `dsc-weather` を自分のサイトに埋め込んで偽ダッシュボードを作る、みたいな攻撃を防御します。

Next.jsでは `next.config.ts` の `headers()` で設定します。

### 5-3. X-Frame-Options と frame-ancestors 'none'
ダッシュボード自身を守るための設定。

```
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'
```

これを付けないと、悪意あるサイトが `<iframe src="dsc-dashboard.vercel.app">` でダッシュボードをまるごと埋め込んで、部員を騙して偽クリックさせる「クリックジャッキング攻撃」が成立します。

X-Frame-Options は古い仕組み、frame-ancestors は新しい仕組み。両方付けると古いブラウザも新しいブラウザも両方守れます。

### 5-4. APIキーが漏れるとどうなるか
例：天気APIの無料枠が1日1000回まで。キーが漏れると他人に使われ、あっという間に上限到達 → 自分のアプリが動かなくなる。有料プランだと請求が来ることも。

GitHubに誤ってpushすると、自動でスキャンしているBotに数秒で拾われます。**一度pushしたら削除しても復旧できないと思うこと**（リセットしてもGitHubのキャッシュに残る）。

対策：
- `.env.local` は `.gitignore` に入れてコミット対象にしない
- 漏れたら即座にキー再発行

### 5-5. `NEXT_PUBLIC_` プレフィックスの意味
Next.jsの環境変数ルール：

- `DATABASE_URL` → サーバー側のみ使える（ブラウザには届かない）
- `NEXT_PUBLIC_API_URL` → ブラウザにも埋め込まれる（誰でも見える）

**ブラウザに埋め込まれるとは何か**: ビルド時に `process.env.NEXT_PUBLIC_XXX` は実際の値に置き換えられ、JSファイルに文字列として焼き込まれます。そのJSはブラウザに配信されるので、開発者ツールで覗けば誰でも見れます。

- ダッシュボードのURLのように「公開して問題ないもの」 → `NEXT_PUBLIC_` を付ける
- APIキーのように「絶対秘密のもの」 → `NEXT_PUBLIC_` を付けない

### 5-6. 外部API呼び出しはサーバー側から
クライアント側から直接天気APIを叩こうとすると、APIキーがブラウザに必要 = 露出します。代わりに：

```
ブラウザ → 自分のNext.jsサーバー（APIキーを持つ） → 外部API
         ↑
        この経路ならキーがブラウザに出ない
```

Next.jsでこれをやるには：
- **Server Component**: `app/page.tsx` でそのままfetch（デフォルトはサーバー実行）
- **Route Handler**: `app/api/weather/route.ts` に専用エンドポイントを作る

---

## 6. 実装ガイド

### 6-1. 環境変数の使い方
各アプリのルートに `.env.local` を作り、以下を書きます：
```
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000
WEATHER_API_KEY=sk-xxxxxx
```

コードから参照：
```typescript
// サーバー側（Route Handler / Server Component）
const key = process.env.WEATHER_API_KEY;

// クライアントでも使えるもの
const url = process.env.NEXT_PUBLIC_DASHBOARD_URL;
```

**注意**: `.env.local` は Git にコミットしない。`.env.example` にサンプルを置き、中身は空にする：
```
# .env.example (コミットOK)
NEXT_PUBLIC_DASHBOARD_URL=
WEATHER_API_KEY=
```

### 6-2. 環境変数の未設定チェック
`lib/env.ts` を作ってまとめてチェック：
```typescript
if (!process.env.NEXT_PUBLIC_DASHBOARD_URL) {
  throw new Error("NEXT_PUBLIC_DASHBOARD_URL is required");
}

export const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL;
```
各所で `import { DASHBOARD_URL } from "@/lib/env"` して使う。

### 6-3. CSP設定の書き方
`next.config.ts`:
```typescript
const dashboardUrl = process.env.NEXT_PUBLIC_DASHBOARD_URL;
if (!dashboardUrl) throw new Error("NEXT_PUBLIC_DASHBOARD_URL is required");

export default {
  async headers() {
    return [
      {
        source: "/widget",
        headers: [
          {
            key: "Content-Security-Policy",
            value: `frame-ancestors ${dashboardUrl}`,
          },
        ],
      },
    ];
  },
};
```

### 6-4. /widget ページの作り方
`app/widget/page.tsx`:
```tsx
export const revalidate = 60;  // 60秒ごとにサーバーで再生成

export default async function WidgetPage() {
  const data = await fetchWeather();

  return (
    <>
      <meta httpEquiv="refresh" content="60" />
      <div className="h-[180px] w-full overflow-hidden bg-background">
        <p className="text-primary">{data.temperature}°C</p>
      </div>
    </>
  );
}
```

ポイント：
- **Server Components のみで書く**。`'use client'` ディレクティブは禁止（iPad Safari のメモリフットプリント削減のため・spec §3-1）
- `setInterval` / `setTimeout` 等の JS タイマーは禁止。自動更新は `<meta http-equiv="refresh" content="60">` を使う
- 依存ライブラリは最小限に。`/widget` 側で新規 npm パッケージ追加は原則却下（必要なら上級生レビュー）
- 高さは180px固定
- `overflow-hidden` でスクロール禁止
- `bg-primary` 等のテーマ変数を使う（直接色禁止）
- `revalidate = 60`（サーバー側データ更新）と meta refresh（ページ再読み込み）の二段で同期する

### 6-5. 戻るボタンの実装
`components/ui/back-to-dashboard.tsx`（テンプレートに同梱）：
```tsx
import { Button } from "@/components/ui/button";
import { DASHBOARD_URL } from "@/lib/env";

export function BackToDashboard() {
  return (
    <a
      href={DASHBOARD_URL}
      className="fixed bottom-4 right-4"
    >
      <Button variant="secondary" className="min-h-[48px] min-w-[48px]">
        ← ダッシュボードへ戻る
      </Button>
    </a>
  );
}
```

`app/page.tsx` で使う：
```tsx
import { BackToDashboard } from "@/components/ui/back-to-dashboard";

export default function Page() {
  return (
    <main>
      {/* 各チームの画面内容 */}
      <BackToDashboard />
    </main>
  );
}
```

### 6-6. フォールバック付きウィジェット埋め込み（ダッシュボード側）
`components/WidgetFrame.tsx`:
```tsx
"use client";
import { useState, useEffect, useRef } from "react";

export function WidgetFrame({ src, fallback }: { src: string; fallback: string }) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const timerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      if (!loaded) setFailed(true);
    }, 10000);
    return () => clearTimeout(timerRef.current);
  }, [loaded]);

  if (failed) {
    return <div className="h-[180px] grid place-items-center text-muted-foreground">{fallback}</div>;
  }

  return (
    <iframe
      src={src}
      sandbox="allow-scripts"
      className="h-[180px] w-full"
      style={{ pointerEvents: "none" }}
      onLoad={() => setLoaded(true)}
      onError={() => setFailed(true)}
    />
  );
}
```

上は最小実装。spec §7-5 では次の 3 点を追加で要求している：

- **stale バッジ**: データ取得が失敗しても最後の成功値を保持して表示し、右上に `stale HH:MM` バッジで最終更新時刻を示す
- **オフライン検知**: ダッシュボード側で `window.addEventListener('online' | 'offline', ...)` を監視し、オフライン時は画面上部に細いバナーを出す
- **通信断 5 分でグレースケール**: オフラインが 5 分続いたら全 iframe を `filter: grayscale(1)` で暗く（異常を視覚的に伝える）

これらも `WidgetFrame` またはダッシュボードルートレイアウトに組み込むこと。

---

## 7. デプロイガイド（Vercel）

### 7-1. Vercelアカウント作成と最初のデプロイ
1. https://vercel.com/ にアクセス、GitHubでサインアップ
2. **Add New → Project** をクリック
3. `dsc_dashboard` リポジトリを選んで **Import**
4. **Root Directory** を `apps/weather`（自分のアプリのディレクトリ）に変更する ← モノレポでは必須
5. Framework Preset は自動で **Next.js** が選ばれる
6. **Environment Variables** セクションで必要な環境変数を入力：
   - `NEXT_PUBLIC_DASHBOARD_URL` = `https://dsc-dashboard.vercel.app`
   - `WEATHER_API_KEY` = 取得したキー
7. **Deploy** をクリック → 数分待つと本番URLが発行される

### 7-2. 以降の更新
`git push origin main` するだけで、Vercelが自動で再デプロイしてくれます。

PR（プルリクエスト）を作ると、本番とは別の **プレビューURL** が自動で作られます。本番に出す前に動作確認ができます。

### 7-3. 環境変数の変更
Vercelのプロジェクトページ → **Settings → Environment Variables** から追加・変更。変更後は **Deployments → Redeploy** で反映。

### 7-4. カスタムドメイン（任意）
`.vercel.app` のままでも動きます。独自ドメインを当てたい場合は Settings → Domains から追加。学生ならGitHub Student Packでドメインが無料で貰えます。

---

## 8. iPad運用ガイド

### 8-1. ホーム画面への追加
1. iPadのSafariでダッシュボードURLを開く
2. 共有ボタン → **ホーム画面に追加**
3. アプリアイコンが作られる。これをタップして開くとアドレスバー非表示の「フルスクリーンに近いモード」になります

### 8-2. アクセスガイドでフルスクリーン固定
1. **設定 → アクセシビリティ → アクセスガイド** をON
2. パスコードを設定
3. ダッシュボードをアプリアイコンから起動
4. サイドボタン（または電源ボタン）を3回押してアクセスガイド開始
5. これで画面遷移や他アプリへの切り替えがロックされ、サイネージ専用端末になる

### 8-3. 自動スリープをオフ
**設定 → 画面表示と明るさ → 自動ロック → なし**

### 8-4. Wi-Fi切断時の挙動
ダッシュボードのリロードは「累積稼働 12h + `visibilitychange` で visible に復帰した時」をトリガにする（spec §7-3）。固定時刻（例: 朝 6 時）はスリープ中に JS タイマーが発火しないため採用しない。

Wi-Fi 切断中はリロードしても iframe が真っ白になるだけなので、spec §7-5 のオフライン検知バナー・通信断 5 分でのグレースケール化で「異常が起きていること」を視覚的に伝える設計になっている。

---

## 9. よくあるハマりどころ

### 9-1. `process.env.XXX` が undefined
- `.env.local` に書き忘れ
- `NEXT_PUBLIC_` 付きの変数を、ファイル変更後に `next dev` を再起動していない
- Vercel側に環境変数を登録し忘れ

### 9-2. iframeが真っ白になる
- CSP `frame-ancestors` でダッシュボードURLを許可していない
- ローカルでダッシュボードを `localhost:3000`、ウィジェット側の環境変数には `localhost:3001` など異なるURLを登録
- HTTPSとHTTPの混在（Mixed Content）

### 9-3. タップがiframe内に吸われる
- `pointer-events: none` を付け忘れている
- 外側の `<Link>` を `<div>` で囲んでしまっている

### 9-4. ビルドは通るが本番で壊れる
- Server Component と Client Component の混同（`"use client"` の付け忘れ）
- 環境変数が本番（Vercel）側に登録されていない

### 9-5. デザインがバラバラになる
- `components/ui/` 以外で独自ボタンを作った → ルール2違反
- `text-red-500` のような直接カラー指定 → ルール4違反

### 9-6. Supabaseに接続できない
- 本プロジェクトでは「状態管理が必要なアプリだけ」使う方針。天気アプリなどに無理に導入しない
- Supabase URLとanon keyを環境変数に設定し忘れ
- Row Level Security (RLS) で読み取りが拒否されている

### 9-7. iPadで文字が小さい・大きい
- Tailwindのremベースのサイズで書くと、iPadのアクセシビリティ設定（文字サイズ）でズレる場合あり
- ウィジェットは180px固定なので、中身の文字サイズもテストして調整

### 9-8. AIが謎のパッケージを足してくる
- GEMINI.mdルール5を見せて「許可取れ」と伝える
- 入れてしまった後でも `package.json` から消して `npm install` でロールバック可能

---

## 10. 運用品質のための追加対策

spec の §6-5 / §7-3〜7-5 / §8-5〜8-6 で追加された項目の「なぜ」解説。

### 10-1. メモリリーク対策（spec §7-3 解説）

iPad Safari でダッシュボードを何時間も表示し続けると、JS ヒープが少しずつ増えて最終的に「このWebページに問題が起きたため、再読み込みされました」と落ちるリスクがあります。対策は二段構え：

- **30 分ごとのソフトリロード**: JS で `iframe.src = iframe.src` を各 iframe に対して実行。親 DOM は保持したまま子 iframe だけリセット → メモリが定期的に解放され、見た目のチラつきはほぼなし
- **累積 12h + 復帰時の全体リロード**: 「朝 6 時にリロード」ではなく「起動してから 12h 経過＋スリープから復帰した瞬間」に `location.reload()`。理由は、iPad がスリープ中は JS タイマー (`setTimeout`/`setInterval`) が発火しないため、固定時刻トリガは当てにならない

### 10-2. 焼き付き対策（spec §7-4 解説）

液晶は同じピクセルを光らせ続けると色あせ（焼き付き）ます。10 分おきに画面全体を ±1〜2px だけ `transform: translate` でずらすと、人の目には気づかれないが発光ピクセルは入れ替わり、焼き付きリスクを下げられます。

### 10-3. 新ウィジェット追加の手順（spec §8-5 解説）

ダッシュボード本体のコードに触らず、`public/widgets.json` に 1 行足すだけで新しいウィジェットを追加できる設計です。

```json
[
  { "id": "weather", "title": "天気", "url": "https://dsc-weather.vercel.app/widget", "order": 1 }
]
```

新入生チームは自分のアプリを Vercel にデプロイして URL を取得 → このファイルに 1 行 PR → マージされれば部室 iPad に映る、という体験ができます。

### 10-4. 展開前の 24 時間放置テスト（spec §8-6 解説）

本番投入前に、実機（iPad）に本番 URL を表示して 24 時間放置し、Mac の Safari のリモートデバッグ機能で JS ヒープを計測します。

- Mac の Safari → 開発メニュー → USB 接続した iPad を選ぶと、Web Inspector で iPad のページをデバッグできる
- Timelines タブで JS heap size を初期・12h 後・24h 後で比較
- **合格基準**: 24h 後のヒープ成長が 200MB 未満、クラッシュ・白画面・目立つチラつきなし
- 超えていたら §7-2〜7-4 の対策を見直す（特に `'use client'` の紛れ込みや JS タイマーの使用）

### 10-5. シークレット漏洩の CI チェック（spec §6-5 解説）

「`NEXT_PUBLIC_` に API キーを付けるな」はルール 7 で明文化していますが、AI に書かせる都合上、ルール文だけでは漏れる可能性があります。機械的にチェックする最終防衛線を CI に入れます：

- GitHub Actions で `gitleaks` を走らせる（無料）、または `NEXT_PUBLIC_*_API_KEY` / `_TOKEN` / `_SECRET` のような名前を grep で検知
- PR 時点で弾けば、本番に漏れることは構造的に防げる

## 参考リンク

- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Tailwind CSS公式](https://tailwindcss.com/docs)
- [shadcn/ui公式](https://ui.shadcn.com/)
- [Vercel公式](https://vercel.com/docs)
- [Supabase公式](https://supabase.com/docs)
- [MDN Web Docs（HTML/CSS/JSの辞書）](https://developer.mozilla.org/ja/)
