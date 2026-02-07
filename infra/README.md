# Confee インフラストラクチャ

AWS CDK (TypeScript) によるインフラ定義。

## スタック構成

| スタック | リソース | 説明 |
|---------|---------|------|
| `ConfeeAgentCoreStack` | ECR + IAM + Custom Resource + AgentCore Runtime | エージェントコンテナのビルド・デプロイ、AgentCore Runtime の管理 |
| `ConfeeApiStack` | Lambda + API Gateway REST API + Secrets Manager | `/health`・`/chat` エンドポイント、connpass APIキー管理 |
| `ConfeeFrontendStack` | S3 + CloudFront + BucketDeployment | React SPA のホスティング |

> 詳細なデプロイ手順は [docs/deployment.md](../docs/deployment.md) を参照。

## 前提条件

- Node.js v20 以上
- AWS CLI v2 がインストール済み
- Docker がインストール済み（エージェントコンテナイメージのビルドに必要）
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
npx cdk deploy ConfeeAgentCoreStack
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

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `AWS_ACCESS_KEY_ID` | Yes* | AWS クレデンシャル |
| `AWS_SECRET_ACCESS_KEY` | Yes* | AWS クレデンシャル |
| `AWS_DEFAULT_REGION` | Yes | デプロイ先リージョン（推奨: `ap-northeast-1`） |
| `AWS_PROFILE` | No | AWS CLI プロファイル名（クレデンシャルの代替） |

> \* `AWS_PROFILE` を使用する場合は不要

connpass API キーは AWS Secrets Manager (`confee/connpass-api-key`) で管理。デプロイ後に設定する。

## ディレクトリ構成

```
infra/
├── bin/
│   └── infra.ts                        # CDK アプリエントリポイント
├── lib/
│   ├── agentcore-stack.ts              # AgentCore Runtime スタック
│   ├── api-stack.ts                    # API Gateway + Lambda スタック
│   └── frontend-stack.ts              # S3 + CloudFront スタック
├── lambda/
│   ├── agentcore-custom-resource/
│   │   └── index.py                   # AgentCore Runtime 管理 Custom Resource
│   └── health/
│       └── index.py                   # ヘルスチェック Lambda ハンドラー
├── frontend/
│   └── index.html                     # プレースホルダーページ
└── test/
    ├── agentcore-stack.test.ts        # AgentCore スタックのテスト
    ├── api-stack.test.ts              # API スタックのテスト
    └── frontend-stack.test.ts         # フロントエンドスタックのテスト
```
