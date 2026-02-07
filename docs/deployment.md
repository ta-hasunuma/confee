# デプロイ手順

confee を AWS 環境にデプロイするための手順書。

## 前提条件

### 必要なツール

| ツール | バージョン | 用途 |
|--------|----------|------|
| Node.js | >= 20 | CDK CLI 実行 |
| npm | Node.js 付属 | パッケージ管理 |
| AWS CLI | v2 | AWS 操作・クレデンシャル管理 |
| AWS CDK CLI | >= 2.x | インフラデプロイ (`npm install` で `devDependencies` に含まれる) |
| Docker | 最新 | エージェントコンテナイメージのビルド |
| Python | >= 3.13 | エージェント開発・テスト (デプロイ自体には不要) |
| uv | 最新 | Python パッケージ管理 (エージェント開発時のみ) |

### AWS アカウント要件

- Amazon Bedrock の Claude モデルへのアクセスが有効化されていること（`ap-northeast-1` リージョン）
  - 使用モデル: `apac.anthropic.claude-sonnet-4-20250514-v1:0`
- Amazon Bedrock AgentCore が利用可能なリージョンであること
- IAM で CDK デプロイに必要な権限（AdministratorAccess 推奨、または必要最低限のポリシー）

### connpass API キー

- [connpass API v2](https://connpass.com/about/api/) のページから API キーを取得しておくこと
- デプロイ後に AWS Secrets Manager に登録する（後述）

---

## 環境変数一覧

### デプロイ時に必要

| 変数名 | 必須 | 説明 | 例 |
|--------|------|------|----|
| `AWS_ACCESS_KEY_ID` | Yes* | AWS クレデンシャル | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | Yes* | AWS クレデンシャル | `wJal...` |
| `AWS_DEFAULT_REGION` | Yes | デプロイ先リージョン | `ap-northeast-1` |
| `AWS_PROFILE` | No | AWS CLI プロファイル名（クレデンシャルの代替） | `confee` |

> \* `AWS_PROFILE` を使用する場合は `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` は不要

### デプロイ後に設定（AWS Secrets Manager）

| シークレット名 | 説明 | 設定方法 |
|---------------|------|---------|
| `confee/connpass-api-key` | connpass API v2 の API キー | デプロイ後に Secrets Manager で値を設定 |

### エージェント実行時（CDK が自動設定）

以下はCDK が Lambda / AgentCore Runtime に自動的に設定する環境変数であり、手動設定は不要。

| 変数名 | 設定先 | 説明 |
|--------|-------|------|
| `AGENT_RUNTIME_ARN` | Chat Lambda | AgentCore Runtime の ARN |

---

## デプロイ手順

### 1. AWS クレデンシャルの設定

以下のいずれかの方法で AWS クレデンシャルを設定する。

**方法A: 環境変数**

```bash
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=ap-northeast-1
```

**方法B: AWS CLI プロファイル**

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

対象の AWS アカウント・リージョンで初めて CDK を使う場合に必要。CDK がアセット（Docker イメージ、Lambda コード等）を格納するための S3 バケットと ECR リポジトリを作成する。

```bash
cd infra
npx cdk bootstrap
```

### 4. デプロイ前の差分確認（任意）

```bash
cd infra
npx cdk diff
```

### 5. 全スタックをデプロイ

```bash
cd infra
npx cdk deploy --all --require-approval broadening
```

> `--require-approval broadening` は IAM 権限の拡大時のみ承認を求めるオプション。初回デプロイ時は複数回承認を求められる。

デプロイは以下の順序で実行される（CDK が依存関係を自動解決）:

1. **ConfeeAgentCoreStack** (10〜30分)
   - エージェントの Docker イメージをビルドし ECR にプッシュ
   - AgentCore Runtime 用の IAM ロールを作成
   - Custom Resource で AgentCore Runtime を作成（microVM 起動待ち）
2. **ConfeeApiStack** (5分程度)
   - Secrets Manager シークレット (`confee/connpass-api-key`) を作成
   - Health Check Lambda / Chat Lambda Proxy を作成
   - API Gateway REST API を作成
3. **ConfeeFrontendStack** (5分程度)
   - S3 バケットを作成しプレースホルダーページをデプロイ
   - CloudFront ディストリビューションを作成

> **注意**: ConfeeAgentCoreStack は AgentCore Runtime の起動完了を待つため、初回デプロイ時は **最大30分** かかる場合がある。

### 6. connpass API キーの設定

デプロイ後、AWS Secrets Manager に connpass API キーを登録する。

**AWS CLI を使用する場合:**

```bash
aws secretsmanager put-secret-value \
  --secret-id confee/connpass-api-key \
  --secret-string "your-connpass-api-key"
```

**AWS マネジメントコンソールを使用する場合:**

1. [Secrets Manager コンソール](https://console.aws.amazon.com/secretsmanager/) を開く
2. シークレット `confee/connpass-api-key` を選択
3. 「シークレットの値を取得する」→「編集」でAPI キーを入力
4. 保存

> **補足**: API キーを未設定のままでもエージェントは動作する（モックデータで応答）。本番運用時は必ず設定すること。

---

## デプロイ後の確認

デプロイ完了後、CloudFormation の出力からエンドポイント URL を確認する。

```bash
# スタック出力の確認
cd infra
npx cdk list
aws cloudformation describe-stacks --stack-name ConfeeApiStack --query 'Stacks[0].Outputs'
aws cloudformation describe-stacks --stack-name ConfeeFrontendStack --query 'Stacks[0].Outputs'
aws cloudformation describe-stacks --stack-name ConfeeAgentCoreStack --query 'Stacks[0].Outputs'
```

### API ヘルスチェック

```bash
curl https://<API_GATEWAY_URL>/health
# 期待レスポンス: {"status": "ok"}
```

### Chat エンドポイントのテスト

```bash
curl -X POST https://<API_GATEWAY_URL>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "TypeScriptのカンファレンスある？"}'
```

### フロントエンドの確認

```bash
open https://<CLOUDFRONT_DOMAIN_NAME>
```

---

## 個別スタックのデプロイ

特定のスタックのみ更新する場合:

```bash
cd infra

# AgentCore Runtime のみ（エージェントコード変更時）
npx cdk deploy ConfeeAgentCoreStack

# API スタックのみ（Lambda / API Gateway 変更時）
npx cdk deploy ConfeeApiStack

# フロントエンドのみ（UI 変更時）
npx cdk deploy ConfeeFrontendStack
```

---

## スタック構成とリソース一覧

| スタック | リソース | 説明 |
|---------|---------|------|
| `ConfeeAgentCoreStack` | ECR (Docker Image Asset) | エージェントコンテナイメージ (ARM64) |
| | IAM Role | AgentCore Runtime 用 (Bedrock InvokeModel 権限) |
| | Custom Resource Lambda x2 | AgentCore Runtime の作成/削除/ステータス確認 |
| | AgentCore Runtime | Strands Agent のホスティング (microVM) |
| `ConfeeApiStack` | Secrets Manager | connpass API キーの管理 |
| | Lambda (Health) | GET /health エンドポイント |
| | Lambda (Chat Proxy) | POST /chat → AgentCore Runtime 呼び出し |
| | API Gateway REST API | HTTP エンドポイント |
| `ConfeeFrontendStack` | S3 Bucket | 静的ファイルホスティング |
| | CloudFront Distribution | CDN + HTTPS 配信 |
| | S3 BucketDeployment | フロントエンドファイルのアップロード |

---

## 削除（クリーンアップ）

全リソースを削除する場合:

```bash
cd infra
npx cdk destroy --all
```

> **注意**: AgentCore Runtime の削除には数分かかる場合がある。S3 バケットは `autoDeleteObjects: true` が設定されているため、オブジェクトごと自動削除される。

---

## トラブルシューティング

### AgentCore Runtime の作成がタイムアウトする

Custom Resource の最大待機時間は30分。タイムアウトした場合は CloudFormation スタックがロールバックされる。

- CloudWatch Logs で Custom Resource Lambda のログを確認
- AgentCore Runtime のステータスを直接確認: `aws bedrock-agentcore get-agent-runtime --agent-runtime-id <id>`

### Docker ビルドが失敗する

- Docker Desktop が起動していることを確認
- ARM64 プラットフォームのビルドが必要なため、Docker の Buildx が利用可能であることを確認

```bash
docker buildx ls
```

### Chat Lambda が 503 を返す

- AgentCore Runtime が `READY` 状態であることを確認
- Lambda の環境変数 `AGENT_RUNTIME_ARN` が正しく設定されていることを確認
- CloudWatch Logs で Lambda のエラーログを確認

### connpass API 検索結果が返らない

- Secrets Manager に正しい API キーが設定されていることを確認
- API キー未設定の場合はモックデータが返される（正常動作）
