# 技術スタック

## アーキテクチャ概要

```
ユーザー
  ↓
CloudFront (CDN + HTTPS)
  ↓
S3 (React SPA)
  ↓ POST /chat
API Gateway REST API
  ↓
Lambda (Chat Proxy)
  ↓ InvokeAgentRuntime
Bedrock AgentCore Runtime (microVM)
  ├── Strands Agent + System Prompt
  ├── Bedrock LLM (Amazon Nova Micro)
  └── search_connpass ツール → connpass API v2
```

## フロントエンド

| 技術 | バージョン | 用途 |
|------|----------|------|
| React | ^19.2.0 | UI フレームワーク |
| TypeScript | ~5.9.3 | 型安全な開発 |
| Tailwind CSS | ^4.1.18 | ユーティリティファースト CSS |
| Vite | ^7.2.4 | ビルドツール・開発サーバー |
| react-markdown | ^10.1.0 | エージェント応答の Markdown レンダリング |
| Vitest | ^4.0.18 | テストフレームワーク |
| @testing-library/react | ^16.3.2 | コンポーネントテスト |

## バックエンド (エージェント)

| 技術 | バージョン | 用途 |
|------|----------|------|
| Python | >= 3.13 | エージェントランタイム |
| Strands Agents SDK | >= 0.1.0 | AI エージェントフレームワーク |
| httpx | >= 0.28.0 | HTTP クライアント (connpass API 呼び出し) |
| bedrock-agentcore | >= 1.0.0 | AgentCore ランタイム統合 |
| boto3 | >= 1.40.0 | Lambda から AgentCore 呼び出し |
| pytest | >= 8.0.0 | テストフレームワーク |

### LLM モデル

- **使用モデル**: `apac.amazon.nova-micro-v1:0` (Amazon Nova Micro)
- **リージョン**: ap-northeast-1
- **選定理由**: 軽量・高速で MVP に十分な性能

## インフラストラクチャ (IaC)

| 技術 | バージョン | 用途 |
|------|----------|------|
| AWS CDK | ^2.237.1 | Infrastructure as Code |
| TypeScript | ~5.9.3 | CDK スタック定義 |
| Jest | ^30 | CDK テスト |

### AWS リソース構成

| スタック | リソース | 説明 |
|---------|---------|------|
| ConfeeAgentCoreStack | ECR, IAM Role, Custom Resource Lambda x2, AgentCore Runtime | エージェントコンテナ (ARM64) のホスティング |
| ConfeeApiStack | Secrets Manager, Lambda (Health/Chat), API Gateway REST API | REST API レイヤー |
| ConfeeFrontendStack | S3, CloudFront, BucketDeployment | 静的フロントエンドホスティング |

## 開発環境

### 必要なツール

| ツール | バージョン | 用途 |
|--------|----------|------|
| Python | >= 3.13 | エージェント開発 |
| uv | 最新 | Python パッケージ管理 |
| Node.js | >= 20 | フロントエンド / CDK |
| Docker | 最新 | エージェントコンテナビルド |
| AWS CLI | v2 | AWS 操作 |

### よく使うコマンド

```bash
# エージェント
cd agent && uv sync --all-extras    # セットアップ
cd agent && uv run pytest           # テスト実行

# フロントエンド
cd frontend && npm install          # セットアップ
cd frontend && npm run dev          # 開発サーバー起動
cd frontend && npm run build        # ビルド
cd frontend && npx vitest           # テスト実行

# インフラ
cd infra && npm install             # セットアップ
cd infra && npm test                # CDK テスト
cd infra && npx cdk synth           # テンプレート生成
cd infra && npx cdk deploy --all    # 全スタックデプロイ
```

## 環境変数

### ローカル開発用 (`.env`)

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CONNPASS_API_KEY` | No | connpass API キー (未設定時はモックデータ) |
| `AWS_DEFAULT_REGION` | Yes | AWS リージョン (`ap-northeast-1`) |

### フロントエンド (`frontend/.env`)

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `VITE_API_URL` | Yes | API Gateway のエンドポイント URL |

### AWS 環境 (CDK が自動設定)

| 変数名 | 設定先 | 説明 |
|--------|-------|------|
| `AGENT_RUNTIME_ARN` | Chat Lambda | AgentCore Runtime の ARN |

### AWS Secrets Manager

| シークレット名 | 説明 |
|---------------|------|
| `confee/connpass-api-key` | connpass API v2 の API キー |

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/health` | ヘルスチェック (`{"status": "ok"}`) |
| POST | `/chat` | チャットメッセージ送信 (`{message, session_id}` → `{response, session_id}`) |

## 外部 API

- **connpass API v2**: `https://connpass.com/api/v2/events/`
  - レート制限: 1秒1リクエスト
  - タイムアウト: 5秒
  - User-Agent: `confee/1.0`
  - 認証: API キー (`X-API-Key` ヘッダー)
