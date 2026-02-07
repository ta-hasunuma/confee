# プロジェクト構造

## ルートディレクトリ

```
confee/
├── agent/              # Python - AI エージェント (Strands Agent + connpass ツール)
├── frontend/           # TypeScript/React - チャット UI (SPA)
├── infra/              # TypeScript - AWS CDK インフラ定義
├── docs/               # プロジェクトドキュメント
├── .kiro/              # Kiro Spec-Driven Development 設定・仕様
├── .claude/            # Claude Code 設定
├── .env                # 環境変数 (gitignore 対象)
├── .gitignore
└── CLAUDE.md           # Claude Code プロジェクト指示
```

## agent/ — AI エージェント

```
agent/
├── src/confee_agent/
│   ├── __init__.py
│   ├── agent.py            # ConfeeAgent クラス (Strands Agent 構成・システムプロンプト)
│   ├── main.py             # BedrockAgentCoreApp エントリーポイント
│   ├── models.py           # データクラス (ConnpassEvent, ConnpassSearchResult)
│   ├── mock_events.py      # モックイベントデータ (API キー未設定時のフォールバック)
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search_connpass.py  # @tool connpass 検索ツール
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_agent.py
│       ├── test_main.py
│       └── test_search_connpass.py
├── lambda/
│   ├── handler.py          # Lambda ハンドラー (API Gateway → AgentCore プロキシ)
│   ├── requirements.txt    # Lambda 依存関係 (boto3)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_handler.py
├── Dockerfile              # ARM64 コンテナイメージ定義
├── pyproject.toml          # Python プロジェクト設定 (uv)
└── uv.lock                 # 依存関係ロックファイル
```

### エージェントのコード構成パターン

- `agent.py`: エージェント初期化 (モデル設定・システムプロンプト・ツール登録)
- `main.py`: AgentCore ランタイムのエントリーポイント (遅延初期化パターン)
- `tools/`: Strands `@tool` デコレータで定義されたツール関数
- `models.py`: `@dataclass` によるデータ型定義
- `lambda/handler.py`: API Gateway イベントを受けて AgentCore Runtime を呼び出すプロキシ

## frontend/ — React チャット UI

```
frontend/
├── src/
│   ├── main.tsx            # React DOM レンダリングエントリーポイント
│   ├── App.tsx             # ルートコンポーネント (ヘッダー・セッション管理)
│   ├── index.css           # Tailwind CSS 設定・カスタムカフェテーマカラー
│   ├── types.ts            # TypeScript 型定義 (ChatMessage, SuggestedPrompt)
│   ├── api/
│   │   └── chat.ts         # API クライアント (POST /chat)
│   ├── components/
│   │   ├── ChatContainer.tsx     # チャットロジック・状態管理
│   │   ├── MessageList.tsx       # メッセージ一覧表示 + オートスクロール
│   │   ├── MessageBubble.tsx     # 個別メッセージ (Markdown レンダリング)
│   │   ├── ChatInput.tsx         # テキスト入力フォーム
│   │   ├── SuggestedPrompts.tsx  # おすすめプロンプトチップ
│   │   ├── LoadingIndicator.tsx  # ローディングアニメーション
│   │   └── __tests__/           # コンポーネントテスト
│   ├── data/
│   │   └── suggestedPrompts.ts  # おすすめプロンプトデータ
│   └── test/
│       └── setup.ts             # Vitest セットアップ
├── index.html              # HTML エントリーポイント (lang="ja")
├── vite.config.ts          # Vite + Tailwind + Vitest 設定
├── tsconfig.json           # TypeScript 設定 (参照用)
├── tsconfig.app.json       # アプリケーション TypeScript 設定 (strict)
├── tsconfig.node.json      # Node.js ユーティリティ TypeScript 設定
├── eslint.config.js        # ESLint 設定
├── package.json
└── .env                    # VITE_API_URL 環境変数
```

### フロントエンドのコード構成パターン

- `components/`: 各コンポーネントは単一責任。コンテナコンポーネント (`ChatContainer`) がロジックを集約
- `api/`: API クライアントを分離。`ChatApiError` カスタムエラークラスでエラーハンドリング
- `data/`: 静的データ (おすすめプロンプト) を分離
- `types.ts`: 共有型定義を一箇所に集約
- スタイリング: Tailwind ユーティリティクラスをインラインで使用。カスタムテーマは `index.css` で定義

## infra/ — AWS CDK インフラ

```
infra/
├── bin/
│   └── infra.ts            # CDK アプリケーションエントリーポイント
├── lib/
│   ├── agentcore-stack.ts  # AgentCore Runtime スタック (ECR, IAM, Custom Resource)
│   ├── api-stack.ts        # API スタック (Lambda, API Gateway, Secrets Manager)
│   └── frontend-stack.ts   # フロントエンドスタック (S3, CloudFront)
├── lambda/
│   ├── health/
│   │   └── index.py        # ヘルスチェック Lambda
│   └── agentcore-custom-resource/
│       └── index.py        # AgentCore Runtime 管理 Custom Resource
├── test/
│   ├── agentcore-stack.test.ts
│   ├── api-stack.test.ts
│   └── frontend-stack.test.ts
├── cdk.json                # CDK 設定
├── package.json
└── tsconfig.json
```

### インフラのコード構成パターン

- `lib/`: スタックごとに 1 ファイル。リソースの責務で分割
- `lambda/`: CDK から参照される Lambda 関数コード (Python)
- スタック間の依存: `agentRuntimeArn` を ApiStack にプロパティとして渡す
- Custom Resource パターン: 非同期リソース (AgentCore Runtime) の管理

## ファイル命名規則

| ディレクトリ | 規則 | 例 |
|------------|------|-----|
| agent/src/ | snake_case | `search_connpass.py`, `mock_events.py` |
| agent/tests/ | `test_` プレフィックス + snake_case | `test_search_connpass.py` |
| frontend/src/ | PascalCase (コンポーネント), camelCase (ユーティリティ) | `ChatContainer.tsx`, `chat.ts` |
| frontend/tests/ | `.test.tsx` サフィックス | `ChatContainer.test.tsx` |
| infra/lib/ | kebab-case | `agentcore-stack.ts`, `api-stack.ts` |
| infra/test/ | `.test.ts` サフィックス | `api-stack.test.ts` |

## 主要なアーキテクチャ原則

- **モノレポ構成**: `agent/`, `frontend/`, `infra/` を独立したサブプロジェクトとして管理。各ディレクトリが独自のパッケージ管理を持つ
- **Lambda Proxy パターン**: API Gateway → Lambda → AgentCore Runtime の間接呼び出し。SigV4 認証を Lambda 側で処理
- **遅延初期化**: エージェントインスタンスは初回呼び出し時に作成し、コンテナ内で再利用
- **モックフォールバック**: connpass API キー未設定時は自動的にモックデータに切り替え。開発・テスト時の外部依存を排除
- **SPA ルーティング対応**: CloudFront で 403/404 を `index.html` にリダイレクト
