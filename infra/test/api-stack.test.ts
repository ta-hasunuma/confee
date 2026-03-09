import * as cdk from "aws-cdk-lib/core";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ConfeeApiStack } from "../lib/api-stack";

describe("ConfeeApiStack", () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new ConfeeApiStack(app, "TestApiStack", {
      agentRuntimeArn: "arn:aws:bedrock:ap-northeast-1:123456789012:agent-runtime/test-id",
    });
    template = Template.fromStack(stack);
  });

  test("Health Lambda関数が作成される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.13",
      Handler: "index.handler",
    });
  });

  test("API Gateway REST APIが作成される", () => {
    template.hasResourceProperties("AWS::ApiGateway::RestApi", {
      Name: "confee-api",
    });
  });

  test("/health GETメソッドが作成される", () => {
    template.hasResourceProperties("AWS::ApiGateway::Method", {
      HttpMethod: "GET",
    });
  });

  test("Chat Lambda関数が作成される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.13",
      Handler: "handler.handler",
      Timeout: 60,
    });
  });

  test("Chat Lambda関数にAGENT_RUNTIME_ARN環境変数が設定される", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Environment: {
        Variables: Match.objectLike({
          AGENT_RUNTIME_ARN: "arn:aws:bedrock:ap-northeast-1:123456789012:agent-runtime/test-id",
        }),
      },
    });
  });

  test("/chat POSTメソッドが作成される", () => {
    template.hasResourceProperties("AWS::ApiGateway::Method", {
      HttpMethod: "POST",
    });
  });

  test("Secrets Managerシークレットが作成される", () => {
    template.hasResourceProperties("AWS::SecretsManager::Secret", {
      Name: "confee/connpass-api-key",
    });
  });

  test("Chat Lambda関数にIAMポリシーが付与される", () => {
    template.hasResourceProperties("AWS::IAM::Policy", {
      PolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({
            Effect: "Allow",
          }),
        ]),
      }),
    });
  });

  test("WAF IPSetが8つのIPアドレス（REGIONAL）で作成される", () => {
    template.hasResourceProperties("AWS::WAFv2::IPSet", {
      Scope: "REGIONAL",
      IPAddressVersion: "IPV4",
      Addresses: Match.arrayWith([
        "66.159.192.8/32",
        "66.159.192.9/32",
        "66.159.200.79/32",
        "114.141.123.64/32",
        "114.141.123.65/32",
        "137.83.216.7/32",
        "137.83.216.125/32",
        "208.127.111.180/32",
      ]),
    });
  });

  test("WAF WebACLのデフォルトアクションがBlockでスコープがREGIONALである", () => {
    template.hasResourceProperties("AWS::WAFv2::WebACL", {
      DefaultAction: { Block: {} },
      Scope: "REGIONAL",
    });
  });

  test("WAF WebACLにIPセット参照のAllowルールが含まれる", () => {
    template.hasResourceProperties("AWS::WAFv2::WebACL", {
      Rules: Match.arrayWith([
        Match.objectLike({
          Name: "AllowWhitelistedIPs",
          Action: { Allow: {} },
          Statement: {
            IPSetReferenceStatement: Match.objectLike({
              Arn: Match.anyValue(),
            }),
          },
        }),
      ]),
    });
  });

  test("WAF WebACLでCloudWatchメトリクスが有効化されている", () => {
    template.hasResourceProperties("AWS::WAFv2::WebACL", {
      VisibilityConfig: {
        CloudWatchMetricsEnabled: true,
        MetricName: "confee-api-waf",
        SampledRequestsEnabled: true,
      },
    });
  });

  test("WAF WebACLがAPI Gatewayに関連付けられる", () => {
    template.resourceCountIs("AWS::WAFv2::WebACLAssociation", 1);
  });
});
