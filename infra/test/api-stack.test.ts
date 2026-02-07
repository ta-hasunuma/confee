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
      Timeout: 30,
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
});
