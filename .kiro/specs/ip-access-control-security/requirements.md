# 要件ドキュメント

## はじめに

本機能は、社内向けシステム「confee」のインフラストラクチャに対して、IPアドレスベースのアクセス制御とセキュリティ強化を実装するものである。CloudFrontディストリビューションにはCloudFront Functionを用いたIPフィルタリングを、API Gateway（REST API）にはAWS WAF（REGIONALスコープ、ap-northeast-1）を適用し、指定されたIPアドレスのみからのアクセスを許可するホワイトリスト方式のアクセス制限を導入する。すべてのリソースをap-northeast-1リージョンで管理し、クロスリージョンの複雑性を排除する。

### ホワイトリストIPアドレス

| # | IPアドレス |
|---|-----------|
| 1 | 66.159.192.8 |
| 2 | 66.159.192.9 |
| 3 | 66.159.200.79 |
| 4 | 114.141.123.64 |
| 5 | 114.141.123.65 |
| 6 | 137.83.216.7 |
| 7 | 137.83.216.125 |
| 8 | 208.127.111.180 |

## 要件

### 要件1: AWS WAF IPセットによるIPホワイトリスト管理

**ユーザーストーリー:** インフラ管理者として、許可されたIPアドレスをAWS WAFで一元的に管理したい。それにより、API Gatewayに対して標準的なAWSセキュリティサービスによるアクセス制御を適用できるようにする。

#### 受入基準

1. WHEN システムがデプロイされる THEN AWS WAF IPセットが上記8つのIPアドレス（/32 CIDR表記）を含んで作成されるものとする
2. WHEN WAF IPセットが作成される THEN IPセットのスコープは「REGIONAL」としてap-northeast-1リージョンに設定されるものとする
3. WHEN WAF WebACLが作成される THEN デフォルトアクションはブロック（Block）に設定されるものとする
4. WHEN リクエスト元IPアドレスがIPセットに含まれる THEN WAF WebACLはリクエストを許可（Allow）するものとする
5. WHEN リクエスト元IPアドレスがIPセットに含まれない THEN WAF WebACLはリクエストをブロックするものとする

### 要件2: CloudFrontディストリビューションへのIPベースアクセス制限

**ユーザーストーリー:** インフラ管理者として、CloudFrontディストリビューションに対してIPベースのアクセス制限を実装したい。それにより、許可されたIPアドレスからのみフロントエンドにアクセスできるようにする。

#### 受入基準

1. WHEN CloudFrontディストリビューションがデプロイされる THEN CloudFront Functionが関連付けられ、viewer-requestイベントでIPフィルタリングが実行されるものとする
2. WHEN ホワイトリスト外のIPアドレスからCloudFrontにアクセスする THEN 403 Forbiddenレスポンスが返されるものとする
3. WHEN ホワイトリスト内のIPアドレスからCloudFrontにアクセスする THEN 通常どおりコンテンツが配信されるものとする
4. WHEN CloudFront FunctionのIPホワイトリストが更新される THEN CDKコードの変更とデプロイにより反映可能であるものとする

### 要件3: API GatewayへのWAF適用

**ユーザーストーリー:** インフラ管理者として、API GatewayにWAF WebACLを関連付けたい。それにより、APIエンドポイントが許可されたネットワークからのみ呼び出し可能となるようにする。

#### 受入基準

1. WHEN API Gatewayがデプロイされる THEN WAF WebACL（REGIONALスコープ）がAPI Gatewayステージに関連付けられるものとする
2. WHEN ホワイトリスト外のIPアドレスからAPIリクエストが送信される THEN 403 Forbiddenレスポンスが返されるものとする
3. WHEN ホワイトリスト内のIPアドレスからAPIリクエストが送信される THEN リクエストが正常に処理されるものとする
4. WHEN WAF WebACLがAPI Gatewayに関連付けられる THEN すべてのエンドポイント（/health, /chat）に対してアクセス制限が有効になるものとする

### 要件4: CORS設定の厳格化

**ユーザーストーリー:** セキュリティ管理者として、CORS設定を社内利用に適した設定に厳格化したい。それにより、意図しないオリジンからのAPIアクセスを防止する。

#### 受入基準

1. WHEN API GatewayのCORS設定がデプロイされる THEN 許可オリジンがCloudFrontディストリビューションのドメイン名に限定されるものとする
2. WHEN 許可されていないオリジンからのCORSプリフライトリクエストが送信される THEN 適切なCORSヘッダーが返されず、ブラウザがリクエストをブロックするものとする
3. WHEN Gateway Responsesが返される THEN CORSヘッダーのAccess-Control-Allow-Originが「*」ではなくCloudFrontドメインに設定されるものとする

### 要件5: WAFログ及びモニタリング

**ユーザーストーリー:** セキュリティ管理者として、WAFによるアクセス制御の状況を把握したい。それにより、不正アクセスの試行を検知し、セキュリティインシデントに迅速に対応できるようにする。

#### 受入基準

1. WHEN WAF WebACLがリクエストを評価する THEN CloudWatch メトリクスが記録されるものとする
2. WHEN WAFメトリクスが利用可能になる THEN ブロックされたリクエスト数とAllowされたリクエスト数が確認可能であるものとする

### 要件6: CDKスタック間の依存関係管理

**ユーザーストーリー:** インフラ管理者として、WAFリソースおよびCloudFront Functionが適切なスタック構成で管理されるようにしたい。それにより、既存のスタック構成との整合性を保ちつつ、デプロイの順序を正しく処理する。

#### 受入基準

1. WHEN WAFリソースがデプロイされる THEN WAF WebACL（REGIONALスコープ）はap-northeast-1リージョンに作成されるものとする
2. WHEN CDKスタックがデプロイされる THEN 既存のConfeeFrontendStackおよびConfeeApiStackとの互換性が維持されるものとする
3. WHEN IPアドレスの追加・変更が必要になる THEN CDKコード内のIPリスト定義を変更しデプロイすることで、WAF IPセットとCloudFront Functionの両方に反映可能であるものとする
