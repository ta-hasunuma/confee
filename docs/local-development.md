# ローカル開発ガイド

## 前提条件

| ツール | バージョン | 用途 |
|--------|----------|------|
| Python | >= 3.13 | エージェント開発 |
| uv | 最新 | Python パッケージ管理 |
| Node.js | >= 20 | インフラ (CDK) / フロントエンド |
| AWS CLI | v2 | AWS操作 |
| AWS CDK CLI | >= 2.x | インフラデプロイ |

## プロジェクト構成

```
confee/
├── agent/          # Python - Strands Agent + connpass ツール
├── frontend/       # React SPA (未実装)
├── infra/          # AWS CDK (TypeScript)
└── docs/           # ドキュメント
```

## 1. エージェント (agent/)

### セットアップ

```bash
cd agent
uv sync --all-extras
```

### 環境変数

`.env` ファイルをプロジェクトルートに作成:

```bash
# connpass API キー (未設定の場合はモックデータで動作)
CONNPASS_API_KEY=

# AWS Bedrock 用 (エージェント実行時に必要)
AWS_DEFAULT_REGION=ap-northeast-1
```

> **Note**: `CONNPASS_API_KEY` が未設定の場合、10件のモックイベントデータを使用して動作します。API キー取得前でも開発・テストが可能です。

### テスト実行

```bash
cd agent

# 全テスト実行
uv run pytest

# 詳細出力
uv run pytest -v

# 特定テストクラスのみ
uv run pytest src/confee_agent/tests/test_search_connpass.py::TestMockFallback -v
```

### connpass ツール手動テスト

```bash
cd agent

# モックデータでテスト (API キー不要)
uv run python -c "
from confee_agent.tools.search_connpass import _search_connpass_api
result = _search_connpass_api(keyword='TypeScript')
print(f'件数: {result.results_returned}/{result.results_available}')
for e in result.events:
    print(f'  - {e.title} ({e.started_at})')
"

# OR検索テスト
uv run python -c "
from confee_agent.tools.search_connpass import _search_connpass_api
result = _search_connpass_api(keyword_or='Python,Rust')
print(f'件数: {result.results_returned}/{result.results_available}')
for e in result.events:
    print(f'  - {e.title}')
"
```

`CONNPASS_API_KEY` を設定した場合は実際の connpass API を呼び出します:

```bash
CONNPASS_API_KEY=your-key uv run python -c "
from confee_agent.tools.search_connpass import _search_connpass_api
result = _search_connpass_api(keyword='TypeScript', count=3)
print(f'件数: {result.results_returned}/{result.results_available}')
for e in result.events:
    print(f'  - {e.title} | {e.url}')
"
```

## 2. インフラ (infra/)

### セットアップ

```bash
cd infra
npm install
```

### テスト実行

```bash
cd infra
npm test
```

### CDK テンプレート生成 (デプロイなし)

```bash
cd infra
npx cdk synth
```

### AWS デプロイ

```bash
cd infra

# 初回のみ: CDK Bootstrap
npx cdk bootstrap

# デプロイ (全スタック)
npx cdk deploy --all

# 個別スタック
npx cdk deploy ConfeeApiStack
npx cdk deploy ConfeeFrontendStack
```

### デプロイ後の確認

```bash
# API ヘルスチェック
curl https://<API_GATEWAY_URL>/health

# フロントエンド
open https://<CLOUDFRONT_URL>
```

## 3. フロントエンド (frontend/) - 未実装

タスク5で実装予定。

## トラブルシューティング

### `VIRTUAL_ENV` 警告が出る

pyenv 等の仮想環境がアクティブな場合に表示されます。動作に影響はありません。

```
warning: `VIRTUAL_ENV=...` does not match the project environment path `.venv`
```

対処法: `deactivate` で既存の仮想環境を無効化するか、そのまま無視してください。

### connpass API で 403 が返る

`User-Agent` ヘッダーが必須です（ツール側で自動設定済み）。手動で curl テストする場合は:

```bash
curl -H "X-API-Key: your-key" -H "User-Agent: confee/1.0" \
  "https://connpass.com/api/v2/events/?keyword=TypeScript&count=3"
```

### connpass API で 429 が返る

レート制限（1秒1リクエスト）を超過しています。1秒以上間隔を空けて再試行してください。
