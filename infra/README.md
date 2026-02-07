# Confee インフラストラクチャ

AWS CDK (TypeScript) によるインフラ定義。

## スタック構成

| スタック | リソース | 説明 |
|---------|---------|------|
| `ConfeeApiStack` | Lambda + API Gateway REST API | `/health` エンドポイント（MVP後に `/chat` を追加） |
| `ConfeeFrontendStack` | S3 + CloudFront + BucketDeployment | React SPA のホスティング |

## 前提条件

- Node.js v22 以上
- AWS CLI がインストール済み
- デプロイ先の AWS アカウントへのアクセス権限

## セットアップ

### 1. AWS クレデンシャルの設定

以下のいずれかの方法で設定する。

**環境変数を使う場合:**

```bash
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=ap-northeast-1
```

**AWS CLI プロファイルを使う場合:**

```bash
aws configure --profile confee
export AWS_PROFILE=confee
```

### 2. 依存パッケージのインストール

```bash
cd infra
npm install
```

### 3. CDK Bootstrap（初回のみ）

対象の AWS アカウント・リージョンで初めて CDK を使う場合に必要。CDK がアセットを格納する S3 バケットと IAM ロールを作成する。

```bash
npx cdk bootstrap
```

## デプロイ

### 全スタックをデプロイ

```bash
npx cdk deploy --all
```

### 個別にデプロイ

```bash
npx cdk deploy ConfeeApiStack
npx cdk deploy ConfeeFrontendStack
```

### デプロイ前の差分確認

```bash
npx cdk diff
```

## テスト

```bash
npm test
```

## 環境変数一覧

| 変数名 | 必要なタスク | 説明 |
|--------|------------|------|
| `AWS_ACCESS_KEY_ID` | 全タスク | AWS クレデンシャル |
| `AWS_SECRET_ACCESS_KEY` | 全タスク | AWS クレデンシャル |
| `AWS_DEFAULT_REGION` | 全タスク | デプロイ先リージョン（推奨: `ap-northeast-1`） |
| `CONNPASS_API_KEY` | タスク2以降 | connpass API v2 の API キー |

## ディレクトリ構成

```
infra/
├── bin/
│   └── infra.ts              # CDK アプリエントリポイント
├── lib/
│   ├── api-stack.ts          # API Gateway + Lambda スタック
│   └── frontend-stack.ts     # S3 + CloudFront スタック
├── lambda/
│   └── health/
│       └── index.py          # ヘルスチェック Lambda ハンドラー
├── frontend/
│   └── index.html            # プレースホルダーページ
└── test/
    ├── api-stack.test.ts     # API スタックのテスト
    └── frontend-stack.test.ts # フロントエンドスタックのテスト
```
