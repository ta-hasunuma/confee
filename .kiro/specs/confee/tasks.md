# 実装計画

> **方針**: 各タスク完了時にローカル動作確認 → AWS環境デプロイが可能な状態を維持する。「常に動くものが提供できる」インクリメンタルデリバリーを徹底する。

## プロジェクト基盤

- [x] 1. プロジェクト構造 + AWS CDK基盤セットアップ
  - モノレポ構造を作成: `agent/`（Python）、`frontend/`（React）、`infra/`（CDK）
  - `infra/`: AWS CDK (TypeScript) プロジェクトを初期化し、基本スタック構成を定義
  - `infra/`: プレースホルダーLambda（ヘルスチェック `/health` のみ返す）+ API Gateway REST APIスタックを作成
  - `infra/`: S3バケット + CloudFrontディストリビューション + プレースホルダー `index.html`（「confee - 準備中」）のスタックを作成
  - ローカル確認: `cdk synth` でテンプレート生成を検証 → `cdk deploy` でAWSにデプロイし、CloudFront URL でプレースホルダーページ表示、API Gateway `/health` エンドポイント疎通を確認
  - _Requirements: 6.1, 6.2, 6.4_

## connpass API連携

- [x] 2. connpass APIツール実装 + ユニットテスト
  - `agent/`: Python プロジェクトを初期化（`pyproject.toml`、`uv` でパッケージ管理、`strands-agents` / `httpx` 等の依存追加）
  - `agent/tools/search_connpass.py`: Strands `@tool` デコレータを使用した `search_connpass` 関数を実装。connpass API v2（`GET /api/v2/events/`）を呼び出し、keyword, keyword_or, ym, ymd, prefecture, order, count パラメータをサポート。APIキーは環境変数 `CONNPASS_API_KEY` から取得。タイムアウト5秒、レート制限（1秒間隔）を考慮
  - `agent/models.py`: `ConnpassEvent` / `ConnpassSearchResult` dataclass を定義
  - `agent/tests/test_search_connpass.py`: connpass APIレスポンスのモックを使用したユニットテスト（正常系: キーワード検索、0件結果、エラーレスポンス、タイムアウト）
  - ローカル確認: `uv run pytest` で全テスト通過 → 実際のconnpass APIキーを使って手動でツール単体テスト
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3_

## エージェント実装

- [x] 3. Strands Agent構築 + ローカル動作確認
  - `agent/agent.py`: `ConfeeAgent` クラスを実装。Strands `Agent` を生成し、`search_connpass` ツールを登録。Bedrock Claude Sonnet をモデルプロバイダーとして設定
  - `agent/agent.py`: システムプロンプトを定義。カンファレンス情報の構造化出力（名前、日時、場所、概要、おすすめ度、申込期限、申込URL）、おすすめ度の付与、推薦理由の明示、期限切れの処理、日本語応答を指示
  - `agent/main.py`: `BedrockAgentCoreApp` エントリポイントを作成。`@app.entrypoint` で `invoke` 関数を定義し、payload から prompt を取得してエージェントを呼び出す
  - `agent/Dockerfile`: ARM64ベースのコンテナイメージを作成（`uv` でのビルド、ポート8080公開）
  - ローカル確認: `uv run python main.py` でローカルサーバー起動 → `curl -X POST http://localhost:8080/invocations -d '{"prompt":"TypeScriptのカンファレンスある？"}'` で応答確認
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 4. AgentCore Runtimeデプロイ + Lambda Proxy実装
  - `infra/`: ECRリポジトリスタックを追加。エージェントコンテナイメージのビルド＆プッシュをCDKで管理
  - `infra/`: AgentCore Runtime作成スタックを追加（boto3 Custom Resource で `create_agent_runtime` を呼び出し。networkMode: PUBLIC、IAMロール設定）
  - `agent/lambda/handler.py`: Lambda Proxy を実装。API Gatewayリクエストを受け取り、boto3 `bedrock-agentcore` クライアントで `invoke_agent_runtime` を呼び出し。session_id はリクエストボディから取得（未指定時はUUID生成）
  - `infra/`: タスク1のヘルスチェックLambdaを置き換え、Lambda Proxy + API Gateway `POST /chat` エンドポイントを構成。CORS設定、タイムアウト30秒、Secrets Manager からconnpass APIキーをLambda環境変数に注入
  - ローカル確認: Dockerコンテナをローカルビルド＆起動してエージェント動作確認 → `cdk deploy` でAWSにデプロイ → API Gateway `POST /chat` エンドポイントに `curl` で疎通確認
  - _Requirements: 3.1, 3.4, 6.1, 6.3, 8.1, 8.3_

## フロントエンド

- [x] 5. React チャットUI実装 + フロントエンドデプロイ
  - `frontend/`: Vite + React + TypeScript + Tailwind CSS プロジェクトを初期化
  - `frontend/src/types.ts`: `ChatMessage`、`ConnpassEvent`、`SuggestedPrompt` 型定義を作成
  - `frontend/src/api/chat.ts`: `POST /chat` APIクライアントを実装。API Gateway の URL は環境変数 `VITE_API_URL` で管理。session_id 生成・管理ロジックを含む
  - `frontend/src/components/`: `App`、`ChatContainer`、`MessageList`、`MessageBubble`、`ChatInput`、`LoadingIndicator` コンポーネントを実装。会話履歴の状態管理、ローディング表示、Markdown応答のレンダリング
  - `infra/`: S3バケットへのフロントエンドビルド成果物デプロイをCDKで構成（`BucketDeployment`）。CloudFront のキャッシュ無効化設定
  - ローカル確認: `npm run dev` でローカル開発サーバー起動 → タスク4のAPI GatewayエンドポイントへのAPI呼び出しでチャット送受信確認 → `npm run build && cdk deploy` でAWSデプロイ → CloudFront URLでE2E動作確認
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.2_

- [ ] 6. おすすめプロンプト表示 + エラーハンドリング強化
  - `frontend/src/data/suggestedPrompts.ts`: おすすめプロンプトデータを定義。キーワード検索例（「TypeScriptのカンファレンスある？」「今月開催のLT会を教えて」等）とあいまい質問例（「面白そうなカンファレンスを見つけてきて」「おすすめの勉強会ある？」等）を含む
  - `frontend/src/components/SuggestedPrompts.tsx`: クリック可能なチップ形式のおすすめプロンプトコンポーネントを実装。クリック時にクエリとして自動送信。会話開始後は非表示に遷移
  - `frontend/src/components/ChatContainer.tsx`: エラー表示を追加。API接続エラー、タイムアウト、503エラー時にフレンドリーなメッセージを表示。セッションタイムアウト時の自動リカバリ（新規session_id生成）
  - `agent/agent.py`: システムプロンプトを改善。構造化出力の一貫性向上、期限切れイベントの処理、おすすめ度の基準明確化
  - ローカル確認: フロントエンドでおすすめプロンプト表示→クリック→検索結果表示の一連のフローを確認 → `cdk deploy` でAWSデプロイ → CloudFront URLで最終MVP動作確認
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 3.2, 3.3, 6.3, 8.1_
