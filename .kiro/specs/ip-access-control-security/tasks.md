# 実装計画

## IP アドレス定数と WAF リソース

- [x] 1. IP アドレスホワイトリスト定数を作成する
  - `infra/lib/config/allowed-ips.ts` を新規作成し、`ALLOWED_IPS` (生 IP 配列) と `ALLOWED_IP_CIDRS` (/32 CIDR 配列) をエクスポートする
  - 8つの IP アドレスを要件ドキュメントの順序で定義する
  - このファイルは後続のタスク 2, 3 で WAF IPSet と CloudFront Function の両方からインポートされる
  - _Requirements: 1.1, 1.2, 6.3_

- [x] 2. WAF IPSet と WebACL を ConfeeApiStack に追加し、テストを書く
  - `infra/lib/api-stack.ts` に `aws-cdk-lib/aws-wafv2` をインポートし、`ALLOWED_IP_CIDRS` を使って `CfnIPSet`（REGIONAL スコープ）を作成する
  - `CfnWebACL`（デフォルトアクション: Block、ルール: IPSet 参照で Allow）を作成し、`visibilityConfig` で CloudWatch メトリクスを有効化する
  - `CfnWebACLAssociation` で WebACL を API Gateway ステージに関連付ける
  - `infra/test/api-stack.test.ts` に WAF IPSet（REGIONAL、8 IP）、WebACL（デフォルト Block）、WebACLAssociation のアサーションテストを追加する
  - テストを実行して全テストがパスすることを確認する
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 6.1_

## CloudFront Function による IP フィルタリング

- [x] 3. CloudFront Function を ConfeeFrontendStack に追加し、テストを書く
  - `infra/lib/frontend-stack.ts` に `ALLOWED_IPS` をインポートし、IP ホワイトリストの JavaScript コードを動的生成する
  - `cloudfront.Function`（runtime: JS_2_0）を作成し、Distribution の `defaultBehavior.functionAssociations` に viewer-request として関連付ける
  - `distributionDomainName` プロパティをスタッククラスの public readonly として公開する（タスク 4 で使用）
  - `infra/test/frontend-stack.test.ts` に CloudFront Function リソースの存在と Distribution への viewer-request 関連付けのアサーションテストを追加する
  - テストを実行して全テストがパスすることを確認する
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.2_

## CORS 厳格化とスタック依存関係

- [ ] 4. CORS 設定を厳格化し、スタック依存関係を更新する
  - `infra/lib/api-stack.ts` の `ConfeeApiStackProps` に `cloudFrontDomainName: string` を追加する
  - `defaultCorsPreflightOptions.allowOrigins` を `Cors.ALL_ORIGINS` から `[https://${props.cloudFrontDomainName}]` に変更する
  - `addGatewayResponse` の `Access-Control-Allow-Origin` ヘッダーを `'*'` から CloudFront ドメインの URL に変更する
  - `infra/bin/infra.ts` のスタック生成順序を変更: `ConfeeFrontendStack` を先に生成し、`distributionDomainName` を `ConfeeApiStack` の props に渡す
  - `infra/test/api-stack.test.ts` の `beforeAll` で `cloudFrontDomainName` のテスト値を props に追加し、既存テストが壊れないことを確認する
  - テストを実行して全テストがパスすることを確認する
  - _Requirements: 4.1, 4.2, 4.3, 6.2_

## 統合検証

- [ ] 5. cdk synth による全スタック統合検証
  - `npx cdk synth` を実行し、全スタック（ConfeeAgentCoreStack、ConfeeFrontendStack、ConfeeApiStack）のテンプレートが正常に生成されることを確認する
  - 生成された CloudFormation テンプレートで WAF リソースが ap-northeast-1 に、CloudFront Function が正しく配置されていることを目視確認する
  - 全テスト (`npm test`) を再実行し、すべてのテストがパスすることを最終確認する
  - _Requirements: 6.1, 6.2, 6.3_
